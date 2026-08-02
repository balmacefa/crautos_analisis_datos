"""
epaenlinea_scrapper.py — Scraper for cr.epaenlinea.com (Ferretería EPA Costa Rica).

First source of the open-data pivot beyond cars: hardware / home-improvement
products. See `epaenlinea_strategy.md` for the full site-structure writeup
and, importantly, a big "UNVALIDATED" disclaimer — the selectors below were
authored without direct browser access to the real site (outbound access to
cr.epaenlinea.com was blocked in the sandbox this was written in), so every
selector is tried as a cascade of fallbacks rather than a single hard-coded
value. Validate against the live site before relying on this for production
data, and see the strategy doc's "Recon Checklist" before enabling a cron
schedule for it.
"""

import asyncio
import logging
import re
import json
import os
from urllib.parse import urljoin, urlparse

from playwright.async_api import async_playwright

try:
    from data_scrapper.repository import ScraperRepository
except ImportError:
    from repository import ScraperRepository

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

BASE_URL = "https://cr.epaenlinea.com"
SOURCE_NAME = "EpaEnLinea"

# Pilot scope: a couple of known real categories, not a full catalog crawl.
PILOT_CATEGORY_PATHS = ["/rodines.html", "/amarre.html"]

# Pages that are not product categories/details — never treat these as products.
EXCLUDE_PATH_FRAGMENTS = (
    "/tiendas/",
    "/preguntas-frecuentes",
    "catalogo.html",
    "productos.html",
    "empresas.",
    "/carrito",
    "/checkout",
    "/login",
    "/cuenta",
)

PRODUCT_CARD_SELECTORS = (
    ".product a[href]",
    ".product-item a[href]",
    ".vtex-product-summary a[href]",
    "[data-product] a[href]",
    ".item a[href]",
)

PAGINATION_NEXT_SELECTORS = (
    "a.next",
    "a[rel='next']",
    ".pagination a.next",
    "button.pagination-btn--next",
)


def _is_excluded(url: str) -> bool:
    return any(fragment in url for fragment in EXCLUDE_PATH_FRAGMENTS)


def _slug_from_url(url: str) -> str:
    path = urlparse(url).path
    slug = path.rstrip("/").split("/")[-1]
    slug = re.sub(r"\.html?$", "", slug)
    return slug or "producto"


class EpaEnLineaScraper:
    def __init__(self, repository: ScraperRepository = None, headless: bool = True, category_paths=None):
        self.repository = repository
        self.headless = headless
        self.category_paths = category_paths or list(PILOT_CATEGORY_PATHS)
        # url -> category slug
        self.discovered_urls: dict[str, str] = {}

    async def run(self, limit_pages: int = 2):
        """Main entry point: crawl the configured pilot categories, then scrape each product."""
        logger.info("Starting EPA en Línea Scraper (pilot categories: %s)...", self.category_paths)
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=self.headless)
            context = await browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36"
            )

            for category_path in self.category_paths:
                await self._collect_category_urls(context, category_path, limit_pages)

            logger.info("Found %d unique product URLs across %d categories.", len(self.discovered_urls), len(self.category_paths))

            for url, category in self.discovered_urls.items():
                if self.repository and self.repository.is_product_url_done(url):
                    logger.info("Skipping already processed URL: %s", url)
                    continue
                await self._scrape_product_detail(context, url, category)
                await asyncio.sleep(1)  # Polite delay

            await browser.close()
            logger.info("EPA en Línea Scraper finished.")

    async def _collect_category_urls(self, context, category_path: str, limit_pages: int):
        """Crawl a single category page (with best-effort pagination)."""
        category_slug = category_path.strip("/")
        category_slug = re.sub(r"\.html?$", "", category_slug)
        category_url = urljoin(BASE_URL, category_path)

        page = await context.new_page()
        page_urls = []
        try:
            await page.goto(category_url, wait_until="networkidle", timeout=60000)

            for page_num in range(1, limit_pages + 1):
                logger.info("Processing %s — page %d", category_slug, page_num)

                candidates = set()
                for selector in PRODUCT_CARD_SELECTORS:
                    try:
                        links = await page.locator(selector).all()
                    except Exception:
                        continue
                    for link in links:
                        href = await link.get_attribute("href")
                        if href:
                            candidates.add(href)

                if not candidates:
                    # Generic fallback: any .html link that isn't a known non-product page.
                    try:
                        links = await page.locator("a[href$='.html']").all()
                        for link in links:
                            href = await link.get_attribute("href")
                            if href:
                                candidates.add(href)
                    except Exception:
                        pass

                new_on_page = 0
                for href in candidates:
                    abs_url = urljoin(BASE_URL, href)
                    if abs_url == category_url or _is_excluded(abs_url):
                        continue
                    if abs_url not in self.discovered_urls:
                        self.discovered_urls[abs_url] = category_slug
                        page_urls.append(abs_url)
                        new_on_page += 1

                logger.info("Found %d new product URLs on %s page %d", new_on_page, category_slug, page_num)

                if page_num >= limit_pages:
                    break

                advanced = await self._advance_page(page, category_url, page_num)
                if not advanced:
                    logger.info("No more pages for %s.", category_slug)
                    break

        except Exception as e:
            logger.error("Error collecting URLs for category %s: %s", category_slug, e)
        finally:
            await page.close()

        if self.repository and page_urls:
            self.repository.upsert_product_urls(page_urls, source=SOURCE_NAME, category=category_slug)

        return page_urls

    async def _advance_page(self, page, category_url: str, current_page_num: int) -> bool:
        """Try clicking a 'next' control; fall back to a `?page=N` query string. Returns True if advanced."""
        for selector in PAGINATION_NEXT_SELECTORS:
            try:
                next_btn = page.locator(selector)
                if await next_btn.count() > 0 and await next_btn.is_enabled():
                    await next_btn.click()
                    await page.wait_for_timeout(2000)
                    return True
            except Exception:
                continue

        try:
            next_url = f"{category_url}?page={current_page_num + 1}"
            await page.goto(next_url, wait_until="networkidle", timeout=60000)
            return True
        except Exception:
            return False

    async def _scrape_product_detail(self, context, url: str, category: str):
        """Extract metadata from a single product detail page."""
        logger.info("Scraping EPA product: %s", url)
        page = await context.new_page()
        try:
            await page.goto(url, wait_until="networkidle", timeout=60000)
            await page.locator("h1").first.wait_for(state="attached", timeout=10000)

            nombre = (await page.locator("h1").first.inner_text()).strip()

            precio_crc = await self._extract_price(page)
            sku = await self._extract_sku(page, url)
            breadcrumb_category = await self._extract_breadcrumb_category(page)
            descripcion = await self._extract_description(page)
            especificaciones = await self._extract_specs(page)
            images = await self._extract_images(page)

            product_id = f"epa-{_slug_from_url(url)}"

            structured_data = {
                "nombre": nombre or "Producto EPA",
                "categoria": breadcrumb_category or category,
                "subcategoria": category if breadcrumb_category else None,
                "marca": especificaciones.get("marca"),
                "sku": sku,
                "precio_crc": precio_crc,
                "precio_usd": None,
                "disponibilidad": especificaciones.get("disponibilidad"),
                "descripcion": descripcion,
                "especificaciones": especificaciones,
                "images": images,
                "imagen_principal": images[0] if images else "",
            }

            if self.repository:
                self.repository.mark_product_url_done(url, product_id, structured_data, source=SOURCE_NAME, category=category)
                logger.info("Saved EPA product %s to DB", product_id)
            else:
                logger.info("Scraped data for %s: %s", product_id, json.dumps(structured_data, indent=2, ensure_ascii=False))

        except Exception as e:
            logger.error("Failed to scrape EPA product %s: %s", url, e)
            if self.repository:
                self.repository.mark_product_url_failed(url)
        finally:
            await page.close()

    @staticmethod
    async def _extract_price(page) -> float:
        # CRC prices are conventionally whole colones (no centavos) and use
        # '.' or ',' purely as thousands separators — so we just strip both
        # and parse the remaining digits as an integer amount.
        for selector in (".price", ".product-price", "[itemprop='price']"):
            try:
                loc = page.locator(selector).first
                if await loc.count() > 0:
                    text = await loc.inner_text()
                    digits = re.sub(r"[^\d]", "", text)
                    if digits:
                        return float(digits)
            except Exception:
                continue

        # Full-page fallback: look for a colón-prefixed amount.
        try:
            body_text = await page.locator("body").inner_text()
            match = re.search(r"₡\s*[\d.,]+", body_text)
            if match:
                digits = re.sub(r"[^\d]", "", match.group(0))
                if digits:
                    return float(digits)
        except Exception:
            pass
        return 0.0

    @staticmethod
    async def _extract_sku(page, url: str) -> str:
        try:
            body_text = await page.locator("body").inner_text()
            match = re.search(r"(?:SKU|C[oó]digo)\s*[:#]?\s*([A-Za-z0-9\-]+)", body_text)
            if match:
                return match.group(1)
        except Exception:
            pass
        return _slug_from_url(url)

    @staticmethod
    async def _extract_breadcrumb_category(page) -> str | None:
        for selector in (".breadcrumb a", "nav[aria-label='breadcrumb'] a"):
            try:
                crumbs = await page.locator(selector).all()
                if crumbs:
                    texts = [await c.inner_text() for c in crumbs]
                    texts = [t.strip() for t in texts if t.strip() and t.strip().lower() not in ("inicio", "home")]
                    if texts:
                        return texts[-1]
            except Exception:
                continue
        return None

    @staticmethod
    async def _extract_description(page) -> str | None:
        for selector in (".product-description", "#description"):
            try:
                loc = page.locator(selector).first
                if await loc.count() > 0:
                    text = (await loc.inner_text()).strip()
                    if text:
                        return text
            except Exception:
                continue
        try:
            paragraphs = await page.locator("p").all()
            for p_loc in paragraphs:
                text = (await p_loc.inner_text()).strip()
                if len(text) > 20:
                    return text
        except Exception:
            pass
        return None

    @staticmethod
    async def _extract_specs(page) -> dict:
        specs = {}
        try:
            dt_items = await page.locator("dl dt").all()
            dd_items = await page.locator("dl dd").all()
            for dt, dd in zip(dt_items, dd_items):
                key = (await dt.inner_text()).strip().lower()
                val = (await dd.inner_text()).strip()
                if key:
                    specs[key] = val
        except Exception:
            pass

        if not specs:
            try:
                rows = await page.locator("table tr").all()
                for row in rows:
                    cells = await row.locator("th, td").all()
                    if len(cells) >= 2:
                        key = (await cells[0].inner_text()).strip().lower()
                        val = (await cells[1].inner_text()).strip()
                        if key:
                            specs[key] = val
            except Exception:
                pass

        return specs

    @staticmethod
    async def _extract_images(page) -> list[str]:
        images = []
        for selector in (".product-images img", ".gallery img", ".swiper-slide img"):
            try:
                img_locators = await page.locator(selector).all()
            except Exception:
                continue
            for img in img_locators:
                src = await img.get_attribute("src")
                if src:
                    images.append(urljoin(BASE_URL, src))
            if images:
                break
        return images


async def main():
    db_path = os.getenv("SCRAPER_DB_PATH", "data/crautos.db")
    if not os.path.exists(db_path) and os.path.exists("backend/data/crautos.db"):
        db_path = "backend/data/crautos.db"
    elif not os.path.exists(db_path) and "backend" in os.getcwd():
        db_path = "data/crautos.db"

    repo = ScraperRepository(db_path) if os.path.exists(db_path) else None
    if repo is None:
        logger.warning("Repository not found at %s. Running in dry-run mode.", db_path)

    scraper = EpaEnLineaScraper(repository=repo, headless=True)
    await scraper.run(limit_pages=1)


if __name__ == "__main__":
    asyncio.run(main())
