import sqlite3
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent.parent
DB_PATH = BASE_DIR / "data" / "crautos.db"

def main():
    conn = sqlite3.connect(DB_PATH)
    
    print("Creating FTS5 table...")
    conn.execute('''
        CREATE VIRTUAL TABLE IF NOT EXISTS car_details_fts USING fts5(
            car_id UNINDEXED, marca, modelo, ano, provincia, equipamiento, raw_json UNINDEXED
        )
    ''')
    
    print("Clearing old index...")
    conn.execute('DELETE FROM car_details_fts')
    
    print("Populating FTS5 index. This may take a moment...")
    conn.execute('''
        INSERT INTO car_details_fts(car_id, marca, modelo, ano, provincia, equipamiento, raw_json)
        SELECT 
            car_id, 
            json_extract(raw_json, '$.marca'), 
            json_extract(raw_json, '$.modelo'), 
            json_extract(raw_json, '$.año'), 
            json_extract(raw_json, '$.informacion_general.provincia'),
            json_extract(raw_json, '$.equipamiento'),
            raw_json
        FROM car_details
    ''')
    
    conn.commit()
    conn.close()
    print("FTS5 indexing complete!")

if __name__ == "__main__":
    main()
