"""
High-Concurrency Caching Layer (L1 In-Memory LRU + Pre-Encoded GZip + Optional L2 Redis)
Features:
- Sub-10 microsecond L1 RAM hits directly from asyncio routes (zero DB checkout)
- Pre-validated, pre-serialized, pre-compressed HTTP payloads built once per TTL
- Single-flight per-key locking to eliminate cache-stampede / thundering-herd DB crashes
- Bounded LRU eviction to cap RAM under arbitrary query keys
- Optional Redis L2 distribution for multi-worker / multi-container horizontal scaling
"""
import gzip
import json
import threading
import time
from collections import OrderedDict
from typing import Any, Callable, Dict, Optional, Tuple
from fastapi import Response
from starlette.concurrency import run_in_threadpool

from app.core.config import settings

try:
    import redis  # type: ignore
except ImportError:
    redis = None


class PreEncodedPayload:
    """Immutable pre-serialized JSON + pre-compressed GZip payload cached in L1 RAM."""

    __slots__ = ("data", "raw_bytes", "gzip_bytes")

    def __init__(self, data: Any, raw_bytes: Optional[bytes] = None):
        self.data = data
        if raw_bytes is not None:
            self.raw_bytes = raw_bytes
        else:
            self.raw_bytes = json.dumps(data, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
        self.gzip_bytes = gzip.compress(self.raw_bytes, compresslevel=6) if len(self.raw_bytes) >= 512 else None

    def to_response(self, accept_encoding: Optional[str] = None) -> Response:
        if self.gzip_bytes is not None and accept_encoding and "gzip" in accept_encoding.lower():
            return Response(
                content=self.gzip_bytes,
                media_type="application/json",
                headers={"Content-Encoding": "gzip", "Vary": "Accept-Encoding"},
            )
        return Response(content=self.raw_bytes, media_type="application/json")


class HybridCacheService:
    """Thread-safe two-level TTL cache with single-flight stampede protection."""

    def __init__(self, max_entries: int = 2048):
        self._max_entries = max(128, max_entries)
        self._l1: OrderedDict[str, Tuple[float, Any]] = OrderedDict()
        self._l1_lock = threading.RLock()
        self._locks_guard = threading.Lock()
        self._key_locks: Dict[str, threading.Lock] = {}

        # Metrics
        self._hits_l1 = 0
        self._hits_l2 = 0
        self._misses = 0
        self._singleflight_waits = 0
        self._invalidations = 0

        # Optional L2 Redis client
        self._redis = None
        if settings.REDIS_URL and redis is not None:
            try:
                self._redis = redis.Redis.from_url(
                    settings.REDIS_URL,
                    decode_responses=True,
                    socket_connect_timeout=1.5,
                    socket_timeout=1.5,
                    max_connections=64,
                )
                self._redis.ping()
            except Exception:
                self._redis = None

    def _get_key_lock(self, key: str) -> threading.Lock:
        with self._locks_guard:
            if len(self._key_locks) > self._max_entries * 2:
                self._key_locks = {k: v for k, v in self._key_locks.items() if v.locked()}
            lock = self._key_locks.get(key)
            if lock is None:
                lock = threading.Lock()
                self._key_locks[key] = lock
            return lock

    def get_l1(self, key: str) -> Optional[Any]:
        """Fast RAM lookup (returns None if missing or expired)."""
        now = time.monotonic()
        with self._l1_lock:
            entry = self._l1.get(key)
            if entry is None:
                return None
            expires_at, value = entry
            if now >= expires_at:
                del self._l1[key]
                return None
            self._l1.move_to_end(key)
            self._hits_l1 += 1
            return value

    def set_l1(self, key: str, value: Any, ttl: int) -> None:
        """Stores a value in bounded L1 RAM cache."""
        if ttl <= 0:
            return
        expires_at = time.monotonic() + ttl
        with self._l1_lock:
            self._l1[key] = (expires_at, value)
            self._l1.move_to_end(key)
            while len(self._l1) > self._max_entries:
                self._l1.popitem(last=False)

    def _get_l2(self, key: str) -> Optional[Any]:
        if self._redis is None:
            return None
        try:
            raw = self._redis.get(f"tip:{key}")
            if raw is None:
                return None
            self._hits_l2 += 1
            return json.loads(raw)
        except Exception:
            return None

    def _set_l2(self, key: str, value: Any, ttl: int) -> None:
        if self._redis is None or ttl <= 0:
            return
        try:
            payload = json.dumps(value)
            self._redis.setex(f"tip:{key}", ttl, payload)
        except Exception:
            pass

    def get_or_compute(
        self,
        key: str,
        ttl: int,
        loader: Callable[[], Any],
        should_cache: Optional[Callable[[Any], bool]] = None,
    ) -> Any:
        """Synchronously returns cached value or computes once per key under single-flight lock."""
        cached = self.get_l1(key)
        if cached is not None:
            return cached

        key_lock = self._get_key_lock(key)
        if key_lock.locked():
            self._singleflight_waits += 1

        with key_lock:
            cached = self.get_l1(key)
            if cached is not None:
                return cached

            l2_val = self._get_l2(key)
            if l2_val is not None:
                self.set_l1(key, l2_val, min(ttl, 60))
                return l2_val

            self._misses += 1
            value = loader()

            cache_ok = should_cache(value) if should_cache is not None else (value is not None)
            if cache_ok and ttl > 0:
                self.set_l1(key, value, ttl)
                self._set_l2(key, value, ttl)

            return value

    async def get_or_compute_async(
        self,
        key: str,
        ttl: int,
        loader: Callable[[], Any],
        should_cache: Optional[Callable[[Any], bool]] = None,
    ) -> Any:
        """Event-loop zero-hop fast-path on L1 hit; dispatches to threadpool only on miss."""
        cached = self.get_l1(key)
        if cached is not None:
            return cached
        return await run_in_threadpool(self.get_or_compute, key, ttl, loader, should_cache)

    async def get_or_encode_async(
        self,
        encoded_key: str,
        ttl: int,
        builder: Callable[[], Tuple[Any, Optional[bytes]]],
        should_cache: Optional[Callable[[Any], bool]] = None,
    ) -> PreEncodedPayload:
        """Returns pre-serialized + pre-gzipped HTTP payload directly from L1 RAM."""
        cached = self.get_l1(encoded_key)
        if isinstance(cached, PreEncodedPayload):
            return cached

        def _compute_encoded():
            data, raw_bytes = builder()
            payload = PreEncodedPayload(data, raw_bytes)
            return payload

        def _build_under_lock():
            existing = self.get_l1(encoded_key)
            if isinstance(existing, PreEncodedPayload):
                return existing
            self._misses += 1
            payload = _compute_encoded()
            cache_ok = should_cache(payload.data) if should_cache is not None else bool(payload.data)
            if cache_ok and ttl > 0:
                self.set_l1(encoded_key, payload, ttl)
            return payload

        key_lock = self._get_key_lock(encoded_key)
        return await run_in_threadpool(self._run_locked, key_lock, _build_under_lock)

    @staticmethod
    def _run_locked(lock: threading.Lock, fn: Callable[[], Any]) -> Any:
        with lock:
            return fn()

    def invalidate_prefix(self, prefix: str) -> None:
        with self._l1_lock:
            keys_to_delete = [k for k in self._l1.keys() if k.startswith(prefix)]
            for k in keys_to_delete:
                del self._l1[k]
            self._invalidations += len(keys_to_delete)

        if self._redis is not None:
            try:
                for k in self._redis.scan_iter(match=f"tip:{prefix}*", count=200):
                    self._redis.delete(k)
            except Exception:
                pass

    def invalidate_all(self) -> None:
        with self._l1_lock:
            self._invalidations += len(self._l1)
            self._l1.clear()

        if self._redis is not None:
            try:
                for k in self._redis.scan_iter(match="tip:*", count=500):
                    self._redis.delete(k)
            except Exception:
                pass

    def stats(self) -> Dict[str, Any]:
        with self._l1_lock:
            entries = len(self._l1)
        total_lookups = self._hits_l1 + self._hits_l2 + self._misses
        hit_ratio = round(((self._hits_l1 + self._hits_l2) / total_lookups) * 100.0, 2) if total_lookups else 100.0
        return {
            "backend": "redis+l1" if self._redis is not None else "memory-l1",
            "l1_entries": entries,
            "l1_max_entries": self._max_entries,
            "hits_l1": self._hits_l1,
            "hits_l2_redis": self._hits_l2,
            "misses": self._misses,
            "singleflight_coalesced": self._singleflight_waits,
            "hit_ratio_percent": hit_ratio,
        }


# Global cache singleton
cache_service = HybridCacheService(max_entries=settings.CACHE_MAX_ENTRIES)


def dump_validated_json(adapter: Any, data: Any) -> bytes:
    """Validates data once against a Pydantic TypeAdapter and emits compact JSON bytes without warnings."""
    validated = adapter.validate_python(data)
    return adapter.dump_json(validated)
