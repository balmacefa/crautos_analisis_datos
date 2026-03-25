"""
exporter.py — Export CrAutos SQLite database to JSON, CSV, or SQLite backup.

Supported formats
-----------------
  json   : Exports car_details (with raw_json fields flattened) and car_urls
            as a JSON file with top-level keys per table.
  csv    : Exports car_details (flattened) as a single CSV file.
  sqlite : Binary backup of the entire database using sqlite3.Connection.backup().
"""

import csv
import io
import json
import logging
import shutil
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Literal

logger = logging.getLogger(__name__)

ExportFormat = Literal["json", "csv", "sqlite"]

# Tables included in full exports
_TABLES = ["scrape_runs", "car_urls", "car_details", "pagination_progress"]

_MIGRATION_DIR = Path("migration_data")


def get_default_export_path(fmt: ExportFormat) -> Path:
    """
    Return a default output path in migration_data/ with a Unix timestamp.
    Example: migration_data/backup_1616584200.db
    """
    _MIGRATION_DIR.mkdir(parents=True, exist_ok=True)
    ts = int(datetime.now(timezone.utc).timestamp())
    ext = "json" if fmt == "json" else "csv" if fmt == "csv" else "db"
    return _MIGRATION_DIR / f"backup_{ts}.{ext}"


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _connect(db_path: Path) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path, timeout=30)
    conn.row_factory = sqlite3.Row
    return conn


def _fetch_table(conn: sqlite3.Connection, table: str) -> list[dict]:
    """Return all rows of *table* as plain dicts."""
    rows = conn.execute(f"SELECT * FROM {table}").fetchall()  # noqa: S608
    return [dict(r) for r in rows]


def _flatten_car_details(rows: list[dict]) -> list[dict]:
    """
    Expand the raw_json column of car_details rows into individual fields.
    The result dict puts car_id / url / scraped_at first, then all car fields.
    """
    out = []
    for r in rows:
        base = {
            "car_id": r["car_id"],
            "url": r["url"],
            "scraped_at": r["scraped_at"],
        }
        try:
            car_data = json.loads(r.get("raw_json", "{}"))
        except (json.JSONDecodeError, TypeError):
            car_data = {}
        out.append({**base, **car_data})
    return out


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def export_json(db_path: Path, out_path: Path, tables: list[str] | None = None) -> int:
    """
    Export selected *tables* (default: all) to a JSON file at *out_path*.

    Returns the total number of rows exported.
    """
    tables = tables or _TABLES
    out_path.parent.mkdir(parents=True, exist_ok=True)

    conn = _connect(db_path)
    total = 0
    payload: dict[str, list[dict]] = {}
    try:
        for table in tables:
            try:
                rows = _fetch_table(conn, table)
            except sqlite3.OperationalError:
                logger.warning("Table %r not found – skipping.", table)
                rows = []
            if table == "car_details":
                rows = _flatten_car_details(rows)
            payload[table] = rows
            total += len(rows)
    finally:
        conn.close()

    payload["_meta"] = {
        "exported_at": datetime.now(timezone.utc).isoformat(),
        "db_path": str(db_path),
        "tables": tables,
    }

    out_path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, default=str),
        encoding="utf-8",
    )
    logger.info("JSON export → %s  (%d total rows)", out_path, total)
    return total


def export_csv(db_path: Path, out_path: Path) -> int:
    """
    Export car_details (flattened) to a CSV file at *out_path*.

    Returns the number of rows written.
    """
    out_path.parent.mkdir(parents=True, exist_ok=True)

    conn = _connect(db_path)
    try:
        rows = _fetch_table(conn, "car_details")
    finally:
        conn.close()

    if not rows:
        logger.warning("car_details is empty – CSV file will only have a header.")
        out_path.write_text("", encoding="utf-8")
        return 0

    flat = _flatten_car_details(rows)
    # Gather a stable superset of all keys (preserving insertion order)
    all_keys: list[str] = []
    seen: set[str] = set()
    for row in flat:
        for k in row:
            if k not in seen:
                all_keys.append(k)
                seen.add(k)

    buf = io.StringIO()
    writer = csv.DictWriter(buf, fieldnames=all_keys, extrasaction="ignore")
    writer.writeheader()
    writer.writerows(flat)

    out_path.write_text(buf.getvalue(), encoding="utf-8")
    logger.info("CSV export → %s  (%d rows)", out_path, len(flat))
    return len(flat)


def export_sqlite(db_path: Path, out_path: Path) -> None:
    """
    Create a binary SQLite backup of *db_path* at *out_path*.
    Uses the sqlite3 online backup API so the source DB can remain open.
    """
    out_path.parent.mkdir(parents=True, exist_ok=True)

    src = sqlite3.connect(db_path, timeout=30)
    dst = sqlite3.connect(out_path)
    try:
        src.backup(dst, pages=100)
        logger.info("SQLite backup → %s", out_path)
    finally:
        dst.close()
        src.close()

    # --- Verification Step ---
    if not validate_sqlite_backup(db_path, out_path):
        logger.error("SQLite backup verification FAILED for %s", out_path)
        raise RuntimeError(f"Backup verification failed: {out_path}")
    logger.info("SQLite backup verification PASSED.")


def validate_sqlite_backup(src_path: Path, dst_path: Path) -> bool:
    """
    Compare row counts and run integrity check on the backup.
    Returns True if valid, False otherwise.
    """

    def get_stats(path: Path) -> dict[str, int]:
        conn = sqlite3.connect(path)
        try:
            # Check integrity
            res = conn.execute("PRAGMA integrity_check").fetchone()
            if not res or res[0] != "ok":
                logger.error("Integrity check failed for %s: %s", path, res)
                return {}

            # Count rows per table
            tabs = conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'"
            ).fetchall()
            stats = {}
            for (tname,) in tabs:
                stats[tname] = conn.execute(f'SELECT COUNT(*) FROM "{tname}"').fetchone()[0]
            return stats
        finally:
            conn.close()

    src_stats = get_stats(src_path)
    dst_stats = get_stats(dst_path)

    if not src_stats or not dst_stats:
        return False

    if src_stats != dst_stats:
        logger.error("Row count mismatch between source and backup!")
        logger.error("Source: %s", src_stats)
        logger.error("Backup: %s", dst_stats)
        return False

    return True


# ---------------------------------------------------------------------------
# Convenience dispatcher
# ---------------------------------------------------------------------------

def export(
    fmt: ExportFormat,
    db_path: str | Path,
    out_path: str | Path,
    tables: list[str] | None = None,
) -> None:
    """Dispatch export to the appropriate function based on *fmt*."""
    db_path = Path(db_path)
    out_path = Path(out_path)

    if not db_path.exists():
        raise FileNotFoundError(f"Database not found: {db_path}")

    if fmt == "json":
        export_json(db_path, out_path, tables=tables)
    elif fmt == "csv":
        export_csv(db_path, out_path)
    elif fmt == "sqlite":
        export_sqlite(db_path, out_path)
    else:
        raise ValueError(f"Unknown export format: {fmt!r}. Choose json | csv | sqlite.")
