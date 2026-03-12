"""
run_scraper.py — Safe orchestrator for the crautos scraper pipeline.

Features
--------
* Step 1: Seed car URLs into SQLite if none exist yet (01_scraper_pagination_list)
* Step 2: Scrape car details for all pending URLs (02_scraper_car_details)
* Pause / Resume: on SIGINT/SIGTERM the run is marked 'paused'; next start resumes
* Retry: built into the repository layer (up to MAX_RETRIES per URL)
* All configuration via environment variables (Docker-friendly)

Usage (direct)
--------------
    python -m data_scrapper.run_scraper

Usage (Docker)
--------------
    docker compose -f docker-compose.dev.yml up
"""

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
    sig_name = signal.Signals(signum).name
    logger.warning("Received %s — initiating graceful shutdown (pause)...", sig_name)
    _shutdown_event.set()


# ---------------------------------------------------------------------------
# Main orchestrator
# ---------------------------------------------------------------------------

async def run(repo: ScraperRepository) -> str:
    """
    Orchestrate the full pipeline.
    Returns the final status string: 'done' | 'paused' | 'failed'
    """
    # Import here to avoid circular deps and allow scraper modules to be used standalone
    from data_scrapper import scraper_pagination_list as step1  # type: ignore[import]
    from data_scrapper import scraper_car_details as step2      # type: ignore[import]

    # ── Step 1: Seed URLs ──────────────────────────────────────────────────
    if not repo.has_urls():
        logger.info("No URLs in DB yet. Running Step 1: pagination list scraper...")
        try:
            await step1.main(repository=repo, headless=HEADLESS)
        except Exception as exc:
            logger.error("Step 1 failed: %s", exc, exc_info=True)
            return "failed"

        stats = repo.get_run_stats()
        logger.info("Step 1 complete. Seeded %d URLs.", stats.get("total", 0))
    else:
        stats = repo.get_run_stats()
        logger.info(
            "Resuming — DB stats: total=%d done=%d pending=%d failed=%d",
            stats["total"], stats["done"], stats["pending"], stats["failed"],
        )

    # ── Step 2: Scrape details ─────────────────────────────────────────────
    if _shutdown_event.is_set():
        logger.info("Shutdown requested before Step 2. Pausing.")
        return "paused"

    logger.info("Running Step 2: car details scraper...")
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
        logger.error("Step 2 failed unexpectedly: %s", exc, exc_info=True)
        return "failed"

    return status  # 'done' or 'paused'


async def main():
    # Register signal handlers
    loop = asyncio.get_event_loop()
    for sig in (signal.SIGINT, signal.SIGTERM):
        try:
            loop.add_signal_handler(sig, lambda s=sig: _handle_signal(s, None))
        except NotImplementedError:
            # Windows — fall back to the default signal module
            signal.signal(sig, _handle_signal)

    repo = ScraperRepository(DB_PATH)
    run_id = repo.start_run(notes=f"headless={HEADLESS} concurrency=[{MIN_CONCURRENCY}-{MAX_CONCURRENCY}]")

    final_status = "failed"
    try:
        final_status = await run(repo)
    except Exception as exc:
        logger.critical("Unhandled exception in orchestrator: %s", exc, exc_info=True)
        final_status = "failed"
    finally:
        repo.finish_run(run_id, status=final_status)
        stats = repo.get_run_stats()
        logger.info(
            "Run #%d finished [%s]. Stats — total:%d done:%d pending:%d failed:%d",
            run_id, final_status,
            stats["total"], stats["done"], stats["pending"], stats["failed"],
        )

    # Exit non-zero on failure so Docker/compose triggers the restart policy
    if final_status == "failed":
        sys.exit(1)
    # 'paused' or 'done' → clean exit (no restart triggered)
    sys.exit(0)


if __name__ == "__main__":
    asyncio.run(main())
