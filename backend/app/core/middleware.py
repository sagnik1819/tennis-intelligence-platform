"""
High-Concurrency Pure ASGI Middleware:
1. Tiered Rate Limiting (Protects Origin & Auth/OTP against abuse and traffic bursts)
2. Edge CDN Cache-Control & Vary Injection (Enables Vercel/Cloudflare/Nginx to serve 95%+ reads at edge)
3. Zero-buffering Response Latency Telemetry (X-Response-Time-Ms)
"""
import json
import math
import threading
import time
from typing import Any, Dict, Tuple
from starlette.concurrency import run_in_threadpool
from starlette.datastructures import MutableHeaders
from starlette.types import ASGIApp, Message, Receive, Scope, Send

from app.core.cache import cache_service
from app.core.config import settings

PUBLIC_CACHEABLE_PREFIXES = (
    "/api/v1/players",
    "/api/v1/rankings",
    "/api/v1/competitions",
    "/api/v1/venues",
    "/api/v1/analytics",
    "/api/v1/auth/providers",
)

PRIVATE_NO_STORE_PREFIXES = (
    "/api/v1/auth",
    "/api/v1/workspace",
    "/api/v1/assistant",
    "/api/v1/admin",
)


class InMemoryRateLimiter:
    """Bounded thread-safe sliding-window approximation rate limiter."""

    def __init__(self, max_keys: int = 50000):
        self._max_keys = max_keys
        self._lock = threading.Lock()
        # key -> (window_id, prev_count, curr_count)
        self._buckets: Dict[str, Tuple[int, int, int]] = {}

    def check(self, key: str, limit: int, window_seconds: int = 60) -> Tuple[bool, int, int]:
        now = time.time()
        window_id = int(now // window_seconds)
        elapsed_ratio = (now % window_seconds) / window_seconds
        reset_after = max(1, int(math.ceil(window_seconds - (now % window_seconds))))

        with self._lock:
            if len(self._buckets) > self._max_keys:
                # Evict stale entries older than previous window
                stale_cutoff = window_id - 1
                self._buckets = {
                    k: v for k, v in self._buckets.items() if v[0] >= stale_cutoff
                }
                if len(self._buckets) > self._max_keys:
                    self._buckets.clear()

            entry = self._buckets.get(key)
            if entry is None:
                prev_count, curr_count = 0, 0
            else:
                stored_win, stored_prev, stored_curr = entry
                if stored_win == window_id:
                    prev_count, curr_count = stored_prev, stored_curr
                elif stored_win == window_id - 1:
                    prev_count, curr_count = stored_curr, 0
                else:
                    prev_count, curr_count = 0, 0

            estimated = prev_count * (1.0 - elapsed_ratio) + curr_count
            if estimated >= limit:
                return False, 0, reset_after

            curr_count += 1
            self._buckets[key] = (window_id, prev_count, curr_count)
            remaining = max(0, int(limit - (prev_count * (1.0 - elapsed_ratio) + curr_count)))
            return True, remaining, reset_after


local_rate_limiter = InMemoryRateLimiter()


class TrafficControlMiddleware:
    """Pure ASGI middleware avoiding BaseHTTPMiddleware buffering overhead."""

    def __init__(self, app: ASGIApp):
        self.app = app

    @staticmethod
    def _extract_client_ip(scope: Scope) -> str:
        if settings.TRUST_PROXY_HEADERS:
            for k, v in scope.get("headers", []):
                if k == b"x-forwarded-for":
                    ip = v.decode("latin1").split(",")[0].strip()
                    if ip:
                        return ip
                elif k == b"x-real-ip":
                    ip = v.decode("latin1").strip()
                    if ip:
                        return ip
        client = scope.get("client")
        return client[0] if client else "unknown"

    @staticmethod
    def _classify_bucket(method: str, path: str) -> Tuple[str, int]:
        if path.startswith("/api/v1/auth") and not (
            method in ("GET", "HEAD") and path in ("/api/v1/auth/providers", "/api/v1/auth/me")
        ):
            return "auth", max(1, settings.RATE_LIMIT_AUTH_PER_MIN)
        if path.startswith("/api/v1/assistant/chat"):
            return "chat", max(1, settings.RATE_LIMIT_CHAT_PER_MIN)
        return "read", max(1, settings.RATE_LIMIT_READ_PER_MIN)

    @staticmethod
    def _check_redis_limit(redis_client: Any, key: str, limit: int, window_seconds: int = 60) -> Tuple[bool, int, int]:
        now = time.time()
        window_id = int(now // window_seconds)
        reset_after = max(1, int(math.ceil(window_seconds - (now % window_seconds))))
        r_key = f"tip:rl:{key}:{window_id}"
        pipe = redis_client.pipeline()
        pipe.incr(r_key, 1)
        pipe.expire(r_key, window_seconds * 2)
        count, _ = pipe.execute()
        allowed = int(count) <= limit
        remaining = max(0, limit - int(count))
        return allowed, remaining, reset_after

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        method = scope.get("method", "GET").upper()
        path = scope.get("path", "/")

        if method == "OPTIONS":
            await self.app(scope, receive, send)
            return

        start = time.perf_counter()
        headers_raw = scope.get("headers", [])
        has_auth_header = any(k == b"authorization" for k, _ in headers_raw)

        limit = settings.RATE_LIMIT_READ_PER_MIN
        remaining = limit
        reset_after = 60

        if settings.RATE_LIMIT_ENABLED and path.startswith("/api/"):
            client_ip = self._extract_client_ip(scope)
            bucket, limit = self._classify_bucket(method, path)
            rl_key = f"{bucket}:{client_ip}"

            if cache_service._redis is not None:
                try:
                    allowed, remaining, reset_after = await run_in_threadpool(
                        self._check_redis_limit, cache_service._redis, rl_key, limit
                    )
                except Exception:
                    allowed, remaining, reset_after = local_rate_limiter.check(rl_key, limit)
            else:
                allowed, remaining, reset_after = local_rate_limiter.check(rl_key, limit)

            if not allowed:
                body = json.dumps({
                    "detail": f"Rate limit exceeded ({limit} req/min for {bucket}). Please retry after {reset_after}s."
                }).encode("utf-8")
                await send({
                    "type": "http.response.start",
                    "status": 429,
                    "headers": [
                        (b"content-type", b"application/json"),
                        (b"content-length", str(len(body)).encode("ascii")),
                        (b"retry-after", str(reset_after).encode("ascii")),
                        (b"x-ratelimit-limit", str(limit).encode("ascii")),
                        (b"x-ratelimit-remaining", b"0"),
                        (b"x-ratelimit-reset", str(reset_after).encode("ascii")),
                        (b"cache-control", b"no-store"),
                    ],
                })
                await send({"type": "http.response.body", "body": body})
                return

        async def send_wrapper(message: Message) -> None:
            if message["type"] == "http.response.start":
                status_code = message.get("status", 200)
                headers = MutableHeaders(scope=message)

                elapsed_ms = (time.perf_counter() - start) * 1000.0
                headers["x-response-time-ms"] = f"{elapsed_ms:.2f}"

                if settings.RATE_LIMIT_ENABLED and path.startswith("/api/"):
                    headers["x-ratelimit-limit"] = str(limit)
                    headers["x-ratelimit-remaining"] = str(remaining)
                    headers["x-ratelimit-reset"] = str(reset_after)

                if "cache-control" not in headers:
                    is_public_cacheable = (
                        method in ("GET", "HEAD")
                        and status_code == 200
                        and not has_auth_header
                        and path.startswith(PUBLIC_CACHEABLE_PREFIXES)
                    )
                    if is_public_cacheable:
                        headers["cache-control"] = (
                            f"public, max-age={settings.CDN_MAX_AGE}, "
                            f"s-maxage={settings.CDN_S_MAXAGE}, stale-while-revalidate=300"
                        )
                        headers.add_vary_header("Authorization")
                    elif method not in ("GET", "HEAD") or has_auth_header or path.startswith(PRIVATE_NO_STORE_PREFIXES):
                        headers["cache-control"] = "no-store, private"

            await send(message)

        await self.app(scope, receive, send_wrapper)
