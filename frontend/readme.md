# CrAutos Frontend Dashboard

This is a Python Dash application that interacts with the backend API to pull data, providing a user interface to search for cars and view market statistics.

## Running Locally

To run the frontend dashboard locally, follow these steps:

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

3. **Set the `API_BASE` environment variable:**

   By default, the application will look for the backend API at `http://localhost:8000`. If your API is running on a different port or host, you can set the `API_BASE` environment variable.

   - Windows (PowerShell):
     ```bash
     $env:API_BASE="http://localhost:8000"
     ```
   - macOS / Linux:
     ```bash
     export API_BASE="http://localhost:8000"
     ```

4. **Run the Dash app:**

   ```bash
   python app.py
   ```

The dashboard will be available at `http://localhost:8050`.
