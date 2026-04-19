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