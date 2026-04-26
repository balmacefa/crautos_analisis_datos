#!/bin/bash
set -e

echo "[entrypoint] Starting CrAutos Backend..."

# 1. Ensure SQLite database directory and basic integrity
DB_DIR="/app/data"
DB_PATH="${DB_DIR}/crautos.db"

echo "[entrypoint] Checking SQLite Database..."
mkdir -p "$DB_DIR"
if [ ! -f "$DB_PATH" ]; then
    echo "[entrypoint] Database not found at $DB_PATH. A new one will be created."
else
    echo "[entrypoint] Checking database integrity..."
    if ! sqlite3 "$DB_PATH" "PRAGMA integrity_check;" > /dev/null 2>&1; then
        echo "[entrypoint] WARNING: Database integrity check failed for $DB_PATH. Proceeding with caution."
    else
        echo "[entrypoint] Database integrity check passed."
    fi
fi

# 2. Run automated migrations
echo "[entrypoint] Checking for pending migrations..."
python -m db_tools.auto_migrate

# 3. Sync data to Typesense
echo "[entrypoint] Syncing data to Typesense..."
python -m data_ops.sync_typesense || echo "[entrypoint] Warning: Typesense sync failed. Is Typesense running?"

# 4. Start the main process (as defined in CMD or passed via docker run)
exec "$@"