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
- If shutdown_event is set between batches, the function returns "paused"
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
import time
from datetime import datetime, timedelta
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
    context,
    concurrency: int = 5,
    repository=None,
    run_id: int | None = None,
    shutdown_event: asyncio.Event | None = None,
) -> str:
    """
    Scrape every pagination page and return all discovered car detail URLs.

    Parameters
    ----------
    context     : Playwright BrowserContext
    concurrency : int — number of concurrent tabs to open
    repository  : ScraperRepository | None — when provided, URLs are upserted
                  into SQLite and progress is check-pointed after every page.
    run_id      : int | None — required when repository is provided.
    shutdown_event : asyncio.Event | None — when set, the loop exits early
                  and returns "paused" so the run can be resumed later.

    Returns
    -------
    "done"   — all pages scraped successfully.
    "paused" — shutdown_event was set; progress has been saved.
    "failed" — unrecoverable error.
    """
    if shutdown_event is None:
        shutdown_event = asyncio.Event()  # never fires in standalone mode

    # --- Determine resume state ---
    start_page = 1
    detail_urls: set[str] = set()
    known_total_pages: int | None = None

    if repository is not None:
        # Look for a checkpoint from a previously interrupted run.
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

    logger.info("Initializing pool of %d worker tabs...", concurrency)
    worker_pages = []

    async def init_worker_tab():
        try:
            p = await context.new_page()
            await p.goto(
                "https://crautos.com/autosusados/",
                timeout=60000,
                wait_until="domcontentloaded",
            )
            await p.locator(".btn.btn-lg.btn-success").click(timeout=30000)
            await p.wait_for_selector('a[href^="cardetail.cfm"]', timeout=30000)
            return p
        except Exception as exc:
            logger.error("Error initializing worker tab: %s", exc)
            return None

    # Sequence initialization to avoiding spamming connection or navigation limits all at once
    for i in range(concurrency):
        wp = await init_worker_tab()
        if wp:
            worker_pages.append(wp)

    if not worker_pages:
        logger.error("Could not initialize any worker tabs. Aborting.")
        return "failed"

    actual_concurrency = len(worker_pages)
    base_page = worker_pages[0]

    # --- Determine total pages ---
    if known_total_pages is None:
        try:
            last_page_link = base_page.locator('a:has-text("Última Página")')
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

    # --- Page Batch Loop ---
    start_time = time.time()
    for batch_start in range(start_page, last_page_number + 1, actual_concurrency):
        if shutdown_event.is_set():
            logger.info(
                "Shutdown requested at batch %d — saving progress and pausing.",
                batch_start,
            )
            if repository is not None and run_id is not None:
                repository.save_pagination_progress(
                    run_id, batch_start - 1, last_page_number, list(detail_urls)
                )
            for p in worker_pages:
                try:
                    if p:
                        await p.close()
                except:
                    pass
            return "paused"

        batch_end = min(batch_start + actual_concurrency - 1, last_page_number)
        batch_pages = list(range(batch_start, batch_end + 1))

        logger.info("Processing batch of pages %s to %s (out of %d)...", batch_start, batch_end, last_page_number)

        async def scrape_single_page(worker_index: int, page_num: int):
            max_retries = 5
            for attempt in range(max_retries):
                wp = worker_pages[worker_index]
                
                # If worker page is broken/closed, attempt to re-initialize it
                if wp is None or wp.is_closed():
                    if attempt > 0:
                        logger.info("Re-initializing worker %d for page %d (attempt %d/%d)...", worker_index, page_num, attempt + 1, max_retries)
                    wp = await init_worker_tab()
                    worker_pages[worker_index] = wp
                    if not wp:
                        if attempt == max_retries - 1:
                            return page_num, False, 0
                        await asyncio.sleep(2)
                        continue
                    
                page_new_count = 0

                # It's possible the context doesn't have `p` if it navigated away or threw an error earlier.
                if page_num > 1:
                    try:
                        await wp.wait_for_function("typeof p === 'function'", timeout=15000)
                        async with wp.expect_navigation(wait_until="domcontentloaded", timeout=45000):
                            await wp.evaluate(f"p('{page_num}')")
                    except Exception as exc:
                        logger.warning("Failed to navigate to page %d on attempt %d/%d: %s", page_num, attempt + 1, max_retries, exc)
                        # Close page so it's re-initialized next time
                        try:
                            await wp.close()
                        except:
                            pass
                        worker_pages[worker_index] = None
                        if attempt == max_retries - 1:
                            return page_num, False, 0
                        continue

                try:
                    await wp.wait_for_selector('a[href^="cardetail.cfm"]', timeout=30000)
                    links = await wp.locator('a[href^="cardetail.cfm"]').all()
                    for link in links:
                        href = await link.get_attribute("href")
                        if href:
                            absolute_url = urljoin(wp.url, href)
                            if absolute_url not in detail_urls:
                                detail_urls.add(absolute_url)
                                page_new_count += 1
                    return page_num, True, page_new_count
                except PlaywrightTimeoutError:
                    logger.warning("No links found on page %d (attempt %d/%d).", page_num, attempt + 1, max_retries)
                    if attempt == max_retries - 1:
                        return page_num, False, 0
                except Exception as exc:
                    logger.error("Error extracting links on page %d (attempt %d/%d): %s", page_num, attempt + 1, max_retries, exc)
                    try:
                        await wp.close()
                    except:
                        pass
                    worker_pages[worker_index] = None
                    if attempt == max_retries - 1:
                        return page_num, False, 0

            return page_num, False, 0

        # Run tasks concurrently
        tasks = []
        for i, p_num in enumerate(batch_pages):
            tasks.append(scrape_single_page(i, p_num))

        results = await asyncio.gather(*tasks)

        # Process results
        for p_num, success, p_new in results:
            if not success:
                if repository is None:
                    _append_failed_url(f"PAGE::{p_num}")
                else:
                    logger.warning("Skipping failed page %d (will not retry).", p_num)
            else:
                logger.debug("Page %d: +%d URLs", p_num, p_new)

        elapsed_time = time.time() - start_time
        pages_processed = batch_end - start_page + 1
        avg_speed = pages_processed / elapsed_time if elapsed_time > 0 else 0
        pages_left = last_page_number - batch_end
        eta_seconds = pages_left / avg_speed if avg_speed > 0 else 0
        eta_str = str(timedelta(seconds=int(eta_seconds)))

        logger.info(
            "Batch %s-%s done. Total URLs so far: %d. ETA: %s (%.2f pages/sec)",
            batch_start, batch_end, len(detail_urls), eta_str, avg_speed
        )

        # Save checkpoint to DB after every successfully attempted batch
        if repository is not None and run_id is not None:
            repository.save_pagination_progress(
                run_id, batch_end, last_page_number, list(detail_urls)
            )

    # --- Cleanup workers ---
    for p in worker_pages:
        try:
            await p.close()
        except:
            pass

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


async def _retry_failed_pages(context, repository=None):
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

    page = await context.new_page()
    try:
        await page.goto(
            "https://crautos.com/autosusados/",
            timeout=60000,
            wait_until="domcontentloaded",
        )
        await page.locator(".btn.btn-lg.btn-success").click()
    except Exception as exc:
        logger.error("Could not navigate to base page for retries: %s", exc)
        await page.close()
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

    await page.close()


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------

async def main(
    repository=None,
    headless: bool = False,
    run_id: int | None = None,
    shutdown_event: asyncio.Event | None = None,
    concurrency: int = 5,
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
    concurrency : int
        Number of tabs to keep open simultaneously for checking pagination grid.
        
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

        await _retry_failed_pages(context, repository)
        result = await _collect_all_urls(
            context,
            concurrency=concurrency,
            repository=repository,
            run_id=run_id,
            shutdown_event=shutdown_event,
        )

        try:
            await browser.close()
        except:
            pass

    logger.info("URL collection finished with status: %s", result)
    return result


if __name__ == "__main__":
    asyncio.run(main(headless=False, concurrency=5))
