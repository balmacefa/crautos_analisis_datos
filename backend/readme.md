# CrAutos Backend & Data Scraper

This directory contains the Playwright-based web scraper to extract car data and the FastAPI application to serve it.

## Running Locally

To set up and run the backend components locally, follow these steps:

1. **Create and activate a virtual environment:**

   ```bash
   python -m venv venv
   ```

   - Windows:
     ```bash
     .\venv\Scripts\activate
     ```
   - macOS / Linux:
     ```bash
     source venv/bin/activate
     ```

2. **Install requirements:**

   ```bash
   pip install -r requirements.txt
   ```

3. **Install Playwright browsers:**

   ```bash
   playwright install
   ```

### Running the Scraper

To manually run the Playwright web scraper locally, you can use the `data_scrapper` module. The data will be saved to an SQLite database (by default, `data/crautos.db`).

```bash
# Scrape car listing URLs
python -m data_scrapper.run_scraper urls

# Scrape detailed information for each car URL
python -m data_scrapper.run_scraper details

# Scrape both URLs and detailed information sequentially
python -m data_scrapper.run_scraper all
```

### Running the API

To start the FastAPI server locally:

```bash
python -m uvicorn api.main:app --reload
```

The API will be accessible at `http://localhost:8000`, and the interactive Swagger documentation will be available at `http://localhost:8000/docs`.

### Running Tests

To run the unit tests for the API and other backend components:

```bash
pytest
```

## Technical Scripts & Tooling

The backend includes several scripts and tools for database migration, data cleaning, operations, and Docker setups:

### Database Tooling (`db_tools/`)
- `python -m db_tools.cli`: A CLI utility for exporting and importing the SQLite database data. Supports JSON, CSV, and SQLite binary formats. Example: `python -m db_tools export --format json --db ./data/crautos.db`
- `python -m db_tools.auto_migrate`: A startup script intended to automatically detect and apply the latest pending SQLite database backup/migration located in the `migration_data/` directory.

### Data Operations (`data_ops/`)
- `build_fts.py`: Connects to the SQLite database and populates an FTS5 (Full-Text Search) virtual table (`car_details_fts`) to enable fast text searches across the scraped cars.
- `data_cleaner.py`: Normalizes and cleans raw scraped JSON files in the `datos_vehiculos/` directory (e.g., swapping inverted prices, standardizing numeric fields).
- `03_modeling.py`: Trains a `RandomForestRegressor` to predict car prices using the cleaned CSV data (`output/data/cleaned_cars.csv`), saving the model to `models/car_price_model.pkl` and a feature importance plot to `output/plots/`.
- `04_reporting_dashboard.py`: A standalone Dash application that provides a dashboard specifically for the trained prediction model and historical price depreciation insights.

### DevOps Job Orchestrator (`cron/`)
- `devops_job_orchestrator.py`: A production-grade web application built with Dash and Flask. It provides a real-time GUI for managing, scheduling, and monitoring cron jobs. Features include PTY-based unbuffered I/O, secure HTTP Basic Auth, and interactive real-time logging.
- `job_definitions.py`: Configuration file that returns the list of `JobModel` instances to be registered and scheduled by the orchestrator.
- `job_model.py`: Defines the `JobModel` dataclass used to represent the state, metadata, and subprocess details of each scheduled job.

### Shell Scripts (`sh_scripts/`)
- `entrypoint.sh`: Used as the main Docker entrypoint script.
- `setup.sh`: Used for setting up the Docker images.
