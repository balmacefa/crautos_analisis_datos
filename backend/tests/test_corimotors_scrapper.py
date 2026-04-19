import pytest
from unittest.mock import AsyncMock, MagicMock
from data_scrapper.corimotors_scrapper import CorimotorsScraper

@pytest.mark.asyncio
async def test_corimotors_scraper_parsing():
    # Helper to create a mock locator with async methods
    def create_async_locator(text=None, count=0, all_val=None, attr=None):
        loc = MagicMock()
        loc.wait_for = AsyncMock()
        loc.inner_text = AsyncMock(return_value=text)
        loc.count = AsyncMock(return_value=count)
        loc.all = AsyncMock(return_value=all_val if all_val is not None else [])
        loc.get_attribute = AsyncMock(return_value=attr)
        return loc

    mock_page = MagicMock()
    mock_page.goto = AsyncMock()
    mock_page.wait_for_selector = AsyncMock()
    mock_page.close = AsyncMock()
    
    # Mock Title
    mock_title_loc = create_async_locator(text="MITSUBISHI XPANDER 2024", count=1)
    
    # Mock Price
    mock_price_loc = create_async_locator(text="$28,900", count=1)
    
    # Mock Properties
    prop1 = create_async_locator(text="Recorrido: 5,000 km", count=1)
    prop1_name = create_async_locator(text="Recorrido", count=1)
    prop1_val = create_async_locator(text="5,000 km", count=1)
    prop1.locator.side_effect = lambda s: prop1_name if "name" in s else prop1_val

    # Mock properties list
    mock_props_container = create_async_locator(count=1)
    mock_props_container.locator.return_value.all = AsyncMock(return_value=[prop1])

    def mock_locator(selector):
        if "h1.product-item-detail-title" in selector: return mock_title_loc
        if ".product-item-detail-price-current" in selector: return mock_price_loc
        if ".product-item-detail-properties" in selector: return mock_props_container
        return create_async_locator()

    mock_page.locator.side_effect = mock_locator
    
    scraper = CorimotorsScraper(repository=None)
    mock_repo = MagicMock()
    scraper.repository = mock_repo
    
    mock_context = MagicMock()
    mock_context.new_page = AsyncMock(return_value=mock_page)
    
    await scraper._scrape_car_detail(mock_context, "https://usadoscori.com/catalog/car-999")
    
    # Assertions
    mock_repo.mark_url_done.assert_called_once()
    args, _ = mock_repo.mark_url_done.call_args
    url, car_id, data = args
    
    assert car_id == "cori-car-999"
    assert data["marca"] == "MITSUBISHI"
    assert data["modelo"] == "XPANDER"
    assert data["año"] == 2024
    assert data["informacion_general"]["kilometraje_number"] == 5000

@pytest.mark.asyncio
async def test_corimotors_url_discovery():
    mock_page = MagicMock()
    mock_page.goto = AsyncMock()
    mock_page.wait_for_selector = AsyncMock()
    mock_page.close = AsyncMock()
    
    mock_link = MagicMock()
    mock_link.get_attribute = AsyncMock(return_value="/catalog/car-123")
    
    mock_locator = MagicMock()
    mock_locator.all = AsyncMock(return_value=[mock_link])
    
    mock_page.locator.return_value = mock_locator
    
    scraper = CorimotorsScraper()
    mock_context = MagicMock()
    mock_context.new_page = AsyncMock(return_value=mock_page)
    
    await scraper._collect_listing_urls(mock_context, limit_pages=1)
    
    assert "https://usadoscori.com/catalog/car-123" in scraper.discovered_urls
