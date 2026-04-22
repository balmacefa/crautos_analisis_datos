import asyncio
import logging
import re
import json
import os
from datetime import datetime
from urllib.parse import urljoin

from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeoutError

try:
    from data_scrapper.repository import ScraperRepository
except ImportError:
    from repository import ScraperRepository

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

BASE_URL = "https://www.purdyusados.com"
SEARCH_URL = f"{BASE_URL}/buscar"

class PurdyUsadosScraper:
    def __init__(self, repository: ScraperRepository = None, headless: bool = True):
        self.repository = repository
        self.headless = headless
        self.discovered_urls = set()

    async def run(self, limit_clicks: int = None):
        """Main entry point to run the scraper."""
        logger.info("Starting Purdy Usados Scraper...")
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=self.headless)
            context = await browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36"
            )
            
            # Step 1: Collect all listing URLs
            logger.info("Step 1: Collecting listing URLs from %s", SEARCH_URL)
            await self._collect_listing_urls(context, limit_clicks)
            
            # Step 2: Extract details for each URL
            logger.info("Step 2: Extracting details for %d URLs", len(self.discovered_urls))
            for url in self.discovered_urls:
                if self.repository and self.repository.is_url_done(url):
                    logger.info("Skipping already processed URL: %s", url)
                    continue
                await self._scrape_car_detail(context, url)
                await asyncio.sleep(1) # Polite delay
                
            await browser.close()
            logger.info("Purdy Usados Scraper finished.")

    async def _collect_listing_urls(self, context, limit_clicks: int = None):
        page = await context.new_page()
        try:
            await page.goto(SEARCH_URL, wait_until="networkidle", timeout=60000)
            
            clicks = 0
            while True:
                # Find the "VER MÁS" button
                load_more_btn = page.locator("button.loadMore")
                if await load_more_btn.count() > 0 and await load_more_btn.is_visible():
                    logger.info("Clicking 'VER MÁS' (click #%d)", clicks + 1)
                    await load_more_btn.scroll_into_view_if_needed()
                    await load_more_btn.click()
                    await asyncio.sleep(2) # Wait for content to load
                    clicks += 1
                    if limit_clicks and clicks >= limit_clicks:
                        logger.info("Reached limit of clicks (%d). Stopping.", limit_clicks)
                        break
                else:
                    logger.info("No more 'VER MÁS' button found.")
                    break
            
            # Extract all car links
            links = await page.locator("a[href^='/auto/']").all()
            for locator in links:
                href = await locator.get_attribute("href")
                if href:
                    abs_url = urljoin(BASE_URL, href)
                    # Deduplicate
                    self.discovered_urls.add(abs_url)
            
            logger.info("Discovered %d unique URLs.", len(self.discovered_urls))
            
        except Exception as e:
            logger.error("Error during URL collection: %s", e)
        finally:
            await page.close()

    async def _scrape_car_detail(self, context, url: str):
        """Extract metadata from a single car detail page."""
        logger.info("Scraping detail: %s", url)
        page = await context.new_page()
        try:
            await page.goto(url, wait_until="networkidle", timeout=60000)
            
            # Wait for content
            await page.wait_for_selector(".v-detail__brand", timeout=10000)
            
            # 1. Brand, Model, Year
            marca = (await page.locator(".v-detail__brand").inner_text()).strip()
            model_text = (await page.locator(".v-detail__model").inner_text()).strip()
            year_text = (await page.locator(".v-detail__year").inner_text()).strip()
            
            # 2. Price
            price_text = (await page.locator(".v-detail__price").inner_text()).strip()
            
            # 3. Specs
            details = {}
            spec_items = await page.locator(".v-detail__spec-item").all()
            for item in spec_items:
                # Structure: div contains span(label) and p(value) or similar
                label_loc = item.locator("span")
                value_loc = item.locator("p")
                if await label_loc.count() > 0 and await value_loc.count() > 0:
                    label = (await label_loc.inner_text()).strip().lower()
                    value = (await value_loc.inner_text()).strip()
                    details[label] = value

            # 4. Images
            # We might need to click the "FOTOS" tab if images are not in DOM
            # But usually thumbnails or a popup gallery links are present.
            # Let's try to find a.js-popup-img
            images = []
            img_locators = await page.locator("a.js-popup-img").all()
            for img in img_locators:
                href = await img.get_attribute("href")
                if href:
                    images.append(urljoin(BASE_URL, href))
            
            # Fallback if no images found via link (check for img tags in a specific container)
            if not images:
                img_tags = await page.locator(".v-detail__gallery img").all()
                for img in img_tags:
                    src = await img.get_attribute("src")
                    if src:
                        images.append(urljoin(BASE_URL, src))

            # Parse Year from text if not just a number
            year = 0
            if year_text.isdigit():
                year = int(year_text)
            else:
                # Try to find 4-digit year in model_text or year_text
                year_match = re.search(r"(\d{4})", f"{year_text} {model_text}")
                if year_match:
                    year = int(year_match.group(1))

            # Unit ID
            unit_id_raw = details.get("no. unidad", url.rstrip("/").split("/")[-1])
            car_id = f"purdy-{unit_id_raw}"

            # Normalize data
            structured_data = {
                "marca": marca,
                "modelo": model_text,
                "año": year,
                "precio_usd": price_text,
                "precio_crc": "0", # Purdy usually lists in USD
                "informacion_general": {
                    "kilometraje": details.get("kilometraje", "0 km"),
                    "kilometraje_number": int(re.sub(r"\D", "", details.get("kilometraje", "0")) or 0),
                    "combustible": details.get("combustible", "Desconocido"),
                    "transmisión": details.get("transmisión", "Desconocida"),
                    "motor": details.get("motor", "Desconocido"),
                    "tracción": details.get("tracción", "Desconocida"),
                    "provincia": "San José (Purdy)", # Default as they are national but centered in SJ
                },
                "images": images,
                "imagen_principal": images[0] if images else ""
            }

            if self.repository:
                self.repository.mark_url_done(url, car_id, structured_data)
                logger.info("Saved car %s to DB", car_id)
            else:
                logger.info("Scraped data: %s", json.dumps(structured_data, indent=2))

        except Exception as e:
            logger.error("Failed to scrape %s: %s", url, e)
        finally:
            await page.close()

async def main():
    db_path = os.getenv("SCRAPER_DB_PATH", "data/crautos.db")
    # Adjust path if running from backend dir or root
    if not os.path.exists(db_path) and os.path.exists("backend/data/crautos.db"):
        db_path = "backend/data/crautos.db"
    elif not os.path.exists(db_path) and "backend" in os.getcwd():
         db_path = "data/crautos.db"

    repo = None
    if os.path.exists(db_path):
        repo = ScraperRepository(db_path)
    else:
        logger.warning("Repository not found at %s. Running in dry-run mode.", db_path)
        
    scraper = PurdyUsadosScraper(repository=repo, headless=True)
    await scraper.run(limit_clicks=1) # Limit for initial testing

if __name__ == "__main__":
    asyncio.run(main())
