"""
data_scrapper package

Exposes the main scraper modules and the repository for use by run_scraper.
"""

from data_scrapper import scraper_pagination_list  # noqa: F401
from data_scrapper import scraper_car_details       # noqa: F401
from data_scrapper.repository import ScraperRepository  # noqa: F401

__all__ = [
    "scraper_pagination_list",
    "scraper_car_details",
    "ScraperRepository",
]
