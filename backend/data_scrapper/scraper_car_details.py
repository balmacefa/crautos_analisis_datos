"""
02 — Car details scraper for crautos.com  (V4 — adaptive concurrency + SQLite)

Scrapes structured data for each car detail page.

When called via run_scraper, a ScraperRepository and shutdown_event are passed
in; results are persisted to SQLite. When run standalone, output falls back to
JSON files in datos_vehiculos/.
"""

import asyncio
import json
import logging
import os
import random
import re
import time
from collections import deque
from datetime import timedelta
from urllib.parse import parse_qs, urlparse

import argparse
from playwright.async_api import async_playwright

# Optional import — only needed when running inside the package
try:
    from data_scrapper.repository import ScraperRepository
except ImportError:
    ScraperRepository = None  # type: ignore[assignment,misc]

logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

OUTPUT_DIR = "datos_vehiculos"   # standalone fallback
TRIES = 3
USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/127.0.0.0 Safari/537.36 "
    "(VehicleDataScraper/1.4; +http://your-contact-info.com)"
)

MARCAS = [
    "ACURA", "ALFA ROMEO", "AMC", "ARO", "ASIA", "ASTON MARTIN",
    "AUDI", "AUSTIN", "BAW", "BENTLEY", "BLUEBIRD", "BMW", "BRILLIANCE",
    "BUICK", "BYD", "CADILLAC", "CHANA", "CHANGAN", "CHERY", "CHEVROLET",
    "CHRYSLER", "CITROEN", "DACIA", "DAEWOO", "DAIHATSU", "DATSUN",
    "DODGE/RAM", "DODGE", "RAM", "DONFENG(ZNA)", "DONFENG", "ZNA",
    "EAGLE", "FAW", "FERRARI", "FIAT", "FORD", "FOTON", "FREIGHTLINER",
    "GEELY", "GENESIS", "GEO", "GMC", "GONOW", "GREAT WALL", "HAFEI",
    "HAIMA", "HEIBAO", "HIGER", "HINO", "HONDA", "HUMMER", "HYUNDAI",
    "INFINITI", "INTERNATIONAL", "ISUZU", "IVECO", "JAC", "JAGUAR",
    "JEEP", "JINBEI", "JMC", "JONWAY", "KENWORTH", "KIA", "LADA",
    "LAMBORGHINI", "LANCIA", "LAND ROVER", "LEXUS", "LIFAN", "LINCOLN",
    "LOTUS", "MACK", "MAGIRUZ", "MAHINDRA", "MASERATI", "MAZDA",
    "MERCEDES BENZ", "MERCURY", "MG", "MINI", "MITSUBISHI", "NISSAN",
    "OLDSMOBILE", "OPEL", "PETERBILT", "PEUGEOT", "PLYMOUTH", "POLARSUN",
    "PONTIAC", "PORSCHE", "PROTON", "RAMBLER", "RENAULT", "REVA",
    "ROLLS ROYCE", "ROVER", "SAAB", "SAMSUNG", "SATURN", "SCANIA",
    "SCION", "SEAT", "SKODA", "SMART", "SOUEAST", "SSANG YONG",
    "SUBARU", "SUZUKI", "TIANMA", "TIGER TRUCK", "TOYOTA", "VOLKSWAGEN",
    "VOLVO", "WESTERN STAR", "YUGO", "ZOTYE",
]


# ---------------------------------------------------------------------------
# Adaptive concurrency manager
# ---------------------------------------------------------------------------

class ConcurrencyManager:
    """Adjusts target concurrency based on a rolling throughput history."""

    def __init__(self, initial: int, min_val: int, max_val: int):
        self.target_concurrency = initial
        self.min = min_val
        self.max = max_val
        self._success_count = 0
        self._error_count = 0
        self._last_check_time = time.monotonic()
        self._lock = asyncio.Lock()
        self.throughput_history: deque[tuple[int, float]] = deque(maxlen=30)

    async def record_success(self):
        async with self._lock:
            self._success_count += 1

    async def record_error(self):
        async with self._lock:
            self._error_count += 1

    async def adjust_concurrency(self):
        async with self._lock:
            elapsed = time.monotonic() - self._last_check_time
            if elapsed < 20:
                return

            total = self._success_count + self._error_count
            if total == 0:
                self._reset_counters()
                return

            error_rate = self._error_count / total
            throughput = self._success_count / elapsed

            logger.info(
                "[ADJUSTER] target=%d throughput=%.2f url/s error_rate=%.2%%",
                self.target_concurrency, throughput, error_rate * 100,
            )

            if error_rate > 0.1:
                new = max(self.min, int(self.target_concurrency * 0.7))
                if new != self.target_concurrency:
                    logger.warning("🚨 High error rate — lowering concurrency to %d", new)
                    self.target_concurrency = new
                self._reset_counters()
                return

            self.throughput_history.append((self.target_concurrency, throughput))

            if len(self.throughput_history) < 5:
                self.target_concurrency = min(self.max, self.target_concurrency + 1)
                self._reset_counters()
                return

            perf: dict[int, list[float]] = {}
            for c, t in self.throughput_history:
                perf.setdefault(c, []).append(t)
            avg_perf = {c: sum(ts) / len(ts) for c, ts in perf.items()}
            best = max(avg_perf, key=avg_perf.get)  # type: ignore[arg-type]

            if self.target_concurrency < best:
                self.target_concurrency = min(self.max, self.target_concurrency + 1)
                logger.info("📈 Towards optimum (%d) → %d", best, self.target_concurrency)
            elif self.target_concurrency > best:
                self.target_concurrency = max(self.min, self.target_concurrency - 1)
                logger.info("📉 Passed optimum (%d) → %d", best, self.target_concurrency)
            else:
                self.target_concurrency = min(self.max, self.target_concurrency + 1)
                logger.info("✅ At optimum, probing higher → %d", self.target_concurrency)

            self._reset_counters()

    def _reset_counters(self):
        self._success_count = 0
        self._error_count = 0
        self._last_check_time = time.monotonic()


# ---------------------------------------------------------------------------
# Page-level helpers
# ---------------------------------------------------------------------------

async def _adjuster_task(manager: ConcurrencyManager, shutdown_event: asyncio.Event):
    while not shutdown_event.is_set():
        await asyncio.sleep(5)
        await manager.adjust_concurrency()


def _get_car_id(url: str) -> str | None:
    try:
        return parse_qs(urlparse(url).query).get("c", [None])[0]
    except Exception:
        return None


async def _block_unnecessary(page):
    await page.route(
        "**/*",
        lambda route: (
            route.abort()
            if route.request.resource_type in ["image", "stylesheet", "font", "media"]
            else route.continue_()
        ),
    )


def _log_eta(completed: int, total: int, start: float):
    if completed == 0:
        return
    elapsed = time.monotonic() - start
    eta = str(timedelta(seconds=int((elapsed / completed) * (total - completed))))
    logger.info("Progress: [%d/%d] — ETA: %s", completed, total, eta)


async def _scrape_detail_page(page) -> dict:
    data: dict = {"url": page.url}
    try:
        title_el = page.locator("div.header-text h1").first
        full_title = (await title_el.inner_text()).strip()
        parts = full_title.split()
        if parts and parts[-1].isdigit() and len(parts[-1]) == 4:
            data["año"] = int(parts.pop())
        remaining = " ".join(parts)
        for marca in MARCAS:
            if remaining.upper().startswith(marca):
                data["marca"] = marca
                data["modelo"] = remaining[len(marca):].strip()
                break
        if "modelo" not in data:
            data["modelo"] = remaining
    except Exception:
        pass
    try:
        price_usd_text = await page.locator("div.header-text h1").nth(1).inner_text()
        data["precio_crc"] = float(re.sub(r"[^\d.]", "", price_usd_text))
    except Exception:
        pass
    try:
        price_crc_text = await page.locator("div.header-text h3").first.inner_text()
        data["precio_usd"] = int(re.sub(r"[^\d]", "", price_crc_text))
    except Exception:
        pass
    try:
        data["imagen_principal"] = await page.locator("div.bannerimg").get_attribute("data-image-src")
        data["galeria_imagenes"] = [
            await img.get_attribute("src")
            for img in await page.locator("div.ws_images ul li img").all()
        ]
    except Exception:
        pass
    try:
        seller_info: dict = {}
        seller_table = page.locator('//table[.//td[contains(., "Vendedor")]]')
        for row in await seller_table.locator("tr").all():
            cells = await row.locator("td").all()
            if len(cells) == 2:
                k = (await cells[0].inner_text()).strip().lower().replace(":", "")
                v = (await cells[1].inner_text()).strip()
                if k and v:
                    seller_info[k] = re.sub(r"\s+", " ", v)
        data["vendedor"] = seller_info
    except Exception:
        pass
    try:
        general: dict = {}
        for row in await page.locator("table.mytext2 tbody tr").all():
            cells = await row.locator("td").all()
            if len(cells) == 2:
                k = (await cells[0].inner_text()).strip().lower().replace(" ", "_")
                v = (await cells[1].inner_text()).strip()
                general[k] = re.sub(r"\s+", " ", v)
            elif len(cells) == 1 and await cells[0].get_attribute("bgcolor") == "#FAF7B4":
                general["comentario_vendedor"] = (await cells[0].inner_text()).strip()
        data["informacion_general"] = general
    except Exception:
        pass
    for field, dest in [("kilometraje", "kilometraje_number"), ("cilindrada", "cilindrada_number")]:
        if field in data.get("informacion_general", {}):
            try:
                val = re.sub(r"[^\d]", "", data["informacion_general"][field])
                data["informacion_general"][dest] = int(val) if val else None
            except ValueError:
                pass
    try:
        equip: list[str] = []
        tables = page.locator('//table[@class="table table-bordered border-top table-striped"]')
        for row in await tables.locator("tbody tr").all():
            cells = await row.locator("td").all()
            if len(cells) == 2 and await cells[1].locator("i.icon-check").count() > 0:
                equip.append((await cells[0].inner_text()).strip())
        data["equipamiento"] = sorted(equip)
    except Exception:
        pass
    return data


# ---------------------------------------------------------------------------
# URL task worker
# ---------------------------------------------------------------------------

async def _scrape_single_url(
    url: str,
    context,
    semaphore: asyncio.Semaphore,
    manager: ConcurrencyManager,
    repository=None,
    shutdown_event: asyncio.Event | None = None,
) -> None:
    if shutdown_event and shutdown_event.is_set():
        return

    async with semaphore:
        car_id = _get_car_id(url)
        if not car_id:
            logger.error("Invalid car ID for URL %s — skipping.", url)
            await manager.record_error()
            return

        # Standalone mode: skip already-processed files
        if repository is None:
            out_path = os.path.join(OUTPUT_DIR, f"{car_id}.json")
            if os.path.exists(out_path):
                return

        page = None
        for attempt in range(TRIES):
            if shutdown_event and shutdown_event.is_set():
                return
            try:
                page = await context.new_page()
                await _block_unnecessary(page)
                logger.info("Scraping ID %s (attempt %d/%d)", car_id, attempt + 1, TRIES)
                await page.goto(url, wait_until="domcontentloaded", timeout=45000)
                car_data = await _scrape_detail_page(page)

                if repository is not None:
                    repository.mark_url_done(url, car_id, car_data)
                else:
                    os.makedirs(OUTPUT_DIR, exist_ok=True)
                    with open(os.path.join(OUTPUT_DIR, f"{car_id}.json"), "w", encoding="utf-8") as f:
                        json.dump(car_data, f, ensure_ascii=False, indent=4)

                logger.info("✅ ID %s saved.", car_id)
                await manager.record_success()
                await asyncio.sleep(random.uniform(1, 4))
                return
            except Exception as exc:
                logger.warning("⚠️ Attempt %d failed for ID %s: %s", attempt + 1, car_id, type(exc).__name__)
                if attempt == TRIES - 1:
                    logger.error("❌ Giving up on ID %s after %d attempts.", car_id, TRIES)
                    if repository is not None:
                        repository.mark_url_failed(url)
                    await manager.record_error()
                else:
                    await asyncio.sleep(3 + attempt * 2)
            finally:
                if page:
                    await page.close()


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------

async def main(
    repository=None,
    headless: bool = True,
    initial_concurrency: int = 3,
    min_concurrency: int = 1,
    max_concurrency: int = 10,
    shutdown_event: asyncio.Event | None = None,
    # standalone-mode args
    urls_file: str = "urls.json",
) -> str:
    """
    Scrape car detail pages.

    Returns 'done' when finished, 'paused' when shutdown_event was set early.

    Parameters
    ----------
    repository   : ScraperRepository | None
        SQLite repo. When None, falls back to JSON file I/O.
    headless     : bool   — headless Chromium
    shutdown_event : asyncio.Event | None
        Signals graceful stop (set by SIGINT/SIGTERM in run_scraper).
    urls_file    : str
        Standalone-mode only — path to the JSON URL list.
    """
    if shutdown_event is None:
        shutdown_event = asyncio.Event()

    # Collect URLs to process
    if repository is not None:
        urls_to_process = repository.get_pending_urls(limit=99_999)
        logger.info("Loaded %d pending URLs from DB.", len(urls_to_process))
    else:
        # Standalone: load from json file, skip already-done
        if not os.path.exists(urls_file):
            logger.error("URL file '%s' not found.", urls_file)
            return "failed"
        with open(urls_file, "r", encoding="utf-8") as f:
            all_urls: list[str] = json.load(f)
        os.makedirs(OUTPUT_DIR, exist_ok=True)
        urls_to_process = [
            u for u in all_urls
            if not os.path.exists(os.path.join(OUTPUT_DIR, f"{_get_car_id(u)}.json"))
        ]
        logger.info(
            "Loaded %d URLs; %d already scraped; %d remaining.",
            len(all_urls), len(all_urls) - len(urls_to_process), len(urls_to_process),
        )

    if not urls_to_process:
        logger.info("🎉 Nothing to scrape — all URLs are done.")
        return "done"

    manager = ConcurrencyManager(initial_concurrency, min_concurrency, max_concurrency)
    start_time = time.monotonic()

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=headless)
        context = await browser.new_context(user_agent=USER_AGENT)
        adjuster = asyncio.create_task(_adjuster_task(manager, shutdown_event))
        semaphore = asyncio.Semaphore(max_concurrency)

        tasks = [
            _scrape_single_url(url, context, semaphore, manager, repository, shutdown_event)
            for url in urls_to_process
        ]

        completed = 0
        for fut in asyncio.as_completed(tasks):
            await fut
            completed += 1
            if completed % 10 == 0 or completed == len(urls_to_process):
                _log_eta(completed, len(urls_to_process), start_time)
            if shutdown_event.is_set():
                logger.info("Shutdown requested — stopping remaining tasks.")
                break

        adjuster.cancel()
        try:
            await adjuster
        except asyncio.CancelledError:
            pass
        await browser.close()

    if shutdown_event.is_set():
        logger.info("Scraping paused by shutdown signal.")
        return "paused"

    logger.info("🎉 Scraping complete.")
    return "done"


# ---------------------------------------------------------------------------
# Standalone entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Crautos car details scraper.")
    parser.add_argument("-f", "--file", default="urls.json", help="JSON URL list file.")
    parser.add_argument("--initial", type=int, default=3)
    parser.add_argument("--min", type=int, default=1)
    parser.add_argument("--max", type=int, default=30)
    parser.add_argument("--headless", action="store_true", default=False)
    args = parser.parse_args()

    asyncio.run(
        main(
            urls_file=args.file,
            headless=args.headless,
            initial_concurrency=args.initial,
            min_concurrency=args.min,
            max_concurrency=args.max,
        )
    )
