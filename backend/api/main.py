from fastapi import FastAPI, Query, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from typing import Optional, List
import json
from cachetools import TTLCache
from asyncache import cached
from .database import execute_query
from .models import CarsResponse, CarDetail, SummaryStats, BrandStat, YearStat, ProvinceStat, ModelStat

app = FastAPI(title="Crautos Async Data API")

# Setup CORS so frontends can consume this API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def _parse_car_row(row: dict) -> dict:
    raw_json = json.loads(row["raw_json"])
    # Convert 'pasajeros' key or handle other renames if necessary
    if "informacion_general" in raw_json:
        gen_info = raw_json["informacion_general"]
        if "#_de_pasajeros" in gen_info:
            gen_info["pasajeros"] = gen_info.pop("#_de_pasajeros")
        if "#_de_puertas" in gen_info:
            gen_info["puertas"] = gen_info.pop("#_de_puertas")
            
    car_dict = {
        "car_id": row["car_id"],
        "scraped_at": row["scraped_at"]
    }
    car_dict.update(raw_json)
    return car_dict

@app.get("/api/cars", response_model=CarsResponse)
async def get_cars(
    page: int = Query(1, ge=1),
    limit: int = Query(50, ge=1, le=100),
    marca: Optional[str] = None,
    modelo: Optional[str] = None,
    year_min: Optional[int] = None,
    year_max: Optional[int] = None
):
    offset = (page - 1) * limit
    
    # We build the query and use SQLite's json_extract() to filter without loading all rows into Python
    query = "SELECT car_id, raw_json, scraped_at FROM car_details WHERE 1=1"
    params = []

    if marca:
        query += " AND json_extract(raw_json, '$.marca') COLLATE NOCASE = ?"
        params.append(marca)
    if modelo:
        query += " AND json_extract(raw_json, '$.modelo') COLLATE NOCASE = ?"
        params.append(modelo)
    if year_min:
        query += " AND json_extract(raw_json, '$.año') >= ?"
        params.append(year_min)
    if year_max:
        query += " AND json_extract(raw_json, '$.año') <= ?"
        params.append(year_max)

    # Get total count for pagination
    count_query = query.replace("SELECT car_id, raw_json, scraped_at", "SELECT count(*) as c")
    total_rows = await execute_query(count_query, tuple(params))
    total = total_rows[0]["c"] if total_rows else 0

    # Add limits and execute main query
    query += " LIMIT ? OFFSET ?"
    params.extend([limit, offset])
    
    rows = await execute_query(query, tuple(params))
    cars = [_parse_car_row(r) for r in rows]

    return CarsResponse(
        total=total,
        page=page,
        limit=limit,
        cars=cars
    )

@app.get("/api/search", response_model=CarsResponse)
async def search_cars(
    q: str = Query(..., min_length=2),
    page: int = Query(1, ge=1),
    limit: int = Query(50, ge=1, le=100)
):
    offset = (page - 1) * limit
    
    # Use SQLite FTS5 for native blazing-fast text searches
    count_query = "SELECT count(*) as c FROM car_details_fts WHERE car_details_fts MATCH ?"
    total_rows = await execute_query(count_query, (q,))
    total = total_rows[0]["c"] if total_rows else 0
    
    query = """
        SELECT car_id, raw_json
        FROM car_details_fts
        WHERE car_details_fts MATCH ?
        ORDER BY rank
        LIMIT ? OFFSET ?
    """
    rows = await execute_query(query, (q, limit, offset))
    
    cars = []
    for r in rows:
        raw_json = json.loads(r["raw_json"])
        if "informacion_general" in raw_json:
            gen_info = raw_json["informacion_general"]
            if "#_de_pasajeros" in gen_info:
                gen_info["pasajeros"] = gen_info.pop("#_de_pasajeros")
            if "#_de_puertas" in gen_info:
                gen_info["puertas"] = gen_info.pop("#_de_puertas")
        
        car_dict = {"car_id": r["car_id"], "scraped_at": ""}
        car_dict.update(raw_json)
        cars.append(car_dict)
        
    return CarsResponse(
        total=total,
        page=page,
        limit=limit,
        cars=cars
    )

@app.get("/api/cars/{car_id}", response_model=CarDetail)
async def get_car(car_id: str):
    rows = await execute_query("SELECT car_id, raw_json, scraped_at FROM car_details WHERE car_id=?", (car_id,))
    if not rows:
        raise HTTPException(status_code=404, detail="Car not found")
    return _parse_car_row(rows[0])

# Cache the response for 1 hour to prevent constant SQLite recalculations
@app.get("/api/insights/summary", response_model=SummaryStats)
@cached(cache=TTLCache(maxsize=1, ttl=3600))
async def get_summary():
    total_cars_row = await execute_query("SELECT count(*) as c FROM car_details")
    total_cars = total_cars_row[0]["c"]
    
    avg_row = await execute_query("""
        SELECT 
            AVG(NULLIF(json_extract(raw_json, '$.precio_usd'), 0)) as avg_usd,
            AVG(NULLIF(json_extract(raw_json, '$.precio_crc'), 0)) as avg_crc
        FROM car_details
    """)
    
    avg_usd = avg_row[0]["avg_usd"] or 0.0
    avg_crc = avg_row[0]["avg_crc"] or 0.0
    
    top_brands_rows = await execute_query("""
        SELECT 
            json_extract(raw_json, '$.marca') as marca, 
            COUNT(*) as count
        FROM car_details
        WHERE json_extract(raw_json, '$.marca') IS NOT NULL
        GROUP BY marca
        ORDER BY count DESC
        LIMIT 5
    """)
    top_brands = [{"marca": r["marca"], "count": r["count"]} for r in top_brands_rows]
    
    return SummaryStats(
        total_cars=total_cars,
        avg_price_usd=round(avg_usd, 2),
        avg_price_crc=round(avg_crc, 2),
        top_brands=top_brands
    )

# Cache the response for 1 hour
@app.get("/api/insights/brands", response_model=List[BrandStat])
@cached(cache=TTLCache(maxsize=1, ttl=3600))
async def get_brands_insight():
    rows = await execute_query("""
        SELECT 
            json_extract(raw_json, '$.marca') as marca, 
            COUNT(*) as count,
            AVG(NULLIF(json_extract(raw_json, '$.precio_usd'), 0)) as avg_price_usd,
            AVG(NULLIF(json_extract(raw_json, '$.precio_crc'), 0)) as avg_price_crc
        FROM car_details
        WHERE json_extract(raw_json, '$.marca') IS NOT NULL
        GROUP BY marca
        ORDER BY count DESC
    """)
    
    res = []
    for r in rows:
        res.append(BrandStat(
            marca=r["marca"], 
            count=r["count"], 
            avg_price_usd=round(r["avg_price_usd"] or 0.0, 2),
            avg_price_crc=round(r["avg_price_crc"] or 0.0, 2)
        ))
        
    return res

# Cache the response for 1 hour
@app.get("/api/insights/years", response_model=List[YearStat])
@cached(cache=TTLCache(maxsize=1, ttl=3600))
async def get_years_insight():
    rows = await execute_query("""
        SELECT 
            json_extract(raw_json, '$.año') as año, 
            COUNT(*) as count,
            AVG(NULLIF(json_extract(raw_json, '$.precio_usd'), 0)) as avg_price_usd,
            AVG(NULLIF(json_extract(raw_json, '$.precio_crc'), 0)) as avg_price_crc
        FROM car_details
        WHERE json_extract(raw_json, '$.año') IS NOT NULL
        GROUP BY año
        ORDER BY año DESC
    """)
    
    res = []
    for r in rows:
        res.append(YearStat(
            año=r["año"], 
            count=r["count"], 
            avg_price_usd=round(r["avg_price_usd"] or 0.0, 2),
            avg_price_crc=round(r["avg_price_crc"] or 0.0, 2)
        ))
        
    return res

# Cache the response for 1 hour
@app.get("/api/insights/provinces", response_model=List[ProvinceStat])
@cached(cache=TTLCache(maxsize=1, ttl=3600))
async def get_provinces_insight():
    rows = await execute_query("""
        SELECT 
            json_extract(raw_json, '$.informacion_general.provincia') as provincia, 
            COUNT(*) as count,
            AVG(NULLIF(json_extract(raw_json, '$.precio_usd'), 0)) as avg_price_usd,
            AVG(NULLIF(json_extract(raw_json, '$.precio_crc'), 0)) as avg_price_crc
        FROM car_details
        WHERE json_extract(raw_json, '$.informacion_general.provincia') IS NOT NULL
        GROUP BY provincia
        ORDER BY count DESC
    """)
    
    res = []
    for r in rows:
        res.append(ProvinceStat(
            provincia=r["provincia"], 
            count=r["count"], 
            avg_price_usd=round(r["avg_price_usd"] or 0.0, 2),
            avg_price_crc=round(r["avg_price_crc"] or 0.0, 2)
        ))
        
    return res

# Cache the response for 1 hour
@app.get("/api/insights/models", response_model=List[ModelStat])
@cached(cache=TTLCache(maxsize=1, ttl=3600))
async def get_models_insight():
    rows = await execute_query("""
        SELECT 
            json_extract(raw_json, '$.marca') as marca, 
            json_extract(raw_json, '$.modelo') as modelo, 
            COUNT(*) as count,
            AVG(NULLIF(json_extract(raw_json, '$.precio_usd'), 0)) as avg_price_usd,
            AVG(NULLIF(json_extract(raw_json, '$.precio_crc'), 0)) as avg_price_crc
        FROM car_details
        WHERE json_extract(raw_json, '$.marca') IS NOT NULL 
          AND json_extract(raw_json, '$.modelo') IS NOT NULL
        GROUP BY marca, modelo
        ORDER BY count DESC
        LIMIT 50
    """)
    
    res = []
    for r in rows:
        res.append(ModelStat(
            marca=r["marca"], 
            modelo=r["modelo"], 
            count=r["count"], 
            avg_price_usd=round(r["avg_price_usd"] or 0.0, 2),
            avg_price_crc=round(r["avg_price_crc"] or 0.0, 2)
        ))
        
    return res

@app.get("/api/insights/price-ranges-crc")
@cached(cache=TTLCache(maxsize=1, ttl=3600))
async def get_price_ranges_crc():
    query = """
        SELECT
            json_extract(raw_json, '$.marca') as marca,
            json_extract(raw_json, '$.modelo') as modelo,
            json_extract(raw_json, '$.año') as año,
            json_extract(raw_json, '$.precio_crc') as precio_crc
        FROM car_details
        WHERE json_extract(raw_json, '$.precio_crc') IS NOT NULL
        AND json_extract(raw_json, '$.marca') IS NOT NULL
        AND json_extract(raw_json, '$.modelo') IS NOT NULL
        AND json_extract(raw_json, '$.año') IS NOT NULL
    """
    rows = await execute_query(query)

    # We will process ranges in frontend or return raw data. For analytical flexibility,
    # returning the filtered records to allow frontend to group into ranges is best.
    # To keep response small, maybe we can group them here.

    # Let's create an aggregation directly
    import math
    results = []
    for r in rows:
        if not r["precio_crc"]: continue
        price_crc = r["precio_crc"]
        # Determine the range: 0.5M, 1M, 1.5M, etc.
        # We can calculate the range bucket by multiplying and dividing.
        # Bucket = ceil(price_crc / 500000) * 0.5
        bucket = math.ceil(price_crc / 500000.0) * 0.5
        results.append({
            "marca": r["marca"],
            "modelo": r["modelo"],
            "año": r["año"],
            "precio_crc": price_crc,
            "rango_m_crc": bucket
        })
    return results

@app.get("/api/insights/mileage")
@cached(cache=TTLCache(maxsize=1, ttl=3600))
async def get_mileage_insight():
    query = """
        SELECT
            json_extract(raw_json, '$.marca') as marca,
            json_extract(raw_json, '$.modelo') as modelo,
            json_extract(raw_json, '$.año') as año,
            json_extract(raw_json, '$.precio_crc') as precio_crc,
            json_extract(raw_json, '$.precio_usd') as precio_usd,
            json_extract(raw_json, '$.informacion_general.kilometraje_number') as kilometraje_number
        FROM car_details
        WHERE json_extract(raw_json, '$.informacion_general.kilometraje_number') IS NOT NULL
        AND json_extract(raw_json, '$.informacion_general.kilometraje_number') > 0
    """
    rows = await execute_query(query)

    results = []
    for r in rows:
        results.append({
            "marca": r["marca"],
            "modelo": r["modelo"],
            "año": r["año"],
            "precio_crc": r["precio_crc"],
            "precio_usd": r["precio_usd"],
            "kilometraje_number": r["kilometraje_number"]
        })
    return results
