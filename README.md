# 🎾 TENNIS INTELLIGENCE PLATFORM (TIP)
### AI-Powered Tennis Analytics, Player Intelligence, Ranking Analysis & Smart Insights
*A Capstone & Industry-Grade Sports SaaS Platform Engineered by a 4-Member B.Tech IT Team*

---

## 🌟 Executive Project Overview
The **Tennis Intelligence Platform (TIP)** is a full-stack sports technology SaaS product that ingests live data from the official **SportRadar Tennis API**, transforms and normalizes hierarchical structures into a **3NF PostgreSQL database**, applies **Scikit-Learn Machine Learning clustering**, provides **context-grounded AI sports analytics**, and renders an eye-catching, responsive sports dashboard built with **React 18, Tailwind CSS, and Recharts**.

### 🎨 Visual Identity & Design System
* **Primary Background:** Midnight Navy (`#0B1220`)
* **Card & Surface Background:** Deep Slate Glass (`#111B2E`, `#172338`) with subtle border glows (`#263449`)
* **Primary Brand Accent:** Tennis Court Volt Green (`#B7F34A` / `#CCFF00`)
* **Secondary Accent:** Electric Cyan / Aqua (`#43C6AC`)
* **Typography:** `Manrope` (Headings), `Inter` (UI/Body), `JetBrains Mono` (Metrics & Rankings)

---

## 🚀 The 6 Unique Differentiating Features

1. **Player Intelligence Profile:**
   Complete competitor dossiers featuring an explainable **5-Axis ML Trait Radar** (*Consistency*, *Power Volume*, *Tournament Stamina*, *Rank Momentum*, and *Efficiency*), official world rankings, and automated similar-player recommendations.
2. **Smart Head-to-Head Comparison:**
   Side-by-side player evaluation comparing points volume, tournament frequency, and efficiency ratios with automated statistical advantage badges and dual radar chart overlays.
3. **Data-Grounded AI Tennis Assistant:**
   An intelligent sports chat analyst executing strictly parameterized, read-only analytical queries against database records with zero hallucination and cited data references.
4. **Global Tennis Geographic Intelligence:**
   Interactive national density maps and federation rankings evaluating player counts and cumulative point distribution per country.
5. **Data Quality & Freshness Monitoring Center:**
   Live administrative auditing dashboard displaying API sync telemetry, duplicate detection counters (0 duplicates), and column completeness ratios (100% verified).
6. **Personalized Analyst Workspace:**
   Interactive user workspace allowing analysts to bookmark favorite competitors, persist comparison pairs, and export custom analytical datasets to CSV.

---

## 👥 4-Member Team Division & Deliverables

| Team Member | Role | Primary Tech Stack | Key Deliverables |
|---|---|---|---|
| **Member 1** | **Backend & API Architect** | FastAPI, Python, Pydantic, JWT, Bcrypt | REST API endpoints (`/api/v1`), Swagger docs, JWT auth, request throttling, error handlers. |
| **Member 2** | **Data Engineer & Database Architect** | PostgreSQL, SQLAlchemy, Pandas, NumPy | 3NF Schema, ETL normalization pipeline, 20 analytical SQL queries, CSV staging. |
| **Member 3** | **Frontend & UI/UX Specialist** | React 18, Tailwind CSS, Recharts, Axios | Responsive SaaS dashboard, Landing page, 5-Axis Radar charts, Player Explorer, comparison UI. |
| **Member 4** | **AI/ML & DevOps Engineer** | Scikit-Learn, Pytest, Docker, GitHub Actions | K-Means clustering, AI assistant tool callers, Docker Compose, CI/CD pipeline, test suites. |

---

## 📊 All 20 Curriculum Analytical SQL Queries (Verified)

All queries are located in [`sql/queries.sql`](file:///C:/Users/sagni/.gemini/antigravity/scratch/tennis-intelligence-platform/sql/queries.sql) and verified in [`sql/test_queries.py`](file:///C:/Users/sagni/.gemini/antigravity/scratch/tennis-intelligence-platform/sql/test_queries.py):

* **Part 1: Competitions & Categories (Q1 – Q7)**
  1. *List all competitions along with their category name.*
  2. *Count the number of competitions in each category.*
  3. *Find all competitions of type 'doubles'.*
  4. *Get competitions that belong to a specific category (e.g. ITF Men).*
  5. *Identify parent competitions and their sub-competitions.*
  6. *Analyze the distribution of competition types by category.*
  7. *List all competitions with no parent (top-level competitions).*
* **Part 2: Complexes & Venues (Q8 – Q14)**
  8. *List all venues along with their associated complex name.*
  9. *Count the number of venues in each complex.*
  10. *Get details of venues in a specific country (e.g. Chile).*
  11. *Identify all venues and their timezones.*
  12. *Find complexes that have more than one venue.*
  13. *List venues grouped by country.*
  14. *Find all venues for a specific complex (e.g. Nacional).*
* **Part 3: Competitors & Rankings (Q15 – Q20)**
  15. *Get all competitors with their rank and points.*
  16. *Find competitors ranked in the top 5.*
  17. *List competitors with no rank movement (stable rank).*
  18. *Get the total points of competitors from a specific country (e.g. Croatia).*
  19. *Count the number of competitors per country.*
  20. *Find competitors with the highest points in the current week.*

---

## 💻 How to Run the Project Locally

### 1. Prerequisites
* Python 3.10+
* Node.js 18+ and npm

### 2. Backend Setup
```powershell
cd C:\Users\sagni\.gemini\antigravity\scratch\tennis-intelligence-platform

# Install dependencies
pip install -r requirements.txt

# Run database seed and verification
python sql/seed_database.py
python sql/test_queries.py
python backend/test_backend.py

# Launch FastAPI Server
uvicorn backend.app.main:app --host 0.0.0.0 --port 8000 --reload
```
* Interactive Swagger Docs: `http://localhost:8000/docs`
* Alternative Redoc: `http://localhost:8000/redoc`

### 3. Frontend Setup
```powershell
cd C:\Users\sagni\.gemini\antigravity\scratch\tennis-intelligence-platform\frontend

# Install dependencies (already built & verified)
npm install

# Start Vite Development Server
npm run dev
```
* Open in browser: `http://localhost:5173`
* Demo Login: `analyst@tennisintel.com` / `Analyst@123`

---

## 🐳 Running with Docker Compose
```bash
docker-compose up --build
```
* Frontend available at `http://localhost:3000`
* Backend available at `http://localhost:8000`
* PostgreSQL available on port `5432`

---

## 🎓 College Viva & Interview Preparation Guide

1. **Why FastAPI over Flask/Django?**
   FastAPI provides native asynchronous operations, automated OpenAPI documentation (`/docs`), and compile-time data validation using Pydantic.
2. **How does the AI Assistant avoid hallucinations?**
   The AI engine executes strictly parameterized read-only analytical functions against the database. It answers only based on returned SQL records and provides direct entity citations.
3. **How does the ML clustering work?**
   We extract four normalized features: total points, competitions played, rank movement, and points per tournament efficiency. We apply `MinMaxScaler` followed by `KMeans(n_clusters=3)` to classify competitors into *Elite Grand Slam Tier*, *High-Yield Contender*, and *Challenger Circuit*.
4. **How are SportRadar API rate limits respected?**
   Our `SportRadarClient` enforces a 1 request/second throttling interval and applies exponential backoff ($2^1, 2^2, 2^3$) on HTTP 429 or 5xx responses, falling back to cached fixtures if quotas expire.
