#!/bin/bash
set -e

echo "[entrypoint] Starting CrAutos Backend..."

# 1. Run automated migrations
echo "[entrypoint] Checking for pending migrations..."
python -m db_tools.auto_migrate

# 2. Sync data to Typesense
echo "[entrypoint] Syncing data to Typesense..."
python -m data_ops.sync_typesense

# 3. Start the main process (as defined in CMD or passed via docker run)
exec "$@"
