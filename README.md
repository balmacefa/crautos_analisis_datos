# CrAutos Marketplace Scraper & API

CrAutos is a comprehensive marketplace of cars in Costa Rica. This project provides a robust data pipeline, backend API, and a visualization frontend to scrape, serve, and analyze vehicle data.

## Project Architecture

The project consists of several components, all containerized and orchestrated via Docker Compose:

1. **Backend API (FastAPI)**: Serves the scraped car data and analytical insights via REST endpoints. Found in the `backend/` directory.
2. **Frontend Dashboard (Dash)**: A Python Dash application that provides a user interface to search for cars and view market statistics. Found in the `frontend/` directory.
3. **Data Scraper (Playwright)**: An asynchronous web scraper built with Playwright that periodically extracts data from the target website. Located within the `backend/` directory.
4. **Task Scheduler (Cron)**: A Python-based cron job scheduler that automates the daily execution of the data scraper.
5. **Database (SQLite)**: A shared SQLite database used to store the scraped data, accessible by both the scraper and the API.

## Running the Project

The easiest way to run the project is using Docker Compose. Make sure you have Docker and Docker Compose installed on your system.

### Development Environment

To start the project in development mode:

```bash
docker compose -f docker-compose.dev.yml up -d --build
```

This will spin up the `api`, `frontend`, and `scheduler` services. The `scraper` container will be built and remain idle, ready for manual execution or automated scheduling.

- The Backend API will be available at `http://localhost:8000` (Swagger docs at `/docs`).
- The Frontend Dash UI will be available at `http://localhost:8050`.

#### Manually Triggering the Scraper

In development mode, you can manually trigger the scraper by executing a command within the running `scraper` container:

```bash
# Scrape only URLs
docker compose -f docker-compose.dev.yml exec scraper python -m data_scrapper.run_scraper urls

# Scrape all details
docker compose -f docker-compose.dev.yml exec scraper python -m data_scrapper.run_scraper all
```

### Production Environment

To run the project in production mode:

```bash
docker compose -f docker-compose.prod.yml up -d --build
```

In production, the `scheduler` service is configured to run the scraper periodically (e.g., at 07:00, 13:00, and 19:00 daily). The frontend service is exposed on port 8050, but the API service is only exposed internally to the Docker network.

## Further Documentation

For more detailed instructions on setting up and running individual components locally, please refer to the specific README files:

- [Backend README](backend/readme.md)
- [Frontend README](frontend/readme.md)
