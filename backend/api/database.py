import aiosqlite
import json
from pathlib import Path

# The path to the SQLite database
# Since the api will be run inside `backend/` or `backend/api/`, 
# we need to make sure the path to `data/crautos.db` resolves correctly.
BASE_DIR = Path(__file__).resolve().parent.parent.parent
DB_PATH = BASE_DIR / "data" / "crautos.db"

async def get_db_connection():
    """Create and return an async read-only database connection."""
    conn = await aiosqlite.connect(
        f"file:{DB_PATH}?mode=ro", 
        uri=True
    )
    conn.row_factory = aiosqlite.Row
    return conn

async def execute_query(query: str, parameters: tuple = ()):
    """Helper to execute an async query and return rows as dictionaries."""
    conn = await get_db_connection()
    try:
        async with conn.execute(query, parameters) as cursor:
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]
    finally:
        await conn.close()
