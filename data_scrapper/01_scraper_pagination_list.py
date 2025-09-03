import asyncio
import json
import re
import logging
from playwright.async_api import (
    async_playwright,
    TimeoutError as PlaywrightTimeoutError,
)
from urllib.parse import urljoin
import os
from datetime import datetime

# --- Configuration ---
# Configure logging to show progress
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)

# Constants for file paths
# get day in format dd_mm_yyyy
today = datetime.now().strftime("%d_%m_%Y")

URLS_FILE = f"data/{today}/urls.json"

# --- Helper Functions for Progress Management ---


def save_json_file(data, filename):
    """Saves data to a JSON file."""
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)


# --- Core Scraping Functions ---


async def ensure_url_list_exists(page):
    """
    Scrapes all pages to create a list of car detail URLs.
    It determines the total number of pages and iterates through each one.
    """
    if os.path.exists(URLS_FILE):
        logging.info(
            f"El archivo '{URLS_FILE}' ya existe. Se omite la recolección de URLs."
        )
        return

    logging.info(f"'{URLS_FILE}' no encontrado. Iniciando recolección de URLs...")
    detail_urls = set()

    await page.goto("https://crautos.com/autosusados/")
    await page.locator(".btn.btn-lg.btn-success").click()
    # await page.wait_for_load_state('networkidle')

    # --- NEW PAGINATION LOGIC ---
    # 1. Find the "Last Page" button to determine the total number of pages.
    try:
        last_page_link = page.locator('a:has-text("Última Página")')
        href = await last_page_link.get_attribute("href", timeout=5000)
        # Extract the number from the javascript:p('NUMBER') string
        match = re.search(r"p\('(\d+)'\)", href)
        if not match:
            logging.error(
                "No se pudo determinar el número de la última página. Abortando."
            )
            return

        last_page_number = int(match.group(1))
        logging.info(f"Se encontraron {last_page_number} páginas para raspar.")
    except (PlaywrightTimeoutError, AttributeError):
        logging.error(
            "No se encontró el botón de 'Última Página'. Puede que solo haya una página de resultados."
        )
        # If the button doesn't exist, assume there's only one page.
        last_page_number = 1
    except Exception as e:
        logging.error(
            f"Error al buscar la última página: {e}. Abortando recolección de URLs."
        )
        return

    # 2. Loop through each page number.
    for page_num in range(1, last_page_number + 1):
        logging.info(f"Procesando página {page_num}/{last_page_number}...")

        # For pages after the first, navigate by executing the JavaScript function.
        if page_num > 1:
            try:
                await page.evaluate(f"p('{page_num}')")
                # Wait for the network to be idle to ensure new content is loaded
                # await page.wait_for_load_state('networkidle', timeout=30000)
            except Exception as e:
                logging.error(
                    f"Fallo al navegar a la página {page_num}: {e}. Omitiendo página."
                )
                continue

        # 3. Scrape the URLs from the current page.
        try:
            await page.wait_for_selector('a[href^="cardetail.cfm"]', timeout=10000)
            links = await page.locator('a[href^="cardetail.cfm"]').all()

            page_urls_found = 0
            for link in links:
                href = await link.get_attribute("href")
                if href:
                    absolute_url = urljoin(page.url, href)
                    if absolute_url not in detail_urls:
                        detail_urls.add(absolute_url)
                        page_urls_found += 1
            logging.info(
                f"Se encontraron {page_urls_found} nuevas URLs. Total de URLs únicas: {len(detail_urls)}"
            )

        except PlaywrightTimeoutError:
            logging.warning(
                f"No se encontraron links de autos en la página {page_num} o la página no cargó correctamente."
            )

    # 4. Save the final list of URLs.
    save_json_file(list(detail_urls), URLS_FILE)
    logging.info(f"Se guardaron {len(detail_urls)} URLs en '{URLS_FILE}'.")


async def main():
    """Función principal para orquestar el proceso de raspado."""
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context()
        page = await context.new_page()

        # Step 1: Ensure the list of URLs exists.
        await ensure_url_list_exists(page)

        await browser.close()
        logging.info("Proceso finalizado.")


if __name__ == "__main__":
    asyncio.run(main())
