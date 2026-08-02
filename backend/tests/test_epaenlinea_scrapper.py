import pytest
from unittest.mock import AsyncMock, MagicMock
from data_scrapper.epaenlinea_scrapper import EpaEnLineaScraper, _slug_from_url, _is_excluded


def create_async_locator(text=None, count=0, all_val=None, attr=None, enabled=True):
    loc = MagicMock()
    loc.wait_for = AsyncMock()
    loc.inner_text = AsyncMock(return_value=text)
    loc.count = AsyncMock(return_value=count)
    loc.all = AsyncMock(return_value=all_val if all_val is not None else [])
    loc.get_attribute = AsyncMock(return_value=attr)
    loc.is_enabled = AsyncMock(return_value=enabled)
    loc.click = AsyncMock()
    loc.first = loc
    return loc


def test_slug_from_url():
    assert _slug_from_url("https://cr.epaenlinea.com/producto-de-prueba.html") == "producto-de-prueba"
    assert _slug_from_url("https://cr.epaenlinea.com/rodines.html") == "rodines"


def test_is_excluded():
    assert _is_excluded("https://cr.epaenlinea.com/tiendas/epa.html")
    assert _is_excluded("https://cr.epaenlinea.com/productos.html")
    assert not _is_excluded("https://cr.epaenlinea.com/rodin-industrial.html")


@pytest.mark.asyncio
async def test_epa_scraper_parsing():
    mock_page = MagicMock()
    mock_page.goto = AsyncMock()
    mock_page.close = AsyncMock()

    mock_title_loc = create_async_locator(text="Rodín Industrial 4 pulgadas", count=1)
    mock_price_loc = create_async_locator(text="₡ 12,500", count=1)
    mock_body_loc = create_async_locator(text="SKU: ROD-1234\nDisponible en tienda", count=1)

    def mock_locator(selector):
        if selector == "h1":
            return mock_title_loc
        if selector == "body":
            return mock_body_loc
        if selector == ".price":
            return mock_price_loc
        return create_async_locator(count=0, all_val=[])

    mock_page.locator.side_effect = mock_locator

    scraper = EpaEnLineaScraper(repository=None)
    mock_repo = MagicMock()
    mock_repo.is_product_url_done = MagicMock(return_value=False)
    scraper.repository = mock_repo

    mock_context = MagicMock()
    mock_context.new_page = AsyncMock(return_value=mock_page)

    await scraper._scrape_product_detail(mock_context, "https://cr.epaenlinea.com/rodin-industrial-4-pulgadas.html", "rodines")

    mock_repo.mark_product_url_done.assert_called_once()
    args, kwargs = mock_repo.mark_product_url_done.call_args
    url, product_id, data = args

    assert product_id == "epa-rodin-industrial-4-pulgadas"
    assert data["nombre"] == "Rodín Industrial 4 pulgadas"
    assert data["precio_crc"] == 12500.0
    assert data["categoria"] == "rodines"
    assert kwargs["source"] == "EpaEnLinea"
    assert kwargs["category"] == "rodines"


@pytest.mark.asyncio
async def test_epa_scraper_detail_failure_marks_url_failed():
    mock_page = MagicMock()
    mock_page.goto = AsyncMock(side_effect=Exception("boom"))
    mock_page.close = AsyncMock()

    mock_context = MagicMock()
    mock_context.new_page = AsyncMock(return_value=mock_page)

    scraper = EpaEnLineaScraper(repository=None)
    mock_repo = MagicMock()
    scraper.repository = mock_repo

    await scraper._scrape_product_detail(mock_context, "https://cr.epaenlinea.com/broken.html", "rodines")

    mock_repo.mark_product_url_done.assert_not_called()
    mock_repo.mark_product_url_failed.assert_called_once_with("https://cr.epaenlinea.com/broken.html")


@pytest.mark.asyncio
async def test_epa_category_url_discovery():
    mock_page = MagicMock()
    mock_page.goto = AsyncMock()
    mock_page.wait_for_timeout = AsyncMock()
    mock_page.close = AsyncMock()

    link1 = create_async_locator(attr="/rodin-a.html")
    link2 = create_async_locator(attr="/rodin-b.html")
    excluded_link = create_async_locator(attr="/tiendas/epa.html")
    links_loc = create_async_locator(all_val=[link1, link2, excluded_link])

    def mock_locator(selector):
        if selector == "a[href$='.html']":
            return links_loc
        return create_async_locator(count=0, all_val=[])

    mock_page.locator.side_effect = mock_locator

    scraper = EpaEnLineaScraper(repository=None)
    mock_context = MagicMock()
    mock_context.new_page = AsyncMock(return_value=mock_page)

    urls = await scraper._collect_category_urls(mock_context, "/rodines.html", limit_pages=1)

    assert "https://cr.epaenlinea.com/rodin-a.html" in urls
    assert "https://cr.epaenlinea.com/rodin-b.html" in urls
    assert not any("tiendas" in u for u in urls)
    assert scraper.discovered_urls["https://cr.epaenlinea.com/rodin-a.html"] == "rodines"
