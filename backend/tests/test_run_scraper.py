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
