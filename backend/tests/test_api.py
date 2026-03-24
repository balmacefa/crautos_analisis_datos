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
