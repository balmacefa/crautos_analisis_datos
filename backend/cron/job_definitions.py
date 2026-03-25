# job_definitions.py
# Job definitions for the DevOps Job Orchestrator

from cron_jobs.job_model import JobModel


def get_job_definitions():
    """Returns a list of JobModel instances to be added to the controller"""
    return [
        JobModel(
            "Test_job executed every minute",
            "echo 'Starting Test_job...' && sleep 3 && echo 'Test_job complete!'",
            "* * * * *",  # Every minute
        ),
        # ----------------------------------------------
        # CRON JOBS SECTION
        # ----------------------------------------------
        #  🤖‼️ 
        # JobModel(
        #     "sps_cr_pr_merge_automation_sprint_158",
        #     "python script.py --yes",
        #     "0 * * * *",  # At the hour every hour
        # ),
    ]
