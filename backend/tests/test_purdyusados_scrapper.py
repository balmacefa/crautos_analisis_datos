import pytest
import re
import json
from unittest.mock import AsyncMock, MagicMock
from data_scrapper.purdyusados_scrapper import PurdyUsadosScraper

# Helper to create a mock locator with async methods
def create_async_locator(text=None, count=0, all_val=None, attr=None, visible=True):
    loc = MagicMock()
    loc.wait_for = AsyncMock()
    loc.wait_for_selector = AsyncMock()
    loc.scroll_into_view_if_needed = AsyncMock()
    loc.click = AsyncMock()
    loc.inner_text = AsyncMock(return_value=text)
    loc.count = AsyncMock(return_value=count)
    loc.all = AsyncMock(return_value=all_val if all_val is not None else [])
    loc.get_attribute = AsyncMock(return_value=attr)
    loc.is_visible = AsyncMock(return_value=visible)
    return loc

@pytest.mark.asyncio
async def test_purdy_scraper_parsing():
    mock_page = MagicMock()
    mock_page.goto = AsyncMock()
    mock_page.wait_for_selector = AsyncMock()
    mock_page.close = AsyncMock()
    
    # Mock Data
    mock_brand_loc = create_async_locator(text="TOYOTA", count=1)
    mock_model_loc = create_async_locator(text="COROLLA", count=1)
    mock_year_loc = create_async_locator(text="2022", count=1)
    mock_price_loc = create_async_locator(text="$ 25,000", count=1)
    
    # Mock Specs
    spec1 = MagicMock()
    spec1.locator.side_effect = lambda s: create_async_locator(text="Kilometraje", count=1) if s == "span" else create_async_locator(text="15,000 km", count=1)
    spec2 = MagicMock()
    spec2.locator.side_effect = lambda s: create_async_locator(text="No. Unidad", count=1) if s == "span" else create_async_locator(text="UNIT123", count=1)
    
    mock_specs_loc = create_async_locator(all_val=[spec1, spec2])
    
    # Mock Images
    mock_img_link = create_async_locator(attr="/images/car1.jpg", count=1)
    mock_images_loc = create_async_locator(all_val=[mock_img_link])
    
    def mock_locator(selector):
        if ".v-detail__brand" in selector: return mock_brand_loc
        if ".v-detail__model" in selector: return mock_model_loc
        if ".v-detail__year" in selector: return mock_year_loc
        if ".v-detail__price" in selector: return mock_price_loc
        if ".v-detail__spec-item" in selector: return mock_specs_loc
        if "a.js-popup-img" in selector: return mock_images_loc
        return create_async_locator()

    mock_page.locator.side_effect = mock_locator
    
    scraper = PurdyUsadosScraper(repository=None)
    mock_repo = MagicMock()
    scraper.repository = mock_repo
    
    mock_context = MagicMock()
    mock_context.new_page = AsyncMock(return_value=mock_page)
    
    await scraper._scrape_car_detail(mock_context, "https://www.purdyusados.com/auto/corolla-2022-UNIT123")
    
    # Assertions
    mock_repo.mark_url_done.assert_called_once()
    args, _ = mock_repo.mark_url_done.call_args
    url, car_id, data = args
    
    assert car_id == "purdy-UNIT123"
    assert data["marca"] == "TOYOTA"
    assert data["modelo"] == "COROLLA"
    assert data["año"] == 2022
    assert data["informacion_general"]["kilometraje_number"] == 15000
    assert "https://www.purdyusados.com/images/car1.jpg" in data["images"]

@pytest.mark.asyncio
async def test_purdy_url_discovery():
    mock_page = MagicMock()
    mock_page.goto = AsyncMock()
    mock_page.wait_for_selector = AsyncMock()
    mock_page.close = AsyncMock()
    
    # Mock "VER MÁS" button - first visible, then not to stop loop
    mock_load_more = create_async_locator(visible=False, count=0) 
    
    # Mock car links
    link1 = create_async_locator(attr="/auto/car1")
    link2 = create_async_locator(attr="/auto/car2")
    mock_links_loc = create_async_locator(all_val=[link1, link2])
    
    def mock_locator(selector):
        if "button.loadMore" in selector: return mock_load_more
        if "a[href^='/auto/']" in selector: return mock_links_loc
        return create_async_locator()
        
    mock_page.locator.side_effect = mock_locator
    
    scraper = PurdyUsadosScraper()
    mock_context = MagicMock()
    mock_context.new_page = AsyncMock(return_value=mock_page)
    
    await scraper._collect_listing_urls(mock_context, limit_clicks=0)
    
    assert "https://www.purdyusados.com/auto/car1" in scraper.discovered_urls
    assert "https://www.purdyusados.com/auto/car2" in scraper.discovered_urls
    assert len(scraper.discovered_urls) == 2
