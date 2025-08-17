# -----------------------------------------------------------------------------
# SCRAPER AVANZADO PARA VEHÍCULOS
#
# Descripción:
# Este script extrae información detallada de publicaciones de vehículos a 
# partir de una lista de URLs, aplicando mejoras de rendimiento y robustez.
#
# Características:
# - Procesamiento concurrente para mayor velocidad.
# - Bloqueo de recursos (CSS, imágenes) para acelerar la carga de páginas.
# - Reintentos automáticos en caso de fallos de red.
# - Pausas aleatorias para un scraping más ético.
# - Reanudación automática del proceso (omite URLs ya procesadas).
# - Uso de argumentos de línea de comandos para mayor flexibilidad.
#
# Autor: Gemini
# Fecha: 2024-05-17
# -----------------------------------------------------------------------------

import asyncio
import json
import re
import logging
import os
import argparse
import random
from urllib.parse import urlparse, parse_qs
from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeoutError

# --- Configuración Global ---
# Carpeta donde se guardarán los archivos JSON resultantes.
OUTPUT_DIR = 'datos_vehiculos'
# Número de reintentos para una URL que falle.
TRIES = 3
# User-Agent para identificar a nuestro bot de forma educada.
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36 (VehicleDataScraper/1.1)"
# Configuración del logging para mostrar el progreso en la terminal.
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Lista de marcas para ayudar en la extracción del título.
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

# --- Funciones Auxiliares ---

def load_urls_from_file(filename: str) -> list:
    """Carga una lista de URLs desde un archivo JSON."""
    if not os.path.exists(filename):
        logging.error(f"El archivo de entrada '{filename}' no fue encontrado.")
        return []
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            return json.load(f)
    except json.JSONDecodeError:
        logging.error(f"No se pudo decodificar el JSON de '{filename}'. Revisa el formato.")
        return []

def save_data_to_json(data: dict, filename: str):
    """Guarda un diccionario de datos en un archivo JSON con formato legible."""
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

def get_car_id_from_url(url: str) -> str | None:
    """Extrae el ID único del vehículo desde la URL (parámetro 'c')."""
    try:
        query_params = parse_qs(urlparse(url).query)
        return query_params.get('c', [None])[0]
    except Exception:
        return None

async def block_unnecessary_resources(page):
    """Configura el bloqueo de recursos no esenciales para acelerar la carga."""
    await page.route(
        "**/*", 
        lambda route: route.abort() 
        if route.request.resource_type in ["image", "stylesheet", "font", "media"] 
        else route.continue_()
    )

# --- Lógica Principal de Extracción ---

async def scrape_detail_page(page) -> dict:
    """Extrae todos los datos de la página de detalles de un vehículo."""
    data = {'url': page.url}

    # 1. Extraer Título, Marca, Modelo y Año
    try:
        title_element = page.locator('div.header-text h1').first
        full_title_text = (await title_element.inner_text()).strip()
        title_parts = full_title_text.split()
        if title_parts and title_parts[-1].isdigit() and len(title_parts[-1]) == 4:
            data['año'] = int(title_parts.pop())
        
        remaining_title = " ".join(title_parts)
        for marca in MARCAS:
            if remaining_title.upper().startswith(marca):
                data['marca'] = marca
                data['modelo'] = remaining_title[len(marca):].strip()
                break
        if 'modelo' not in data:
             data['modelo'] = remaining_title
    except Exception as e:
        logging.warning(f"No se pudo extraer el título/año para {page.url}: {e}")

    # 2. Extraer Precios
    try:
        price_usd_text = await page.locator('div.header-text h1').nth(1).inner_text()
        data['precio_crc'] = float(re.sub(r'[^\d.]', '', price_usd_text))
    except Exception:
        pass # Ignora si el precio no está presente
    try:
        price_crc_text = await page.locator('div.header-text h3').first.inner_text()
        data['precio_usd'] = int(re.sub(r'[^\d]', '', price_crc_text))
    except Exception:
        pass

    # 3. Extraer Imágenes
    try:
        data['imagen_principal'] = await page.locator('div.bannerimg').get_attribute('data-image-src')
        data['galeria_imagenes'] = [
            await img.get_attribute('src') 
            for img in await page.locator('div.ws_images ul li img').all()
        ]
    except Exception as e:
        logging.warning(f"No se pudieron extraer las imágenes para {page.url}: {e}")
        
    # 4. Extraer Información del Vendedor
    try:
        seller_info = {}
        seller_table = page.locator('//table[.//td[contains(., "Vendedor")]]')
        for row in await seller_table.locator('tr').all():
            cells = await row.locator('td').all()
            if len(cells) == 2:
                key = (await cells[0].inner_text()).strip().lower().replace(':', '')
                value = (await cells[1].inner_text()).strip()
                if key and value:
                    seller_info[key] = re.sub(r'\s+', ' ', value)
        data['vendedor'] = seller_info
    except Exception as e:
        logging.warning(f"No se pudo extraer la info del vendedor para {page.url}: {e}")

    # 5. Extraer Información General
    try:
        general_info = {}
        for row in await page.locator('table.mytext2 tbody tr').all():
            cells = await row.locator('td').all()
            if len(cells) == 2:
                key = (await cells[0].inner_text()).strip().lower().replace(' ', '_')
                value = (await cells[1].inner_text()).strip()
                general_info[key] = re.sub(r'\s+', ' ', value)
            elif await cells[0].get_attribute('bgcolor') == '#FAF7B4':
                 general_info['comentario_vendedor'] = (await cells[0].inner_text()).strip()
        data['informacion_general'] = general_info
    except Exception as e:
        logging.warning(f"No se pudo extraer la info general para {page.url}: {e}")
    
    # Convertir data['informacion_general']['kilometraje'] a entero si es posible
    if 'kilometraje' in data.get('informacion_general', {}):
        try:
            km_text = data['informacion_general']['kilometraje']
            km_value = re.sub(r'[^\d]', '', km_text)
            data['informacion_general']['kilometraje_number'] = int(km_value) if km_value else None
        except ValueError:
            logging.warning(f"Kilometraje no es un número válido: {data['informacion_general']['kilometraje']}")
    
    # convertir cilindrada
    if 'cilindrada' in data.get('informacion_general', {}):
        try:
            cc_text = data['informacion_general']['cilindrada']
            cc_value = re.sub(r'[^\d]', '', cc_text)
            data['informacion_general']['cilindrada_number'] = int(cc_value) if cc_value else None
        except ValueError:
            logging.warning(f"Cilindrada no es un número válido: {data['informacion_general']['cilindrada']}")
            
    # 6. Extraer Equipamiento
    try:
        equipment_list = []
        equipment_tables = page.locator('//table[@class="table table-bordered border-top table-striped"]')
        for row in await equipment_tables.locator('tbody tr').all():
            cells = await row.locator('td').all()
            if len(cells) == 2 and await cells[1].locator('i.icon-check').count() > 0:
                equipment_list.append((await cells[0].inner_text()).strip())
        data['equipamiento'] = sorted(equipment_list)
    except Exception as e:
        logging.warning(f"No se pudo extraer el equipamiento para {page.url}: {e}")

    return data


# --- Orquestador Concurrente ---

async def scrape_single_url(url: str, context, semaphore: asyncio.Semaphore):
    """
    Gestiona el proceso completo para una única URL: adquisición de semáforo,
    reintentos, scraping, guardado y liberación de recursos.
    """
    async with semaphore:
        car_id = get_car_id_from_url(url)
        if not car_id:
            logging.error(f"ID inválido para la URL {url}. Omitiendo.")
            return

        output_filename = os.path.join(OUTPUT_DIR, f"{car_id}.json")
        if os.path.exists(output_filename):
            logging.info(f"El archivo para ID {car_id} ({url}) ya existe. Omitiendo.")
            return

        page = None
        for attempt in range(TRIES):
            try:
                page = await context.new_page()
                await block_unnecessary_resources(page)
                
                logging.info(f"Procesando ID {car_id} (Intento {attempt + 1}/{TRIES})")
                await page.goto(url, wait_until='domcontentloaded', timeout=45000)
                
                car_data = await scrape_detail_page(page)
                
                save_data_to_json(car_data, output_filename)
                logging.info(f"✅ Datos de ID {car_id} guardados exitosamente.")
                
                # Pausa aleatoria para ser respetuoso con el servidor
                await asyncio.sleep(random.uniform(1, 4))
                return # Salir de la función si tuvo éxito

            except Exception as e:
                logging.warning(f"⚠️ Fallo en intento {attempt + 1} para ID {car_id}. Error: {type(e).__name__}")
                if attempt == TRIES - 1:
                    logging.error(f"❌ No se pudo procesar ID {car_id} después de {TRIES} intentos.")
                else:
                    await asyncio.sleep(3 + attempt * 2) # Espera un poco más en cada reintento
            finally:
                if page:
                    await page.close()


async def main(urls_file: str, concurrency_level: int):
    """Función principal que orquesta todo el proceso de scraping."""
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    logging.info(f"Los archivos se guardarán en la carpeta: '{OUTPUT_DIR}'")
    
    urls_to_process = load_urls_from_file(urls_file)
    if not urls_to_process:
        logging.warning("No hay URLs para procesar. Finalizando.")
        return
        
    logging.info(f"Se encontraron {len(urls_to_process)} URLs. Iniciando scraping con {concurrency_level} procesos concurrentes.")

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(user_agent=USER_AGENT)
        
        semaphore = asyncio.Semaphore(concurrency_level)
        tasks = [scrape_single_url(url, context, semaphore) for url in urls_to_process]
        
        await asyncio.gather(*tasks)

        await browser.close()
    
    logging.info("🎉 Proceso de scraping completado.")


# --- Punto de Entrada del Script ---

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Scraper avanzado de vehículos de crautos.com")
    parser.add_argument(
        "-f", "--file", 
        default="urls.json", 
        help="Archivo JSON de entrada con la lista de URLs. (default: urls.json)"
    )
    parser.add_argument(
        "-c", "--concurrency", 
        type=int, 
        default=1, 
        help="Número de páginas a procesar en paralelo. (default: 5)"
    )
    args = parser.parse_args()

    # Inicia el bucle de eventos de asyncio para ejecutar la función main.
    asyncio.run(main(urls_file=args.file, concurrency_level=args.concurrency))