import asyncio
import logging
import re
import json
from urllib.parse import urljoin
from playwright.async_api import async_playwright
from .repository import ScraperRepository

# Setup
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

BASE_URL = "https://veinsausados.com"
CATALOG_URL = "https://veinsausados.com/buscador?search=true"

class VeinsaScraper:
    def __init__(self, repository=None, headless=True):
        self.repository = repository
        self.headless = headless
        self.discovered_urls = set()

    async def run(self, limit_pages=10):
        """Main entry point for scraping Veinsa."""
        logger.info("Starting Veinsa Scraper...")
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=self.headless)
            context = await browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36"
            )
            
            # 1. Collect car URLs via pagination
            await self._collect_listing_urls(context, limit_pages)
            
            # 2. Scrape each car detail
            logger.info("Found %d URLs to scrape.", len(self.discovered_urls))
            for url in self.discovered_urls:
                if self.repository and self.repository.is_url_done(url):
                    logger.info("Skipping already processed URL: %s", url)
                    continue
                await self._scrape_car_detail(context, url)
                await asyncio.sleep(1) # Polite delay

            await browser.close()
            logger.info("Veinsa Scraper finished.")

    async def _collect_listing_urls(self, context, limit_pages):
        """Crawl the catalog page by page."""
        page = await context.new_page()
        try:
            await page.goto(CATALOG_URL, wait_until="networkidle", timeout=60000)
            
            for p_num in range(1, limit_pages + 1):
                logger.info("Processing listings page %d", p_num)
                
                # Wait for loading spinner to disappear if it exists
                try:
                    await page.wait_for_selector(".loader", state="hidden", timeout=5000)
                    await page.wait_for_selector(".loading", state="hidden", timeout=5000)
                except:
                    pass

                # Clic on each card to get the detail URL, because it relies on JS
                cards = await page.locator(".categorySlider__item-body").all()
                found_on_page = 0
                page_urls = []
                
                for i in range(len(cards)):
                    # Reload locators as DOM might change when we go back
                    current_cards = await page.locator(".categorySlider__item-body").all()
                    if i >= len(current_cards):
                        break
                    card = current_cards[i]

                    try:
                        # Click the card to navigate
                        await card.click()
                        await page.wait_for_timeout(2000) # Wait for url to change

                        full_url = page.url
                        if "/caracteristica-del-vehiculo/" in full_url or "/detalle/" in full_url:
                            if full_url not in self.discovered_urls:
                                self.discovered_urls.add(full_url)
                                page_urls.append(full_url)
                                found_on_page += 1
                    except Exception as e:
                        logger.error(f"Error clicking card {i}: {e}")
                    finally:
                        # Go back to the listing
                        if "/caracteristica-del-vehiculo/" in page.url or "/detalle/" in page.url:
                            await page.go_back(wait_until="networkidle")
                            await page.wait_for_timeout(1000)
                
                if self.repository and page_urls:
                    self.repository.upsert_urls(page_urls, source="VeinsaUsados")
                
                logger.info("Found %d new URLs on page %d", found_on_page, p_num)

                # Pagination: Find the "Next" button
                next_btn = page.locator("button.pagination-btn--next")
                if await next_btn.count() > 0 and await next_btn.is_enabled():
                    # Check if next button is actually clickable (not just present)
                    # Often Bitrix or other frameworks disable it when at last page
                    await next_btn.click()
                    # Wait for either a reload or the grid to change
                    await asyncio.sleep(2)
                else:
                    logger.info("No more pages or next button disabled.")
                    break
                    
        except Exception as e:
            logger.error("Error during Veinsa URL collection: %s", e)
        finally:
            await page.close()

    async def _scrape_car_detail(self, context, url: str):
        """Extract metadata from a car detail page."""
        logger.info("Scraping Veinsa detail: %s", url)
        page = await context.new_page()
        try:
            await page.goto(url, wait_until="networkidle", timeout=60000)
            
            # Wait for content to stabilize
            # Use state='attached' instead of 'visible' just in case h1 is hidden initially
            await page.locator("h1").first.wait_for(state="attached", timeout=10000)

            # 1. Title & IDs
            title = (await page.locator("h1").first.inner_text()).strip()
            
            # 2. Extract price
            # Usually an h2 with $ or a div with "Total$"
            price_str = "0"
            h2_locators = await page.locator("h2").all()
            for h2 in h2_locators:
                text = await h2.inner_text()
                if text and "$" in text:
                    price_str = text.strip()
                    break

            if price_str == "0":
                price_loc = page.locator("div:has-text('Total$')").first
                if await price_loc.count() > 0:
                    text = await price_loc.inner_text()
                    match = re.search(r'\$\s*[\d,]+', text)
                    if match:
                        price_str = match.group(0)

            # 3. Attributes (Kilometraje, Transmision, etc)
            details = {}
            # Technical specs are usually h2 with the value, and parent contains the key
            for h2 in h2_locators:
                val = (await h2.inner_text()).strip()
                if val and not "$" in val:
                    # Evaluate parent text in page
                    parent_text = await h2.evaluate("node => node.parentElement ? node.parentElement.innerText : ''")
                    if parent_text:
                        # Extract the key by removing the value from the parent text
                        key = parent_text.replace(val, "").strip().lower()
                        if key:
                            details[key] = val

            # 4. Images
            images = []
            img_locators = await page.locator("img").all()
            for img in img_locators:
                src = await img.get_attribute("src")
                # Filter for reasonably sized images or those in a gallery container
                if src and ("/images/vehiculos/" in src or "/uploads/" in src):
                    images.append(urljoin(BASE_URL, src))

            # Parsin Brand/Model/Year
            # Title format often MARCA MODELO (YEAR)
            # Example: "CITROEN C-ELYSEE (2016)"
            year = 0
            year_match = re.search(r"\((\d{4})\)", title)
            if year_match:
                year = int(year_match.group(1))
            
            # If not in title, check details
            if year == 0 and "año" in details and details["año"].isdigit():
                year = int(details["año"])

            clean_title = re.sub(r"\(\d{4}\)", "", title).strip()
            parts = clean_title.split()
            marca = parts[0] if parts else "Desconocida"
            modelo = " ".join(parts[1:]) if len(parts) > 1 else "Desconocido"

            # Normalize
            # Extract ID from URL tail
            car_id_match = re.search(r"-(\d+)$", url.rstrip("/"))
            suffix = car_id_match.group(1) if car_id_match else url.rstrip("/").split("/")[-1]
            car_id = f"veinsa-{suffix}"

            # To ensure compatibility with the search engine (FTS5), we synthesize an 'equipamiento' field
            equipment_list = [f"{k}: {v}" for k, v in details.items() if k not in ["kilometraje", "año", "marca", "modelo"]]

            structured_data = {
                "marca": marca,
                "modelo": modelo,
                "año": year,
                "precio_usd": price_str,
                "precio_crc": "0",
                "informacion_general": {
                    "kilometraje": details.get("kilometraje", "0 km"),
                    "kilometraje_number": int(re.sub(r"\D", "", details.get("kilometraje", "0")) or 0),
                    "combustible": details.get("combustible", "Gasolina"),
                    "transmisión": details.get("transmisión", "Manual"),
                    "motor": details.get("motor", "N/A"),
                    "provincia": "San José (Veinsa)",
                },
                "equipamiento": ", ".join(equipment_list),
                "images": images,
                "imagen_principal": images[0] if images else ""
            }

            if self.repository:
                self.repository.mark_url_done(url, car_id, structured_data, source="VeinsaUsados")
                logger.info("Saved Veinsa car %s to DB", car_id)
            else:
                logger.info("Scraped data for %s: %s", car_id, json.dumps(structured_data, indent=4))

        except Exception as e:
            logger.error("Failed to scrape Veinsa detail %s: %s", url, e)
        finally:
            await page.close()

if __name__ == "__main__":
    scraper = VeinsaScraper(headless=False)
    asyncio.run(scraper.run(limit_pages=1))
