import pytest
from unittest.mock import AsyncMock, MagicMock
from data_scrapper.evmarket_scrapper import EVMarketScraper

@pytest.mark.asyncio
async def test_evmarket_scraper_parsing():
    # 1. Setup nested mocks for Playwright
    mock_page = MagicMock()
    mock_page.goto = AsyncMock()
    mock_page.wait_for_selector = AsyncMock()
    mock_page.close = AsyncMock()
    
    # helper to create a mock locator
    def create_mock_locator(text=None, count=1, details=None):
        loc = MagicMock()
        loc.wait_for = AsyncMock()
        loc.inner_text = AsyncMock(return_value=text)
        loc.count = AsyncMock(return_value=count)
        if details:
            loc.all = AsyncMock(return_value=details)
        else:
            loc.all = AsyncMock(return_value=[])
        return loc

    mock_title_loc = create_mock_locator(text="BYD Yuan Plus 2024")
    mock_price_crc_loc = create_mock_locator(text="₡25,000,000", count=1)
    mock_price_usd_loc = create_mock_locator(text="$35,000", count=1)
    
    # Mock details list
    mock_li1 = MagicMock()
    mock_li1.inner_text = AsyncMock(return_value="Kilometraje: 5,000 km")
    mock_li2 = MagicMock()
    mock_li2.inner_text = AsyncMock(return_value="Combustible: Eléctrico")
    mock_li3 = MagicMock()
    mock_li3.inner_text = AsyncMock(return_value="Ubicación: San José")
    mock_details_loc = create_mock_locator(details=[mock_li1, mock_li2, mock_li3])
    
    def mock_locator_side_effect(selector):
        if ".listing-title h2" in selector: return mock_title_loc
        if ".price-crc" in selector: return mock_price_crc_loc
        if ".price-usd" in selector: return mock_price_usd_loc
        if ".listing-details li" in selector: return mock_details_loc
        return create_mock_locator()

    mock_page.locator.side_effect = mock_locator_side_effect
    
    scraper = EVMarketScraper(repository=None)
    mock_repo = MagicMock()
    scraper.repository = mock_repo
    
    mock_context = MagicMock()
    mock_context.new_page = AsyncMock(return_value=mock_page)
    
    await scraper._scrape_car_detail(mock_context, "https://evmarket.cr/listings/car-123")
    
    # Verify parsing
    mock_repo.mark_url_done.assert_called_once()
    args, _ = mock_repo.mark_url_done.call_args
    url, car_id, data = args
    
    assert car_id == "ev-car-123"
    assert data["marca"] == "BYD"
    assert data["año"] == 2024
    assert data["informacion_general"]["kilometraje_number"] == 5000

@pytest.mark.asyncio
async def test_evmarket_url_discovery():
    mock_page = MagicMock()
    mock_page.goto = AsyncMock()
    mock_page.wait_for_selector = AsyncMock()
    mock_page.close = AsyncMock()
    
    mock_link = MagicMock()
    mock_link.get_attribute = AsyncMock(return_value="/listings/car-456")
    
    mock_locator = MagicMock()
    mock_locator.all = AsyncMock(return_value=[mock_link])
    
    mock_page.locator.return_value = mock_locator
    
    scraper = EVMarketScraper()
    mock_context = MagicMock()
    mock_context.new_page = AsyncMock(return_value=mock_page)
    
    await scraper._collect_listing_urls(mock_context, limit_pages=1)
    
    assert "https://evmarket.cr/listings/car-456" in scraper.discovered_urls
