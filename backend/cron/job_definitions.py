# job_definitions.py
# Job definitions for the DevOps Job Orchestrator

from cron.job_model import JobModel


import os

def get_job_definitions():
    """Returns a list of JobModel instances to be added to the controller"""
    # Removing surrounding quotes from environment variables if present

    # Separate schedules for different sources
    cron_schedule_crautos = os.getenv("SCRAPER_CRON", "0 7,19 * * *").strip('"\'')
    cron_schedule_evmarket = os.getenv("EV_SCRAPER_CRON", "0 8,20 * * *").strip('"\'')
    cron_schedule_corimotors = os.getenv("CORI_SCRAPER_CRON", "0 9,21 * * *").strip('"\'')
    cron_schedule_veinsa = os.getenv("VEINSA_SCRAPER_CRON", "0 10,22 * * *").strip('"\'')

    return [
        JobModel(
            "CrAutos Data Scraper",
            "python -m data_scrapper.run_scraper all",
            cron_schedule_crautos,
        ),
        JobModel(
            "EVMarket Data Scraper",
            "python -m data_scrapper.run_scraper evmarket",
            cron_schedule_evmarket,
        ),
        JobModel(
            "Corimotors Data Scraper",
            "python -m data_scrapper.run_scraper cori",
            cron_schedule_corimotors,
        ),
        JobModel(
            "Veinsa Data Scraper",
            "python -m data_scrapper.run_scraper veinsa",
            cron_schedule_veinsa,
        ),
    ]
