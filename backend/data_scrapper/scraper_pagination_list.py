"""
01 — Pagination list scraper for crautos.com

Discovers all car detail URLs by paginating through the used-car listing.

When called via run_scraper, a ScraperRepository and run_id are passed in.
Progress (last completed page + discovered URLs) is saved to SQLite after
every page, enabling resume after interruption.

When run standalone (python -m data_scrapper.scraper_pagination_list),
results fall back to JSON files in data_scrapper/data/<today>/.

Pause / Resume behaviour
------------------------
- If shutdown_event is set between pages, the function returns "paused"
  without losing progress (the DB checkpoint was already written).
- On the next run, _collect_all_urls detects the existing checkpoint via
  repository.get_latest_pagination_progress() and skips already-done pages.
- When all pages finish, the checkpoint row is deleted (clean state).
"""

import asyncio
import json
import re
import logging
import os
from datetime import datetime
from urllib.parse import urljoin

from playwright.async_api import (
    async_playwright,
    TimeoutError as PlaywrightTimeoutError,
)

# Optional import — only available when running inside the package
try:
    from data_scrapper.repository import ScraperRepository
except ImportError:
    ScraperRepository = None  # type: ignore[assignment,misc]

logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)

# --- File-based fallback paths (standalone mode) ---
today = datetime.now().strftime("%d_%m_%Y")
_DATA_DIR = f"data_scrapper/data/{today}"
URLS_FILE = f"{_DATA_DIR}/urls.json"
FAILED_URLS_FILE = f"{_DATA_DIR}/failed_urls.json"


# ---------------------------------------------------------------------------
# File-based helpers (standalone / backward-compat)
# ---------------------------------------------------------------------------

def _save_json(data, filename):
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)


def _append_failed_url(url):
    failed_urls = []
    if os.path.exists(FAILED_URLS_FILE):
        with open(FAILED_URLS_FILE, "r", encoding="utf-8") as f:
            try:
                failed_urls = json.load(f)
            except json.JSONDecodeError:
                failed_urls = []
    if url not in failed_urls:
        failed_urls.append(url)
    _save_json(failed_urls, FAILED_URLS_FILE)


# ---------------------------------------------------------------------------
# Core scraping logic
# ---------------------------------------------------------------------------

async def _collect_all_urls(
    page,
    repository=None,
    run_id: int | None = None,
    shutdown_event: asyncio.Event | None = None,
) -> str:
    """
    Scrape every pagination page and return all discovered car detail URLs.

    Parameters
    ----------
    page        : Playwright page object
    repository  : ScraperRepository | None — when provided, URLs are upserted
                  into SQLite and progress is check-pointed after every page.
    run_id      : int | None — required when repository is provided.
    shutdown_event : asyncio.Event | None — when set, the loop exits early
                  and returns "paused" so the run can be resumed later.

    Returns
    -------
    "done"   — all pages scraped successfully.
    "paused" — shutdown_event was set; progress has been saved.
    """
    if shutdown_event is None:
        shutdown_event = asyncio.Event()  # never fires in standalone mode

    # --- Determine resume state ---
    start_page = 1
    detail_urls: set[str] = set()
    known_total_pages: int | None = None

    if repository is not None:
        # Look for a checkpoint from a previously interrupted run.
        # Note: we look for ANY latest paused/interrupted checkpoint, not just
        # this run_id, because after a crash we get a fresh run_id.
        checkpoint = repository.get_latest_pagination_progress()
        if checkpoint:
            start_page = checkpoint["last_page"] + 1
            detail_urls = set(checkpoint["urls"])
            known_total_pages = checkpoint["total_pages"] or None
            logger.info(
                "Resuming pagination from page %d (checkpoint had %d URLs, total_pages=%s)",
                start_page,
                len(detail_urls),
                known_total_pages,
            )
    elif os.path.exists(URLS_FILE):
        # Standalone fallback: already done
        logger.info("'%s' exists — skipping URL collection.", URLS_FILE)
        return "done"

    logger.info("Starting URL collection from crautos.com...")
    await page.goto(
        "https://crautos.com/autosusados/",
        timeout=60000,
        wait_until="domcontentloaded",
    )
    await page.locator(".btn.btn-lg.btn-success").click()

    # --- Determine total pages ---
    if known_total_pages is None:
        try:
            last_page_link = page.locator('a:has-text("Última Página")')
            href = await last_page_link.get_attribute("href", timeout=5000)
            match = re.search(r"p\('(\d+)'\)", href)
            if not match:
                logger.error("Could not determine last page number. Aborting.")
                return "failed"
            known_total_pages = int(match.group(1))
            logger.info("Found %d pages to scrape.", known_total_pages)
        except (PlaywrightTimeoutError, AttributeError):
            logger.warning("'Última Página' button not found — assuming 1 page.")
            known_total_pages = 1
        except Exception as exc:
            logger.error("Error determining last page: %s. Aborting.", exc)
            return "failed"

    last_page_number = known_total_pages

    # --- Page loop ---
    for page_num in range(start_page, last_page_number + 1):

        # Check for shutdown before navigating to the next page
        if shutdown_event.is_set():
            logger.info(
                "Shutdown requested at page %d/%d — saving progress and pausing.",
                page_num,
                last_page_number,
            )
            if repository is not None and run_id is not None:
                repository.save_pagination_progress(
                    run_id, page_num - 1, last_page_number, list(detail_urls)
                )
            return "paused"

        logger.info("Processing page %d/%d...", page_num, last_page_number)

        if page_num > 1:
            try:
                async with page.expect_navigation(wait_until="domcontentloaded"):
                    await page.evaluate(f"p('{page_num}')")
            except Exception as exc:
                logger.error("Failed to navigate to page %d: %s", page_num, exc)
                if repository is None:
                    _append_failed_url(f"PAGE::{page_num}")
                else:
                    logger.warning("Skipping failed page %d (will not retry).", page_num)
                # Save progress so we can at least skip done pages on next run
                if repository is not None and run_id is not None:
                    repository.save_pagination_progress(
                        run_id, page_num - 1, last_page_number, list(detail_urls)
                    )
                continue

        try:
            await page.wait_for_selector('a[href^="cardetail.cfm"]', timeout=10000)
            links = await page.locator('a[href^="cardetail.cfm"]').all()
            page_new = 0
            for link in links:
                href = await link.get_attribute("href")
                if href:
                    absolute_url = urljoin(page.url, href)
                    if absolute_url not in detail_urls:
                        detail_urls.add(absolute_url)
                        page_new += 1
            logger.info(
                "Page %d: +%d URLs (total %d)", page_num, page_new, len(detail_urls)
            )
        except PlaywrightTimeoutError:
            logger.warning("No links found on page %d — skipping.", page_num)
            if repository is None:
                _append_failed_url(f"PAGE::{page_num}")

        # Save checkpoint to DB after every successfully attempted page
        if repository is not None and run_id is not None:
            repository.save_pagination_progress(
                run_id, page_num, last_page_number, list(detail_urls)
            )

    # --- All pages done ---
    url_list = list(detail_urls)

    if repository is not None:
        repository.upsert_urls(url_list)
        if run_id is not None:
            repository.clear_pagination_progress(run_id)
        logger.info("Seeded %d URLs into DB. Pagination checkpoint cleared.", len(url_list))
    else:
        os.makedirs(_DATA_DIR, exist_ok=True)
        _save_json(url_list, URLS_FILE)
        logger.info("Saved %d URLs to '%s'.", len(url_list), URLS_FILE)

    return "done"


async def _retry_failed_pages(page, repository=None):
    """Retry pages that failed during the initial collection pass (standalone mode only)."""
    if repository is not None:
        return  # Repository mode: retries are handled at URL level, not page level

    if not os.path.exists(FAILED_URLS_FILE):
        return

    with open(FAILED_URLS_FILE, "r", encoding="utf-8") as f:
        try:
            failed_items = json.load(f)
        except json.JSONDecodeError:
            failed_items = []

    if not failed_items:
        return

    logger.info("Retrying %d failed pages...", len(failed_items))

    try:
        await page.goto(
            "https://crautos.com/autosusados/",
            timeout=60000,
            wait_until="domcontentloaded",
        )
        await page.locator(".btn.btn-lg.btn-success").click()
    except Exception as exc:
        logger.error("Could not navigate to base page for retries: %s", exc)
        return

    existing_urls: set[str] = set()
    if os.path.exists(URLS_FILE):
        with open(URLS_FILE, "r", encoding="utf-8") as f:
            try:
                existing_urls = set(json.load(f))
            except json.JSONDecodeError:
                pass

    still_failed: list[str] = []
    newly_scraped: set[str] = set()

    for item in failed_items:
        if item.startswith("PAGE::"):
            page_num_str = item.split("::")[1]
            try:
                page_num = int(page_num_str)
                if page_num > 1:
                    async with page.expect_navigation(wait_until="domcontentloaded"):
                        await page.evaluate(f"p('{page_num_str}')")
                await page.wait_for_selector('a[href^="cardetail.cfm"]', timeout=10000)
                links = await page.locator('a[href^="cardetail.cfm"]').all()
                for link in links:
                    href = await link.get_attribute("href")
                    if href:
                        abs_url = urljoin(page.url, href)
                        if abs_url not in existing_urls and abs_url not in newly_scraped:
                            newly_scraped.add(abs_url)
                logger.info("Retry OK for page %d.", page_num)
            except Exception as exc:
                logger.error("Retry failed for page %s: %s", page_num_str, exc)
                still_failed.append(item)

    if newly_scraped:
        all_urls = list(existing_urls | newly_scraped)
        _save_json(all_urls, URLS_FILE)
        logger.info("Added %d URLs from retried pages.", len(newly_scraped))

    if still_failed:
        _save_json(still_failed, FAILED_URLS_FILE)
    else:
        os.remove(FAILED_URLS_FILE)
        logger.info("All failed pages retried successfully.")


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------

async def main(
    repository=None,
    headless: bool = False,
    run_id: int | None = None,
    shutdown_event: asyncio.Event | None = None,
) -> str:
    """
    Orchestrate URL collection.

    Parameters
    ----------
    repository : ScraperRepository | None
        When provided, URLs are saved to SQLite.  Otherwise, written to JSON.
    headless : bool
        Whether to launch Chromium in headless mode.
    run_id : int | None
        The active scrape_run ID (required for DB checkpointing when
        repository is not None).
    shutdown_event : asyncio.Event | None
        When set, the scraper exits gracefully after the current page and
        returns "paused" so the run can be resumed later.

    Returns
    -------
    "done"   — completed successfully.
    "paused" — stopped early due to shutdown_event; progress saved to DB.
    "failed" — an unrecoverable error occurred.
    """
    result = "failed"
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=headless)
        context = await browser.new_context()
        page = await context.new_page()

        await _retry_failed_pages(page, repository)
        result = await _collect_all_urls(
            page,
            repository=repository,
            run_id=run_id,
            shutdown_event=shutdown_event,
        )

        await browser.close()

    logger.info("URL collection finished with status: %s", result)
    return result


if __name__ == "__main__":
    asyncio.run(main(headless=False))
