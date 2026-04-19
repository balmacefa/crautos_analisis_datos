import pytest
import re
from unittest.mock import AsyncMock, MagicMock
from data_scrapper.veinsa_scrapper import VeinsaScraper

# Helper to create a mock locator with async methods
def create_async_locator(text=None, count=0, all_val=None, attr=None, hidden=True, enabled=True):
    loc = MagicMock()
    loc.wait_for = AsyncMock()
    loc.inner_text = AsyncMock(return_value=text)
    loc.count = AsyncMock(return_value=count)
    loc.all = AsyncMock(return_value=all_val if all_val is not None else [])
    loc.get_attribute = AsyncMock(return_value=attr)
    loc.is_hidden = AsyncMock(return_value=hidden)
    loc.is_enabled = AsyncMock(return_value=enabled)
    loc.first = loc # Self-reference so .first.inner_text works
    return loc

@pytest.mark.asyncio
async def test_veinsa_scraper_parsing():
    mock_page = MagicMock()
    mock_page.goto = AsyncMock()
    mock_page.wait_for_selector = AsyncMock()
    mock_page.close = AsyncMock()
    
    # Mock Title
    mock_title_loc = create_async_locator(text="CITROEN C-ELYSEE (2016)", count=1)
    
    # Mock Price
    mock_price_loc = create_async_locator(text="$ 7,900", count=1)
    
    # Mock Specs (div:has(> p))
    spec1 = create_async_locator(text="Kilometraje\n54,000 km", count=1)
    spec2 = create_async_locator(text="Combustible\nGasolina", count=1)
    
    def mock_locator(selector):
        if "h1" in selector: return mock_title_loc
        if "has-text('$')" in selector: return mock_price_loc
        if "div:has(> p)" in selector:
            m = create_async_locator(all_val=[spec1, spec2])
            return m
        return create_async_locator()

    mock_page.locator.side_effect = mock_locator
    
    scraper = VeinsaScraper(repository=None)
    mock_repo = MagicMock()
    scraper.repository = mock_repo
    
    mock_context = MagicMock()
    mock_context.new_page = AsyncMock(return_value=mock_page)
    
    await scraper._scrape_car_detail(mock_context, "https://veinsausados.com/detalle/citroen-c-elysee-12345")
    
    # Assertions
    mock_repo.mark_url_done.assert_called_once()
    args, _ = mock_repo.mark_url_done.call_args
    url, car_id, data = args
    
    assert car_id == "veinsa-12345"
    assert data["marca"] == "CITROEN"
    assert data["año"] == 2016
    assert data["informacion_general"]["kilometraje_number"] == 54000

@pytest.mark.asyncio
async def test_veinsa_url_discovery():
    mock_page = MagicMock()
    mock_page.goto = AsyncMock()
    mock_page.wait_for_selector = AsyncMock()
    mock_page.close = AsyncMock()
    
    # Mock Card for discovery
    mock_card = MagicMock()
    mock_link = create_async_locator(attr="/detalle/test-car-678", count=1)
    
    # Mock locators for the card
    mock_h3 = create_async_locator(count=1)
    mock_a_loc = MagicMock()
    mock_a_loc.count = AsyncMock(return_value=1)
    mock_a_loc.first = mock_link
    
    def card_locator_side_effect(selector):
        if selector == "h3": return mock_h3
        if selector == "a": return mock_a_loc
        return create_async_locator()
    
    mock_card.locator.side_effect = card_locator_side_effect
    
    # Grid locator
    mock_grid_loc = create_async_locator(all_val=[mock_card])
    
    def mock_locator(selector):
        if "grid-cols" in selector: return mock_grid_loc
        return create_async_locator(count=0) # next button etc
        
    mock_page.locator.side_effect = mock_locator
    
    scraper = VeinsaScraper()
    mock_context = MagicMock()
    mock_context.new_page = AsyncMock(return_value=mock_page)
    
    await scraper._collect_listing_urls(mock_context, limit_pages=1)
    
    assert "https://veinsausados.com/detalle/test-car-678" in scraper.discovered_urls
