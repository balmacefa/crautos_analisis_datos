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
    status      TEXT    NOT NULL DEFAULT 'running',   -- running | paused | done | failed
    notes       TEXT
);

CREATE TABLE IF NOT EXISTS car_urls (
    url          TEXT    PRIMARY KEY,
    status       TEXT    NOT NULL DEFAULT 'pending',  -- pending | done | failed
    retry_count  INTEGER NOT NULL DEFAULT 0,
    created_at   TEXT    NOT NULL,
    scraped_at   TEXT
);

CREATE TABLE IF NOT EXISTS car_details (
    car_id       TEXT    PRIMARY KEY,
    url          TEXT    NOT NULL,
    raw_json     TEXT    NOT NULL,
    scraped_at   TEXT    NOT NULL,
    FOREIGN KEY (url) REFERENCES car_urls(url)
);

CREATE INDEX IF NOT EXISTS idx_car_urls_status ON car_urls(status);
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
        if status not in ("done", "paused", "failed"):
            raise ValueError(f"Invalid run status: {status!r}")
        with self._conn() as conn:
            conn.execute(
                "UPDATE scrape_runs SET ended_at=?, status=? WHERE id=?",
                (self._now(), status, run_id),
            )
        logger.info("Run #%d finished with status '%s'", run_id, status)

    # ------------------------------------------------------------------
    # URL management
    # ------------------------------------------------------------------

    def upsert_urls(self, urls: list[str]) -> int:
        """Insert new URLs as 'pending'; skip already-known URLs. Returns count inserted."""
        now = self._now()
        inserted = 0
        with self._conn() as conn:
            for url in urls:
                cur = conn.execute(
                    """
                    INSERT OR IGNORE INTO car_urls (url, status, retry_count, created_at)
                    VALUES (?, 'pending', 0, ?)
                    """,
                    (url, now),
                )
                inserted += cur.rowcount
        logger.info("upsert_urls: %d new URLs inserted (of %d provided)", inserted, len(urls))
        return inserted

    def get_pending_urls(self, limit: int = 500) -> list[str]:
        """Return up to *limit* pending URLs. These are the next ones to scrape (resume-safe)."""
        with self._conn() as conn:
            rows = conn.execute(
                "SELECT url FROM car_urls WHERE status='pending' ORDER BY created_at LIMIT ?",
                (limit,),
            ).fetchall()
        return [r["url"] for r in rows]

    def has_urls(self) -> bool:
        """True if any URLs have been seeded into the DB."""
        with self._conn() as conn:
            count = conn.execute("SELECT COUNT(*) FROM car_urls").fetchone()[0]
        return count > 0

    def mark_url_done(self, url: str, car_id: str, data: dict) -> None:
        """Persist scraped car data and mark URL as done."""
        now = self._now()
        with self._conn() as conn:
            conn.execute(
                "UPDATE car_urls SET status='done', scraped_at=? WHERE url=?",
                (now, url),
            )
            conn.execute(
                """
                INSERT OR REPLACE INTO car_details (car_id, url, raw_json, scraped_at)
                VALUES (?, ?, ?, ?)
                """,
                (car_id, url, json.dumps(data, ensure_ascii=False), now),
            )

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
        """Return a dict with counts per status."""
        with self._conn() as conn:
            rows = conn.execute(
                "SELECT status, COUNT(*) AS cnt FROM car_urls GROUP BY status"
            ).fetchall()
        stats = {r["status"]: r["cnt"] for r in rows}
        stats.setdefault("pending", 0)
        stats.setdefault("done", 0)
        stats.setdefault("failed", 0)
        stats["total"] = sum(stats.values())
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
