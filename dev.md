# Development Guide

This document provides detailed instructions on how to run and develop for the CrAutos Analysis project.

## 🚀 Quick Start (Docker)

The fastest way to get the entire project (API, Scraper, and Dashboards) running is via Docker Compose.

```bash
# Build and start all services in the background
docker compose -f docker-compose.dev.yml up -d --build
```

### 📍 Service Map (Development)
| Service | URL | Description |
| :--- | :--- | :--- |
| **Backend API** | [http://localhost:8000](http://localhost:8000) | FastAPI with Swagger docs at `/docs` |
| **Job Orchestrator** | [http://localhost:8081](http://localhost:8081) | Dashboard to manage & trigger scrapers |
| **Dash Dashboard** | [http://localhost:8050](http://localhost:8050) | Main data visualization dashboard |
| **Wrapped UI** | [http://localhost:3001](http://localhost:3001) | Premium Next.js frontend |
| **Typesense** | [http://localhost:8108](http://localhost:8108) | Search engine API |

---

## ✨ Wrapped Frontend (Next.js)

The "Wrapped" experience is a separate Next.js application.

### Running with Docker (Automatic)
The service is automatically started at [http://localhost:3001](http://localhost:3001) when running the full stack.

### Running Locally (Manual)
If you want to run it without Docker's `wrapped` container:
```bash
cd wrapped-frontend
npm install
npm run dev
```
By default, this will run on [http://localhost:3000](http://localhost:3000).

---

## 🛠️ Scraper & Database Management

### 1. The Job Orchestrator (GUI)
Navigate to [http://localhost:8081](http://localhost:8081). 
*   **Default User:** `admin`
*   **Default Pass:** `admin` (Configurable via `AUTH_PASSWORD` in `.env`)

### 2. Manual CLI Execution
You can bypass the GUI and run tasks directly in the container:

```bash
# Scrape car listing URLs
docker compose -f docker-compose.dev.yml exec scraper python -m data_scrapper.run_scraper urls

# Scrape all details (requires URLs to be present)
docker compose -f docker-compose.dev.yml exec scraper python -m data_scrapper.run_scraper all

# Database Tooling: Export SQLite to JSON
docker compose -f docker-compose.dev.yml exec scraper python -m db_tools export --format json
```

---

## 🐍 Local Python Development (No Docker)

### 1. Backend & Scraper
```bash
cd backend
python -m venv venv
# Activate venv (.\venv\Scripts\activate on Windows)
pip install -r requirements.txt
playwright install
python -m uvicorn api.main:app --reload
```

### 2. Dashboard
```bash
cd frontend
pip install -r requirements.txt
$env:API_BASE="http://localhost:8000" # Windows
python app.py
```

---

## 🌐 Environment & Coolify

The project is compatible with [Coolify](https://coolify.io).

### Magic Environment Variables
For Service Stack deployments, Coolify can generate dynamic values:

| Variable Type | Purpose |
| :--- | :--- |
| `SERVICE_URL_<ID>` | Public URL for the service |
| `SERVICE_PASSWORD_<ID>` | Secure random string for `AUTH_PASSWORD` |

> [!IMPORTANT]
> Always check your `.env` file. If using Typesense, ensure `TYPESENSE_API_KEY` matches between the server and the frontend environment variables.

---

---

## 🤖 LLM_MANIFEST (v2 - High Density)
*Token-optimized context for AI onboarding. Load legend first.*

### 🔑 LEGEND
`:S:` Symbol | `:D:` Definition
- `$` : Logic_Node/Service
- `@` : FS_Path (Relative to root)
- `{}`: Entrypoint/CMD
- `&` : Stack/Dependency
- `!` : Feature/Meta
- `->`: Flow/Dependency
- `[T]`: Compressed_Dir_Tree

### 🧱 TOPOGRAPHY ($)
- **$BE_API**: `@/backend/api` {main.py} &FastAPI &SQLAlchemy !Swagger:/docs
- **$BE_SC**: `@/backend/data_scrapper` {run_scraper.py} &Playwright !ResumeSafe -> $SQL
- **$BE_OPS**: `@/backend/data_ops` {sync_typesense.py} !SQLite2Typesense !Cleaning
- **$FE_PR**: `@/wrapped-frontend` &NextJS &Tailwind !Premium_UI !Typesense_Search
- **$FE_LG**: `@/frontend` {app.py} &Dash &Plotly !Internal_Dashboard
- **$DB_SRC**: `@/backend/data/crautos.db` !SQLite_Source
- **$DB_VEC**: `@/typesense` &Typesense !Vector_Search_Engine

### 🌳 TREE_MAP [T] (90% Coverage)
- **/**: config:[.env, docker-compose.*.yml]
  - **backend/**:
    - **api/**: [{main,models,database}.py]
    - **data_scrapper/**: [{run_scraper,repository}.py, *_{scrapper.py,strategy.md}]
    - **data_ops/**: [sync_typesense,data_cleaner,03_modeling,04_reporting].py
    - **db_tools/**: [auto_migrate.py, migration_data/]
    - **tests/**: [test_*.py]
  - **frontend/**: [app.py, assets/]
  - **wrapped-frontend/**: [src/{app,components,lib}, scripts/, Dockerfile*]
  - **typesense/**: [Dockerfile.prod]

### 🔄 LIFECYCLE
1. **$BE_SC** -> **$DB_SRC** (Store raw/parsed listings)
2. **$BE_OPS** [sync_typesense] <- **$DB_SRC** -> **$DB_VEC** (Normalize & Vectorize)
3. **$FE_PR** <-> **$DB_VEC** (Fast Search/Filter)
4. **$FE_LG** <- **$DB_SRC** (Static Reporting)

### 🏁 EXECS
- **SCRAPE_ALL**: `docker exec -it scraper python -m data_scrapper.run_scraper all`
- **SYNC_SEARCH**: `python -m data_ops.sync_typesense`
- **MIGRATE**: `python -m db_tools.auto_migrate`
- **DEV_SH**: `docker compose -f docker-compose.dev.yml up`
- **PROD_DATA_EXPORT**: `ssh root@207.180.208.11 "docker exec \$(docker ps -q -f name=scraper) python -m db_tools export --format sqlite"`

---

## 🌍 Production Data Export

To pull data from the production server to your local development environment:

### 1. Manual Steps
If you want to run the process manually:

1.  **SSH into the server**:
    ```bash
    ssh root@207.180.208.11
    ```
2.  **Run the exporter in the scraper container**:
    ```bash
    docker exec $(docker ps -q -f name=scraper) python -m db_tools export --format sqlite --out /app/data/prod_dump.db
    ```
3.  **Download the file to your local machine**:
    ```bash
    # Run this on your LOCAL machine
    scp root@207.180.208.11:~/crautos_analisis_datos/data/prod_dump.db ./data/prod_dump.db
    ```

### 2. Automated Script
Use the provided utility script for a one-click sync:
```bash
bash get_data_from_prod.sh
```
This script handles container discovery, execution (defaulting to SQLite), and secure transfer.