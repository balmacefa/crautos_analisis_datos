# -----------------------------------------------------------------------------------
# SCRAPER AVANZADO PARA VEHÍCULOS (V4 - OPTIMIZACIÓN BASADA EN HISTORIAL)
#
# Descripción:
# Esta versión mejora el sistema de concurrencia adaptativa utilizando un historial
# de los últimos 30 intervalos de rendimiento para tomar decisiones más inteligentes,
# enfocándose en maximizar el throughput (URLs por segundo).
#
# Autor: Gemini
# Fecha: 2024-05-17
# Modificado: 2025-08-16
# -----------------------------------------------------------------------------------

import asyncio
import json
import re
import logging
import os
import argparse
import random
import time
from collections import deque
from datetime import timedelta
from urllib.parse import urlparse, parse_qs
from playwright.async_api import async_playwright

# --- Configuración Global ---
OUTPUT_DIR = "datos_vehiculos"
TRIES = 3
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36 (VehicleDataScraper/1.4; +http://your-contact-info.com)"
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)

# Lista de marcas (sin cambios)
MARCAS = [
    "ACURA",
    "ALFA ROMEO",
    "AMC",
    "ARO",
    "ASIA",
    "ASTON MARTIN",
    "AUDI",
    "AUSTIN",
    "BAW",
    "BENTLEY",
    "BLUEBIRD",
    "BMW",
    "BRILLIANCE",
    "BUICK",
    "BYD",
    "CADILLAC",
    "CHANA",
    "CHANGAN",
    "CHERY",
    "CHEVROLET",
    "CHRYSLER",
    "CITROEN",
    "DACIA",
    "DAEWOO",
    "DAIHATSU",
    "DATSUN",
    "DODGE/RAM",
    "DODGE",
    "RAM",
    "DONFENG(ZNA)",
    "DONFENG",
    "ZNA",
    "EAGLE",
    "FAW",
    "FERRARI",
    "FIAT",
    "FORD",
    "FOTON",
    "FREIGHTLINER",
    "GEELY",
    "GENESIS",
    "GEO",
    "GMC",
    "GONOW",
    "GREAT WALL",
    "HAFEI",
    "HAIMA",
    "HEIBAO",
    "HIGER",
    "HINO",
    "HONDA",
    "HUMMER",
    "HYUNDAI",
    "INFINITI",
    "INTERNATIONAL",
    "ISUZU",
    "IVECO",
    "JAC",
    "JAGUAR",
    "JEEP",
    "JINBEI",
    "JMC",
    "JONWAY",
    "KENWORTH",
    "KIA",
    "LADA",
    "LAMBORGHINI",
    "LANCIA",
    "LAND ROVER",
    "LEXUS",
    "LIFAN",
    "LINCOLN",
    "LOTUS",
    "MACK",
    "MAGIRUZ",
    "MAHINDRA",
    "MASERATI",
    "MAZDA",
    "MERCEDES BENZ",
    "MERCURY",
    "MG",
    "MINI",
    "MITSUBISHI",
    "NISSAN",
    "OLDSMOBILE",
    "OPEL",
    "PETERBILT",
    "PEUGEOT",
    "PLYMOUTH",
    "POLARSUN",
    "PONTIAC",
    "PORSCHE",
    "PROTON",
    "RAMBLER",
    "RENAULT",
    "REVA",
    "ROLLS ROYCE",
    "ROVER",
    "SAAB",
    "SAMSUNG",
    "SATURN",
    "SCANIA",
    "SCION",
    "SEAT",
    "SKODA",
    "SMART",
    "SOUEAST",
    "SSANG YONG",
    "SUBARU",
    "SUZUKI",
    "TIANMA",
    "TIGER TRUCK",
    "TOYOTA",
    "VOLKSWAGEN",
    "VOLVO",
    "WESTERN STAR",
    "YUGO",
    "ZOTYE",
]


# --- MODIFICADO: Gestor de Concurrencia con Historial ---
class ConcurrencyManager:
    """Gestiona la concurrencia basándose en un historial de throughput."""

    def __init__(self, initial: int, min_val: int, max_val: int):
        self.target_concurrency = initial
        self.min = min_val
        self.max = max_val
        self._success_count = 0
        self._error_count = 0
        self._last_check_time = time.monotonic()
        self._lock = asyncio.Lock()
        # NUEVO: Guardar historial de (concurrencia, throughput)
        self.throughput_history = deque(maxlen=30)

    async def record_success(self):
        async with self._lock:
            self._success_count += 1

    async def record_error(self):
        async with self._lock:
            self._error_count += 1

    async def adjust_concurrency(self):
        """Ajusta la concurrencia usando un historial para maximizar el throughput."""
        async with self._lock:
            elapsed = time.monotonic() - self._last_check_time
            if elapsed < 20:  # Intervalo mínimo de ajuste: 20 segundos
                return

            total_requests = self._success_count + self._error_count
            if total_requests == 0:
                self._reset_counters()
                return

            error_rate = self._error_count / total_requests
            current_throughput = self._success_count / elapsed

            logging.info(
                f"[ADJUSTER] Stats (last {elapsed:.1f}s): "
                f"Target: {self.target_concurrency}, "
                f"Throughput: {current_throughput:.2f} url/s, "
                f"Error Rate: {error_rate:.2%}"
            )

            # 1. FRENO DE EMERGENCIA: Si hay muchos errores, bajar siempre.
            if error_rate > 0.1:
                new_target = max(self.min, int(self.target_concurrency * 0.7))
                if new_target != self.target_concurrency:
                    logging.warning(
                        f"🚨 Alta tasa de errores. Bajando concurrencia a {new_target}"
                    )
                    self.target_concurrency = new_target
                self._reset_counters()
                return  # Salir para estabilizar

            # 2. Guardar el rendimiento del intervalo actual en el historial
            self.throughput_history.append(
                (self.target_concurrency, current_throughput)
            )

            # 3. Lógica de optimización basada en el historial (si hay suficientes datos)
            if len(self.throughput_history) < 5:
                # Al principio, subir con cautela mientras se recolectan datos
                self.target_concurrency = min(self.max, self.target_concurrency + 1)
                self._reset_counters()
                return

            # Calcular el rendimiento promedio para cada nivel de concurrencia en el historial
            perf_by_concurrency = {}
            for c, t in self.throughput_history:
                if c not in perf_by_concurrency:
                    perf_by_concurrency[c] = []
                perf_by_concurrency[c].append(t)

            avg_perf = {
                c: sum(t_list) / len(t_list)
                for c, t_list in perf_by_concurrency.items()
            }

            # Encontrar la concurrencia que dio el mejor resultado histórico
            if not avg_perf:
                self._reset_counters()
                return

            best_concurrency = max(avg_perf, key=avg_perf.get)

            # 4. Tomar la decisión
            if self.target_concurrency < best_concurrency:
                # Si estamos por debajo del óptimo histórico, subir
                new_target = min(self.max, self.target_concurrency + 1)
                logging.info(
                    f"📈 Hacia el óptimo ({best_concurrency}). Subiendo concurrencia a {new_target}"
                )
                self.target_concurrency = new_target
            elif self.target_concurrency > best_concurrency:
                # Si nos pasamos del óptimo histórico, bajar
                new_target = max(self.min, self.target_concurrency - 1)
                logging.info(
                    f"📉 Pasamos el óptimo ({best_concurrency}). Bajando concurrencia a {new_target}"
                )
                self.target_concurrency = new_target
            else:  # Estamos en el mejor punto conocido
                # Probar a subir un poco más para encontrar un nuevo pico
                new_target = min(self.max, self.target_concurrency + 1)
                logging.info(
                    f"✅ En el punto óptimo. Probando a subir a {new_target} para buscar mejoras."
                )
                self.target_concurrency = new_target

            self._reset_counters()

    def _reset_counters(self):
        self._success_count = 0
        self._error_count = 0
        self._last_check_time = time.monotonic()


# --- El resto del script (tareas, funciones auxiliares, main) permanece sin cambios ---


async def adjuster_task(manager: ConcurrencyManager):
    """Tarea que se ejecuta en segundo plano para llamar al ajustador."""
    while True:
        await asyncio.sleep(5)
        await manager.adjust_concurrency()


def load_urls_from_file(filename: str) -> list:
    if not os.path.exists(filename):
        logging.error(f"El archivo de entrada '{filename}' no fue encontrado.")
        return []
    try:
        with open(filename, "r", encoding="utf-8") as f:
            return json.load(f)
    except json.JSONDecodeError:
        logging.error(f"No se pudo decodificar el JSON de '{filename}'.")
        return []


def save_data_to_json(data: dict, filename: str):
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)


def get_car_id_from_url(url: str) -> str | None:
    try:
        return parse_qs(urlparse(url).query).get("c", [None])[0]
    except Exception:
        return None


async def block_unnecessary_resources(page):
    await page.route(
        "**/*",
        lambda route: (
            route.abort()
            if route.request.resource_type in ["image", "stylesheet", "font", "media"]
            else route.continue_()
        ),
    )


def _log_progress_and_estimate_time(completed: int, total: int, start_time: float):
    elapsed_time = time.monotonic() - start_time
    if completed == 0:
        return
    avg_time_per_url = elapsed_time / completed
    remaining_urls = total - completed
    eta = str(timedelta(seconds=int(avg_time_per_url * remaining_urls)))
    logging.info(f"Progreso: [{completed}/{total}] - Tiempo restante estimado: {eta}")


async def scrape_detail_page(page) -> dict:
    # Esta función no cambia en su lógica de extracción.
    data = {"url": page.url}
    try:
        title_element = page.locator("div.header-text h1").first
        full_title_text = (await title_element.inner_text()).strip()
        title_parts = full_title_text.split()
        if title_parts and title_parts[-1].isdigit() and len(title_parts[-1]) == 4:
            data["año"] = int(title_parts.pop())
        remaining_title = " ".join(title_parts)
        for marca in MARCAS:
            if remaining_title.upper().startswith(marca):
                data["marca"] = marca
                data["modelo"] = remaining_title[len(marca) :].strip()
                break
        if "modelo" not in data:
            data["modelo"] = remaining_title
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
        data["imagen_principal"] = await page.locator("div.bannerimg").get_attribute(
            "data-image-src"
        )
        data["galeria_imagenes"] = [
            await img.get_attribute("src")
            for img in await page.locator("div.ws_images ul li img").all()
        ]
    except Exception:
        pass
    try:
        seller_info = {}
        seller_table = page.locator('//table[.//td[contains(., "Vendedor")]]')
        for row in await seller_table.locator("tr").all():
            cells = await row.locator("td").all()
            if len(cells) == 2:
                key = (await cells[0].inner_text()).strip().lower().replace(":", "")
                value = (await cells[1].inner_text()).strip()
                if key and value:
                    seller_info[key] = re.sub(r"\s+", " ", value)
        data["vendedor"] = seller_info
    except Exception:
        pass
    try:
        general_info = {}
        for row in await page.locator("table.mytext2 tbody tr").all():
            cells = await row.locator("td").all()
            if len(cells) == 2:
                key = (await cells[0].inner_text()).strip().lower().replace(" ", "_")
                value = (await cells[1].inner_text()).strip()
                general_info[key] = re.sub(r"\s+", " ", value)
            elif await cells[0].get_attribute("bgcolor") == "#FAF7B4":
                general_info["comentario_vendedor"] = (
                    await cells[0].inner_text()
                ).strip()
        data["informacion_general"] = general_info
    except Exception:
        pass
    if "kilometraje" in data.get("informacion_general", {}):
        try:
            km_text = data["informacion_general"]["kilometraje"]
            km_value = re.sub(r"[^\d]", "", km_text)
            data["informacion_general"]["kilometraje_number"] = (
                int(km_value) if km_value else None
            )
        except ValueError:
            pass
    if "cilindrada" in data.get("informacion_general", {}):
        try:
            cc_text = data["informacion_general"]["cilindrada"]
            cc_value = re.sub(r"[^\d]", "", cc_text)
            data["informacion_general"]["cilindrada_number"] = (
                int(cc_value) if cc_value else None
            )
        except ValueError:
            pass
    try:
        equipment_list = []
        equipment_tables = page.locator(
            '//table[@class="table table-bordered border-top table-striped"]'
        )
        for row in await equipment_tables.locator("tbody tr").all():
            cells = await row.locator("td").all()
            if len(cells) == 2 and await cells[1].locator("i.icon-check").count() > 0:
                equipment_list.append((await cells[0].inner_text()).strip())
        data["equipamiento"] = sorted(equipment_list)
    except Exception:
        pass
    return data


async def scrape_single_url(
    url: str, context, semaphore: asyncio.Semaphore, manager: ConcurrencyManager
):
    """Gestiona el proceso para una única URL y reporta el resultado."""
    async with semaphore:
        car_id = get_car_id_from_url(url)
        if not car_id:
            logging.error(f"ID inválido para la URL {url}. Omitiendo.")
            await manager.record_error()
            return

        page = None
        for attempt in range(TRIES):
            try:
                page = await context.new_page()
                await block_unnecessary_resources(page)
                logging.info(f"Procesando ID {car_id} (Intento {attempt + 1}/{TRIES})")
                await page.goto(url, wait_until="domcontentloaded", timeout=45000)
                car_data = await scrape_detail_page(page)
                output_filename = os.path.join(OUTPUT_DIR, f"{car_id}.json")
                save_data_to_json(car_data, output_filename)
                logging.info(f"✅ Datos de ID {car_id} guardados.")
                await manager.record_success()
                await asyncio.sleep(random.uniform(1, 4))
                return
            except Exception as e:
                logging.warning(
                    f"⚠️ Fallo en intento {attempt + 1} para ID {car_id}. Error: {type(e).__name__}"
                )
                if attempt == TRIES - 1:
                    logging.error(
                        f"❌ No se pudo procesar ID {car_id} después de {TRIES} intentos."
                    )
                    await manager.record_error()
                else:
                    await asyncio.sleep(3 + attempt * 2)
            finally:
                if page:
                    await page.close()


async def main(
    urls_file: str, initial_concurrency: int, min_concurrency: int, max_concurrency: int
):
    """Función principal que orquesta el scraping con concurrencia adaptativa."""
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    all_urls = load_urls_from_file(urls_file)
    if not all_urls:
        return

    urls_to_process = [
        url
        for url in all_urls
        if not os.path.exists(
            os.path.join(OUTPUT_DIR, f"{get_car_id_from_url(url)}.json")
        )
    ]
    total_urls, remaining_to_scrape = len(all_urls), len(urls_to_process)
    logging.info(
        f"Se encontraron {total_urls} URLs. Ya descargados: {total_urls - remaining_to_scrape}. Restantes: {remaining_to_scrape}."
    )
    if not urls_to_process:
        logging.info("🎉 No hay vehículos nuevos que descargar.")
        return

    manager = ConcurrencyManager(
        initial=initial_concurrency, min_val=min_concurrency, max_val=max_concurrency
    )
    logging.info(
        f"Iniciando scraping adaptativo. Rango: [{min_concurrency}-{max_concurrency}], Inicial: {initial_concurrency}"
    )

    start_time = time.monotonic()

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(user_agent=USER_AGENT)
        adjuster = asyncio.create_task(adjuster_task(manager))
        semaphore = asyncio.Semaphore(max_concurrency)
        tasks = [
            scrape_single_url(url, context, semaphore, manager)
            for url in urls_to_process
        ]
        completed_count = 0
        for future in asyncio.as_completed(tasks):
            await future
            completed_count += 1
            if completed_count % 10 == 0 or completed_count == remaining_to_scrape:
                _log_progress_and_estimate_time(
                    completed_count, remaining_to_scrape, start_time
                )

        adjuster.cancel()
        try:
            await adjuster
        except asyncio.CancelledError:
            logging.info("Tarea de ajuste de concurrencia detenida.")
        await browser.close()

    logging.info("🎉 Proceso de scraping completado.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Scraper avanzado de vehículos con optimización de concurrencia basada en historial."
    )
    parser.add_argument(
        "-f",
        "--file",
        default="urls.json",
        help="Archivo JSON con la lista de URLs. (default: urls.json)",
    )
    parser.add_argument(
        "--initial",
        type=int,
        default=8,
        help="Número inicial de trabajos concurrentes. (default: 8)",
    )
    parser.add_argument(
        "--min",
        type=int,
        default=3,
        help="Número mínimo de trabajos concurrentes. (default: 3)",
    )
    parser.add_argument(
        "--max",
        type=int,
        default=30,
        help="Número máximo de trabajos concurrentes. (default: 30)",
    )
    args = parser.parse_args()
    asyncio.run(
        main(
            urls_file=args.file,
            initial_concurrency=args.initial,
            min_concurrency=args.min,
            max_concurrency=args.max,
        )
    )
