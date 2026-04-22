import pytest
from httpx import ASGITransport, AsyncClient
from api.main import app
from unittest.mock import patch, MagicMock

@pytest.mark.asyncio
async def test_get_cars_v2_basic():
    """Test that the v2 cars endpoint returns results and facets."""
    mock_search_results = {
        "found": 1,
        "hits": [
            {
                "document": {
                    "car_id": "test_id",
                    "url": "http://test.com",
                    "marca": "Toyota",
                    "modelo": "Corolla",
                    "año": 2020,
                    "precio_usd": 15000,
                    "precio_crc": 8000000,
                    "provincia": "San José",
                    "combustible": "Gasolina",
                    "transmisión": "Manual",
                    "scraped_at": "2024-01-01"
                }
            }
        ],
        "facet_counts": [
            {
                "field_name": "marca",
                "counts": [{"value": "Toyota", "count": 1}]
            },
            {
                "field_name": "año",
                "counts": [{"value": "2020", "count": 1}]
            }
        ]
    }

    with patch("api.main.ts_client.collections") as mock_collections:
        mock_collections.__getitem__.return_value.documents.search.return_value = mock_search_results
        
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
            response = await ac.get("/api/v2/cars?q=toyota&brands=Toyota")
        
        if response.status_code != 200:
            print("API Error:", response.text)
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        assert len(data["cars"]) == 1
        assert data["cars"][0]["marca"] == "Toyota"
        assert len(data["facets"]) == 2
        assert data["facets"][0]["field_name"] == "marca"

@pytest.mark.asyncio
async def test_get_cars_v2_filters():
    """Test that filters are correctly passed to Typesense."""
    with patch("api.main.ts_client.collections") as mock_collections:
        mock_search = MagicMock(return_value={"found": 0, "hits": [], "facet_counts": []})
        mock_collections.__getitem__.return_value.documents.search = mock_search
        
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
            await ac.get("/api/v2/cars?brands=Toyota,BMW&year_min=2015&year_max=2020")
        
        # Verify search parameters
        args, kwargs = mock_search.call_args
        params = args[0]
        assert "marca:[Toyota,BMW]" in params["filter_by"]
        assert "año:[2015..2020]" in params["filter_by"]
        assert "marca,modelo,provincia,combustible,transmisión" == params["query_by"]

@pytest.mark.asyncio
async def test_get_cars_v2_price_filter():
    """Test price filtering logic for both USD and CRC."""
    with patch("api.main.ts_client.collections") as mock_collections:
        mock_search = MagicMock(return_value={"found": 0, "hits": [], "facet_counts": []})
        mock_collections.__getitem__.return_value.documents.search = mock_search
        
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
            # Test default CRC
            await ac.get("/api/v2/cars?price_min=10000&price_max=50000")
            args, kwargs = mock_search.call_args
            params = args[0]
            assert "precio_crc:[10000.0..50000.0]" in params["filter_by"]
            
            # Test explicit USD
            await ac.get("/api/v2/cars?price_min=5000&price_max=15000&price_currency=USD")
            args, kwargs = mock_search.call_args
            params = args[0]
            assert "precio_usd:[5000.0..15000.0]" in params["filter_by"]
