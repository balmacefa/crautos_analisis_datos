import asyncio
import json
import re
import logging
from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeoutError
from urllib.parse import urljoin
import os

# --- Configuration ---
# Configure logging to show progress
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Constants for file paths
URLS_FILE = 'urls.json'
OUTPUT_FILE = 'output.json'

# List of car brands
MARCAS = [
    "ACURA", "ALFA ROMEO", "AMC", "ARO", "ASIA", "ASTON MARTIN", "AUDI", "AUSTIN",
    "BAW", "BENTLEY", "BLUEBIRD", "BMW", "BRILLIANCE", "BUICK", "BYD", "CADILLAC",
    "CHANA", "CHANGAN", "CHERY", "CHEVROLET", "CHRYSLER", "CITROEN", "DACIA",
    "DAEWOO", "DAIHATSU", "DATSUN", "DODGE/RAM", "DODGE", "RAM", "DONFENG(ZNA)",
    "DONFENG", "ZNA", "EAGLE", "FAW", "FERRARI", "FIAT", "FORD", "FOTON",
    "FREIGHTLINER", "GEELY", "GENESIS", "GEO", "GMC", "GONOW", "GREAT WALL",
    "HAFEI", "HAIMA", "HEIBAO", "HIGER", "HINO", "HONDA", "HUMMER", "HYUNDAI",
    "INFINITI", "INTERNATIONAL", "ISUZU", "IVECO", "JAC", "JAGUAR", "JEEP",
    "JINBEI", "JMC", "JONWAY", "KENWORTH", "KIA", "LADA", "LAMBORGHINI", "LANCIA",
    "LAND ROVER", "LEXUS", "LIFAN", "LINCOLN", "LOTUS", "MACK", "MAGIRUZ",
    "MAHINDRA", "MASERATI", "MAZDA", "MERCEDES BENZ", "MERCURY", "MG", "MINI",
    "MITSUBISHI", "NISSAN", "OLDSMOBILE", "OPEL", "PETERBILT", "PEUGEOT",
    "PLYMOUTH", "POLARSUN", "PONTIAC", "PORSCHE", "PROTON", "RAMBLER", "RENAULT",
    "REVA", "ROLLS ROYCE", "ROVER", "SAAB", "SAMSUNG", "SATURN", "SCANIA", "SCION",
    "SEAT", "SKODA", "SMART", "SOUEAST", "SSANG YONG", "SUBARU", "SUZUKI",
    "TIANMA", "TIGER TRUCK", "TOYOTA", "VOLKSWAGEN", "VOLVO", "WESTERN STAR",
    "YUGO", "ZOTYE",
]

# --- Helper Functions for Progress Management ---

def load_json_file(filename):
    """Loads a JSON file if it exists, otherwise returns an empty list."""
    if os.path.exists(filename):
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                logging.info(f"Loading existing data from {filename}.")
                return json.load(f)
        except json.JSONDecodeError:
            logging.warning(f"Could not decode JSON from {filename}. Starting with an empty list.")
            return []
    return []

def save_json_file(data, filename):
    """Saves data to a JSON file."""
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)
    # Reducing log noise by not logging every single save
    # logging.info(f"Data saved to {filename}.")

def get_already_scraped_urls(data_list):
    """Extracts a set of URLs from a list of scraped data dictionaries."""
    return {item.get('url') for item in data_list if 'url' in item}

# --- Core Scraping Functions ---

async def ensure_url_list_exists(page):
    """
    Verifica si el archivo de URLs existe. Si no, lo crea raspando el sitio.
    No retorna ningún valor.
    """
    # if os.path.exists(URLS_FILE):
    #     logging.info(f"El archivo '{URLS_FILE}' ya existe. Se omite la recolección de URLs.")
    #     return

    logging.info(f"'{URLS_FILE}' no encontrado. Iniciando recolección de URLs...")
    detail_urls = set()
    
    await page.goto("https://crautos.com/autosusados/")
    await page.locator('.btn.btn-lg.btn-success').click()
    
    while True:
        await page.wait_for_selector('a[href^="cardetail.cfm"]')
        links = await page.locator('a[href^="cardetail.cfm"]').all()
        for link in links:
            href = await link.get_attribute('href')
            if href:
                absolute_url = urljoin(page.url, href)
                detail_urls.add(absolute_url)

        # TODO: Here there is a bug, the next button needs to be awaited and checked for visibility, or timeout and break 
        next_button = page.locator('.page-next > a')
        
        if await next_button.is_visible():
            logging.info(f"Navegando a la siguiente página... (URLs colectadas: {len(detail_urls)})")
            await next_button.click()
            await page.wait_for_load_state('domcontentloaded')
        else:
            logging.info("Última página alcanzada. Finalizó la recolección de URLs.")
            break
            
    save_json_file(list(detail_urls), URLS_FILE)
    logging.info(f"Se guardaron {len(detail_urls)} URLs en '{URLS_FILE}'.")


async def scrape_detail_page(page):
    """
    Scrapes the data from a single car detail page with improved resilience.
    Uses try-except blocks to prevent failure if an element is missing.
    """
    data = {'url': page.url}

    try:
        headers = await page.locator('h2').all()
        if len(headers) >= 2:
            detalle_auto_text = (await headers[0].inner_text()).upper()
            detalle_auto_parts = detalle_auto_text.split('\n')
            
            if len(detalle_auto_parts) == 2:
                full_title, year = detalle_auto_parts[0].strip(), detalle_auto_parts[1].strip()
                data['año'] = year
                for marca in MARCAS:
                    if full_title.startswith(marca):
                        data['marca'] = marca
                        data['modelo'] = full_title.replace(marca, '', 1).strip()
                        break

            precio_text = await headers[1].inner_text()
            data['precio_crc'] = re.sub(r'\D', '', precio_text)
    except Exception as e:
        logging.warning(f"Could not extract header/price info from {page.url}: {e}")

    try:
        data['img'] = await page.locator('#largepic').get_attribute('src')
    except Exception as e:
        logging.warning(f"Could not find main image for {page.url}: {e}")
        data['img'] = None

    try:
        for row in await page.locator('#geninfo table tr').all():
            cells = await row.locator('td').all()
            if len(cells) == 2:
                key = (await cells[0].inner_text()).strip().lower().replace(':', '')
                value = (await cells[1].inner_text()).strip()
                if key and value:
                    if key == 'kilometraje' and value != 'ND':
                        data[key] = re.sub(r'\D', '', value)
                    elif key == 'cilindrada' and value != 'ND':
                        data[key] = re.sub(r'\D', '', value)
                    else:
                        data[key] = value
    except Exception as e:
        logging.warning(f"Could not scrape general info table for {page.url}: {e}")

    return data


async def scrape_urls(page):
    """
    Carga las URLs desde el archivo 'urls.json', visita cada una,
    raspa los datos y guarda el progreso.
    """
    logging.info(f"Cargando URLs desde '{URLS_FILE}' para iniciar el raspado.")
    urls_to_process = load_json_file(URLS_FILE)
    
    if not urls_to_process:
        logging.warning(f"No se encontraron URLs en '{URLS_FILE}'. No hay nada que raspar.")
        return

    scraped_data = load_json_file(OUTPUT_FILE)
    already_scraped_urls = get_already_scraped_urls(scraped_data)
    
    urls_to_scrape = [url for url in urls_to_process if url not in already_scraped_urls]
    total_urls_to_scrape = len(urls_to_scrape)
    
    if not urls_to_scrape:
        logging.info("Todas las URLs ya han sido raspadas. El trabajo está completo.")
        return

    logging.info(f"Resumiendo raspado. {len(scraped_data)} registros existentes. {total_urls_to_scrape} URLs pendientes.")

    for i, url in enumerate(urls_to_scrape):
        try:
            await page.goto(url, wait_until='domcontentloaded', timeout=60000)
            car_data = await scrape_detail_page(page)
            scraped_data.append(car_data)
            
            save_json_file(scraped_data, OUTPUT_FILE)
            logging.info(f"Progreso: {i + 1}/{total_urls_to_scrape} - Raspado: {url}")

        except PlaywrightTimeoutError:
            logging.error(f"Timeout en URL {i + 1}/{total_urls_to_scrape}: {url}. Omitiendo.")
        except Exception as e:
            logging.error(f"Fallo al raspar URL {i + 1}/{total_urls_to_scrape}: {url}. Error: {e}")
            
    logging.info(f"Proceso de raspado completado. Total de items en '{OUTPUT_FILE}': {len(scraped_data)}.")


async def main():
    """Función principal para orquestar el proceso de raspado."""
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context()
        page = await context.new_page()

        # Step 1: Ensure the list of URLs exists.
        # This function will create 'urls.json' only if it doesn't exist.
        await ensure_url_list_exists(page)
        
        # Step 2: Start scraping the data.
        # This function will load 'urls.json' internally and resume progress.
        # await scrape_urls(page)
        
        await browser.close()
        logging.info("Proceso finalizado.")

if __name__ == "__main__":
    asyncio.run(main())