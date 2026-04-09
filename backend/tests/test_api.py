import pytest
from httpx import ASGITransport, AsyncClient
from ..api.main import app

@pytest.mark.asyncio
async def test_api_cars_endpoint():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get("/api/cars?limit=10")
    assert response.status_code == 200
    data = response.json()
    assert "total" in data
    assert "cars" in data
    assert isinstance(data["cars"], list)
    assert len(data["cars"]) <= 10

@pytest.mark.asyncio
async def test_api_insights_summary():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get("/api/insights/summary")
    assert response.status_code == 200
    data = response.json()
    assert "total_cars" in data
    assert "avg_price_usd" in data
    assert "top_brands" in data
    assert "last_updated" in data

@pytest.mark.asyncio
async def test_api_insights_brands():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get("/api/insights/brands")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    if len(data) > 0:
        assert "marca" in data[0]
        assert "count" in data[0]

@pytest.mark.asyncio
async def test_api_insights_years():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get("/api/insights/years")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    if len(data) > 0:
        assert "año" in data[0]
        assert "count" in data[0]

@pytest.mark.asyncio
async def test_api_insights_provinces():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get("/api/insights/provinces")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    if len(data) > 0:
        assert "provincia" in data[0]
        assert "count" in data[0]

@pytest.mark.asyncio
async def test_api_insights_models():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get("/api/insights/models")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    if len(data) > 0:
        assert "marca" in data[0]
        assert "modelo" in data[0]
        assert "count" in data[0]

@pytest.mark.asyncio
async def test_api_insights_price_ranges_crc():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get("/api/insights/price-ranges-crc")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    if len(data) > 0:
        assert "marca" in data[0]
        assert "rango_m_crc" in data[0]

@pytest.mark.asyncio
async def test_api_insights_mileage():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get("/api/insights/mileage")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    if len(data) > 0:
        assert "marca" in data[0]
        assert "kilometraje_number" in data[0]

@pytest.mark.asyncio
async def test_api_insights_curiosities():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get("/api/insights/curiosities")
    assert response.status_code == 200
    data = response.json()
    assert "most_expensive" in data
    assert "cheapest" in data
    assert "oldest" in data
    assert "highest_mileage" in data

@pytest.mark.asyncio
async def test_api_insights_explorer():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get("/api/insights/explorer")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    if len(data) > 0:
        assert "car_id" in data[0]
        assert "precio_usd" in data[0]
        assert "kilometraje_number" in data[0]


@pytest.mark.asyncio
async def test_market_extremes_endpoint():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get("/api/insights/market-extremes")
    assert response.status_code == 200
    data = response.json()
    assert "most_popular_brand" in data
    assert "least_popular_brand" in data
    assert "highest_value_model" in data
    assert "lowest_value_model" in data

    if data["most_popular_brand"]:
        assert "marca" in data["most_popular_brand"]
        assert "count" in data["most_popular_brand"]

@pytest.mark.asyncio
async def test_models_transmissions_endpoint():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get("/api/insights/models/transmissions")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    if len(data) > 0:
        assert "marca" in data[0]
        assert "modelo" in data[0]
        assert "transmisión" in data[0]
        assert "count" in data[0]
