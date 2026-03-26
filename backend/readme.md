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
