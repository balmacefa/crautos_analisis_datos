from fastapi import FastAPI, Query, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from typing import Optional, List
import json
from cachetools import TTLCache
from asyncache import cached
from .database import execute_query
from .models import CarsResponse, CarDetail, SummaryStats, BrandStat, YearStat, ProvinceStat, ModelStat, CuriositiesResponse, CuriosityCar, ExplorerData, DepreciationStat, OpportunityCar, FuelStat, TransmissionStat, RatioStat, BrandComparisonStat

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
    total_cars_row = await execute_query("SELECT count(*) as c, MAX(scraped_at) as last_updated FROM car_details")
    total_cars = total_cars_row[0]["c"] if total_cars_row else 0
    last_updated = total_cars_row[0]["last_updated"] if total_cars_row else None
    
    avg_row = await execute_query("""
        SELECT 
            AVG(NULLIF(json_extract(raw_json, '$.precio_usd'), 0)) as avg_usd,
            AVG(NULLIF(json_extract(raw_json, '$.precio_crc'), 0)) as avg_crc
        FROM car_details
    """)
    
    avg_usd = avg_row[0]["avg_usd"] or 0.0 if avg_row else 0.0
    avg_crc = avg_row[0]["avg_crc"] or 0.0 if avg_row else 0.0
    
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
        top_brands=top_brands,
        last_updated=last_updated
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
@app.get("/api/insights/ratios/top", response_model=List[RatioStat])
@cached(cache=TTLCache(maxsize=1, ttl=3600))
async def get_top_ratios():
    rows = await execute_query("""
        SELECT
            json_extract(raw_json, '$.marca') as marca,
            json_extract(raw_json, '$.modelo') as modelo,
            COUNT(*) as count,
            AVG(NULLIF(json_extract(raw_json, '$.precio_usd'), 0)) as avg_price_usd,
            AVG(NULLIF(json_extract(raw_json, '$.precio_crc'), 0)) as avg_price_crc,
            AVG(NULLIF(json_extract(raw_json, '$.informacion_general.kilometraje_number'), 0)) as avg_mileage
        FROM car_details
        WHERE json_extract(raw_json, '$.marca') IS NOT NULL
          AND json_extract(raw_json, '$.modelo') IS NOT NULL
          AND json_extract(raw_json, '$.informacion_general.kilometraje_number') IS NOT NULL
          AND json_extract(raw_json, '$.precio_usd') IS NOT NULL
        GROUP BY marca, modelo
        HAVING count >= 3
    """)

    res = []
    for r in rows:
        if not r["avg_price_usd"] or not r["avg_mileage"]:
            continue
        ratio_usd = r["avg_price_usd"] / r["avg_mileage"]
        ratio_crc = (r["avg_price_crc"] or 0) / r["avg_mileage"]

        res.append(RatioStat(
            marca=r["marca"],
            modelo=r["modelo"],
            count=r["count"],
            avg_price_usd=round(r["avg_price_usd"], 2),
            avg_price_crc=round(r["avg_price_crc"] or 0, 2),
            avg_mileage=round(r["avg_mileage"], 2),
            ratio_usd=round(ratio_usd, 4),
            ratio_crc=round(ratio_crc, 4)
        ))

    return res

@app.get("/api/insights/brands/compare", response_model=List[BrandComparisonStat])
@cached(cache=TTLCache(maxsize=1, ttl=3600))
async def get_brand_comparison(brands: str = Query(..., description="Comma separated list of brands")):
    brand_list = [b.strip() for b in brands.split(",")]
    if not brand_list:
        return []

    placeholders = ",".join(["?"] * len(brand_list))

    query = f"""
        SELECT
            json_extract(raw_json, '$.marca') as marca,
            COUNT(*) as count,
            AVG(NULLIF(json_extract(raw_json, '$.precio_usd'), 0)) as avg_price_usd,
            AVG(NULLIF(json_extract(raw_json, '$.precio_crc'), 0)) as avg_price_crc,
            AVG(NULLIF(json_extract(raw_json, '$.informacion_general.kilometraje_number'), 0)) as avg_mileage,
            AVG(NULLIF(json_extract(raw_json, '$.año'), 0)) as avg_year
        FROM car_details
        WHERE json_extract(raw_json, '$.marca') IN ({placeholders})
        GROUP BY marca
    """

    rows = await execute_query(query, tuple(brand_list))

    res = []
    for r in rows:
        res.append(BrandComparisonStat(
            marca=r["marca"],
            count=r["count"],
            avg_price_usd=round(r["avg_price_usd"] or 0.0, 2),
            avg_price_crc=round(r["avg_price_crc"] or 0.0, 2),
            avg_mileage=round(r["avg_mileage"] or 0.0, 2),
            avg_year=round(r["avg_year"] or 0.0, 1)
        ))

    return res

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
@app.get("/api/insights/depreciation", response_model=List[DepreciationStat])
@cached(cache=TTLCache(maxsize=1, ttl=3600))
async def get_depreciation_insight():
    rows = await execute_query("""
        SELECT
            json_extract(raw_json, '$.marca') as marca,
            json_extract(raw_json, '$.modelo') as modelo,
            json_extract(raw_json, '$.año') as año,
            COUNT(*) as count,
            AVG(NULLIF(json_extract(raw_json, '$.precio_usd'), 0)) as avg_price_usd,
            AVG(NULLIF(json_extract(raw_json, '$.precio_crc'), 0)) as avg_price_crc
        FROM car_details
        WHERE json_extract(raw_json, '$.marca') IS NOT NULL
          AND json_extract(raw_json, '$.modelo') IS NOT NULL
          AND json_extract(raw_json, '$.año') IS NOT NULL
        GROUP BY marca, modelo, año
        HAVING count >= 3
        ORDER BY año DESC
    """)

    res = []
    for r in rows:
        res.append(DepreciationStat(
            marca=r["marca"],
            modelo=r["modelo"],
            año=r["año"],
            count=r["count"],
            avg_price_usd=round(r["avg_price_usd"] or 0.0, 2),
            avg_price_crc=round(r["avg_price_crc"] or 0.0, 2)
        ))

    return res

@app.get("/api/insights/distribution/fuel", response_model=List[FuelStat])
@cached(cache=TTLCache(maxsize=1, ttl=3600))
async def get_fuel_distribution():
    rows = await execute_query("""
        SELECT
            json_extract(raw_json, '$.informacion_general.combustible') as combustible,
            COUNT(*) as count,
            AVG(NULLIF(json_extract(raw_json, '$.precio_usd'), 0)) as avg_price_usd,
            AVG(NULLIF(json_extract(raw_json, '$.precio_crc'), 0)) as avg_price_crc
        FROM car_details
        WHERE json_extract(raw_json, '$.informacion_general.combustible') IS NOT NULL
        GROUP BY combustible
        ORDER BY count DESC
    """)

    res = []
    for r in rows:
        res.append(FuelStat(
            combustible=r["combustible"],
            count=r["count"],
            avg_price_usd=round(r["avg_price_usd"] or 0.0, 2),
            avg_price_crc=round(r["avg_price_crc"] or 0.0, 2)
        ))

    return res

@app.get("/api/insights/distribution/transmission", response_model=List[TransmissionStat])
@cached(cache=TTLCache(maxsize=1, ttl=3600))
async def get_transmission_distribution():
    rows = await execute_query("""
        SELECT
            json_extract(raw_json, '$.informacion_general.transmisión') as transmisión,
            COUNT(*) as count,
            AVG(NULLIF(json_extract(raw_json, '$.precio_usd'), 0)) as avg_price_usd,
            AVG(NULLIF(json_extract(raw_json, '$.precio_crc'), 0)) as avg_price_crc
        FROM car_details
        WHERE json_extract(raw_json, '$.informacion_general.transmisión') IS NOT NULL
        GROUP BY transmisión
        ORDER BY count DESC
    """)

    res = []
    for r in rows:
        res.append(TransmissionStat(
            transmisión=r["transmisión"],
            count=r["count"],
            avg_price_usd=round(r["avg_price_usd"] or 0.0, 2),
            avg_price_crc=round(r["avg_price_crc"] or 0.0, 2)
        ))

    return res

@app.get("/api/insights/opportunities", response_model=List[OpportunityCar])
@cached(cache=TTLCache(maxsize=1, ttl=3600))
async def get_opportunities():
    # Encuentra autos que estén al menos un 15% por debajo del precio promedio de su marca, modelo y año
    # Limitando a los grupos con al menos 3 vehículos para tener un promedio válido
    query = """
    WITH Averages AS (
        SELECT
            json_extract(raw_json, '$.marca') as marca,
            json_extract(raw_json, '$.modelo') as modelo,
            json_extract(raw_json, '$.año') as año,
            COUNT(*) as group_count,
            AVG(NULLIF(json_extract(raw_json, '$.precio_usd'), 0)) as avg_price_usd,
            AVG(NULLIF(json_extract(raw_json, '$.precio_crc'), 0)) as avg_price_crc
        FROM car_details
        WHERE json_extract(raw_json, '$.marca') IS NOT NULL
          AND json_extract(raw_json, '$.modelo') IS NOT NULL
          AND json_extract(raw_json, '$.año') IS NOT NULL
        GROUP BY marca, modelo, año
        HAVING group_count >= 3
    )
    SELECT
        c.car_id,
        json_extract(c.raw_json, '$.url') as url,
        json_extract(c.raw_json, '$.marca') as marca,
        json_extract(c.raw_json, '$.modelo') as modelo,
        json_extract(c.raw_json, '$.año') as año,
        json_extract(c.raw_json, '$.precio_usd') as precio_usd,
        json_extract(c.raw_json, '$.precio_crc') as precio_crc,
        json_extract(c.raw_json, '$.informacion_general.kilometraje_number') as kilometraje_number,
        json_extract(c.raw_json, '$.imagen_principal') as imagen_principal,
        a.avg_price_usd,
        a.avg_price_crc,
        -- Calculate deviation
        ((a.avg_price_usd - json_extract(c.raw_json, '$.precio_usd')) / a.avg_price_usd) * 100 as deviation_percent
    FROM car_details c
    JOIN Averages a
      ON json_extract(c.raw_json, '$.marca') = a.marca
     AND json_extract(c.raw_json, '$.modelo') = a.modelo
     AND json_extract(c.raw_json, '$.año') = a.año
    WHERE json_extract(c.raw_json, '$.precio_usd') > 0
      AND ((a.avg_price_usd - json_extract(c.raw_json, '$.precio_usd')) / a.avg_price_usd) >= 0.15
      AND json_extract(c.raw_json, '$.informacion_general.kilometraje_number') < 150000
    ORDER BY deviation_percent DESC
    LIMIT 20
    """

    rows = await execute_query(query)

    res = []
    for r in rows:
        res.append(OpportunityCar(
            car_id=r["car_id"],
            url=r["url"] or "",
            marca=r["marca"],
            modelo=r["modelo"],
            año=r["año"],
            precio_usd=r["precio_usd"] or 0.0,
            precio_crc=r["precio_crc"] or 0.0,
            kilometraje_number=r["kilometraje_number"],
            avg_price_usd=round(r["avg_price_usd"] or 0.0, 2),
            avg_price_crc=round(r["avg_price_crc"] or 0.0, 2),
            deviation_percent=round(r["deviation_percent"] or 0.0, 2),
            imagen_principal=r["imagen_principal"]
        ))

    return res

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


@app.get("/api/insights/curiosities", response_model=CuriositiesResponse)
@cached(cache=TTLCache(maxsize=1, ttl=3600))
async def get_curiosities():
    query_most_expensive = """
        SELECT car_id, raw_json
        FROM car_details
        WHERE json_extract(raw_json, '$.precio_usd') IS NOT NULL
        ORDER BY json_extract(raw_json, '$.precio_usd') DESC
        LIMIT 1
    """

    query_cheapest = """
        SELECT car_id, raw_json
        FROM car_details
        WHERE json_extract(raw_json, '$.precio_usd') IS NOT NULL
          AND json_extract(raw_json, '$.precio_usd') > 500
        ORDER BY json_extract(raw_json, '$.precio_usd') ASC
        LIMIT 1
    """

    query_oldest = """
        SELECT car_id, raw_json
        FROM car_details
        WHERE json_extract(raw_json, '$.año') IS NOT NULL
          AND json_extract(raw_json, '$.año') > 1900
        ORDER BY json_extract(raw_json, '$.año') ASC
        LIMIT 1
    """

    query_highest_mileage = """
        SELECT car_id, raw_json
        FROM car_details
        WHERE json_extract(raw_json, '$.informacion_general.kilometraje_number') IS NOT NULL
          AND json_extract(raw_json, '$.informacion_general.kilometraje_number') > 0
          AND json_extract(raw_json, '$.informacion_general.kilometraje_number') < 10000000
        ORDER BY json_extract(raw_json, '$.informacion_general.kilometraje_number') DESC
        LIMIT 1
    """

    async def fetch_curiosity(query, title_fmt, desc_fmt):
        rows = await execute_query(query)
        if not rows:
            return None
        r = rows[0]
        rj = json.loads(r["raw_json"])

        # default fallbacks
        marca = rj.get("marca", "Desconocida")
        modelo = rj.get("modelo", "Desconocido")
        año = rj.get("año", 0)
        precio_usd = rj.get("precio_usd", 0.0) or 0.0
        precio_crc = rj.get("precio_crc", 0.0) or 0.0
        imagen_principal = rj.get("imagen_principal")

        gen_info = rj.get("informacion_general", {})
        kilometraje_number = gen_info.get("kilometraje_number")

        return CuriosityCar(
            car_id=r["car_id"],
            marca=marca,
            modelo=modelo,
            año=año,
            precio_usd=precio_usd,
            precio_crc=precio_crc,
            kilometraje_number=kilometraje_number,
            imagen_principal=imagen_principal,
            title=title_fmt.format(marca=marca, modelo=modelo, año=año),
            description=desc_fmt.format(
                precio_usd=precio_usd,
                precio_crc=precio_crc,
                año=año,
                km=kilometraje_number
            )
        )

    most_expensive = await fetch_curiosity(
        query_most_expensive,
        "El más caro: {marca} {modelo} {año}",
        "${precio_usd:,.0f} USD"
    )

    cheapest = await fetch_curiosity(
        query_cheapest,
        "El más económico: {marca} {modelo} {año}",
        "${precio_usd:,.0f} USD"
    )

    oldest = await fetch_curiosity(
        query_oldest,
        "El más antiguo: {marca} {modelo} {año}",
        "Año {año}"
    )

    highest_mileage = await fetch_curiosity(
        query_highest_mileage,
        "Mayor kilometraje: {marca} {modelo} {año}",
        "{km:,} km"
    )

    return CuriositiesResponse(
        most_expensive=most_expensive,
        cheapest=cheapest,
        oldest=oldest,
        highest_mileage=highest_mileage
    )

@app.get("/api/insights/explorer", response_model=List[ExplorerData])
@cached(cache=TTLCache(maxsize=1, ttl=3600))
async def get_explorer_data():
    query = """
        SELECT
            car_id,
            json_extract(raw_json, '$.marca') as marca,
            json_extract(raw_json, '$.modelo') as modelo,
            json_extract(raw_json, '$.año') as año,
            json_extract(raw_json, '$.precio_crc') as precio_crc,
            json_extract(raw_json, '$.precio_usd') as precio_usd,
            json_extract(raw_json, '$.informacion_general.kilometraje_number') as kilometraje_number,
            json_extract(raw_json, '$.informacion_general.provincia') as provincia,
            json_extract(raw_json, '$.informacion_general.combustible') as combustible,
            json_extract(raw_json, '$.informacion_general.transmisión') as transmisión
        FROM car_details
    """
    rows = await execute_query(query)

    results = []
    for r in rows:
        results.append(ExplorerData(
            car_id=r["car_id"],
            marca=r["marca"],
            modelo=r["modelo"],
            año=r["año"],
            precio_crc=r["precio_crc"],
            precio_usd=r["precio_usd"],
            kilometraje_number=r["kilometraje_number"],
            provincia=r["provincia"],
            combustible=r["combustible"],
            transmisión=r["transmisión"]
        ))
    return results
