import pytest
import os
import sqlite3
from unittest.mock import AsyncMock, patch, MagicMock
from data_scrapper.run_scraper import main as scraper_main
from data_scrapper.repository import ScraperRepository

@pytest.fixture
def test_db(tmp_path):
    db_path = tmp_path / "test.db"
    repo = ScraperRepository(str(db_path))
    return str(db_path)

@pytest.mark.asyncio
async def test_run_scraper_evmarket_command(test_db):
    """Verify that 'evmarket' command triggers the EVMarketScraper."""
    
    # Mock the EVMarketScraper.run method
    with patch("data_scrapper.evmarket_scrapper.EVMarketScraper.run", new_callable=AsyncMock) as mock_run:
        with patch.dict(os.environ, {"SCRAPER_DB_PATH": test_db}):
            # We mock sys.exit to avoid test termination
            with patch("sys.exit") as mock_exit:
                await scraper_main("evmarket")
                
                mock_run.assert_called_once()
                # Verify it finished with success (exit 0)
                mock_exit.assert_called_with(0)

@pytest.mark.asyncio
async def test_run_scraper_epa_command(test_db):
    """Verify that 'epa' command triggers the EpaEnLineaScraper."""
    with patch("data_scrapper.epaenlinea_scrapper.EpaEnLineaScraper.run", new_callable=AsyncMock) as mock_run:
        with patch.dict(os.environ, {"SCRAPER_DB_PATH": test_db}):
            with patch("sys.exit") as mock_exit:
                await scraper_main("epa")

                mock_run.assert_called_once()
                mock_exit.assert_called_with(0)


@pytest.mark.asyncio
async def test_run_scraper_invalid_command(test_db):
    """Verify that an invalid command results in failure."""
    with patch.dict(os.environ, {"SCRAPER_DB_PATH": test_db}):
        with patch("sys.exit") as mock_exit:
            await scraper_main("invalid")
            mock_exit.assert_called_with(1)

@pytest.mark.asyncio
async def test_run_scraper_urls_command(test_db):
    """Verify that 'urls' command triggers the Step 1 scraper."""
    with patch("data_scrapper.scraper_pagination_list.main", new_callable=AsyncMock) as mock_step1:
        mock_step1.return_value = "done"
        with patch.dict(os.environ, {"SCRAPER_DB_PATH": test_db}):
            with patch("sys.exit") as mock_exit:
                await scraper_main("urls")
                mock_step1.assert_called_once()
                mock_exit.assert_called_with(0)

def test_sync_to_typesense_run_id(test_db):
    repo = ScraperRepository(test_db)
    repo.ts_client = MagicMock()

    car_id = "test-car-1"
    data = {"marca": "Toyota", "modelo": "Corolla", "año": 2020}
    scraped_at = "2024-01-01"
    url = "http://test.com/car-1"

    repo.get_active_run_id = MagicMock(return_value=123)

    repo.mark_url_done(url, car_id, data, source="Test")

    repo.ts_client.collections['cars'].documents.upsert.assert_called_once()
    upsert_doc = repo.ts_client.collections['cars'].documents.upsert.call_args[0][0]

    assert upsert_doc['sync_version'] == '123'

def test_sync_to_typesense_run_id_none(test_db):
    repo = ScraperRepository(test_db)
    repo.ts_client = MagicMock()

    car_id = "test-car-2"
    data = {"marca": "Honda", "modelo": "Civic", "año": 2021}
    scraped_at = "2024-01-01"
    url = "http://test.com/car-2"

    repo.get_active_run_id = MagicMock(return_value=None)

    # We set the environment variable just in case, to see if fallback works
    os.environ["SYNC_VERSION"] = "test-version-fallback"

    repo.mark_url_done(url, car_id, data, source="Test")

    repo.ts_client.collections['cars'].documents.upsert.assert_called_once()
    upsert_doc = repo.ts_client.collections['cars'].documents.upsert.call_args[0][0]

    assert upsert_doc['sync_version'] == 'test-version-fallback'
