"""
01 — Pagination list scraper for crautos.com

Discovers all car detail URLs by paginating through the used-car listing.

When called via run_scraper, a ScraperRepository is passed in and URLs are
persisted to SQLite.  When run standalone (python -m data_scrapper.01_…),
results fall back to JSON files in data_scrapper/data/<today>/.
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

async def _collect_all_urls(page, repository=None) -> list[str]:
    """
    Scrape every pagination page and return all discovered car detail URLs.
    When *repository* is provided the URL list is upserted into SQLite;
    when None a urls.json file is written instead.
    """
    # Skip if already done (file-based check for standalone mode)
    if repository is None and os.path.exists(URLS_FILE):
        logger.info("'%s' exists — skipping URL collection.", URLS_FILE)
        return []

    logger.info("Starting URL collection from crautos.com...")
    detail_urls: set[str] = set()

    await page.goto("https://crautos.com/autosusados/")
    await page.locator(".btn.btn-lg.btn-success").click()

    # Determine total pages
    try:
        last_page_link = page.locator('a:has-text("Última Página")')
        href = await last_page_link.get_attribute("href", timeout=5000)
        match = re.search(r"p\('(\d+)'\)", href)
        if not match:
            logger.error("Could not determine last page number. Aborting.")
            return []
        last_page_number = int(match.group(1))
        logger.info("Found %d pages to scrape.", last_page_number)
    except (PlaywrightTimeoutError, AttributeError):
        logger.warning("'Última Página' button not found — assuming 1 page.")
        last_page_number = 1
    except Exception as exc:
        logger.error("Error determining last page: %s. Aborting.", exc)
        return []

    failed_pages: list[str] = []

    for page_num in range(1, last_page_number + 1):
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
                    failed_pages.append(f"PAGE::{page_num}")
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
            logger.info("Page %d: +%d URLs (total %d)", page_num, page_new, len(detail_urls))
        except PlaywrightTimeoutError:
            logger.warning("No links found on page %d — queuing for retry.", page_num)
            if repository is None:
                _append_failed_url(f"PAGE::{page_num}")
            else:
                failed_pages.append(f"PAGE::{page_num}")

    url_list = list(detail_urls)

    if repository is not None:
        repository.upsert_urls(url_list)
    else:
        os.makedirs(_DATA_DIR, exist_ok=True)
        _save_json(url_list, URLS_FILE)
        logger.info("Saved %d URLs to '%s'.", len(url_list), URLS_FILE)

    return url_list


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
        await page.goto("https://crautos.com/autosusados/")
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

async def main(repository=None, headless: bool = False):
    """
    Orchestrate URL collection.

    Parameters
    ----------
    repository : ScraperRepository | None
        When provided, URLs are saved to SQLite.  Otherwise, written to JSON.
    headless : bool
        Whether to launch Chromium in headless mode.
    """
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=headless)
        context = await browser.new_context()
        page = await context.new_page()

        await _retry_failed_pages(page, repository)
        await _collect_all_urls(page, repository)

        await browser.close()
    logger.info("URL collection complete.")


if __name__ == "__main__":
    asyncio.run(main(headless=False))
