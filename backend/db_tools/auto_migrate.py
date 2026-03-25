"""
auto_migrate.py — Startup script to automatically apply pending migrations.

This script scans 'migration_data/' for timestamped backup files (*.db)
and applies the latest one if it hasn't been recorded in the 'migrations' table.
"""

import logging
import re
import sqlite3
from pathlib import Path
from db_tools.importer import import_sqlite, ensure_migration_table, is_migration_applied, record_migration
from db_tools.cli import _DEFAULT_DB

logger = logging.getLogger(__name__)

_MIGRATION_DIR = Path("migration_data")
_FILE_PATTERN = re.compile(r"backup_(\d+)\.db$")

def run_auto_migrate(db_path: Path):
    """
    Find and apply the newest pending migration.
    """
    if not _MIGRATION_DIR.exists():
        logger.info("No migration_data directory found. Skipping.")
        return

    # 1. Identify all backup files and their timestamps
    candidates = []
    for f in _MIGRATION_DIR.glob("backup_*.db"):
        match = _FILE_PATTERN.match(f.name)
        if match:
            candidates.append((match.group(1), f))

    if not candidates:
        logger.info("No migration files found in %s.", _MIGRATION_DIR)
        return

    # Sort by timestamp descending (newest first)
    candidates.sort(key=lambda x: int(x[0]), reverse=True)

    # 2. Connect and ensure table
    conn = sqlite3.connect(db_path)
    try:
        ensure_migration_table(conn)
        
        # 3. Find newest unapplied migration
        to_apply = None
        for ts_str, fpath in candidates:
            if not is_migration_applied(conn, ts_str):
                to_apply = (ts_str, fpath)
                break # We only need the newest one for full SQLite backups

        if not to_apply:
            logger.info("All found migrations are already applied.")
            conn.close()
            return

        ts_str, fpath = to_apply
        logger.info("Found pending migration: %s (timestamp=%s)", fpath.name, ts_str)

        # 4. Apply
        conn.close() # Close to avoid locking during backup
        import_sqlite(db_path, fpath)
        
        # 5. Re-check/Re-record in the restored DB
        conn = sqlite3.connect(db_path)
        ensure_migration_table(conn)
        record_migration(conn, ts_str, fpath.name)
        conn.commit()
        logger.info("✓ Migration %s successfully applied.", fpath.name)

    finally:
        conn.close()

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
    db = Path(_DEFAULT_DB)
    run_auto_migrate(db)
