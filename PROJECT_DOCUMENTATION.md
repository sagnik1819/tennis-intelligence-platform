# Tennis Intelligence Platform (TIP) — Complete Code & File Documentation

> **Who this guide is for:** B.Tech IT teammates, code reviewers, capstone evaluators, and new contributors.  
> **What is inside:** An easy-to-read explanation of **every single file in the repository** — what job it performs, how it works step by step, and what every class, function, API route, schema, and React component does.

---

## Table of Contents

1. [How the Whole Project Works (Big Picture)](#1-how-the-whole-project-works-big-picture)
2. [End-to-End System Flows](#2-end-to-end-system-flows)
3. [Part 1 — Root, Launchers, DevOps, Deployment & Tests](#3-part-1--root-launchers-devops-deployment--tests)
4. [Part 2 — Module 1 Foundation (OOP & JSON Reader)](#4-part-2--module-1-foundation-oop--json-reader)
5. [Part 3 — Data Engineering Pipeline & Staged Data](#5-part-3--data-engineering-pipeline--staged-data)
6. [Part 4 — SQL Schema, Seeder & 20 Analytical Queries](#6-part-4--sql-schema-seeder--20-analytical-queries)
7. [Part 5 — Machine Learning Clustering & Trait Engine](#7-part-5--machine-learning-clustering--trait-engine)
8. [Part 6 — FastAPI Backend (Core, DB, Models, Services, Routes)](#8-part-6--fastapi-backend-core-db-models-services-routes)
9. [Part 7 — React Frontend (Config, API Client, Layout, Components, Pages)](#9-part-7--react-frontend-config-api-client-layout-components-pages)

---

## 1. How the Whole Project Works (Big Picture)

The **Tennis Intelligence Platform (TIP)** turns raw tennis tournament, venue, and doubles ranking JSON feeds into an interactive analytics SaaS web app.

```
[SportRadar API or Sample JSON]
        │
        ▼  (data-engineering/extraction + transformation + validation)
[Cleaned 3NF CSV Files] ──▶ [data_quality_report.json]
        │
        ▼  (sql/seed_database.py)
[SQLite WAL (Local) / Neon PostgreSQL (Production)]
        │
        ├──▶ [machine-learning/models/cluster_engine.py] (K-Means + 5-Axis Radar Traits)
        │
        ▼  (backend/app/services + L1 RAM / L2 Redis Cache + Pre-Encoded GZip)
[FastAPI REST API (/api/v1/*) + TrafficControlMiddleware]
        │
        ▼  (frontend/src/services/api.js via Axios)
[React 18 + Tailwind CSS + Recharts Dashboard]
```

### Folder Responsibility Summary

| Folder | Role | Main Tech |
|---|---|---|
| `module1-foundation/` | Starter OOP models & CLI leaderboard parser | Python `dataclasses`, `json` |
| `data-engineering/` | Fetches SportRadar JSON, cleans into 6 relational tables, checks quality | `urllib`, `pandas`, `pydantic` |
| `sql/` | PostgreSQL DDL schema, 20 analytical SQL queries, automated DB seeder | SQL, `SQLAlchemy`, `pandas` |
| `machine-learning/` | Clusters players into 3 tiers & computes 5 radar traits + similar players | `numpy`, `scikit-learn` (`KMeans`) |
| `backend/` | High-concurrency REST API, JWT auth, Gmail OTP, Google OAuth, SMS OTP, AI chat, L1/L2 cache | `FastAPI`, `Uvicorn`, `SQLAlchemy`, `Redis`, `bcrypt`, `PyJWT` |
| `frontend/` | Interactive dark-mode SaaS dashboard, charts, auth screens, CSV export | `React 18`, `Vite`, `Tailwind CSS`, `Recharts`, `Axios` |
| `tests/` | Multi-threaded keep-alive load benchmark for concurrency testing | `http.client`, `ThreadPoolExecutor` |
| `.vscode/`, `.github/` | VS Code run tasks/debugger & GitHub Actions CI pipeline | JSON, YAML |

---

## 2. End-to-End System Flows

### A. Data Ingestion Flow (JSON -> SQL -> Cache)
1. `SportRadarClient` downloads JSON from SportRadar API (or loads `data-engineering/sample_data/*.json` if the API key is missing/rate-limited).
2. `DataTransformer` normalizes nested JSON into 6 flat DataFrames (`categories`, `competitions`, `complexes`, `venues`, `competitors`, `competitor_rankings`).
3. `DataQualityMonitor` checks primary-key uniqueness and column completeness, saving `data_quality_report.json`.
4. `ETLPipeline` saves 6 CSVs into `data-engineering/pipelines/processed/`.
5. `seed_database()` loads those CSVs into SQLite/PostgreSQL and seeds 2 demo users (`analyst@tennisintel.com`, `admin@tennisintel.com`).
6. On FastAPI startup (`lifespan`), `AnalyticsService` pre-warms the ML clustering and KPI caches in RAM.

### B. Authentication & Verification Flow (Gmail OTP + Google OAuth + Free SMS OTP)
1. **Standard Email Registration:** User submits name, Gmail, password, and optional phone in `RegisterPage.jsx` -> `/api/v1/auth/register` saves user with `is_email_verified=False`, generates a SHA-256 hashed 6-digit OTP via `OTPService`, and emails it via Gmail SSL SMTP (`NotificationService.send_email_otp`).
2. **Email OTP Verification:** User enters the 6-digit code -> `/api/v1/auth/verify-email-otp` checks expiry (10 mins) and attempt count (max 5), sets `is_email_verified=True`, and returns a 24-hour HS256 JWT. Unverified users trying `/auth/login` receive `403 EMAIL_NOT_VERIFIED`.
3. **Google Sign-In:** `GoogleSignInButton.jsx` loads Google Identity Services, gets a Google ID token, and sends it to `/api/v1/auth/google`. `NotificationService.verify_google_id_token` verifies it against `https://oauth2.googleapis.com/tokeninfo`, checks `aud == GOOGLE_CLIENT_ID`, creates/links the user (`is_email_verified=True`), and issues a JWT.
4. **Phone SMS OTP (Workspace):** Signed-in user submits E.164 phone number (`+91...`) in `WorkspacePage.jsx` -> `/api/v1/auth/send-phone-otp` sends SMS via Textbelt, Textbee, or Twilio -> `/api/v1/auth/verify-phone-otp` marks `is_phone_verified=True`.

### C. High-Concurrency Read Path (1M-User Scale Ready)
1. `TrafficControlMiddleware` inspects every `/api/*` request for IP rate limits (separate buckets for `read`, `auth`, and `chat`), injects `X-Response-Time-Ms`, and sets CDN `Cache-Control: public, max-age=60, s-maxage=120, stale-while-revalidate=300` on anonymous public GET endpoints so Cloudflare/Vercel/Nginx serve repeat traffic at the edge.
2. When traffic reaches FastAPI, `HybridCacheService.get_or_encode_async` checks L1 RAM first in microseconds, returning pre-validated, pre-serialized, and pre-gzipped `PreEncodedPayload` bytes (`Content-Encoding: gzip`) with **zero database queries**.
3. On a cache miss, a per-key `threading.Lock` (single-flight lock) ensures only **one** thread queries the DB and computes `KMeans`, while all simultaneous callers wait for that single result instead of crashing the database.

---

## 3. Part 1 — Root, Launchers, DevOps, Deployment & Tests

### `.env.example`
- **What it does:** Template listing all environment variables required for local or production deployment (never commit real secrets in `.env`).
- **Key Variables:**
  - `SPORTRADAR_*`: API key, access level (`trial`), version (`v3`), language (`en`), format (`json`).
  - `DATABASE_URL`: Empty for local SQLite, or Neon/PostgreSQL URL for production.
  - `JWT_SECRET_KEY`: Secret key for signing JWT tokens (32+ chars).
  - `SMTP_HOST`, `SMTP_PORT`, `SMTP_EMAIL`, `SMTP_APP_PASSWORD`: Gmail SMTP settings for real email OTPs.
  - `GOOGLE_CLIENT_ID`: Google OAuth 2.0 Web Client ID.
  - `SMS_PROVIDER`, `TEXTBELT_API_KEY`, `TEXTBEE_*`, `TWILIO_*`: Settings for phone SMS OTP.
  - `REDIS_URL`, `CACHE_TTL_*`, `DB_POOL_*`, `RATE_LIMIT_*`, `CDN_*`: Caching, DB connection pool, rate limit, and CDN header tuning.

### `.gitignore`
- **What it does:** Prevents secrets, caches, virtual environments, build artifacts, and local database files from being committed to Git.
- **Ignored patterns:** `__pycache__/`, `*.env`, `.venv/`, `node_modules/`, `dist/`, `build/`, `*.db`, `*.db-wal`, `*.db-shm`, `*.sqlite3`, `.agent/`.

### `requirements.txt`
- **What it does:** Lists all Python packages installed by `pip install -r requirements.txt`.
- **Packages:** `fastapi`, `uvicorn`, `pydantic`, `pydantic-settings`, `email-validator`, `sqlalchemy`, `psycopg2-binary`, `pandas`, `numpy`, `scikit-learn`, `pyjwt`, `bcrypt`, `httpx`, `python-dotenv`, `redis`.

### `README.md`
- **What it does:** Project summary for humans visiting the repository: visual theme, 6 core features, 4-member team roles, list of 20 SQL queries, local/Docker run commands, and college viva Q&A.

### `setup_scaffold.py`
- **What it does:** One-time bootstrap utility script that creates the entire empty folder skeleton for backend, frontend, data engineering, ML, SQL, tests, docs, and module1 using `os.makedirs(..., exist_ok=True)`.

### `start_platform.ps1` & `start_platform.bat`
- **What they do:** One-click local launchers for Windows (PowerShell and Command Prompt versions).
- **How they work:**
  1. Resolve the project root path.
  2. Set `PYTHONPATH` to include `backend/`, project root, and `machine-learning/models/`.
  3. Open Window 1 running `python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --app-dir backend`.
  4. Open Window 2 inside `frontend/` running `npm run dev` on port `5173`.
  5. Print demo credentials (`analyst@tennisintel.com` / `Analyst@123`).

### `.vscode/launch.json` & `.vscode/tasks.json`
- **What they do:** Configure VS Code to run and debug the project without typing manual terminal commands.
- **Configs/Tasks:**
  - `launch.json`: Defines `"FastAPI Backend (Port 8000)"` using `debugpy` to launch `uvicorn` with `PYTHONPATH` configured and `--reload` enabled.
  - `tasks.json`: Defines background tasks `"Start Backend"`, `"Start Frontend"`, and default build task `"Start All (Backend + Frontend)"` which starts both simultaneously (`Ctrl+Shift+B`).

### `.github/workflows/ci.yml`
- **What it does:** GitHub Actions CI/CD workflow triggered on `push` or `pull_request` to `main` or `master`.
- **Jobs:**
  - `backend-tests` (Python 3.11): Installs `requirements.txt` and sequentially executes all 5 verification scripts: `tennis_reader.py`, `test_api_sync.py`, `test_etl_pipeline.py`, `sql/test_queries.py`, and `backend/test_backend.py`.
  - `frontend-build` (Node 20): Runs `npm install` and `npm run build` in `frontend/`.

### `Dockerfile.backend`
- **What it does:** Builds the production FastAPI container image from `python:3.11-slim`.
- **How it works:** Installs `build-essential` and `curl`, installs `requirements.txt`, copies `backend/`, `sql/`, `data-engineering/`, and `machine-learning/`, sets `PYTHONPATH` and `WEB_CONCURRENCY=4`, exposes port `8000`, and starts multi-worker `uvicorn` with `--backlog 2048 --timeout-keep-alive 30 --no-access-log`.

### `Dockerfile.frontend`
- **What it does:** Two-stage Docker build for the React UI.
- **How it works:** Stage 1 (`node:20-alpine`) runs `npm install` and `npm run build` to create static files in `dist/`. Stage 2 (`nginx:alpine`) copies `dist/` to `/usr/share/nginx/html` and applies `nginx.conf`.

### `nginx.conf`
- **What it does:** Production reverse proxy, static server, GZip compressor, and API micro-cache configuration for Nginx.
- **Key behavior:**
  - Defines `proxy_cache_path` (`tip_api_cache`, 256MB max) and `upstream backend_pool` (`keepalive 64`).
  - Serves `/assets/` with 1-year `immutable` browser caching.
  - Routes SPA paths via `try_files $uri $uri/ /index.html`.
  - Proxies `/api/` to FastAPI with `proxy_cache_lock on` (Nginx stampede protection), `proxy_cache_use_stale`, and bypasses cache whenever an `Authorization` header is present (`$http_authorization`). Adds `X-Edge-Cache` response header.

### `docker-compose.yml`
- **What it does:** Orchestrates 4 local production-like containers:
  1. `db` (`postgres:15-alpine`, port `5432`) with healthcheck.
  2. `redis` (`redis:7-alpine`, port `6379`) with 128MB LRU policy for shared L2 cache & distributed rate limiting.
  3. `backend` (built from `Dockerfile.backend`, port `8000`, `WEB_CONCURRENCY=4`, waits for healthy `db` & `redis`).
  4. `frontend` (built from `Dockerfile.frontend`, port `3000`).

### `render.yaml`
- **What it does:** Infrastructure-as-Code blueprint for deploying the FastAPI backend to Render (`free` plan, `oregon` region) with multi-worker Uvicorn start command and env vars (`DATABASE_URL`, `REDIS_URL`, `JWT_SECRET_KEY`, `CORS_ORIGINS`).

### `test_live.py`
- **What it does:** Quick smoke-test script checking that a running local server on `http://localhost:8000` responds cleanly.
- **Function:** `test(name, path)` — opens `http://localhost:8000{path}` via `urllib.request.urlopen`, parses JSON, prints `[OK]` or `[FAIL]`, and prints the top 3 players plus database health.

### `tests/load_benchmark.py`
- **What it does:** Multi-threaded HTTP/1.1 keep-alive stress benchmark simulating concurrent client traffic against the live API.
- **Functions:**
  - `_percentile(sorted_vals, pct)`: Computes linear-interpolated P50/P95/P99 latency in milliseconds.
  - `_worker_task(host, port, worker_id, request_count)`: Runs on each thread using a persistent `HTTPConnection`, cycles through 7 public GET endpoints with unique simulated `X-Forwarded-For` IPs and `Accept-Encoding: gzip`, and records latencies and status codes.
  - `run_benchmark(base_url, concurrency, total_requests)`: Pre-warms all 7 endpoints, runs `ThreadPoolExecutor(max_workers=concurrency)`, fetches `/api/v1/admin/performance` cache stats, and prints throughput (`req/sec`), latency percentiles, errors, and L1 hit ratio.

---

## 4. Part 2 — Module 1 Foundation (OOP & JSON Reader)

### `module1-foundation/player_model.py`
- **What it does:** Demonstrates basic Python Object-Oriented Programming (OOP) models for tennis players before the database existed.
- **Classes:**
  - `Competitor` (`@dataclass`): Holds `id`, `name`, `country`, `country_code`, `abbreviation`.
    - `display_name()`: Returns `"<name> [<country_code>]"`.
  - `PlayerRankingProfile`: Wraps a `Competitor` with `rank`, `points`, `movement`, `competitions_played`.
    - `@property movement_indicator`: Formats positive movement as `"+1 (UP)"`, negative as `"-1 (DN)"`, zero as `" 0 (EQ)"`.
    - `summary()`: Returns a formatted fixed-width summary string for console output.

### `module1-foundation/tennis_reader.py`
- **What it does:** Reads a local JSON file (`data-engineering/sample_data/tennis_sample.json`) into OOP objects and prints an ASCII leaderboard table in the terminal.
- **Class `TennisDataParser`:**
  - `__init__(file_path)`: Stores file path and initializes empty `self.rankings` list.
  - `load_data() -> bool`: Checks file existence, parses JSON safely (catching `FileNotFoundError` / `JSONDecodeError`), and builds `Competitor` + `PlayerRankingProfile` objects.
  - `display_leaderboard()`: Prints formatted columns (`RANK`, `PLAYER NAME`, `COUNTRY`, `POINTS`, `MOVEMENT`, `TOURNAMENTS`), total players, average points, and top seed.

---

## 5. Part 3 — Data Engineering Pipeline & Staged Data

### `data-engineering/extraction/sportradar_client.py`
- **What it does:** Fault-tolerant HTTP client for SportRadar Tennis API v3 with rate limiting, retries, and offline mock fallback.
- **Class `SportRadarClient`:**
  - `__init__(api_key=None)`: Loads API key/config from `.env`, sets `min_request_interval = 1.0` second and local fallback path `data-engineering/sample_data/`.
  - `_throttle()`: Sleeps if less than 1 second passed since the previous API call so rate limits are never violated.
  - `_load_mock_fallback(fallback_filename)`: Loads cached JSON from `sample_data/` when the API key is missing/invalid or network fails.
  - `_execute_request(endpoint, fallback_filename, max_retries=3)`: If no valid key is set, immediately returns mock fallback. Otherwise calls `_throttle()`, performs `GET` with `api_key`, handles `401/403` (quota expired -> fallback), and retries `429/500/502/503/504` with exponential backoff (`2 ** attempt` seconds).
  - `get_competitions()`: Fetches `/competitions.json` (fallback: `competitions.json`).
  - `get_complexes()`: Fetches `/complexes.json` (fallback: `complexes.json`).
  - `get_doubles_rankings()`: Fetches `/double_competitors_rankings.json` (fallback: `doubles_rankings.json`).

### `data-engineering/extraction/sync_manager.py`
- **What it does:** Orchestrates downloading all 3 SportRadar feeds and writing sync telemetry (`sync_status.json`).
- **Class `SyncManager`:**
  - `__init__()`: Instantiates `SportRadarClient` and sets `sync_status.json` path.
  - `execute_full_sync() -> dict`: Calls `get_competitions()`, `get_complexes()`, and `get_doubles_rankings()`, counts nested records (`categories`, `competitions`, `complexes`, `venues`, `rankings`, `competitors`), records duration and `data_mode` (`LIVE_API` vs `FIXTURE_MOCK`), calls `_save_sync_status`, and returns summary dict.
  - `_save_sync_status(status_payload)`: Writes JSON report to `sync_status.json`.
  - `get_last_sync_info() -> dict`: Reads `sync_status.json` or returns a default placeholder if never synced.

### `data-engineering/extraction/sync_status.json`
- **What it does:** Persists the latest extraction metadata (`last_sync_timestamp`, `status`, entity counts, `errors`, `duration_seconds`, `data_mode`).

### `data-engineering/extraction/test_api_sync.py`
- **What it does:** Verification script (`run_verification()`) that executes `SyncManager.execute_full_sync()`, asserts `"SUCCESS"` and non-zero counts, and prints confirmation.

### `data-engineering/transformation/transformer.py`
- **What it does:** Cleans, flattens, and normalizes deeply nested JSON dictionaries into 6 3NF relational Pandas DataFrames.
- **Class `DataTransformer`:**
  - `clean_text(val)`: Static helper trimming whitespace and replacing empty strings with `None`.
  - `transform_competitions_data(raw_json) -> (df_categories, df_competitions)`: Extracts nested `category` objects into `categories` and competition fields into `competitions`, normalizing `type`/`gender` to lowercase and deduplicating PKs (`category_id`, `competition_id`).
  - `transform_complexes_data(raw_json) -> (df_complexes, df_venues)`: Separates `complexes` from nested `venues[]` lists, forces `country_code` uppercase (first 3 chars), defaults `timezone` to `"UTC"`, and deduplicates on `complex_id` and `venue_id`.
  - `transform_rankings_data(raw_json) -> (df_competitors, df_rankings)`: Iterates `rankings[].competitor_rankings[]`, separates player bio (`competitors`) from weekly score rows (`competitor_rankings`), assigns sequential `rank_id`, casts integer columns, and deduplicates `competitors`.

### `data-engineering/validation/schemas.py`
- **What it does:** Defines strict Pydantic v2 validation contracts for transformed records before storage.
- **Classes (`BaseModel`):**
  - `CategorySchema`: `category_id`, `category_name` (strips whitespace).
  - `CompetitionSchema`: `competition_id`, `competition_name`, `parent_id`, `type`, `gender`, `category_id`.
  - `VenueSchema`: `venue_id`, `venue_name`, `city_name`, `country_name`, `country_code` (max 3 chars), `timezone`, `complex_id`.
  - `ComplexSchema`: `complex_id`, `complex_name`, `venues: List[VenueSchema]`.
  - `CompetitorSchema`: `competitor_id`, `name`, `country`, `country_code`, `abbreviation`.
  - `RankingItemSchema`: `rank` (>=1), `movement`, `points` (>=0), `competitions_played` (>=0), `competitor: CompetitorSchema`.

### `data-engineering/validation/quality_monitor.py`
- **What it does:** Audits transformed DataFrames for duplicate primary keys and missing/null values, saving a JSON quality scorecard.
- **Class `DataQualityMonitor`:**
  - `__init__(report_path)`: Sets path to `data_quality_report.json`.
  - `audit_dataframe(df, entity_name, primary_key_col) -> dict`: Counts `total_records`, `duplicate_keys`, missing counts per column, `completeness_percentage`, and sets `is_valid` (`duplicate_keys == 0`).
  - `generate_full_report(datasets_map) -> dict`: Runs `audit_dataframe` across all 6 tables, sets `overall_status` (`"PASSED"` or `"WARNING"`), and saves `data_quality_report.json`.

### `data-engineering/validation/data_quality_report.json`
- **What it does:** JSON audit report served by `/api/v1/admin/data-quality` showing `total_records`, `duplicate_keys: 0`, and column completeness percentages (`100%` for all mandatory fields; `parent_id` is `14.29%` because only sub-competitions have parents).

### `data-engineering/pipelines/etl_pipeline.py`
- **What it does:** Master Extract-Transform-Audit-Load script connecting client, transformer, monitor, and CSV output.
- **Class `ETLPipeline`:**
  - `__init__()`: Sets `processed_dir = data-engineering/pipelines/processed` and initializes `SportRadarClient`, `DataTransformer`, and `DataQualityMonitor`.
  - `run() -> bool`:
    1. **Extract:** Calls `get_competitions()`, `get_complexes()`, `get_doubles_rankings()`.
    2. **Transform:** Converts them into 6 DataFrames.
    3. **Validate:** Runs `monitor.generate_full_report(...)`.
    4. **Load:** Exports all 6 DataFrames to CSV inside `processed/`.

### `data-engineering/pipelines/test_etl_pipeline.py`
- **What it does:** Runs `ETLPipeline.run()` (`run_etl_verification()`), verifies all 6 CSV files + `data_quality_report.json` exist on disk, and prints exact row counts.

### Sample JSON & Processed CSV Data Files
- **`data-engineering/sample_data/`:**
  - `competitions.json`: Mock SportRadar competition categories and tournament hierarchy (ATP, Grand Slam, ITF, sub-competitions).
  - `complexes.json`: Mock tennis complexes and courts across cities/countries/timezones (e.g., Estadio Nacional in Chile, AELTC in London).
  - `doubles_rankings.json`: Mock weekly ATP doubles rankings feed (rank, movement, points, competitions played, player country/abbreviation).
  - `tennis_sample.json`: Simplified single-feed sample used by Module 1's `tennis_reader.py`.
- **`data-engineering/pipelines/processed/` (Staged 3NF CSV tables):**
  - `categories.csv`: `category_id,category_name` (5 rows)
  - `competitions.csv`: `competition_id,competition_name,parent_id,type,gender,category_id` (7 rows)
  - `complexes.csv`: `complex_id,complex_name` (4 rows)
  - `venues.csv`: `venue_id,venue_name,city_name,country_name,country_code,timezone,complex_id` (7 rows)
  - `competitors.csv`: `competitor_id,name,country,country_code,abbreviation` (10 rows)
  - `competitor_rankings.csv`: `rank_id,rank,movement,points,competitions_played,competitor_id` (10 rows)

---

## 6. Part 4 — SQL Schema, Seeder & 20 Analytical Queries

### `sql/schema.sql`
- **What it does:** PostgreSQL DDL script creating all **11 normalized 3NF tables**, foreign keys, `CHECK` constraints, unique constraints, and 13 lookup indexes (`idx_competitions_category`, `idx_rankings_points DESC`, `idx_otp_lookup`, `idx_users_google_id`, etc.).

### `sql/queries.sql`
- **What it does:** Stores the 20 capstone analytical SQL queries split into 3 parts:
  - **Q1–Q7:** Competitions & Categories (`JOIN`, `GROUP BY`, `COUNT`, `'doubles'` filter, `'ITF Men'`, self-join for `parent_id`, top-level `WHERE parent_id IS NULL`).
  - **Q8–Q14:** Complexes & Venues (venues + complex names, venue counts, `'Chile'` filter, timezones, `HAVING COUNT > 1`, grouped by country, `'Nacional'` `LIKE`).
  - **Q15–Q20:** Competitors & Rankings (full leaderboard, top 5, `movement = 0`, `'Croatia'` points sum, players per country, `MAX(points)` subquery).

### `sql/seed_database.py`
- **What it does:** Automated database initializer and CSV bulk loader.
- **Functions:**
  - `hash_password(password)`: Computes SHA-256 hex digest for seeded demo users (note: `security.verify_password` accepts both bcrypt and SHA-256 seed fallback).
  - `seed_database()`: Drops and recreates all tables via SQLAlchemy `Base.metadata`, loads all 6 CSVs from `processed/` via `db.merge()`, creates `admin@tennisintel.com` (`Admin@123`) and `analyst@tennisintel.com` (`Analyst@123`) as verified local accounts, and writes an initial `SyncLog` row (`43` records).

### `sql/test_queries.py`
- **What it does:** Verification suite executing all 20 syllabus SQL queries (`QUERIES` list) against the live database engine (`run_all_queries()`), printing previews of up to 3 rows per query and asserting none return empty results.

---

## 7. Part 5 — Machine Learning Clustering & Trait Engine

### `machine-learning/models/cluster_engine.py`
- **What it does:** Performs Scikit-Learn `KMeans` player tiering, 5-axis radar score calculation, and Euclidean nearest-neighbor player recommendations in a thread-safe, stateless way.
- **Class `TennisMLEngine` (singleton instance `ml_engine`):**
  - `fit_and_profile(players) -> list`:
    1. Builds a NumPy matrix `X` from 4 features: `[points, competitions_played, movement, points/competitions_played]`.
    2. Fits a local `KMeans(n_clusters=min(3, num_players), random_state=42, n_init=10)` model and assigns cluster IDs, then ranks clusters by mean points into `"Elite Grand Slam Tier"`, `"High-Yield Contender"`, and `"Challenger Circuit"`.
    3. Vectorizes 5 radar traits scaled cleanly between ~25 and 99: `consistency`, `power_volume`, `tournament_stamina`, `rank_momentum`, and `efficiency`.
    4. Precomputes pairwise Euclidean distances across the 5-trait matrix (for `<= 1000` players) to attach `_similar_ids` (top 3 closest competitors) for $O(1)$ runtime lookup.
  - `get_similar_players(target_id, profiled_players, top_n=3, player_lookup=None) -> list`: Uses precomputed `_similar_ids` when available in `player_lookup`, or falls back to vectorized `np.linalg.norm` Euclidean distance over `TRAIT_KEYS`.

---

## 8. Part 6 — FastAPI Backend (Core, DB, Models, Services, Routes)

### `backend/app/main.py`
- **What it does:** Main FastAPI entry point wiring database startup, cache pre-warming, middleware stack, CORS, and `/api/v1` routers.
- **Functions & Config:**
  - `lifespan(app)` (`@asynccontextmanager`): Creates tables if missing, calls `ensure_schema_migrations()`, auto-seeds database if `Competitor` count is `0`, and pre-warms `AnalyticsService.get_players_bundle()`, `get_platform_kpis()`, and `get_country_analytics()` before serving traffic.
  - **Middleware order (inner -> outer):** `TrafficControlMiddleware` -> `GZipMiddleware` -> `CORSMiddleware` (allows localhost regex + configured origins).
  - `root()` (`GET /`): Returns platform name, version, `"online"` status, `/docs`, and `/api/v1/health`.

### `backend/app/core/config.py`
- **What it does:** Loads `.env` and exposes strongly typed configuration on a global `settings` object.
- **Class `Settings`:**
  - Stores `CORS_ORIGINS`, Redis/L1 cache TTLs (`CACHE_TTL_PLAYERS=120`, `CACHE_TTL_CATALOG=300`), CDN `max-age`/`s-maxage`, tiered rate limits (`12000` reads/min, `30` auth/min, `60` chat/min), SQLAlchemy pool sizes (`DB_POOL_SIZE=20`, `DB_MAX_OVERFLOW=40`), Gmail SMTP settings, `GOOGLE_CLIENT_ID`, and SMS provider settings.
  - `@property is_gmail_configured`, `@property is_google_configured`, `@property is_sms_configured`: Boolean helpers verifying non-placeholder credentials before attempting external API/SMTP calls.

### `backend/app/core/cache.py`
- **What it does:** Two-tier caching system (L1 in-memory LRU RAM + optional L2 Redis) with pre-serialized/pre-gzipped payloads and single-flight cache-stampede locking.
- **Classes & Helpers:**
  - `PreEncodedPayload`: Stores `data`, compact UTF-8 `raw_bytes`, and pre-compressed `gzip_bytes` (when >= 512 bytes).
    - `to_response(accept_encoding)`: Returns a `Response` directly with `Content-Encoding: gzip` + `Vary: Accept-Encoding` if the client accepts gzip, avoiding re-serialization on every request.
  - `HybridCacheService` (global singleton `cache_service`):
    - `_get_key_lock(key)`: Returns a per-key `threading.Lock` so 10,000 simultaneous misses for the same key only run the DB query once.
    - `get_l1(key)` / `set_l1(key, value, ttl)`: Thread-safe `OrderedDict` LRU cache with TTL expiry and max-entry eviction.
    - `_get_l2(key)` / `_set_l2(key, value, ttl)`: Optional Redis read/write with short timeouts (`1.5s`).
    - `get_or_compute(key, ttl, loader, should_cache)`: Synchronous L1 -> single-flight lock -> L2 -> `loader()`.
    - `get_or_compute_async(...)`: Checks L1 directly on the async event loop (zero threadpool hop on hit) and only dispatches misses to `run_in_threadpool`.
    - `get_or_encode_async(encoded_key, ttl, builder, should_cache)`: Same zero-hop L1 fast path for `PreEncodedPayload` objects.
    - `_run_locked(lock, fn)`: Static helper executing `fn()` inside `with lock:`.
    - `invalidate_prefix(prefix)` / `invalidate_all()`: Evicts keys from L1 and scans/deletes `tip:*` keys in Redis.
    - `stats()`: Returns backend type (`memory-l1` or `redis+l1`), entry counts, L1/L2 hits, misses, coalesced waits, and hit ratio `%`.
  - `dump_validated_json(adapter, data)`: Validates Python dicts once with a Pydantic `TypeAdapter` and returns compact JSON `bytes`.

### `backend/app/core/middleware.py`
- **What it does:** Pure ASGI middleware (avoids Starlette `BaseHTTPMiddleware` memory buffering) implementing rate limiting, CDN cache headers, and response-time telemetry.
- **Classes:**
  - `InMemoryRateLimiter` (instance `local_rate_limiter`):
    - `check(key, limit, window_seconds=60) -> (allowed, remaining, reset_after)`: Thread-safe sliding-window approximation counter with bounded key eviction (`max_keys=50000`).
  - `TrafficControlMiddleware`:
    - `_extract_client_ip(scope)`: Reads `X-Forwarded-For` or `X-Real-IP` when `TRUST_PROXY_HEADERS=True`, else socket client IP.
    - `_classify_bucket(method, path)`: Routes `/api/v1/auth/*` mutations to `auth` (strict limit), `/api/v1/assistant/chat` to `chat`, and public catalog reads to `read`.
    - `_check_redis_limit(redis_client, key, limit, window_seconds)`: Uses a Redis pipeline (`INCR` + `EXPIRE`) for distributed rate limiting across workers/pods.
    - `__call__(scope, receive, send)`: Enforces HTTP `429` + `Retry-After` if rate-limited, measures `X-Response-Time-Ms`, adds `X-RateLimit-*` headers, and sets `Cache-Control: public, max-age=..., s-maxage=..., stale-while-revalidate=300` + `Vary: Authorization` on anonymous public 200 GETs (or `no-store, private` on auth/workspace/admin/chat routes).

### `backend/app/core/security.py`
- **What it does:** Password hashing, JWT generation/verification, and FastAPI auth dependency helpers.
- **Functions:**
  - `hash_password(password)`: Salts and hashes password using `bcrypt`.
  - `verify_password(plain_password, hashed_password)`: Verifies via `bcrypt.checkpw` (rejects `!GOOGLE_OAUTH_ONLY!` sentinel; falls back to SHA-256 check for seeded demo accounts).
  - `create_access_token(data, expires_delta)`: Encodes an HS256 JWT expiring in 24 hours by default.
  - `get_current_user(token, db)`: FastAPI dependency validating `Authorization: Bearer <token>` and returning the `User` row (raises `401` if invalid).
  - `get_optional_user(token, db)`: Same, but returns `None` instead of raising for unauthenticated visitors.

### `backend/app/database/connection.py`
- **What it does:** Configures the SQLAlchemy `engine`, `SessionLocal`, and `Base` for either local SQLite (with WAL mode) or production PostgreSQL/Neon (`QueuePool`), plus safe runtime column/index migrations.
- **Functions:**
  - `_configure_sqlite_wal(dbapi_connection, connection_record)`: SQLite `connect` event listener setting `PRAGMA journal_mode=WAL;`, `synchronous=NORMAL;`, and `busy_timeout=15000;`.
  - `ensure_schema_migrations()`: Uses `sqlalchemy.inspect` to safely `ALTER TABLE users ADD COLUMN ...` if upgrading an older DB without losing data, and creates missing performance indexes.
  - `get_db_context()`: Context-managed DB session used inside background tasks and cache loaders.
  - `get_db()`: FastAPI dependency yielding a DB session per request and closing it afterward.

### `backend/app/models/entities.py`
- **What it does:** Defines all **11 SQLAlchemy ORM table classes** inheriting from `Base`.
- **Models:**
  1. `Category` (`categories`): `category_id`, `category_name`, `competitions` relationship.
  2. `Competition` (`competitions`): `competition_id`, `competition_name`, `parent_id` (self-FK), `type`, `gender`, `category_id`.
  3. `Complex` (`complexes`): `complex_id`, `complex_name`, `venues` relationship.
  4. `Venue` (`venues`): `venue_id`, `venue_name`, `city_name`, `country_name`, `country_code`, `timezone`, `complex_id`.
  5. `Competitor` (`competitors`): `competitor_id`, `name`, `country`, `country_code`, `abbreviation`.
  6. `CompetitorRanking` (`competitor_rankings`): `rank_id`, `rank`, `movement`, `points`, `competitions_played`, `competitor_id`.
  7. `User` (`users`): `user_id`, `email`, `hashed_password`, `full_name`, `phone_number`, `auth_provider` (`local`/`google`), `google_id`, `avatar_url`, `is_email_verified`, `is_phone_verified`, `role`, `created_at`.
  8. `OTPVerification` (`otp_verifications`): `otp_id`, `target`, `channel` (`email`/`phone`), `purpose`, `otp_hash`, `attempts`, `is_used`, `expires_at`, `created_at`, composite index `idx_otp_lookup`.
  9. `UserFavourite` (`user_favourites`): `fav_id`, `user_id`, `competitor_id` with unique constraint `uq_user_competitor`.
  10. `AIInteraction` (`ai_interactions`): `interaction_id`, `user_id`, `prompt`, `response`, `created_at`.
  11. `SyncLog` (`sync_logs`): `sync_id`, `status`, `data_mode`, `records_processed`, `duration_seconds`, `synced_at`.

### `backend/app/schemas/api_schemas.py`
- **What it does:** Defines all Pydantic v2 request/response schemas for automatic FastAPI validation and OpenAPI/Swagger documentation.
- **Schema Groups:**
  - **Auth & OTP:** `UserRegister`, `RegisterPendingResponse`, `VerifyEmailOTPRequest`, `ResendEmailOTPRequest`, `GoogleAuthRequest`, `SendPhoneOTPRequest`, `VerifyPhoneOTPRequest`, `AuthProvidersStatusResponse`, `UserLogin`, `TokenResponse`, `UserResponse`.
  - **Players & Rankings:** `RadarTraits`, `PlayerRankingDetail`, `CompetitorSummary`, `PlayerDetailResponse`, `PaginatedPlayersResponse`.
  - **Catalog:** `CompetitionResponse`, `VenueResponse`, `ComplexResponse`.
  - **Analytics:** `CountryAnalyticsItem`, `MetricComparison`, `PlayerComparisonResponse`, `PlatformKPIs`.
  - **AI & System:** `ChatQueryRequest`, `DataCitation`, `ChatQueryResponse`, `FavouriteToggleResponse`, `HealthResponse`.

### `backend/app/services/otp_service.py`
- **What it does:** Generates, hashes, stores, throttles, and verifies 6-digit OTPs securely.
- **Functions & Class `OTPService`:**
  - `_ensure_utc(dt)`: Converts naive SQLite `datetime` or tz-aware Postgres `datetime` cleanly into UTC for safe comparison.
  - `_hash_otp(target, channel, code)`: Hashes `{target}:{channel}:{code}:{SECRET_KEY}` with SHA-256 so raw OTPs are never stored in the database.
  - `OTPService.generate_and_store_otp(db, target, channel, purpose, enforce_cooldown)`: Enforces 30-second resend cooldown (`429`), invalidates older unused OTPs for that target/channel, generates a cryptographic 6-digit code using `secrets.randbelow(10)`, sets a 10-minute expiry, stores its hash, and returns the plain code to send.
  - `OTPService.verify_otp(db, target, channel, code)`: Checks latest unused OTP exists (`400`), hasn't expired (`400`), hasn't exceeded 5 wrong attempts (`429`), compares hash in constant time via `hmac.compare_digest` (incrementing `attempts` on failure), and marks `is_used = True` on success.

### `backend/app/services/notification_service.py`
- **What it does:** Sends real Gmail OTP emails, dispatches free SMS OTPs, and verifies Google Sign-In ID tokens.
- **Class `NotificationService`:**
  - `send_email_otp(to_email, otp_code, full_name)`: Builds an HTML + plain-text MIME email with `html.escape(full_name)`, connects over SSL (`smtplib.SMTP_SSL` on 465 or `STARTTLS` on 587) to Gmail SMTP using `SMTP_EMAIL` and `SMTP_APP_PASSWORD`, and returns delivery status.
  - `send_sms_otp(phone_number, otp_code)`: Dispatches SMS through whichever free provider is set in `SMS_PROVIDER`: `textbelt` (`https://textbelt.com/text`), `textbee` (`api.textbee.dev`), or `twilio` (`api.twilio.com`).
  - `verify_google_id_token(id_token)`: Calls Google's `https://oauth2.googleapis.com/tokeninfo` endpoint, validates `aud == settings.GOOGLE_CLIENT_ID` and `email_verified == true`, and returns `{google_id, email, full_name, avatar_url}`.

### `backend/app/services/analytics_service.py`
- **What it does:** Executes SQL aggregations and ML profiling behind `HybridCacheService` so heavy calculations happen only once per cache TTL.
- **Internal Loaders & Class `AnalyticsService`:**
  - `_compute_players_bundle(db)`: Joins `Competitor` + `CompetitorRanking`, runs `ml_engine.fit_and_profile(...)`, and returns `{"items": profiled, "by_id": dict}` for O(1) ID lookups.
  - `_compute_platform_kpis(db)`: Counts players, competitions, complexes, venues, distinct countries, highest-scoring player, and average points.
  - `_compute_country_analytics(db)`: Groups players by country/country code and computes `player_count`, `total_points`, and `avg_points`.
  - `AnalyticsService.get_players_bundle` / `get_players_bundle_async` / `get_all_players_profiled`: Cached wrappers around `_compute_players_bundle`.
  - `AnalyticsService.get_platform_kpis` / `get_platform_kpis_async`: Cached wrappers around `_compute_platform_kpis`.
  - `AnalyticsService.get_country_analytics` / `get_country_analytics_async`: Cached wrappers around `_compute_country_analytics`.
  - `AnalyticsService.compare_players_from_bundle(bundle, player_a_id, player_b_id)`: Builds head-to-head comparison table (World Rank, Points, Tournaments, Points/Tournament Efficiency) with winner badges (`player_a`/`player_b`/`equal`), AI summary text, and missing-data warning.
  - `compare_players` / `compare_players_async`: Convenience wrappers fetching the cached bundle first.

### `backend/app/services/ai_assistant.py`
- **What it does:** Context-grounded, zero-hallucination conversational sports analyst answering queries strictly from cached database data and citing record IDs.
- **Functions & Class `AITennisAssistant`:**
  - `persist_ai_interaction(user_id, prompt, response_text)`: Saves chat history in `ai_interactions` using a separate DB session (run asynchronously via FastAPI `BackgroundTasks` so chat responses return immediately).
  - `_get_cached_competitions_summary(db)`: Caches summary of competitions with category names.
  - `AITennisAssistant.answer_query(db, prompt, user_id, background_tasks)`: Extracts user intent across 5 branches:
    1. Top players / rankings (`top`, `highest`, `leader`, `best`, `rank`)
    2. Player comparisons (`compare`, `vs`, `versus`, `difference`) — matches player surnames in prompt
    3. Countries / geographic intelligence (`country`, `countries`, `nation`, `global`)
    4. Competitions & venues (`competition`, `tournament`, `venue`, `complex`, `wimbledon`, `vienna`)
    5. General platform overview (fallback)
    Returns `response`, `citations`, `suggested_actions`, and `created_at`.

### `backend/app/api/v1/api.py`
- **What it does:** Mounts all 10 endpoint routers under `/api/v1` with Swagger OpenAPI tags (`/health`, `/auth`, `/players`, `/rankings`, `/competitions`, `/venues`, `/analytics`, `/assistant`, `/workspace`, `/admin`).

### `backend/app/api/v1/endpoints/health.py`
- **Routes:**
  - `get_health()` (`GET /api/v1/health`): Runs `SELECT 1` to verify DB connectivity and returns status, version, DB state, and UTC timestamp.

### `backend/app/api/v1/endpoints/auth.py`
- **Helper:** `_serialize_user(user)`: Formats `User` fields cleanly into a JSON-safe dictionary.
- **Routes:**
  - `get_auth_providers_status()` (`GET /api/v1/auth/providers`): Returns readiness flags (`gmail_otp_enabled`, `google_enabled`, `google_client_id`, `sms_otp_enabled`, `sms_provider`).
  - `register()` (`POST /api/v1/auth/register`): Creates or updates an unverified user, generates a 6-digit email OTP, sends it via Gmail SMTP, and returns `requires_verification=True` (no JWT yet).
  - `verify_email_otp()` (`POST /api/v1/auth/verify-email-otp`): Validates 6-digit OTP, sets `is_email_verified=True`, and returns JWT + user profile.
  - `resend_email_otp()` (`POST /api/v1/auth/resend-email-otp`): Sends a new email OTP with 30-second cooldown check.
  - `login()` (`POST /api/v1/auth/login`): Checks password (blocking Google-only accounts), requires `is_email_verified=True` (else `403 EMAIL_NOT_VERIFIED`), and returns JWT.
  - `google_auth()` (`POST /api/v1/auth/google`): Verifies Google ID token, creates or links verified `User`, and returns JWT.
  - `send_phone_otp()` (`POST /api/v1/auth/send-phone-otp`): Authenticated route generating and sending a 6-digit SMS OTP.
  - `verify_phone_otp()` (`POST /api/v1/auth/verify-phone-otp`): Authenticated route validating SMS OTP and saving `is_phone_verified=True`.
  - `get_profile()` (`GET /api/v1/auth/me`): Returns the logged-in user's profile and verification badges.

### `backend/app/api/v1/endpoints/players.py`
- **Helpers:**
  - `_check_is_favourite(authorization, competitor_id)`: Optionally decodes JWT and checks if `UserFavourite` exists for logged-in users.
  - `_build_player_detail_dict(bundle, competitor_id, is_fav)`: Looks up player in $O(1)$, retrieves 3 similar players via `ml_engine`, generates AI summary, and returns full player dossier.
- **Routes:**
  - `get_players()` (`GET /api/v1/players`): Paginated list (`page`, `limit`, `search`, `country`). When unfiltered (`not search and not country`), serves pre-serialized + pre-gzipped `PreEncodedPayload` directly from L1 cache.
  - `get_player_intelligence()` (`GET /api/v1/players/{competitor_id}`): Anonymous callers get zero-DB pre-encoded GZip cached responses; authenticated callers also get live `is_favourite` status.

### `backend/app/api/v1/endpoints/rankings.py`
- **Routes:**
  - `get_top_rankings()` (`GET /api/v1/rankings/top`): Returns top `N` (default 5) ranked players from pre-encoded L1 cache.

### `backend/app/api/v1/endpoints/competitions.py`
- **Helper:** `_load_all_competitions()`: Loads all `Competition` rows with eager `joinedload(Competition.category)`.
- **Routes:**
  - `get_competitions()` (`GET /api/v1/competitions`): Supports optional `type_filter` and `category_id` filtering; serves unfiltered catalog from pre-encoded L1 cache.

### `backend/app/api/v1/endpoints/venues.py`
- **Helpers:** `_load_all_venues()` (uses `joinedload(Venue.complex)`) and `_load_all_complexes()` (uses `selectinload(Complex.venues)`).
- **Routes:**
  - `get_venues()` (`GET /api/v1/venues`): Lists venues with optional case-insensitive `country` filter; serves unfiltered list from pre-encoded L1 cache.
  - `get_complexes()` (`GET /api/v1/venues/complexes`): Lists tennis complexes and nested venues from pre-encoded L1 cache.

### `backend/app/api/v1/endpoints/analytics.py`
- **Routes:**
  - `get_kpis()` (`GET /api/v1/analytics/kpis`): Pre-encoded cached global dashboard KPIs.
  - `get_country_analytics()` (`GET /api/v1/analytics/countries`): Pre-encoded cached per-country player counts & points stats.
  - `compare_players()` (`GET /api/v1/analytics/compare?player_a=...&player_b=...`): Cached side-by-side comparison payload (`404` if invalid player ID).

### `backend/app/api/v1/endpoints/assistant.py`
- **Helper:** `_resolve_user_id(authorization)`: Softly extracts `user_id` from optional Bearer token so chat works for both guests and signed-in users.
- **Routes:**
  - `chat_with_assistant()` (`POST /api/v1/assistant/chat`): Calls `AITennisAssistant.answer_query(...)` passing FastAPI `BackgroundTasks` for non-blocking telemetry persistence.

### `backend/app/api/v1/endpoints/workspace.py`
- **Routes (require JWT via `get_current_user`):**
  - `get_user_favourites()` (`GET /api/v1/workspace/favourites`): Queries user's bookmarked `competitor_id`s and resolves profiles in $O(1)$ from cached bundle.
  - `toggle_favourite()` (`POST /api/v1/workspace/favourites/{competitor_id}`): Adds or removes a bookmark row in `user_favourites`.

### `backend/app/api/v1/endpoints/admin.py`
- **Helper:** `_load_data_quality_base()`: Reads `data_quality_report.json` and latest `SyncLog` row.
- **Routes:**
  - `get_data_quality_report()` (`GET /api/v1/admin/data-quality`): Cached 60s audit data merged with live `cache_service.stats()`.
  - `get_performance_telemetry()` (`GET /api/v1/admin/performance`): Returns live L1/L2 cache hit ratio and entry counts.

### `backend/test_backend.py`
- **What it does:** Comprehensive automated integration test suite using Starlette `TestClient(app)` with full `lifespan` execution.
- **Function `run_tests()`:**
  1. Verifies all 10 core `GET` endpoints return HTTP `200`.
  2. Verifies player detail traits & similar players, smart player comparison, and AI assistant citations.
  3. Tests demo user login (`/auth/login`) and `/auth/me`.
  4. Tests full Gmail OTP signup lifecycle (with mocked SMTP/SMS/Google external calls): unverified login blocked (`403 EMAIL_NOT_VERIFIED`), wrong OTP rejected (`400`), valid OTP verified -> JWT issued, SMS OTP verified (`is_phone_verified=True`), Google OAuth login, then cleans up synthetic test rows.
  5. Verifies high-concurrency features: CDN `Cache-Control` + `Vary` + `X-Response-Time-Ms` + `gzip`, `no-store` on `/auth/me`, 20-thread `ThreadPoolExecutor` + `Barrier` proving single-flight lock coalesces 20 simultaneous misses into **1** DB/ML call, and tiered rate limiter returning HTTP `429` + `Retry-After`.

---

## 9. Part 7 — React Frontend (Config, API Client, Layout, Components, Pages)

### Frontend Build & Style Config Files
- **`frontend/.env.example`**: Documents `VITE_API_URL` (`http://localhost:8000/api/v1`) and `VITE_GOOGLE_CLIENT_ID`.
- **`frontend/package.json`**: React 18, `react-router-dom`, `lucide-react` icons, `recharts` charts, `axios`, `clsx`, `tailwind-merge`, plus Vite/Tailwind dev dependencies. Scripts: `dev` (`vite --host`), `build`, `preview`.
- **`frontend/package-lock.json`**: Auto-generated npm dependency lockfile ensuring reproducible installs.
- **`frontend/index.html`**: Root HTML shell in dark mode (`class="dark"`), inline SVG tennis-ball favicon, Google Fonts (`Inter`, `JetBrains Mono`, `Manrope`), and `#root` mount point loading `/src/main.jsx`.
- **`frontend/vite.config.js`**: Enables React plugin, dev server on `0.0.0.0:5173` proxying `/api` -> `http://localhost:8000`, and Rollup manual code splitting (`vendor-react`, `vendor-charts`, `vendor-icons`).
- **`frontend/tailwind.config.js`**: Defines custom design tokens (`background.main` `#0B1220`, `tennis.green` `#B7F34A`, `cyanAccent` `#43C6AC`, `slateBorder` `#263449`, font families).
- **`frontend/postcss.config.js`**: Loads `tailwindcss` and `autoprefixer`.
- **`frontend/vercel.json`**: Vercel SPA deployment config: rewrites all routes to `/index.html` and sets `Cache-Control: public, max-age=31536000, immutable` on `/assets/*`.
- **`frontend/src/index.css`**: Imports Tailwind layers, defines dark custom scrollbars, `.glass-card`, `.glass-card-hover`, and `.tennis-gradient-text`.

### Entry Point & Router
- **`frontend/src/main.jsx`**: Mounts `<App />` inside `<React.StrictMode>` into `#root`.
- **`frontend/src/App.jsx`**: Sets up `<BrowserRouter>` and `<Suspense fallback={<RouteLoader />}>`. Eagerly loads `LandingPage`, `DashboardLayout`, and `DashboardPage`, while code-splitting (`React.lazy`) all 11 secondary pages (`LoginPage`, `RegisterPage`, `PlayerExplorerPage`, `PlayerDetailPage`, `ComparisonPage`, `GlobalIntelligencePage`, `CompetitionExplorerPage`, `AIAssistantPage`, `WorkspacePage`, `ReportsPage`, `DataQualityPage`) and redirecting unknown paths `*` to `/`.
  - Contains helper component `RouteLoader()` showing a spinning loading indicator during lazy route transitions.

### API Client (`frontend/src/services/api.js`)
- **What it does:** Centralized Axios HTTP client with JWT request interceptor, CDN-friendly stateless header rules, and offline fallback fixtures (`MOCK_PLAYERS`, etc.) so the UI remains usable even if the backend is offline.
- **Key logic:**
  - `STATELESS_PUBLIC_PATHS` set prevents sending `Authorization` headers on public endpoints (`/players`, `/analytics/*`, `/rankings/top`, `/competitions`, `/venues*`, `/auth/providers`), keeping browser/CDN edge caches shared across users.
  - All other routes attach `Bearer <tip_token>` from `localStorage`.
- **Methods on exported `TennisAPI` object:**
  - `getKPIs()`, `getPlayers(params)`, `getPlayerDetail(id)`, `comparePlayers(pA, pB)`, `getCountries()`, `getCompetitions()`, `getVenues()`, `askAssistant(prompt)`, `getDataQuality()`, `getAuthProviders()`, `registerWithEmail(...)`, `verifyEmailOTP(email, otp)`, `resendEmailOTP(email)`, `googleLogin(credential)`, `sendPhoneOTP(phone_number)`, `verifyPhoneOTP(phone_number, otp)`, `getProfile()`, `login(email, password)`, `logout()`, `getCurrentUser()`.

### Layout & Reusable Components
- **`frontend/src/layouts/DashboardLayout.jsx`**:
  - **Component `DashboardLayout({ children })`:** Persistent SaaS shell containing desktop left sidebar (`NAV_ITEMS` mapping 9 app routes + SportRadar sync badge + logged-in user avatar/verification status/logout button), responsive mobile navigation drawer (`mobileMenuOpen`), top navbar with `"Ask AI Analyst"` quick button, and scrollable `<main>` viewport. Handles `handleLogout()`.
- **`frontend/src/components/auth/GoogleSignInButton.jsx`**:
  - **Component `GoogleSignInButton({ mode, onSuccess, onError })`:** Queries `TennisAPI.getAuthProviders()` for a Google Client ID (`VITE_GOOGLE_CLIENT_ID` or server-configured). If present, dynamically injects `https://accounts.google.com/gsi/client`, initializes and renders Google's native pill button (`initializeGSI`), and exchanges the credential via `TennisAPI.googleLogin(response.credential)`. If unconfigured, shows a fallback button that toggles a free setup guide card.
- **`frontend/src/components/charts/PlayerRadarChart.jsx`**:
  - **Component `PlayerRadarChart({ traits, playerName, compareTraits, compareName })`:** Uses Recharts (`RadarChart`, `PolarGrid`, `PolarAngleAxis`, `PolarRadiusAxis`, `ResponsiveContainer`) to plot a player's 5 ML traits on a `[0, 100]` scale in Volt Green (`#B7F34A`), optionally overlaying a second player (`compareTraits`) in Cyan (`#43C6AC`).

### Pages (`frontend/src/pages/`)
- **`LandingPage.jsx`** (`LandingPage()`): Marketing homepage at `/` featuring top header, hero CTA, 4 live-style preview metric cards, 6 differentiating capability cards, and footer linking to `/app`, `/app/data-quality`, and Swagger docs.
- **`LoginPage.jsx`** (`LoginPage()`): Sign-in page at `/login` pre-filled with demo credentials, integrated with `GoogleSignInButton`, and smart error handling for `403 EMAIL_NOT_VERIFIED` via `handleGoVerifyOTP()` (which triggers OTP resend and navigates straight to `/register` verification mode). Handles `handleLogin()`.
- **`RegisterPage.jsx`** (`RegisterPage()`): Two-step signup page at `/register`. Step `'form'` offers `GoogleSignInButton` or Gmail registration (name, Gmail, optional E.164 phone validated by `/^\+[1-9]\d{6,14}$/`, password/confirm check) via `handleRegister()`. Step `'verify-otp'` collects the 6-digit OTP (`handleVerifyOTP()`) with a 30-second countdown resend button (`handleResendOTP()`).
- **`DashboardPage.jsx`** (`DashboardPage()`): Main executive view at `/app`. Parallel-fetches KPIs, top 5 players, and country analytics on mount, rendering 4 KPI cards, Top Official Circuit Competitors table, Top Seed 5-Axis ML Radar card, and Recharts National Player Count bar chart.
- **`PlayerExplorerPage.jsx`** (`PlayerExplorerPage()`): Searchable, country-filterable card grid of players at `/app/players` showing world rank, cluster tier, points volume, tournaments, consistency progress bar, and links to Compare / Profile.
- **`PlayerDetailPage.jsx`** (`PlayerDetailPage()`): Dynamic dossier at `/app/players/:id` reading `useParams().id`, showing hero stats strip, Bookmark toggle button, `PlayerRadarChart` + 5 trait progress bars, AI Player Intelligence Brief, and 3 Euclidean nearest-neighbor similar players with one-click compare links.
- **`ComparisonPage.jsx`** (`ComparisonPage()`): Head-to-head page at `/app/compare` (supports `?player_a=...&player_b=...` query params), two player dropdowns, dual `PlayerRadarChart` overlay, AI comparison summary card, data-gap notice, and row-by-row statistical edge table.
- **`GlobalIntelligencePage.jsx`** (`GlobalIntelligencePage()`): Country analytics page at `/app/global` showing active federations, venue count, leading federation, a horizontal Recharts bar chart of total points per nation, and a National Performance Index table.
- **`CompetitionExplorerPage.jsx`** (`CompetitionExplorerPage()`): Tabbed explorer at `/app/competitions` toggling between `competitions` (with category filter pills: All, Grand Slam, ATP, ITF) and `venues` (court name, city, country code, timezone, parent sports complex).
- **`AIAssistantPage.jsx`** (`AIAssistantPage()`): Chat analyst interface at `/app/assistant` with `STARTER_PROMPTS` quick pills, scrollable message stream displaying entity citation badges (`entity`, `reference_id`), loading indicator, and `handleSend()` form submission to `/api/v1/assistant/chat`.
- **`WorkspacePage.jsx`** (`WorkspacePage()`): Analyst workspace at `/app/workspace`. Displays user profile, Email Verified / Google Linked / Phone Verified badges, free SMS OTP verification workflow (`handleSendPhoneOTP()`, `handleVerifyPhoneOTP()`), watchlist cards, and client-side CSV generator (`handleDownloadCSV()`).
- **`ReportsPage.jsx`** (`ReportsPage()`): Reporting hub at `/app/reports` allowing filtering by Country and Cluster Tier, dynamic KPI recalculation (cumulative points & mean consistency), filtered table preview, browser print/PDF trigger (`handlePrint()`), and CSV export (`exportCSV()`).
- **`DataQualityPage.jsx`** (`DataQualityPage()`): Pipeline audit console at `/app/data-quality` fetching `/api/v1/admin/data-quality` and rendering sync health cards (`LIVE SUCCESS`, records processed, `0 DROPPED` duplicates, `100.0%` completeness) plus an entity-by-entity audit table.

---

*End of complete documentation.*
