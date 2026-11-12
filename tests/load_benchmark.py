"""
High-Concurrency Keep-Alive Load Benchmark for Tennis Intelligence Platform
Uses dedicated keep-alive HTTP/1.1 connections per worker thread (avoiding client-side
single-loop pool lock distortion) to measure true origin throughput (req/s), P50/P95/P99
latency, error rate, and L1/L2 cache hit ratio against live FastAPI/Uvicorn.
"""
import argparse
from concurrent.futures import ThreadPoolExecutor
import http.client
import json
import math
import sys
import time
from typing import Dict, List, Tuple
from urllib.parse import urlparse

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ENDPOINTS = [
    "/api/v1/analytics/kpis",
    "/api/v1/players?page=1&limit=10",
    "/api/v1/players/sr:competitor:104253",
    "/api/v1/rankings/top?limit=5",
    "/api/v1/analytics/compare?player_a=sr:competitor:104253&player_b=sr:competitor:119842",
    "/api/v1/competitions",
    "/api/v1/venues",
]


def _percentile(sorted_vals: List[float], pct: float) -> float:
    if not sorted_vals:
        return 0.0
    idx = (len(sorted_vals) - 1) * (pct / 100.0)
    lo = math.floor(idx)
    hi = math.ceil(idx)
    if lo == hi:
        return sorted_vals[lo]
    return sorted_vals[lo] * (hi - idx) + sorted_vals[hi] * (idx - lo)


def _worker_task(
    host: str,
    port: int,
    worker_id: int,
    request_count: int,
) -> Tuple[List[float], int, Dict[int, int]]:
    latencies: List[float] = []
    errors = 0
    statuses: Dict[int, int] = {}
    conn = http.client.HTTPConnection(host, port, timeout=15)

    try:
        for i in range(request_count):
            ep = ENDPOINTS[(worker_id + i) % len(ENDPOINTS)]
            sim_ip = f"10.{(worker_id % 250) + 1}.{(i // 250) % 250}.{(i % 250) + 1}"
            t0 = time.perf_counter()
            try:
                conn.request(
                    "GET",
                    ep,
                    headers={
                        "Accept-Encoding": "gzip",
                        "Connection": "keep-alive",
                        "X-Forwarded-For": sim_ip,
                    },
                )
                resp = conn.getresponse()
                resp.read()
                elapsed = (time.perf_counter() - t0) * 1000.0
                statuses[resp.status] = statuses.get(resp.status, 0) + 1
                if resp.status == 200:
                    latencies.append(elapsed)
                else:
                    errors += 1
            except Exception:
                errors += 1
                conn.close()
                conn = http.client.HTTPConnection(host, port, timeout=15)
    finally:
        conn.close()

    return latencies, errors, statuses


def run_benchmark(base_url: str, concurrency: int, total_requests: int) -> int:
    parsed = urlparse(base_url)
    host = parsed.hostname or "127.0.0.1"
    port = parsed.port or (443 if parsed.scheme == "https" else 80)

    print("=" * 82)
    print("   [TIP] HIGH-CONCURRENCY KEEP-ALIVE ORIGIN BENCHMARK")
    print("=" * 82)
    print(f"Target Origin : http://{host}:{port}")
    print(f"Concurrency   : {concurrency} parallel keep-alive clients")
    print(f"Total Requests: {total_requests} across {len(ENDPOINTS)} endpoints\n")

    # Warm-up pass across all endpoints before timing
    warm_conn = http.client.HTTPConnection(host, port, timeout=10)
    try:
        for ep in ENDPOINTS:
            warm_conn.request("GET", ep, headers={"Accept-Encoding": "gzip", "Connection": "keep-alive"})
            r = warm_conn.getresponse()
            r.read()
            if r.status != 200:
                print(f"[ERROR] Warm-up failed on {ep}: HTTP {r.status}")
                return 1
    finally:
        warm_conn.close()

    per_worker = total_requests // concurrency
    remainder = total_requests % concurrency
    counts = [per_worker + (1 if w < remainder else 0) for w in range(concurrency)]

    t_start = time.perf_counter()
    with ThreadPoolExecutor(max_workers=concurrency) as pool:
        results = list(
            pool.map(
                lambda args: _worker_task(host, port, args[0], args[1]),
                enumerate(counts),
            )
        )
    total_sec = time.perf_counter() - t_start

    latencies_ms: List[float] = []
    errors = 0
    status_counts: Dict[int, int] = {}
    for w_lats, w_errs, w_stats in results:
        latencies_ms.extend(w_lats)
        errors += w_errs
        for code, cnt in w_stats.items():
            status_counts[code] = status_counts.get(code, 0) + cnt

    cache_stats = {}
    try:
        stat_conn = http.client.HTTPConnection(host, port, timeout=5)
        stat_conn.request("GET", "/api/v1/admin/performance")
        sr = stat_conn.getresponse()
        body = sr.read()
        if sr.status == 200:
            cache_stats = json.loads(body.decode("utf-8")).get("cache", {})
        stat_conn.close()
    except Exception:
        pass

    latencies_ms.sort()
    ok_count = len(latencies_ms)
    rps = total_requests / total_sec if total_sec > 0 else 0.0

    print(f"Completed     : {ok_count}/{total_requests} succeeded | Errors: {errors}")
    print(f"Status Codes  : {status_counts}")
    print(f"Elapsed Time  : {total_sec:.3f} s")
    print(f"Throughput    : {rps:,.1f} req/sec (1 local Uvicorn worker)")
    if latencies_ms:
        print(f"Latency P50   : {_percentile(latencies_ms, 50):.2f} ms")
        print(f"Latency P95   : {_percentile(latencies_ms, 95):.2f} ms")
        print(f"Latency P99   : {_percentile(latencies_ms, 99):.2f} ms")
        print(f"Latency Max   : {latencies_ms[-1]:.2f} ms")
    if cache_stats:
        print(
            f"Cache Telemetry: backend={cache_stats.get('backend')} | "
            f"hit_ratio={cache_stats.get('hit_ratio_percent')}% | "
            f"l1_hits={cache_stats.get('hits_l1')} | misses={cache_stats.get('misses')}"
        )
    print("=" * 82)
    return 0 if errors == 0 else 1


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run concurrency benchmark against TIP API")
    parser.add_argument("--url", default="http://127.0.0.1:8000", help="Base API URL")
    parser.add_argument("--concurrency", type=int, default=50, help="Concurrent keep-alive clients")
    parser.add_argument("--requests", type=int, default=5000, help="Total requests to issue")
    args = parser.parse_args()
    raise SystemExit(run_benchmark(args.url, args.concurrency, args.requests))
