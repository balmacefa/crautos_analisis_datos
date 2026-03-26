# job_definitions.py
# Job definitions for the DevOps Job Orchestrator

from cron.job_model import JobModel


import os

def get_job_definitions():
    """Returns a list of JobModel instances to be added to the controller"""
    # Removing surrounding quotes from environment variables if present
    cron_schedule = os.getenv("SCRAPER_CRON", "0 0 * * *").strip('"\'')

    return [
        JobModel(
            "CrAutos Data Scraper",
            "python -m data_scrapper.run_scraper all",
            cron_schedule,
        ),
    ]
