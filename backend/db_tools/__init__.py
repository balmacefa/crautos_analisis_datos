"""
db_tools — Import / Export tooling for the CrAutos SQLite database.

Usage
-----
  python -m db_tools export --format json   --db ./data/crautos.db --out export.json
  python -m db_tools export --format csv    --db ./data/crautos.db --out export_cars.csv
  python -m db_tools export --format sqlite --db ./data/crautos.db --out backup.db

  python -m db_tools import --format json   --db ./data/crautos.db --src export.json [--dry-run]
  python -m db_tools import --format csv    --db ./data/crautos.db --src export_cars.csv [--dry-run]
  python -m db_tools import --format sqlite --db ./data/crautos.db --src backup.db [--dry-run]
"""
