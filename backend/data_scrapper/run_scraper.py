"""
run_scraper.py — Safe orchestrator for the crautos scraper pipeline.

Commands
--------
  urls     — Step 1: scrape pagination list and seed car URLs into SQLite
  details  — Step 2: scrape car detail pages for pending URLs (resume-safe)
  all      — Step 1 then Step 2 in sequence

Graceful shutdown
-----------------
  SIGINT / SIGTERM → run is marked 'paused', exits 0 (no restart triggered)
  Unhandled crash  → exits 1

Single-run enforcement
-----------------------
  Only one scrape process may be 'running' at a time.
  On startup, any leftover 'running' rows from a prior crash are marked
  'interrupted' before a new run starts.

Configuration (env vars)
------------------------
  SCRAPER_DB_PATH              default: data/crautos.db
  SCRAPER_HEADLESS             default: true
  SCRAPER_INITIAL_CONCURRENCY  default: 3
  SCRAPER_MIN_CONCURRENCY      default: 1
  SCRAPER_MAX_CONCURRENCY      default: 10

Usage
-----
  # Inside the running container:
  python -m data_scrapper.run_scraper urls
  python -m data_scrapper.run_scraper details
  python -m data_scrapper.run_scraper all

  # Via docker compose:
  docker compose -f docker-compose.dev.yml exec scraper python -m data_scrapper.run_scraper urls
  docker compose -f docker-compose.dev.yml exec scraper python -m data_scrapper.run_scraper details
  docker compose -f docker-compose.dev.yml exec scraper python -m data_scrapper.run_scraper all
"""

import argparse
import asyncio
import logging
import os
import signal
import sys

from data_scrapper.repository import ScraperRepository

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s — %(message)s",
)
logger = logging.getLogger("run_scraper")

# ---------------------------------------------------------------------------
# Configuration from environment
# ---------------------------------------------------------------------------

DB_PATH = os.environ.get("SCRAPER_DB_PATH", "data/crautos.db")
HEADLESS = os.environ.get("SCRAPER_HEADLESS", "true").lower() not in ("false", "0", "no")
INITIAL_CONCURRENCY = int(os.environ.get("SCRAPER_INITIAL_CONCURRENCY", "3"))
MIN_CONCURRENCY = int(os.environ.get("SCRAPER_MIN_CONCURRENCY", "1"))
MAX_CONCURRENCY = int(os.environ.get("SCRAPER_MAX_CONCURRENCY", "10"))

# ---------------------------------------------------------------------------
# Graceful shutdown
# ---------------------------------------------------------------------------

_shutdown_event = asyncio.Event()


def _handle_signal(signum, frame):  # noqa: ARG001
    try:
        sig_name = signal.Signals(signum).name
    except Exception:
        sig_name = f"Signal {signum}"
    logger.warning("Received %s — initiating graceful shutdown (pause)...", sig_name)
    try:
        loop = asyncio.get_running_loop()
        loop.call_soon_threadsafe(_shutdown_event.set)
    except RuntimeError:
        _shutdown_event.set()


def _register_signals():
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        return
    for sig in (signal.SIGINT, signal.SIGTERM):
        try:
            loop.add_signal_handler(sig, lambda s=sig: _handle_signal(s, None))
        except NotImplementedError:
            signal.signal(sig, _handle_signal)  # Windows fallback


# ---------------------------------------------------------------------------
# Individual step runners
# ---------------------------------------------------------------------------

async def run_urls(repo: ScraperRepository, run_id: int) -> str:
    """Step 1: discover and seed all car URLs into SQLite (resume-safe)."""
    from data_scrapper import scraper_pagination_list as step1  # noqa: PLC0415
    from datetime import datetime, timezone

    # Record the start time so we can soft-delete cars that aren't seen in this run
    run_start_time = datetime.now(timezone.utc).isoformat()

    logger.info("Starting Step 1: collecting car URLs...")
    try:
        status = await step1.main(
            repository=repo,
            headless=HEADLESS,
            run_id=run_id,
            shutdown_event=_shutdown_event,
        )
    except Exception as exc:
        logger.error("Step 1 failed: %s", exc, exc_info=True)
        return "failed"

    if status == "done":
        inactive_count = repo.mark_all_inactive_before(run_start_time)
        stats = repo.get_run_stats()
        logger.info(
            "Step 1 complete. URLs: %d active (%d new/pending), %d marked sold/inactive.",
            stats["total_active"], stats["pending"], inactive_count
        )
    else:
        logger.info("Step 1 %s.", status)
    return status


async def run_details(repo: ScraperRepository, run_id: int) -> str:  # noqa: ARG001
    """Step 2: scrape car detail pages for all pending URLs (resume-safe)."""
    from data_scrapper import scraper_car_details as step2  # noqa: PLC0415

    if not repo.has_urls():
        logger.error("No URLs in DB. Run 'urls' command first.")
        return "failed"

    stats = repo.get_run_stats()
    logger.info(
        "Starting Step 2 — Active: %d (done:%d, pending:%d, failed:%d). Inactive: %d",
        stats["total_active"], stats["done"], stats["pending"], stats["failed"], stats["inactive"]
    )

    if _shutdown_event.is_set():
        logger.info("Shutdown requested before Step 2 started. Pausing.")
        return "paused"

    try:
        status = await step2.main(
            repository=repo,
            headless=HEADLESS,
            initial_concurrency=INITIAL_CONCURRENCY,
            min_concurrency=MIN_CONCURRENCY,
            max_concurrency=MAX_CONCURRENCY,
            shutdown_event=_shutdown_event,
        )
    except Exception as exc:
        logger.error("Step 2 failed: %s", exc, exc_info=True)
        return "failed"

    return status  # 'done' or 'paused'


async def run_all(repo: ScraperRepository, run_id: int) -> str:
    """Step 1 then Step 2 in sequence."""
    status = await run_urls(repo, run_id)
    if status == "failed":
        return "failed"
    if _shutdown_event.is_set():
        return "paused"
    return await run_details(repo, run_id)


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

COMMANDS = {
    "urls": run_urls,
    "details": run_details,
    "all": run_all,
}


async def main(command: str):
    _register_signals()

    repo = ScraperRepository(DB_PATH)

    # --- Stale-run cleanup ---
    # Any 'running' row left over from a prior crash is marked 'interrupted'.
    stale = repo.interrupt_stale_runs()
    if stale:
        logger.warning(
            "%d stale run(s) marked 'interrupted'. Starting a fresh run.", stale
        )

    # --- Single-run guard ---
    # After cleanup, no 'running' row should exist.  If one does (race condition
    # or concurrent invocation), refuse to start and exit with code 2.
    active_run_id = repo.get_active_run_id()
    if active_run_id is not None:
        logger.error(
            "Another scrape run is already active (run #%d). "
            "If this is stale, delete the DB or wait for it to finish.",
            active_run_id,
        )
        sys.exit(2)

    run_id = repo.start_run(
        notes=f"cmd={command} headless={HEADLESS} concurrency=[{MIN_CONCURRENCY}-{MAX_CONCURRENCY}]"
    )

    final_status = "failed"
    try:
        final_status = await COMMANDS[command](repo, run_id)
    except Exception as exc:
        logger.critical("Unhandled exception: %s", exc, exc_info=True)
        final_status = "failed"
    finally:
        repo.finish_run(run_id, status=final_status)
        stats = repo.get_run_stats()
        logger.info(
            "Run #%d [%s] finished — Active: %d (done:%d, pending:%d, failed:%d). Inactive: %d",
            run_id, final_status,
            stats["total_active"], stats["done"], stats["pending"], stats["failed"], stats["inactive"]
        )

    sys.exit(1 if final_status == "failed" else 0)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        prog="python -m data_scrapper.run_scraper",
        description="Crautos scraper — safe runner with pause/resume support.",
    )
    parser.add_argument(
        "command",
        choices=list(COMMANDS.keys()),
        help=(
            "urls    — Step 1: collect all car URLs into SQLite\n"
            "details — Step 2: scrape car detail pages (resumes from last run)\n"
            "all     — Step 1 then Step 2 in sequence"
        ),
    )
    args = parser.parse_args()
    try:
        asyncio.run(main(args.command))
    except KeyboardInterrupt:
        logger.info("Gracefully exited after KeyboardInterrupt (Ctrl+C).")
        sys.exit(0)
