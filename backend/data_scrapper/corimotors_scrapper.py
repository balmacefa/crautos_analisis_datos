import asyncio
import logging
import re
import json
from urllib.parse import urljoin
from playwright.async_api import async_playwright
from .repository import ScraperRepository

# UI / Logging Setup
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

BASE_URL = "https://usadoscori.com"
CATALOG_URL = "https://usadoscori.com/catalog/filtro/"

class CorimotorsScraper:
    def __init__(self, repository=None, headless=True):
        self.repository = repository
        self.headless = headless
        self.discovered_urls = set()

    async def run(self, limit_pages=5):
        """Main entry point for scraping Corimotors."""
        logger.info("Starting Corimotors Scraper...")
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=self.headless)
            context = await browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36"
            )
            
            # 1. Collect car URLs
            await self._collect_listing_urls(context, limit_pages)
            
            # 2. Scrape each car detail
            logger.info("Found %d URLs to scrape.", len(self.discovered_urls))
            for url in self.discovered_urls:
                if self.repository and self.repository.is_url_done(url):
                    logger.info("Skipping already processed URL: %s", url)
                    continue
                await self._scrape_car_detail(context, url)
                # Small wait to be polite
                await asyncio.sleep(1)

            await browser.close()
            logger.info("Corimotors Scraper finished.")

    async def _collect_listing_urls(self, context, limit_pages):
        """Navigate through listing pages and collect detail links."""
        page = await context.new_page()
        try:
            for p_num in range(1, limit_pages + 1):
                url = CATALOG_URL if p_num == 1 else f"{CATALOG_URL}?PAGEN_1={p_num}"
                logger.info("Visiting listings page %d: %s", p_num, url)
                await page.goto(url, wait_until="domcontentloaded", timeout=60000)
                
                # Wait for the item container or a timeout if it's empty
                try:
                    await page.wait_for_selector(".product-item", timeout=10000)
                except:
                    logger.info("No more products found or page timed out at page %d", p_num)
                    break

                # Extract links
                # Usually: <a class="product-item-image-wrapper" href="...">
                links = await page.locator("a.product-item-image-wrapper").all()
                page_urls = []
                found_on_page = 0
                for link in links:
                    href = await link.get_attribute("href")
                    if href:
                        full_url = urljoin(BASE_URL, href)
                        if full_url not in self.discovered_urls:
                            self.discovered_urls.add(full_url)
                            page_urls.append(full_url)
                            found_on_page += 1
                
                if self.repository and page_urls:
                    self.repository.upsert_urls(page_urls, source="CoriMotors")
                
                logger.info("Found %d new URLs on page %d", found_on_page, p_num)
                if found_on_page == 0:
                    break
        except Exception as e:
            logger.error("Error during URL collection: %s", e)
        finally:
            await page.close()

    async def _scrape_car_detail(self, context, url: str):
        """Extract metadata from a single car detail page."""
        logger.info("Scraping detail: %s", url)
        page = await context.new_page()
        try:
            await page.goto(url, wait_until="domcontentloaded", timeout=60 * 1000)

            # 1. Title (Brand Model Year)
            # Usually: <h1 class="product-item-detail-title">...</h1>
            title_loc = page.locator("h1.product-item-detail-title")
            await title_loc.wait_for(timeout=10000)
            title = (await title_loc.inner_text()).strip()

            # 2. Price
            # Usually: <div class="product-item-detail-price-current">...</div>
            price_loc = page.locator(".product-item-detail-price-current")
            price_str = await price_loc.inner_text() if await price_loc.count() > 0 else "0"

            # 3. Properties (Spec Sheet)
            details = {}
            # Bitrix structure for properties
            prop_container = page.locator(".product-item-detail-properties")
            if await prop_container.count() > 0:
                rows = await prop_container.locator(".product-item-detail-properties-item").all()
                for row in rows:
                    name_loc = row.locator(".product-item-detail-properties-item-name")
                    val_loc = row.locator(".product-item-detail-properties-item-value")
                    if await name_loc.count() > 0 and await val_loc.count() > 0:
                        name = (await name_loc.inner_text()).replace(":", "").strip().lower()
                        val = (await val_loc.inner_text()).strip()
                        details[name] = val

            # 4. Images
            images = []
            img_locators = await page.locator(".product-item-detail-slider-container img").all()
            for img in img_locators:
                src = await img.get_attribute("src")
                if src:
                    images.append(urljoin(BASE_URL, src))

            # Logic to split Brand/Model/Year from title if not in props
            # Example: "MITSUBISHI XPANDER 2024"
            parts = title.split()
            marca = details.get("marca", parts[0] if parts else "Desconocida")
            
            # Year discovery in title
            year = 0
            for p in parts:
                if p.isdigit() and len(p) == 4:
                    year = int(p)
                    break
            
            # If "Año" is in properties, trust it more
            if "año" in details and details["año"].isdigit():
                year = int(details["año"])

            modelo = details.get("modelo", " ".join([p for p in parts[1:] if p != str(year)]) if len(parts) > 1 else "Desconocido")

            # Normalization
            car_id = f"cori-{url.rstrip('/').split('/')[-1]}"
            # To ensure compatibility with the search engine (FTS5), we synthesize an 'equipamiento' field
            equipment_list = [f"{k}: {v}" for k, v in details.items() if k not in ["precio", "recorrido", "año", "marca", "modelo"]]
            
            structured_data = {
                "marca": marca,
                "modelo": modelo,
                "año": year,
                "precio_usd": price_str if "$" in price_str else f"${price_str}",
                "precio_crc": "0", # Corimotors mostly lists in USD
                "informacion_general": {
                    "kilometraje": details.get("recorrido", details.get("kilometraje", "0 km")),
                    "kilometraje_number": int(re.sub(r"\D", "", details.get("recorrido", details.get("kilometraje", "0"))) or 0),
                    "combustible": details.get("combustible", "Gasolina"),
                    "transmisión": details.get("transmisión", "Automático"),
                    "provincia": "San José (Corimotors)",
                },
                "equipamiento": ", ".join(equipment_list),
                "images": images,
                "imagen_principal": images[0] if images else ""
            }

            if self.repository:
                self.repository.mark_url_done(url, car_id, structured_data, source="CoriMotors")
                logger.info("Saved Corimotors car %s to DB", car_id)
            else:
                logger.info("Scraped data for %s: %s", car_id, json.dumps(structured_data, indent=4))

        except Exception as e:
            logger.error("Failed to scrape Corimotors detail %s: %s", url, e)
        finally:
            await page.close()

if __name__ == "__main__":
    # Test execution
    scraper = CorimotorsScraper()
    asyncio.run(scraper.run(limit_pages=1))
