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

BASE_URL = "https://evmarket.cr"
LISTINGS_URL = f"{BASE_URL}/listings"

class EVMarketScraper:
    def __init__(self, repository: ScraperRepository = None, headless: bool = True):
        self.repository = repository
        self.headless = headless
        self.discovered_urls = set()

    async def run(self, limit_pages: int = None):
        """Main entry point to run the scraper."""
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=self.headless)
            context = await browser.new_context()
            
            # Step 1: Collect all listing URLs
            logger.info("Step 1: Collecting listing URLs from %s", LISTINGS_URL)
            await self._collect_listing_urls(context, limit_pages)
            
            # Step 2: Extract details for each URL
            logger.info("Step 2: Extracting details for %d URLs", len(self.discovered_urls))
            for url in self.discovered_urls:
                if self.repository and self.repository.is_url_done(url):
                    logger.info("Skipping already processed URL: %s", url)
                    continue
                await self._scrape_car_detail(context, url)
                
            await browser.close()

    async def _collect_listing_urls(self, context, limit_pages: int = None):
        page = await context.new_page()
        current_page = 1
        
        while True:
            url = f"{LISTINGS_URL}?page={current_page}" if current_page > 1 else LISTINGS_URL
            logger.info("Fetching listings from page %d: %s", current_page, url)
            
            try:
                await page.goto(url, wait_until="domcontentloaded", timeout=60000)
                # Wait for the listing grid boxes
                await page.wait_for_selector(".category-grid-box-1", timeout=10000)
                
                # Extract detail links
                # Updated selector: .short-description-1 h3 a
                links = await page.locator(".category-grid-box-1 h3 a").all()
                if not links:
                    logger.info("No more listings found on page %d. Stopping.", current_page)
                    break
                    
                page_urls = []
                for locator in links:
                    href = await locator.get_attribute("href")
                    if href:
                        abs_url = urljoin(BASE_URL, href)
                        page_urls.append(abs_url)
                        self.discovered_urls.add(abs_url)
                
                if self.repository:
                    self.repository.upsert_urls(page_urls, source="EVMarket")
                
                logger.info("Page %d: Found %d unique URLs so far.", current_page, len(self.discovered_urls))
                
                # Check for next page
                # The site uses standard pagination links. If we can't find next, we stop.
                current_page += 1
                if limit_pages and current_page > limit_pages:
                    break
            except Exception as e:
                logger.error("Error on listings page %d: %s", current_page, e)
                break
        
        await page.close()

    async def _scrape_car_detail(self, context, url: str):
        """Extract metadata from a single car detail page."""
        logger.info("Scraping detail: %s", url)
        page = await context.new_page()
        try:
            await page.goto(url, wait_until="domcontentloaded", timeout=60000)
            
            # 1. Title (Brand Model Year)
            title_loc = page.locator(".listing-title h2")
            await title_loc.wait_for(timeout=10000)
            title = await title_loc.inner_text()
            
            # 2. Price
            price_crc_loc = page.locator(".listing-price .price-crc")
            price_usd_loc = page.locator(".listing-price .price-usd")
            
            price_crc = await price_crc_loc.inner_text() if await price_crc_loc.count() > 0 else "0"
            price_usd = await price_usd_loc.inner_text() if await price_usd_loc.count() > 0 else "0"
            
            # 3. Features / Details
            details = {}
            list_items = await page.locator(".listing-details li").all()
            for li in list_items:
                text = await li.inner_text()
                if ":" in text:
                    key, val = text.split(":", 1)
                    details[key.strip().lower()] = val.strip()

            # 4. Images
            img_locators = await page.locator(".gallery-item img").all()
            images = []
            for img in img_locators:
                src = await img.get_attribute("src")
                if src:
                    images.append(urljoin(BASE_URL, src))

            # Parse Marca/Modelo/Año from title
            # Example: "BYD Yuan Plus 2024"
            parts = title.split()
            marca = parts[0] if len(parts) > 0 else "Desconocida"
            año = 0
            # Try to find a 4-digit year
            for p in parts:
                if p.isdigit() and len(p) == 4:
                    año = int(p)
                    break
            modelo = " ".join([p for p in parts[1:] if p != str(año)])

            # Normalize data
            car_id = f"ev-{url.rstrip('/').split('/')[-1]}"
            structured_data = {
                "marca": marca,
                "modelo": modelo,
                "año": año,
                "precio_usd": price_usd,
                "precio_crc": price_crc,
                "informacion_general": {
                    "kilometraje": details.get("kilometraje", "0"),
                    "kilometraje_number": int(re.sub(r"\D", "", details.get("kilometraje", "0")) or 0),
                    "combustible": details.get("combustible", "Eléctrico"),
                    "transmisión": details.get("transmisión", "Automático"),
                    "provincia": details.get("ubicación", "Desconocida"),
                },
                "images": images,
                "imagen_principal": images[0] if images else ""
            }

            if self.repository:
                self.repository.mark_url_done(url, car_id, structured_data, source="EVMarket")
                logger.info("Saved car %s to DB", car_id)
            else:
                logger.info("Scraped data: %s", json.dumps(structured_data, indent=2))

        except Exception as e:
            logger.error("Failed to scrape %s: %s", url, e)
        finally:
            await page.close()

async def main():
    db_path = os.getenv("SCRAPER_DB_PATH", "crautos.db")
    repo = None
    if os.path.exists(db_path) or "backend" in os.getcwd():
        repo = ScraperRepository(db_path)
        
    scraper = EVMarketScraper(repository=repo, headless=True)
    await scraper.run(limit_pages=2) # Limit for initial testing

if __name__ == "__main__":
    asyncio.run(main())
