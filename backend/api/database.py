import aiosqlite
import json
from pathlib import Path

import os
# The path to the SQLite database
# Inside Docker, we prioritize the environment variable, else use absolute path.
DB_PATH = os.environ.get("SCRAPER_DB_PATH", "/app/data/crautos.db")

async def get_db_connection():
    """Create and return an async read-only database connection."""
    # Debug: print the path to uvicorn logs
    if not hasattr(get_db_connection, "_logged"):
        print(f"[API] Connecting to database at: {DB_PATH}")
        get_db_connection._logged = True
        
    # Using simple path string instead of URI mode to avoid driver issues.
    conn = await aiosqlite.connect(DB_PATH)
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
