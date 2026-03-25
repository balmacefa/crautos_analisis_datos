"""
importer.py — Import CrAutos database content from JSON, CSV, or SQLite backup.

Supported formats
-----------------
  json   : Reads a file produced by exporter.export_json() and upserts rows
            into car_urls and car_details.
  csv    : Reads a flat CSV (as produced by exporter.export_csv()) and upserts
            rows into car_details, packing unknown columns back into raw_json.
  sqlite : Replaces the live DB with a backup using sqlite3.Connection.backup().
            When --dry-run is used, the live DB is NOT modified; a temp file is
            validated instead.

Safety
------
  * All JSON/CSV imports use INSERT OR REPLACE (upsert) – existing rows with the
    same primary key are overwritten, other rows are untouched.
  * The --dry-run flag performs all parsing and validation but skips writes.
  * For sqlite imports, the live file is only replaced after a successful backup.
"""

import csv
import json
import logging
import shutil
import sqlite3
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Literal

logger = logging.getLogger(__name__)

ImportFormat = Literal["json", "csv", "sqlite"]


def ensure_migration_table(conn: sqlite3.Connection) -> None:
    """Ensure the migrations table exists."""
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS migrations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL UNIQUE,
            filename TEXT NOT NULL,
            applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
    )


def is_migration_applied(conn: sqlite3.Connection, timestamp: str) -> bool:
    """Check if a migration with the given timestamp has already been applied."""
    res = conn.execute("SELECT 1 FROM migrations WHERE timestamp = ?", (timestamp,)).fetchone()
    return res is not None


def record_migration(conn: sqlite3.Connection, timestamp: str, filename: str) -> None:
    """Record a successful migration application."""
    conn.execute(
        "INSERT INTO migrations (timestamp, filename) VALUES (?, ?)",
        (timestamp, filename),
    )

# Columns that live outside raw_json in car_details
_DETAIL_FIXED_COLS = {"car_id", "url", "scraped_at"}
# Columns that live in car_urls
_URL_COLS = {"url", "status", "retry_count", "created_at", "scraped_at", "is_active", "last_seen_at"}


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _connect(db_path: Path) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path, timeout=30)
    conn.row_factory = sqlite3.Row
    return conn


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _upsert_car_urls(conn: sqlite3.Connection, rows: list[dict]) -> int:
    """Upsert a list of car_urls dicts. Returns number of rows processed."""
    now = _now()
    count = 0
    for r in rows:
        conn.execute(
            """
            INSERT INTO car_urls (url, status, retry_count, created_at, is_active, last_seen_at)
            VALUES (:url, :status, :retry_count, :created_at, :is_active, :last_seen_at)
            ON CONFLICT(url) DO UPDATE SET
                status       = excluded.status,
                retry_count  = excluded.retry_count,
                scraped_at   = excluded.scraped_at,
                is_active    = excluded.is_active,
                last_seen_at = excluded.last_seen_at
            """,
            {
                "url":          r.get("url"),
                "status":       r.get("status", "done"),
                "retry_count":  r.get("retry_count", 0),
                "created_at":   r.get("created_at", now),
                "is_active":    r.get("is_active", 1),
                "last_seen_at": r.get("last_seen_at", now),
            },
        )
        count += 1
    return count


def _upsert_car_details_from_flat(conn: sqlite3.Connection, rows: list[dict]) -> int:
    """
    Upsert rows into car_details from flat dicts (as produced by the JSON/CSV export).
    Columns not in _DETAIL_FIXED_COLS are packed back into raw_json.
    Returns number of rows processed.
    """
    now = _now()
    count = 0
    for r in rows:
        car_id   = r.get("car_id")
        url      = r.get("url", "")
        scraped_at = r.get("scraped_at", now)

        if not car_id:
            logger.warning("Skipping row without car_id: %s", r)
            continue

        # Pack everything else back into raw_json
        car_data = {k: v for k, v in r.items() if k not in _DETAIL_FIXED_COLS}
        raw_json = json.dumps(car_data, ensure_ascii=False)

        # Ensure car_urls entry exists (FK constraint)
        conn.execute(
            """
            INSERT OR IGNORE INTO car_urls (url, status, retry_count, created_at, is_active)
            VALUES (?, 'done', 0, ?, 1)
            """,
            (url, scraped_at),
        )

        conn.execute(
            """
            INSERT OR REPLACE INTO car_details (car_id, url, raw_json, scraped_at)
            VALUES (?, ?, ?, ?)
            """,
            (car_id, url, raw_json, scraped_at),
        )
        count += 1
    return count


def _upsert_car_details_from_raw(conn: sqlite3.Connection, rows: list[dict]) -> int:
    """
    Upsert rows that still have a raw_json column (direct table dump).
    """
    now = _now()
    count = 0
    for r in rows:
        car_id     = r.get("car_id")
        url        = r.get("url", "")
        raw_json   = r.get("raw_json", "{}")
        scraped_at = r.get("scraped_at", now)

        if not car_id:
            logger.warning("Skipping row without car_id: %s", url)
            continue

        conn.execute(
            "INSERT OR IGNORE INTO car_urls (url, status, retry_count, created_at, is_active) VALUES (?, 'done', 0, ?, 1)",
            (url, scraped_at),
        )
        conn.execute(
            "INSERT OR REPLACE INTO car_details (car_id, url, raw_json, scraped_at) VALUES (?, ?, ?, ?)",
            (car_id, url, raw_json, scraped_at),
        )
        count += 1
    return count


# ---------------------------------------------------------------------------
# JSON import
# ---------------------------------------------------------------------------

def import_json(db_path: Path, src_path: Path, dry_run: bool = False) -> dict:
    """
    Import from a JSON export file.

    Returns a summary dict with keys: car_urls, car_details.
    """
    data = json.loads(src_path.read_text(encoding="utf-8"))

    # Detect format: flat (exported JSON has flattened car_details) vs raw
    car_detail_rows: list[dict] = data.get("car_details", [])
    car_url_rows:    list[dict] = data.get("car_urls", [])

    is_flat = car_detail_rows and "raw_json" not in car_detail_rows[0]

    logger.info(
        "JSON import: %d car_detail rows, %d car_url rows (flat=%s, dry_run=%s)",
        len(car_detail_rows), len(car_url_rows), is_flat, dry_run,
    )

    if dry_run:
        logger.info("[dry-run] No changes written.")
        return {"car_details": len(car_detail_rows), "car_urls": len(car_url_rows)}

    conn = _connect(db_path)
    try:
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA foreign_keys=ON")
        with conn:
            url_count = _upsert_car_urls(conn, car_url_rows)
            if is_flat:
                detail_count = _upsert_car_details_from_flat(conn, car_detail_rows)
            else:
                detail_count = _upsert_car_details_from_raw(conn, car_detail_rows)
    finally:
        conn.close()

    logger.info("JSON import done — car_urls: %d, car_details: %d", url_count, detail_count)
    return {"car_urls": url_count, "car_details": detail_count}


# ---------------------------------------------------------------------------
# CSV import
# ---------------------------------------------------------------------------

def import_csv(db_path: Path, src_path: Path, dry_run: bool = False) -> dict:
    """
    Import from a flat CSV export (as produced by export_csv).

    Returns a summary dict with key: car_details.
    """
    with src_path.open(newline="", encoding="utf-8") as fh:
        reader = csv.DictReader(fh)
        rows = list(reader)

    logger.info("CSV import: %d rows (dry_run=%s)", len(rows), dry_run)

    if dry_run:
        logger.info("[dry-run] No changes written.")
        return {"car_details": len(rows)}

    conn = _connect(db_path)
    try:
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA foreign_keys=ON")
        with conn:
            count = _upsert_car_details_from_flat(conn, rows)
    finally:
        conn.close()

    logger.info("CSV import done — car_details: %d", count)
    return {"car_details": count}


# ---------------------------------------------------------------------------
# SQLite backup import (restore)
# ---------------------------------------------------------------------------

def import_sqlite(db_path: Path, src_path: Path, dry_run: bool = False) -> dict:
    """
    Restore a SQLite backup over the live database.

    In dry-run mode the backup is validated (opened & PRAGMA integrity_check)
    but the live DB is NOT modified.

    Returns a summary dict with key: tables (list of tables in the backup).
    """
    # Validate source first
    try:
        check_conn = sqlite3.connect(src_path, timeout=10)
        result = check_conn.execute("PRAGMA integrity_check").fetchone()
        tables_rows = check_conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table'"
        ).fetchall()
        tables = [r[0] for r in tables_rows]
        check_conn.close()
    except sqlite3.DatabaseError as exc:
        raise ValueError(f"Source file is not a valid SQLite database: {exc}") from exc

    if result[0] != "ok":
        raise ValueError(f"Source database integrity check failed: {result[0]}")

    logger.info("SQLite restore: src=%s tables=%s (dry_run=%s)", src_path, tables, dry_run)

    if dry_run:
        logger.info("[dry-run] Validation passed. No changes written.")
        return {"tables": tables}

    # Restore: backup src → live db
    src_conn = sqlite3.connect(src_path, timeout=30)
    dst_conn = sqlite3.connect(db_path, timeout=30)
    try:
        src_conn.backup(dst_conn, pages=100)
        logger.info("SQLite restore done → %s", db_path)
    finally:
        dst_conn.close()
        src_conn.close()

    return {"tables": tables}


# ---------------------------------------------------------------------------
# Convenience dispatcher
# ---------------------------------------------------------------------------

def import_db(
    fmt: ImportFormat,
    db_path: str | Path,
    src_path: str | Path,
    dry_run: bool = False,
) -> dict:
    """Dispatch import to the appropriate function based on *fmt*."""
    db_path  = Path(db_path)
    src_path = Path(src_path)

    if not src_path.exists():
        raise FileNotFoundError(f"Source file not found: {src_path}")

    if fmt == "json":
        return import_json(db_path, src_path, dry_run=dry_run)
    elif fmt == "csv":
        return import_csv(db_path, src_path, dry_run=dry_run)
    elif fmt == "sqlite":
        return import_sqlite(db_path, src_path, dry_run=dry_run)
    else:
        raise ValueError(f"Unknown import format: {fmt!r}. Choose json | csv | sqlite.")
