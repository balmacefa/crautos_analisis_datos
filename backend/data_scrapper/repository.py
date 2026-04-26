"""
repository.py — SQLite data-access layer for the crautos scraper.

Tables
------
scrape_runs   : tracks execution sessions (start/end, status)
car_urls      : all discovered car URLs + their scrape status/retry count
car_details   : scraped structured data per car (stored as JSON)
"""

import json
import logging
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterator
import os
import typesense

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Schema
# ---------------------------------------------------------------------------

_DDL = """
PRAGMA journal_mode=WAL;
PRAGMA foreign_keys=ON;

CREATE TABLE IF NOT EXISTS scrape_runs (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    started_at  TEXT    NOT NULL,
    ended_at    TEXT,
    status      TEXT    NOT NULL DEFAULT 'running',   -- running | paused | done | failed | interrupted
    notes       TEXT
);

CREATE TABLE IF NOT EXISTS car_urls (
    url          TEXT    PRIMARY KEY,
    status       TEXT    NOT NULL DEFAULT 'pending',  -- pending | done | failed
    retry_count  INTEGER NOT NULL DEFAULT 0,
    created_at   TEXT    NOT NULL,
    scraped_at   TEXT,
    is_active    INTEGER NOT NULL DEFAULT 1,
    last_seen_at TEXT,
    source       TEXT                                -- Site identifier (e.g., 'CRAutos', 'EVMarket')
);

CREATE TABLE IF NOT EXISTS car_details (
    car_id       TEXT    PRIMARY KEY,
    url          TEXT    NOT NULL,
    raw_json     TEXT    NOT NULL,
    scraped_at   TEXT    NOT NULL,
    source       TEXT,                               -- Site identifier
    FOREIGN KEY (url) REFERENCES car_urls(url)
);

-- Stores mid-run checkpoint for the pagination scraper (Step 1).
-- Allows resuming from the last successfully completed page on restart.
CREATE TABLE IF NOT EXISTS pagination_progress (
    run_id       INTEGER PRIMARY KEY REFERENCES scrape_runs(id),
    last_page    INTEGER NOT NULL DEFAULT 0,
    total_pages  INTEGER NOT NULL DEFAULT 0,
    urls_json    TEXT    NOT NULL DEFAULT '[]',  -- JSON array of discovered URLs so far
    updated_at   TEXT    NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_car_urls_status ON car_urls(status);
CREATE INDEX IF NOT EXISTS idx_car_details_marca ON car_details(json_extract(raw_json, '$.marca'));
CREATE INDEX IF NOT EXISTS idx_car_details_modelo ON car_details(json_extract(raw_json, '$.modelo'));
CREATE INDEX IF NOT EXISTS idx_car_details_ano ON car_details(json_extract(raw_json, '$.año'));
"""


# ---------------------------------------------------------------------------
# Repository class
# ---------------------------------------------------------------------------

class ScraperRepository:
    """Thread-safe SQLite repository for the crautos scraper pipeline."""

    MAX_RETRIES = 3  # Mark URL as 'failed' permanently after this many attempts

    def __init__(self, db_path: str | Path):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()
        self._init_typesense()

    def _init_typesense(self):
        """Initialize Typesense client from environment variables."""
        try:
            host = os.getenv("TYPESENSE_HOST", "typesense")
            port = os.getenv("TYPESENSE_PORT", "8108")
            protocol = os.getenv("TYPESENSE_PROTOCOL", "http")
            api_key = os.getenv("TYPESENSE_API_KEY", "xyz123abc456")
            
            self.ts_client = typesense.Client({
                'nodes': [{
                    'host': host,
                    'port': port,
                    'protocol': protocol
                }],
                'api_key': api_key,
                'connection_timeout_seconds': 2
            })
            logger.info("Typesense client initialized (host: %s, port: %s)", host, port)
        except Exception as e:
            logger.error("Failed to initialize Typesense client: %s", e)
            self.ts_client = None

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    @contextmanager
    def _conn(self) -> Iterator[sqlite3.Connection]:
        """Yield a connection with row_factory set to sqlite3.Row."""
        conn = sqlite3.connect(self.db_path, timeout=30, check_same_thread=False)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    def _init_db(self) -> None:
        with self._conn() as conn:
            conn.executescript(_DDL)
            # Migration for soft deletes and source tracking
            migrations = [
                "ALTER TABLE car_urls ADD COLUMN is_active INTEGER NOT NULL DEFAULT 1",
                "ALTER TABLE car_urls ADD COLUMN last_seen_at TEXT",
                "ALTER TABLE car_urls ADD COLUMN source TEXT",
                "ALTER TABLE car_details ADD COLUMN source TEXT"
            ]
            for m in migrations:
                try:
                    conn.execute(m)
                except sqlite3.OperationalError:
                    pass
            
            # Create source index AFTER ensuring column exists
            try:
                conn.execute("CREATE INDEX IF NOT EXISTS idx_car_urls_source ON car_urls(source)")
            except sqlite3.OperationalError:
                pass
        logger.info("SQLite DB initialised at %s", self.db_path)

    @staticmethod
    def _now() -> str:
        return datetime.now(timezone.utc).isoformat()

    # ------------------------------------------------------------------
    # Run tracking
    # ------------------------------------------------------------------

    def start_run(self, notes: str = "") -> int:
        """Insert a new scrape_run row and return its id."""
        with self._conn() as conn:
            cur = conn.execute(
                "INSERT INTO scrape_runs (started_at, status, notes) VALUES (?, 'running', ?)",
                (self._now(), notes),
            )
            run_id = cur.lastrowid
        logger.info("Started scrape run #%d", run_id)
        return run_id

    def finish_run(self, run_id: int, status: str = "done") -> None:
        """Update a run's end time and final status."""
        if status not in ("done", "paused", "failed", "interrupted"):
            raise ValueError(f"Invalid run status: {status!r}")
        with self._conn() as conn:
            conn.execute(
                "UPDATE scrape_runs SET ended_at=?, status=? WHERE id=?",
                (self._now(), status, run_id),
            )
        logger.info("Run #%d finished with status '%s'", run_id, status)

    def get_active_run_id(self) -> int | None:
        """Return the id of any currently 'running' run, or None."""
        with self._conn() as conn:
            row = conn.execute(
                "SELECT id FROM scrape_runs WHERE status='running' ORDER BY started_at DESC LIMIT 1"
            ).fetchone()
        return row["id"] if row else None

    def interrupt_stale_runs(self) -> int:
        """
        Mark every 'running' row as 'interrupted' (they are orphaned from a
        previous process that died without a clean shutdown).
        Returns the number of rows updated.
        """
        now = self._now()
        with self._conn() as conn:
            cur = conn.execute(
                "UPDATE scrape_runs SET ended_at=?, status='interrupted'"
                " WHERE status='running'",
                (now,),
            )
            count = cur.rowcount
        if count:
            logger.warning("Marked %d stale running run(s) as 'interrupted'.", count)
        return count

    # ------------------------------------------------------------------
    # Pagination progress (Step 1 resume support)
    # ------------------------------------------------------------------

    def save_pagination_progress(
        self,
        run_id: int,
        last_page: int,
        total_pages: int,
        urls: list[str],
    ) -> None:
        """Upsert a pagination checkpoint so Step 1 can resume after a restart."""
        with self._conn() as conn:
            conn.execute(
                """
                INSERT INTO pagination_progress (run_id, last_page, total_pages, urls_json, updated_at)
                VALUES (?, ?, ?, ?, ?)
                ON CONFLICT(run_id) DO UPDATE SET
                    last_page   = excluded.last_page,
                    total_pages = excluded.total_pages,
                    urls_json   = excluded.urls_json,
                    updated_at  = excluded.updated_at
                """,
                (run_id, last_page, total_pages, json.dumps(urls, ensure_ascii=False), self._now()),
            )

    def get_pagination_progress(self, run_id: int) -> dict | None:
        """
        Return the saved checkpoint for *run_id*, or None if none exists.
        Dict keys: last_page (int), total_pages (int), urls (list[str]).
        """
        with self._conn() as conn:
            row = conn.execute(
                "SELECT last_page, total_pages, urls_json FROM pagination_progress WHERE run_id=?",
                (run_id,),
            ).fetchone()
        if row is None:
            return None
        return {
            "last_page": row["last_page"],
            "total_pages": row["total_pages"],
            "urls": json.loads(row["urls_json"]),
        }

    def get_latest_pagination_progress(self) -> dict | None:
        """
        Return the most recent pagination checkpoint across all runs (for resuming
        after a crash where we don't have the old run_id handy).
        Dict keys: run_id, last_page, total_pages, urls.
        """
        with self._conn() as conn:
            row = conn.execute(
                """
                SELECT pp.run_id, pp.last_page, pp.total_pages, pp.urls_json
                FROM pagination_progress pp
                JOIN scrape_runs sr ON sr.id = pp.run_id
                WHERE sr.status IN ('interrupted', 'paused')
                ORDER BY pp.updated_at DESC LIMIT 1
                """
            ).fetchone()
        if row is None:
            return None
        return {
            "run_id": row["run_id"],
            "last_page": row["last_page"],
            "total_pages": row["total_pages"],
            "urls": json.loads(row["urls_json"]),
        }

    def clear_pagination_progress(self, run_id: int) -> None:
        """Delete the checkpoint once Step 1 finishes successfully."""
        with self._conn() as conn:
            conn.execute(
                "DELETE FROM pagination_progress WHERE run_id=?",
                (run_id,),
            )

    # ------------------------------------------------------------------
    # URL management
    # ------------------------------------------------------------------

    def upsert_urls(self, urls: list[str], source: str = None) -> int:
        """Insert new URLs as 'pending'; update last_seen_at for existing. Revives soft-deleted URLs."""
        now = self._now()
        inserted = 0
        with self._conn() as conn:
            for url in urls:
                cur = conn.execute(
                    """
                    INSERT INTO car_urls (url, status, retry_count, created_at, is_active, last_seen_at, source)
                    VALUES (?, 'pending', 0, ?, 1, ?, ?)
                    ON CONFLICT(url) DO UPDATE SET
                        is_active = 1,
                        last_seen_at = excluded.last_seen_at,
                        source = COALESCE(excluded.source, car_urls.source)
                    """,
                    (url, now, now, source),
                )
                inserted += 1
        logger.info("upsert_urls: %d URLs processed (source: %s)", len(urls), source)
        return inserted

    def mark_all_inactive_before(self, timestamp: str) -> int:
        """Soft-delete cars that weren't seen during the current scrape run."""
        with self._conn() as conn:
            cur = conn.execute(
                "UPDATE car_urls SET is_active = 0 WHERE last_seen_at < ? OR last_seen_at IS NULL",
                (timestamp,)
            )
            return cur.rowcount

    def get_pending_urls(self, limit: int = 500) -> list[str]:
        """Return up to *limit* active, pending URLs. These are the next ones to scrape (resume-safe)."""
        with self._conn() as conn:
            rows = conn.execute(
                "SELECT url FROM car_urls WHERE status='pending' AND is_active=1 ORDER BY created_at LIMIT ?",
                (limit,),
            ).fetchall()
        return [r["url"] for r in rows]

    def is_url_done(self, url: str) -> bool:
        """Check if a URL has already been successfully scraped."""
        with self._conn() as conn:
            row = conn.execute(
                "SELECT 1 FROM car_urls WHERE url=? AND status='done'",
                (url,)
            ).fetchone()
        return row is not None

    def mark_url_done(self, url: str, car_id: str, data: dict, source: str = None) -> None:
        """Persist scraped car data and mark URL as done."""
        now = self._now()
        with self._conn() as conn:
            conn.execute(
                "UPDATE car_urls SET status='done', scraped_at=?, source=COALESCE(?, source) WHERE url=?",
                (now, source, url),
            )
            conn.execute(
                """
                INSERT OR REPLACE INTO car_details (car_id, url, raw_json, scraped_at, source)
                VALUES (?, ?, ?, ?, COALESCE(?, (SELECT source FROM car_urls WHERE url=?)))
                """,
                (car_id, url, json.dumps(data, ensure_ascii=False), now, source, url),
            )
        
        # Determine source if not provided
        if not source:
            with self._conn() as conn:
                row = conn.execute("SELECT source FROM car_urls WHERE url=?", (url,)).fetchone()
                source = row["source"] if row else None

        self._sync_to_typesense(car_id, data, now, url, source)

    def _sync_to_typesense(self, car_id: str, data: dict, scraped_at: str, url: str, source: str = None):
        """Helper to sync a single car record to Typesense."""
        if not self.ts_client:
            return
        
        try:
            gen_info = data.get('informacion_general', {})
            # Sanitize price and numeric fields
            def to_float(val):
                try:
                    if isinstance(val, (int, float)): return float(val)
                    if not val: return 0.0
                    clean = str(val).replace(",", "").replace("$", "").split()[0]
                    return float(clean)
                except (ValueError, IndexError):
                    return 0.0

            def to_int(val):
                try:
                    if isinstance(val, int): return val
                    if not val: return 0
                    if isinstance(val, float): return int(val)
                    clean = "".join(filter(str.isdigit, str(val)))
                    return int(clean) if clean else 0
                except (ValueError, TypeError):
                    return 0

            # Infer source if missing (legacy support)
            if not source:
                if 'crautos.com' in url: source = 'CRAutos'
                elif 'evmarket' in url: source = 'EVMarket'
                elif 'corimotors' in url or 'usadoscori' in url: source = 'CoriMotors'
                elif 'purdyusados' in url: source = 'PurdyUsados'
                elif 'veinsausados' in url: source = 'VeinsaUsados'
                else: source = 'Otro'

            document = {
                'id': car_id,
                'car_id': car_id,
                'marca': data.get('marca', 'Desconocida'),
                'modelo': data.get('modelo', 'Desconocido'),
                'año': to_int(data.get('año', 0)),
                'precio_usd': to_float(data.get('precio_usd', 0)),
                'precio_crc': to_float(data.get('precio_crc', 0)),
                'kilometraje_number': to_int(gen_info.get('kilometraje_number', 0)),
                'provincia': gen_info.get('provincia', 'Desconocida'),
                'combustible': gen_info.get('combustible', 'Desconocido'),
                'transmisión': gen_info.get('transmisión', 'Desconocida'),
                'url': url,
                'imagen_principal': data.get('imagen_principal', ''),
                'scraped_at': scraped_at,
                'fuente': source
            }
            self.ts_client.collections['cars'].documents.upsert(document)
            logger.info("Synced car %s to Typesense (fuente: %s)", car_id, source)
        except Exception as e:
            logger.warning("Failed to sync car %s to Typesense: %s", car_id, e)

    def mark_url_failed(self, url: str) -> None:
        """Increment retry counter; permanently fail after MAX_RETRIES."""
        with self._conn() as conn:
            conn.execute(
                "UPDATE car_urls SET retry_count = retry_count + 1 WHERE url=?",
                (url,),
            )
            conn.execute(
                """
                UPDATE car_urls
                SET status = CASE
                    WHEN retry_count >= ? THEN 'failed'
                    ELSE 'pending'
                END
                WHERE url=?
                """,
                (self.MAX_RETRIES, url),
            )

    # ------------------------------------------------------------------
    # Stats / reporting
    # ------------------------------------------------------------------

    def get_run_stats(self) -> dict:
        """Return a dict with counts per status for active cars."""
        with self._conn() as conn:
            rows = conn.execute(
                "SELECT status, COUNT(*) AS cnt FROM car_urls WHERE is_active=1 GROUP BY status"
            ).fetchall()
            inactive = conn.execute("SELECT COUNT(*) FROM car_urls WHERE is_active=0").fetchone()[0]

        stats = {r["status"]: r["cnt"] for r in rows}
        stats.setdefault("pending", 0)
        stats.setdefault("done", 0)
        stats.setdefault("failed", 0)
        stats["total_active"] = sum(stats.values())
        stats["inactive"] = inactive
        stats["total"] = stats["total_active"] + inactive
        return stats

    def get_all_cars(self) -> list[dict]:
        """Return all scraped car detail records as a list of dicts."""
        with self._conn() as conn:
            rows = conn.execute(
                "SELECT car_id, url, raw_json, scraped_at FROM car_details"
            ).fetchall()
        return [
            {
                "car_id": r["car_id"],
                "url": r["url"],
                "scraped_at": r["scraped_at"],
                **json.loads(r["raw_json"]),
            }
            for r in rows
        ]
