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

### Changed
- **API Performance Optimization**: 
  - *What:* Refactored completely away from fetching all SQLite rows into Python memory and parsing JSON via Python loops.
  - *Why:* Fetching and iterating through the entire database in Python memory scales poorly. Instead, we offloaded sorting, filtering, and aggregation to the database using SQLite's native `json_extract()` function to ensure the API uses minimal memory.
- **Database Index Optimization (`backend/data_scrapper/repository.py`)**:
  - *What:* Added expression-based SQLite indexes (`CREATE INDEX`) targeting the JSON extractions of `marca`, `modelo`, and `año` inside the `raw_json` column of the `car_details` table.
  - *Why:* Even though filtering happens in SQLite now, applying `WHERE json_extract(...)` natively requires a full table scan. Creating these indexes pre-caches the values in a B-Tree structure, accelerating query lookups and aggregation metrics from O(N) linear time to O(log N) near-instant execution.
- **Async Database Driver (`backend/api/database.py`, `backend/api/main.py`)**:
  - *What:* Replaced standard `sqlite3` driver with the `aiosqlite` async library. Refactored all FastAPI endpoints to be native `async def`.
  - *Why:* Unblocks the FastAPI event loop during I/O bound SQLite data retrievals, allowing the backend to scale and serve high concurrency traffic without locking the server thread.
- **API Caching (`backend/api/main.py`)**:
  - *What:* Added an in-memory TTL Cache (via `asyncache` and `cachetools`) set to 1 hour (3600 seconds) for the three aggregate insight endpoints (`/summary`, `/brands`, `/years`).
  - *Why:* These insight calculations don't need to be run per-request since the underlying scraper data updates infrequently. Serving them from cache guarantees immediate zero-latency responses.
