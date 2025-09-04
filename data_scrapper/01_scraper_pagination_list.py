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
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)

# Paths
today = datetime.now().strftime("%d_%m_%Y")
os.makedirs(f"data_scrapper/data/{today}", exist_ok=True)
URLS_FILE = f"data_scrapper/data/{today}/urls.json"
FAILED_URLS_FILE = f"data_scrapper/data/{today}/failed_urls.json"


# --- Helper Functions ---
def save_json_file(data, filename):
    """Saves data to a JSON file."""
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)


def append_failed_url(url):
    """Append a failed URL or page reference to the JSON file."""
    failed_urls = []
    if os.path.exists(FAILED_URLS_FILE):
        with open(FAILED_URLS_FILE, "r", encoding="utf-8") as f:
            try:
                failed_urls = json.load(f)
            except json.JSONDecodeError:
                failed_urls = []
    if url not in failed_urls:
        failed_urls.append(url)
    save_json_file(failed_urls, FAILED_URLS_FILE)


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

    # Determine total pages
    try:
        last_page_link = page.locator('a:has-text("Última Página")')
        href = await last_page_link.get_attribute("href", timeout=5000)
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
            "No se encontró el botón de 'Última Página'. Puede que solo haya una página."
        )
        last_page_number = 1
    except Exception as e:
        logging.error(f"Error al buscar la última página: {e}. Abortando.")
        return

    # Loop through pages
    for page_num in range(1, last_page_number + 1):
        logging.info(f"Procesando página {page_num}/{last_page_number}...")

        if page_num > 1:
            try:
                # Wait for navigation to complete after clicking
                async with page.expect_navigation(wait_until="domcontentloaded"):
                    await page.evaluate(f"p('{page_num}')")
            except Exception as e:
                logging.error(
                    f"Fallo al navegar a la página {page_num}: {e}. Guardando para retry."
                )
                append_failed_url(f"PAGE::{page_num}")
                continue

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
                f"Se encontraron {page_urls_found} nuevas URLs en esta página. Total acumulado: {len(detail_urls)}"
            )

        except PlaywrightTimeoutError:
            logging.warning(
                f"No se encontraron links en la página {page_num}. Guardando para retry."
            )
            append_failed_url(f"PAGE::{page_num}")

    # Save final list
    save_json_file(list(detail_urls), URLS_FILE)
    logging.info(f"Se guardaron {len(detail_urls)} URLs en '{URLS_FILE}'.")


async def retry_failed_pages(page):
    """
    FIXED: Retries pages stored in FAILED_URLS_FILE.
    It now navigates to the base page first, then re-scrapes the failed pages
    and adds the collected URLs to the main urls.json file.
    """
    if not os.path.exists(FAILED_URLS_FILE):
        return

    with open(FAILED_URLS_FILE, "r", encoding="utf-8") as f:
        try:
            failed_items = json.load(f)
        except json.JSONDecodeError:
            failed_items = []

    if not failed_items:
        return

    logging.info(f"Reintentando {len(failed_items)} páginas/ítems fallidos...")

    # --- BUG FIX: Navigate to the base page where pagination scripts exist ---
    try:
        logging.info("Navegando a la página de resultados base para reintentos...")
        await page.goto("https://crautos.com/autosusados/")
        await page.locator(".btn.btn-lg.btn-success").click()
    except Exception as e:
        logging.error(
            f"No se pudo navegar a la página base para reintentos: {e}. Se reintentará en la próxima ejecución."
        )
        return

    # Load existing URLs to append new ones and avoid duplicates
    existing_urls = set()
    if os.path.exists(URLS_FILE):
        with open(URLS_FILE, "r", encoding="utf-8") as f:
            try:
                existing_urls = set(json.load(f))
            except json.JSONDecodeError:
                pass  # File is empty or corrupt

    still_failed = []
    newly_scraped_urls = set()

    for item in failed_items:
        if item.startswith("PAGE::"):
            page_num_str = item.split("::")[1]
            try:
                page_num = int(page_num_str)
                logging.info(f"Reintentando página {page_num}...")

                if page_num > 1:
                    async with page.expect_navigation(wait_until="domcontentloaded"):
                        await page.evaluate(f"p('{page_num_str}')")

                await page.wait_for_selector('a[href^="cardetail.cfm"]', timeout=10000)

                # --- LOGIC ADDED: Actually scrape the URLs from the page ---
                links = await page.locator('a[href^="cardetail.cfm"]').all()
                found_on_page = 0
                for link in links:
                    href = await link.get_attribute("href")
                    if href:
                        absolute_url = urljoin(page.url, href)
                        if (
                            absolute_url not in existing_urls
                            and absolute_url not in newly_scraped_urls
                        ):
                            newly_scraped_urls.add(absolute_url)
                            found_on_page += 1

                logging.info(
                    f"Retry exitoso para página {page_num}. Se encontraron {found_on_page} URLs nuevas."
                )

            except Exception as e:
                logging.error(f"Retry fallido para página {page_num_str}: {e}")
                still_failed.append(item)

    # --- LOGIC ADDED: Save the newly found URLs ---
    if newly_scraped_urls:
        all_urls = list(existing_urls.union(newly_scraped_urls))
        save_json_file(all_urls, URLS_FILE)
        logging.info(
            f"Se agregaron {len(newly_scraped_urls)} URLs de páginas reintentadas a '{URLS_FILE}'."
        )

    # Update the failed URLs file with items that are still failing
    if still_failed:
        save_json_file(still_failed, FAILED_URLS_FILE)
    else:
        os.remove(FAILED_URLS_FILE)
        logging.info("Todas las páginas fallidas fueron procesadas correctamente.")


async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context()
        page = await context.new_page()

        # Retry previously failed pages first
        await retry_failed_pages(page)

        # Then scrape all URLs if the URL file wasn't created by the retry
        await ensure_url_list_exists(page)

        await browser.close()
        logging.info("Proceso finalizado.")


if __name__ == "__main__":
    asyncio.run(main())
