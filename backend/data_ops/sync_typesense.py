import os
import json
import sqlite3
import typesense
import time
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configuration
DB_PATH = os.getenv("SCRAPER_DB_PATH", "/app/data/crautos.db")
TYPESENSE_HOST = os.getenv("TYPESENSE_HOST", "localhost")
TYPESENSE_PORT = os.getenv("TYPESENSE_PORT", "8108")
TYPESENSE_PROTOCOL = os.getenv("TYPESENSE_PROTOCOL", "http")
TYPESENSE_API_KEY = os.getenv("TYPESENSE_API_KEY", "xyz123abc456")
SYNC_VERSION = os.getenv("SYNC_VERSION", "1.1.0")

client = typesense.Client({
    'nodes': [{
        'host': TYPESENSE_HOST,
        'port': TYPESENSE_PORT,
        'protocol': TYPESENSE_PROTOCOL
    }],
    'api_key': TYPESENSE_API_KEY,
    'connection_timeout_seconds': 60
})

COLLECTION_NAME = 'cars'

def create_collection_with_retry(max_retries=5, initial_delay=2):
    schema = {
        'name': COLLECTION_NAME,
        'fields': [
            {'name': 'car_id', 'type': 'string' },
            {'name': 'marca', 'type': 'string', 'facet': True },
            {'name': 'modelo', 'type': 'string', 'facet': True },
            {'name': 'año', 'type': 'int32', 'facet': True },
            {'name': 'precio_usd', 'type': 'float', 'facet': True },
            {'name': 'precio_crc', 'type': 'float', 'facet': True },
            {'name': 'kilometraje_number', 'type': 'int32', 'facet': True },
            {'name': 'provincia', 'type': 'string', 'facet': True },
            {'name': 'combustible', 'type': 'string', 'facet': True },
            {'name': 'transmisión', 'type': 'string', 'facet': True },
            {'name': 'url', 'type': 'string' },
            {'name': 'imagen_principal', 'type': 'string', 'optional': True },
            {'name': 'scraped_at', 'type': 'string' },
            {'name': 'sync_version', 'type': 'string', 'facet': True },
            {'name': 'fuente', 'type': 'string', 'facet': True },
        ],
        'default_sorting_field': 'año'
    }

    print(f"Ensuring collection '{COLLECTION_NAME}' is ready...")

    retries = 0
    delay = initial_delay

    while retries < max_retries:
        try:
            # We try to delete the collection first to ensure we have the latest schema.
            # This might fail if the collection doesn't exist, which is fine.
            try:
                client.collections[COLLECTION_NAME].delete()
                print(f"Deleted existing collection '{COLLECTION_NAME}'")
            except Exception as e:
                if "not found" not in str(e).lower():
                    print(f"Notice: Deletion of collection failed (might not exist): {e}")

            try:
                client.collections.create(schema)
                print(f"Created collection '{COLLECTION_NAME}' with version {SYNC_VERSION}")
            except Exception as e:
                if "already exists" in str(e).lower():
                    print(f"Warning: Collection '{COLLECTION_NAME}' already exists. Skipping creation.")
                else:
                    raise e
            return # Success, exit retry loop
        except Exception as e:
            retries += 1
            print(f"Attempt {retries}/{max_retries} failed to setup Typesense collection: {e}")
            if retries < max_retries:
                print(f"Waiting {delay} seconds before retrying...")
                time.sleep(delay)
                delay *= 2 # Exponential backoff
            else:
                print("Max retries reached. Typesense setup failed.")
                raise e

def sync_data_with_retry(max_retries=5, initial_delay=2):
    if not Path(DB_PATH).exists():
        print(f"Error: Database not found at {DB_PATH}")
        return

    print(f"Connecting to database: {DB_PATH}")
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute("SELECT car_id, url, raw_json, scraped_at FROM car_details")
    rows = cursor.fetchall()

    documents = []
    for row in rows:
        try:
            raw_data = json.loads(row['raw_json'])
            gen_info = raw_data.get('informacion_general', {})
            
            doc = {
                'id': row['car_id'],
                'car_id': row['car_id'],
                'marca': raw_data.get('marca', 'Desconocida'),
                'modelo': raw_data.get('modelo', 'Desconocido'),
                'año': int(raw_data.get('año', 0)),
                'precio_usd': float(raw_data.get('precio_usd', 0) or 0),
                'precio_crc': float(raw_data.get('precio_crc', 0) or 0),
                'kilometraje_number': int(gen_info.get('kilometraje_number', 0) or 0),
                'provincia': gen_info.get('provincia', 'Desconocida'),
                'combustible': gen_info.get('combustible', 'Desconocido'),
                'transmisión': gen_info.get('transmisión', 'Desconocida'),
                'url': row['url'],
                'imagen_principal': raw_data.get('imagen_principal', ''),
                'scraped_at': row['scraped_at'],
                'sync_version': SYNC_VERSION,
                'fuente': 'CRAutos' if 'crautos.com' in row['url'] else ('CoriMotors' if 'corimotors' in row['url'] else ('EVMarket' if 'evmarket' in row['url'] else ('PurdyUsados' if 'purdyusados' in row['url'] else ('VeinsaUsados' if 'veinsausados' in row['url'] else 'Otro'))))
            }
            documents.append(doc)
        except Exception as e:
            print(f"Error parsing row {row['car_id']}: {e}")

    if documents:
        retries = 0
        delay = initial_delay

        while retries < max_retries:
            try:
                print(f"Importing {len(documents)} documents to Typesense...")
                result = client.collections[COLLECTION_NAME].documents.import_(documents, {'action': 'upsert'})
                print(f"Successfully synced {len(documents)} documents (Version: {SYNC_VERSION})")
                break # Success, exit retry loop
            except Exception as e:
                retries += 1
                print(f"Attempt {retries}/{max_retries} failed to import to Typesense: {e}")
                if retries < max_retries:
                    print(f"Waiting {delay} seconds before retrying...")
                    time.sleep(delay)
                    delay *= 2 # Exponential backoff
                else:
                    print("Max retries reached. Typesense import failed.")
                    raise e
    else:
        print("No documents found to sync")

    conn.close()

if __name__ == "__main__":
    create_collection_with_retry()
    sync_data_with_retry()
