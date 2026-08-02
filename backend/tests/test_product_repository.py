import pytest
from unittest.mock import MagicMock
from data_scrapper.repository import ScraperRepository


@pytest.fixture
def repo(tmp_path):
    db_path = tmp_path / "test_products.db"
    return ScraperRepository(str(db_path))


def test_upsert_and_get_pending_product_urls(repo):
    repo.upsert_product_urls(["https://cr.epaenlinea.com/rodin-a.html"], source="EpaEnLinea", category="rodines")

    assert repo.has_product_urls()
    pending = repo.get_pending_product_urls()
    assert pending == ["https://cr.epaenlinea.com/rodin-a.html"]
    assert not repo.is_product_url_done("https://cr.epaenlinea.com/rodin-a.html")


def test_mark_product_url_done_persists_details_and_syncs(repo):
    repo.ts_client = MagicMock()
    repo.get_active_run_id = MagicMock(return_value=42)

    url = "https://cr.epaenlinea.com/rodin-a.html"
    repo.upsert_product_urls([url], source="EpaEnLinea", category="rodines")

    data = {
        "nombre": "Rodín Industrial",
        "categoria": "rodines",
        "precio_crc": 12500.0,
        "sku": "ROD-1",
        "images": [],
        "imagen_principal": "",
    }
    repo.mark_product_url_done(url, "epa-rodin-a", data, source="EpaEnLinea", category="rodines")

    assert repo.is_product_url_done(url)

    products = repo.get_all_products()
    assert len(products) == 1
    assert products[0]["product_id"] == "epa-rodin-a"
    assert products[0]["nombre"] == "Rodín Industrial"

    repo.ts_client.collections['products'].documents.upsert.assert_called_once()
    doc = repo.ts_client.collections['products'].documents.upsert.call_args[0][0]
    assert doc["id"] == "epa-rodin-a"
    assert doc["precio_crc"] == 12500.0
    assert doc["fuente"] == "EpaEnLinea"
    assert doc["sync_version"] == "42"


def test_mark_product_url_failed_increments_retry_then_fails(repo):
    url = "https://cr.epaenlinea.com/broken.html"
    repo.upsert_product_urls([url], source="EpaEnLinea", category="rodines")

    for _ in range(repo.MAX_RETRIES):
        repo.mark_product_url_failed(url)

    stats = repo.get_product_run_stats()
    assert stats["failed"] == 1
    assert stats["pending"] == 0


def test_product_sync_typesense_failure_is_non_fatal(repo):
    repo.ts_client = MagicMock()
    repo.ts_client.collections.__getitem__.side_effect = Exception("collection not found")

    url = "https://cr.epaenlinea.com/rodin-a.html"
    repo.upsert_product_urls([url], source="EpaEnLinea", category="rodines")

    # Should not raise even though Typesense sync fails.
    repo.mark_product_url_done(url, "epa-rodin-a", {"nombre": "Rodín"}, source="EpaEnLinea", category="rodines")

    assert repo.is_product_url_done(url)
