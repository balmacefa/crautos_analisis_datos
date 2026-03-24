# Changelog

All notable changes to this project will be documented in this file.

## [Unreleased]

### Added
- **Backend API Service**: Implemented a new REST API using FastAPI to serve the scraped car data and provide analytical insights.
  - Added dependencies `fastapi`, `uvicorn`, and `pydantic` to `backend/requirements.txt`.
  - Created `backend/api/database.py` to manage a read-only SQLite connection to `data/crautos.db`.
  - Created `backend/api/models.py` with Pydantic schemas validating responses and defining the data structures (e.g., `CarDetail`, `SummaryStats`).
  - Created `backend/api/main.py` containing endpoints:
    - `GET /api/cars`: Paginated list of cars supporting filtering by `marca`, `modelo`, `year_min`, and `year_max`.
    - `GET /api/cars/{car_id}`: Fetch detailed scraped data for a single car.
    - `GET /api/insights/summary`: High-level aggregated statistics (total listings, average prices, top brands).
    - `GET /api/insights/brands`: Aggregated volume and average prices grouped by car brand.
    - `GET /api/insights/years`: Aggregated metrics based on manufacturing year.
- **API Unit Testing**: Added an async pytest suite (`backend/tests/test_api.py`) covering all FastAPI endpoints via `httpx.ASGITransport`.
- **API Dockerization**: Created a standalone Docker container (`backend/Dockerfile.api`) for serving the API endpoints scalably.
- **Docker Compose Setup**: Integrated the API into both `docker-compose.dev.yml` and `docker-compose.prod.yml`, ensuring appropriate volume mappings to the shared SQLite instance.
- **Search Engine**: Implemented SQLite FTS5 full‑text search and added `/api/search` endpoint.
- **Frontend Dash Service**: Added a Dash app (`frontend/app.py`) with a search bar that queries the `/api/search` endpoint and displays results in a table. Dockerized via `frontend/Dockerfile` and added to compose.

### Changed
- **API Performance Optimization**: Refactored to use SQLite `json_extract()` for filtering and aggregation, removing heavy Python processing.
- **Database Index Optimization (`backend/data_scrapper/repository.py`)**: Added expression‑based SQLite indexes for `marca`, `modelo`, and `año`.
- **Async Database Driver (`backend/api/database.py`, `backend/api/main.py`)**: Switched to `aiosqlite` for non‑blocking I/O.
- **API Caching (`backend/api/main.py`)**: Added in‑memory TTL cache for insight endpoints.

## Execution

### Prerequisites
- Docker and Docker Compose installed.
- Python 3.10+ if running locally without Docker.

### Running with Docker (recommended)

```bash
# Start the backend API
docker compose -f docker-compose.dev.yml up -d api

# Start the Dash frontend
docker compose -f docker-compose.dev.yml up -d frontend
```

The API will be available at `http://localhost:8000` (Swagger docs at `/docs`).
The Dash UI will be available at `http://localhost:8050`.

### Running locally without Docker

```bash
# Backend
cd backend
python -m uvicorn api.main:app --reload

# Frontend (in a separate terminal)
cd frontend
python app.py
```

### Running tests

```bash
cd backend
pytest -q
```
