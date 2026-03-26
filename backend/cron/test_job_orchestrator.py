"""
Test Suite for DevOps Job Orchestrator
Tests cron scheduling, timing, concurrency, multiple job executions, and cron breaker
"""

import time
import unittest
from datetime import datetime, timedelta
from threading import Event, Thread
from cron.job_model import JobModel
from cron.devops_job_orchestrator import JobController


class TestJobOrchestrator(unittest.TestCase):
    """Comprehensive test suite for job orchestrator functionality"""

    def setUp(self):
        """Initialize a fresh controller for each test"""
        self.controller = JobController()
        self.test_timeout = 10  # Maximum seconds to wait for async operations

    def tearDown(self):
        """Clean up running jobs after each test"""
        for job in self.controller.jobs.values():
            if job.status == "running":
                self.controller.stop_job(job.name)
        time.sleep(0.5)  # Allow cleanup to complete

    def wait_for_condition(self, condition_func, timeout=None, check_interval=0.1):
        """
        Wait for a condition to become true

        Args:
            condition_func: Function that returns True when condition is met
            timeout: Maximum seconds to wait (default: self.test_timeout)
            check_interval: Seconds between checks

        Returns:
            True if condition met, False if timeout
        """
        timeout = timeout or self.test_timeout
        start_time = time.time()
        while time.time() - start_time < timeout:
            if condition_func():
                return True
            time.sleep(check_interval)
        return False

    # ==================== BASIC EXECUTION TESTS ====================

    def test_simple_job_execution(self):
        """Test basic job execution with simple echo command"""
        job = JobModel("test_simple", "echo 'Hello World'", "")  # Manual execution
        self.controller.add_job(job)

        # Start job
        self.controller.start_job("test_simple")

        # Wait for job to complete
        completed = self.wait_for_condition(lambda: job.status in ["idle", "error"])

        self.assertTrue(completed, "Job did not complete within timeout")
        self.assertEqual(job.status, "idle", "Job should complete successfully")
        self.assertIn("Hello World", "\n".join(job.logs), "Output not captured in logs")

    def test_job_with_exit_code(self):
        """Test job that exits with non-zero code"""
        job = JobModel("test_failure", "exit 42", "")
        self.controller.add_job(job)

        self.controller.start_job("test_failure")

        # Wait for completion
        completed = self.wait_for_condition(lambda: job.status in ["idle", "error"])

        self.assertTrue(completed, "Job did not complete within timeout")
        self.assertEqual(job.status, "error", "Job should be in error state")
        self.assertIn("exit code 42", "\n".join(job.logs), "Exit code not logged")

    def test_long_running_job(self):
        """Test job that takes several seconds to complete"""
        job = JobModel("test_long", "echo 'Starting' && sleep 3 && echo 'Finished'", "")
        self.controller.add_job(job)

        start_time = time.time()
        self.controller.start_job("test_long")

        # Verify job is running
        time.sleep(0.5)
        self.assertEqual(job.status, "running", "Job should be running")

        # Wait for completion
        completed = self.wait_for_condition(lambda: job.status == "idle", timeout=5)
        duration = time.time() - start_time

        self.assertTrue(completed, "Job did not complete")
        self.assertGreaterEqual(duration, 3, "Job completed too quickly")
        self.assertIn("Starting", "\n".join(job.logs))
        self.assertIn("Finished", "\n".join(job.logs))

    # ==================== CONCURRENCY TESTS ====================

    def test_prevent_duplicate_execution(self):
        """Test that a running job cannot be started again"""
        job = JobModel("test_duplicate", "sleep 5", "")
        self.controller.add_job(job)

        # Start job
        self.controller.start_job("test_duplicate")
        time.sleep(0.5)
        self.assertEqual(job.status, "running")

        # Try to start again (should be idempotent)
        initial_log_count = len(job.logs)
        self.controller.start_job("test_duplicate")
        time.sleep(0.5)

        # Should still be running, no duplicate execution
        self.assertEqual(job.status, "running")
        # Log count should not have doubled
        self.assertLess(len(job.logs), initial_log_count * 2)

        # Cleanup
        self.controller.stop_job("test_duplicate")

    def test_multiple_jobs_concurrent(self):
        """Test multiple jobs running concurrently"""
        jobs = [
            JobModel(f"concurrent_{i}", f"echo 'Job {i}' && sleep 2", "")
            for i in range(3)
        ]

        for job in jobs:
            self.controller.add_job(job)

        # Start all jobs
        start_time = time.time()
        for job in jobs:
            self.controller.start_job(job.name)

        time.sleep(0.5)

        # All should be running concurrently
        running_count = sum(1 for j in jobs if j.status == "running")
        self.assertEqual(running_count, 3, "All jobs should be running concurrently")

        # Wait for all to complete
        all_completed = self.wait_for_condition(
            lambda: all(j.status == "idle" for j in jobs), timeout=5
        )
        duration = time.time() - start_time

        self.assertTrue(all_completed, "Not all jobs completed")
        # Should take ~2 seconds (concurrent), not 6 seconds (sequential)
        self.assertLess(duration, 4, "Jobs did not run concurrently")

    # ==================== CRON SCHEDULING TESTS ====================

    def test_cron_every_minute(self):
        """Test cron job that runs every minute"""
        job = JobModel(
            "test_cron_minute", "echo 'Cron executed'", "* * * * *"  # Every minute
        )
        self.controller.add_job(job)

        # Wait for next minute boundary (up to 65 seconds)
        initial_log_count = len(job.logs)

        # Wait for cron trigger
        triggered = self.wait_for_condition(
            lambda: len(job.logs) > initial_log_count
            and "Cron triggered" in "\n".join(job.logs),
            timeout=65,
        )

        self.assertTrue(triggered, "Cron job was not triggered within 65 seconds")
        self.assertIn("Cron triggered", "\n".join(job.logs))

    def test_cron_specific_minute(self):
        """Test cron job scheduled for specific minute"""
        # Schedule for 2 minutes from now
        target_time = datetime.now() + timedelta(minutes=2)
        target_minute = target_time.minute

        job = JobModel(
            "test_cron_specific",
            "echo 'Specific time executed'",
            f"{target_minute} * * * *",  # Specific minute
        )
        self.controller.add_job(job)

        print(
            f"\nWaiting for cron at minute {target_minute} (current: {datetime.now().minute})"
        )

        # Wait for the specific minute (up to 130 seconds)
        triggered = self.wait_for_condition(
            lambda: "Cron triggered" in "\n".join(job.logs), timeout=130
        )

        self.assertTrue(
            triggered, f"Cron job did not trigger at minute {target_minute}"
        )

    def test_cron_hourly_short_job(self):
        """
        Test job scheduled every hour (0 * * * *) that completes quickly.
        This validates the fix for jobs that should run every hour.
        Job takes ~1 minute, so it should complete before next hour.
        """
        # Calculate next two hour marks
        now = datetime.now()
        next_hour = (now + timedelta(hours=1)).replace(
            minute=0, second=0, microsecond=0
        )
        second_hour = next_hour + timedelta(hours=1)

        # Only run this test if we're within 10 minutes of the hour
        # to avoid excessive waiting
        minutes_to_next_hour = (next_hour - now).total_seconds() / 60
        if minutes_to_next_hour > 10:
            self.skipTest(
                f"Too far from next hour ({minutes_to_next_hour:.1f} minutes). Run this test closer to the hour mark."
            )

        job = JobModel(
            "test_hourly_job",
            "echo 'Hourly job started' && sleep 30 && echo 'Hourly job completed'",
            "0 * * * *",  # At minute 0 of every hour
        )
        self.controller.add_job(job)

        print(f"\nWaiting for first hourly trigger at {next_hour.strftime('%H:%M')}")
        print(f"Current time: {now.strftime('%H:%M:%S')}")

        # Wait for first trigger (with buffer)
        first_trigger = self.wait_for_condition(
            lambda: "Cron triggered" in "\n".join(job.logs),
            timeout=int(minutes_to_next_hour * 60)
            + 70,  # Wait until next hour + buffer
        )

        self.assertTrue(first_trigger, "First hourly trigger did not occur")

        # Verify job completes (should take ~30 seconds)
        first_complete = self.wait_for_condition(
            lambda: job.status == "idle"
            and "Hourly job completed" in "\n".join(job.logs),
            timeout=60,
        )

        self.assertTrue(first_complete, "First execution did not complete")

        # Count how many times "Cron triggered" appears
        log_text = "\n".join(job.logs)
        first_trigger_count = log_text.count("Cron triggered")

        print(
            f"First execution completed. Waiting for second hourly trigger at {second_hour.strftime('%H:%M')}"
        )

        # Wait for second trigger (should happen at next hour mark)
        second_trigger = self.wait_for_condition(
            lambda: "\n".join(job.logs).count("Cron triggered") > first_trigger_count,
            timeout=3700,  # Up to 61 minutes + buffer
        )

        self.assertTrue(
            second_trigger, "Second hourly trigger did not occur - job only ran once!"
        )

        # Verify second execution completes
        second_complete = self.wait_for_condition(
            lambda: job.status == "idle"
            and "\n".join(job.logs).count("Hourly job completed") >= 2,
            timeout=60,
        )

        self.assertTrue(second_complete, "Second execution did not complete")

        # Final verification
        final_log = "\n".join(job.logs)
        trigger_count = final_log.count("Cron triggered")
        completion_count = final_log.count("Hourly job completed")

        self.assertGreaterEqual(
            trigger_count,
            2,
            f"Job should have triggered at least 2 times, got {trigger_count}",
        )
        self.assertGreaterEqual(
            completion_count,
            2,
            f"Job should have completed at least 2 times, got {completion_count}",
        )

        print(f"✓ Job successfully ran {trigger_count} times at hourly intervals")

    def test_cron_every_minute_completes_fast(self):
        """
        Test that validates the fix: jobs scheduled every minute that complete
        quickly should run multiple times (not just once).
        This simulates the hourly job scenario but runs faster for testing.
        """
        job = JobModel(
            "test_fast_recurring",
            "echo 'Run started' && sleep 2 && echo 'Run completed'",
            "* * * * *",  # Every minute
        )
        self.controller.add_job(job)

        print("\nWaiting for first cron trigger...")

        # Wait for first trigger
        first_trigger = self.wait_for_condition(
            lambda: "Cron triggered" in "\n".join(job.logs), timeout=65
        )
        self.assertTrue(first_trigger, "First trigger did not occur")

        # Wait for first completion (job takes ~2 seconds)
        first_complete = self.wait_for_condition(
            lambda: job.status == "idle" and "Run completed" in "\n".join(job.logs),
            timeout=10,
        )
        self.assertTrue(first_complete, "First execution did not complete")

        # Count triggers after first completion
        first_trigger_count = "\n".join(job.logs).count("Cron triggered")
        print(f"First execution completed. Trigger count: {first_trigger_count}")

        # Wait for second trigger (should happen at next minute boundary)
        print("Waiting for second cron trigger (up to 65 seconds)...")
        second_trigger = self.wait_for_condition(
            lambda: "\n".join(job.logs).count("Cron triggered") > first_trigger_count,
            timeout=65,
        )

        self.assertTrue(
            second_trigger,
            "Second trigger did not occur! This means the job only ran once (BUG NOT FIXED)",
        )

        # Wait for second completion
        second_complete = self.wait_for_condition(
            lambda: "\n".join(job.logs).count("Run completed") >= 2, timeout=10
        )
        self.assertTrue(second_complete, "Second execution did not complete")

        # Verify multiple executions
        final_log = "\n".join(job.logs)
        trigger_count = final_log.count("Cron triggered")
        completion_count = final_log.count("Run completed")

        self.assertGreaterEqual(
            trigger_count,
            2,
            f"Job should have triggered at least 2 times, got {trigger_count}. "
            f"This indicates the original bug where jobs only run once.",
        )
        self.assertGreaterEqual(
            completion_count,
            2,
            f"Job should have completed at least 2 times, got {completion_count}",
        )

        print(f"✓ SUCCESS: Job ran {trigger_count} times (fix validated!)")

    def test_cron_skip_when_running(self):
        """Test that cron skips execution if job is still running"""
        job = JobModel(
            "test_cron_skip",
            "echo 'Started' && sleep 90",  # Runs longer than 1 minute
            "* * * * *",  # Every minute
        )
        self.controller.add_job(job)

        # Wait for first cron trigger
        triggered = self.wait_for_condition(
            lambda: "Cron triggered" in "\n".join(job.logs), timeout=65
        )
        self.assertTrue(triggered, "First cron trigger failed")

        # Job should be running
        time.sleep(1)
        self.assertEqual(job.status, "running")

        # Wait for next minute boundary - should see skip message
        skipped = self.wait_for_condition(
            lambda: "Skipped cron trigger" in "\n".join(job.logs), timeout=65
        )

        self.assertTrue(skipped, "Cron should have logged skip message")

        # Cleanup
        self.controller.stop_job("test_cron_skip")

    # ==================== MULTIPLE EXECUTION TESTS ====================

    def test_job_multiple_sequential_runs(self):
        """Test running the same job multiple times sequentially"""
        job = JobModel("test_sequential", "echo 'Run' && date", "")
        self.controller.add_job(job)

        run_count = 3
        for i in range(run_count):
            self.controller.start_job("test_sequential")

            # Wait for completion
            completed = self.wait_for_condition(lambda: job.status == "idle")
            self.assertTrue(completed, f"Run {i+1} did not complete")

            time.sleep(0.5)  # Small delay between runs

        # Verify all runs logged
        log_text = "\n".join(job.logs)
        run_occurrences = log_text.count("Starting Job")
        self.assertEqual(
            run_occurrences, run_count, f"Should have {run_count} execution logs"
        )

    def test_restart_count_tracking(self):
        """
        Test that restart count is tracked correctly.
        Note: restart_count only increments on exceptions, not normal exit codes.
        This is by design - it tracks unexpected failures, not intentional exits.
        """
        job = JobModel(
            "test_restart",
            "python3 -c 'import sys; sys.exit(1)'",  # Normal exit with code 1
            "",
        )
        self.controller.add_job(job)

        # Run and fail multiple times
        for i in range(3):
            self.controller.start_job("test_restart")
            completed = self.wait_for_condition(lambda: job.status == "error")
            self.assertTrue(completed, f"Run {i+1} did not complete")
            time.sleep(0.2)

        # Verify job failed (status is error) but restart_count is 0
        # because these are normal exits, not exceptions
        self.assertEqual(job.status, "error", "Job should be in error state")
        self.assertEqual(
            job.restart_count,
            0,
            "Restart count should be 0 for normal exit codes (only exceptions increment it)",
        )

        # Verify multiple executions occurred
        log_text = "\n".join(job.logs)
        start_count = log_text.count("Starting Job")
        self.assertEqual(
            start_count, 3, f"Should have 3 execution starts, got {start_count}"
        )

    # ==================== TIMING TESTS ====================

    def test_execution_duration_tracking(self):
        """Test that execution duration is tracked and logged"""
        job = JobModel("test_duration", "sleep 2", "")
        self.controller.add_job(job)

        self.controller.start_job("test_duration")

        completed = self.wait_for_condition(lambda: job.status == "idle", timeout=5)

        self.assertTrue(completed, "Job did not complete")

        # Check duration is logged
        log_text = "\n".join(job.logs)
        self.assertIn("Duration:", log_text, "Duration not logged")
        self.assertIn("seconds", log_text, "Duration format incorrect")

    def test_last_run_timestamp(self):
        """Test that last_run timestamp is updated"""
        job = JobModel("test_timestamp", "echo 'test'", "")
        self.controller.add_job(job)

        self.assertIsNone(job.last_run, "last_run should be None initially")

        self.controller.start_job("test_timestamp")

        completed = self.wait_for_condition(lambda: job.status == "idle")

        self.assertTrue(completed)
        self.assertIsNotNone(job.last_run, "last_run should be set after execution")

        # Verify timestamp format (handles both with and without timezone suffix)
        try:
            # Try format with timezone suffix first
            datetime.strptime(job.last_run, "%Y-%m-%d %H:%M:%S %Z")
        except ValueError:
            try:
                # Fall back to format without timezone
                datetime.strptime(job.last_run, "%Y-%m-%d %H:%M:%S")
            except ValueError:
                self.fail(f"last_run timestamp format is invalid: {job.last_run}")

    # ==================== LOG MANAGEMENT TESTS ====================

    def test_log_retention_limit(self):
        """Test that logs are capped at 1000 lines"""
        job = JobModel(
            "test_log_limit", "for i in {1..1100}; do echo 'Line '$i; done", ""
        )
        self.controller.add_job(job)

        self.controller.start_job("test_log_limit")

        completed = self.wait_for_condition(lambda: job.status == "idle", timeout=10)

        self.assertTrue(completed)

        # Logs should be capped at 1000 lines
        self.assertLessEqual(len(job.logs), 1000, "Logs exceed 1000 line limit")

    # ==================== STOP/TERMINATE TESTS ====================

    def test_stop_running_job(self):
        """Test stopping a running job"""
        job = JobModel("test_stop", "sleep 30", "")
        self.controller.add_job(job)

        self.controller.start_job("test_stop")
        time.sleep(0.5)
        self.assertEqual(job.status, "running")

        # Stop the job
        self.controller.stop_job("test_stop")

        # Should transition to idle
        stopped = self.wait_for_condition(
            lambda: job.status == "idle", timeout=7  # 5s grace + 2s buffer
        )

        self.assertTrue(stopped, "Job did not stop within timeout")
        self.assertIn("Stopping job", "\n".join(job.logs))

    # ==================== CRON BREAKER TESTS ====================

    def test_cron_enabled_by_default(self):
        """Test that cron scheduler is enabled by default"""
        self.assertTrue(
            self.controller.cron_enabled, "Cron scheduler should be enabled by default"
        )

    def test_cron_can_be_disabled(self):
        """Test that cron scheduler can be disabled"""
        # Initially enabled
        self.assertTrue(self.controller.cron_enabled)

        # Toggle to disabled
        new_state = self.controller.toggle_cron()
        self.assertFalse(new_state, "toggle_cron should return False when disabling")
        self.assertFalse(
            self.controller.cron_enabled, "cron_enabled should be False after toggle"
        )

    def test_cron_can_be_reenabled(self):
        """Test that cron scheduler can be re-enabled after disabling"""
        # Disable
        self.controller.toggle_cron()
        self.assertFalse(self.controller.cron_enabled)

        # Re-enable
        new_state = self.controller.toggle_cron()
        self.assertTrue(new_state, "toggle_cron should return True when enabling")
        self.assertTrue(
            self.controller.cron_enabled,
            "cron_enabled should be True after re-enabling",
        )

    def test_cron_dont_trigger_when_disabled(self):
        """Test that cron jobs don't execute when cron is disabled"""
        # Create a job that should trigger every minute
        job = JobModel(
            name="test_cron_disabled",
            command="echo 'Should not run'",
            cron="* * * * *",  # Every minute
        )
        self.controller.add_job(job)

        # Disable cron
        self.controller.toggle_cron()
        self.assertFalse(self.controller.cron_enabled)

        # Wait for potential trigger (65 seconds to ensure we cross a minute boundary)
        time.sleep(65)

        # Job should still be idle
        self.assertEqual(
            job.status, "idle", "Job should not have started when cron is disabled"
        )

        # Check logs don't contain cron trigger message
        log_text = "\n".join(job.logs)
        self.assertNotIn(
            "Cron triggered",
            log_text,
            "Job logs should not contain 'Cron triggered' when cron is disabled",
        )

    def test_manual_jobs_work_when_cron_disabled(self):
        """Test that manual job execution still works when cron is disabled"""
        job = JobModel(
            name="test_manual_with_cron_disabled",
            command="echo 'Manual execution'",
            cron="",  # Manual job
        )
        self.controller.add_job(job)

        # Disable cron
        self.controller.toggle_cron()
        self.assertFalse(self.controller.cron_enabled)

        # Manually start job
        self.controller.start_job(job.name)

        # Wait for completion
        completed = self.wait_for_condition(lambda: job.status != "running", timeout=5)

        self.assertTrue(
            completed, "Manual job should complete even when cron is disabled"
        )

        # Job should have completed successfully
        self.assertEqual(job.status, "idle")
        log_text = "\n".join(job.logs)
        self.assertIn(
            "Manual execution", log_text, "Job should have executed and logged output"
        )

    def test_toggle_cron_logs_to_all_jobs(self):
        """Test that toggling cron logs the action to all jobs"""
        # Add multiple jobs
        for i in range(3):
            job = JobModel(name=f"test_job_{i}", command="echo test", cron="")
            self.controller.add_job(job)

        # Toggle cron to disabled
        self.controller.toggle_cron()

        # Check all jobs have the log entry
        for job in self.controller.jobs.values():
            log_text = "\n".join(job.logs)
            self.assertIn(
                "Cron scheduler DISABLED",
                log_text,
                f"Job {job.name} should have cron disabled log entry",
            )

        # Toggle back to enabled
        self.controller.toggle_cron()

        # Check all jobs have the enabled log entry
        for job in self.controller.jobs.values():
            log_text = "\n".join(job.logs)
            self.assertIn(
                "Cron scheduler ENABLED",
                log_text,
                f"Job {job.name} should have cron enabled log entry",
            )

    def test_toggle_cron_thread_safety(self):
        """Test that toggle_cron is thread-safe"""
        toggle_count = 20
        results = []

        def toggle_worker():
            """Worker function to toggle cron"""
            result = self.controller.toggle_cron()
            results.append(result)

        # Create multiple threads that toggle cron simultaneously
        threads = [Thread(target=toggle_worker) for _ in range(toggle_count)]

        # Start all threads
        for thread in threads:
            thread.start()

        # Wait for all threads to complete
        for thread in threads:
            thread.join()

        # Verify we got the expected number of results
        self.assertEqual(
            len(results), toggle_count, "Should have received result from each toggle"
        )

        # Count True and False results
        true_count = sum(1 for r in results if r)
        false_count = sum(1 for r in results if not r)

        # With 20 toggles starting from True, we should have 10 True and 10 False
        # (or 11/9 if we started on an odd toggle)
        self.assertIn(
            true_count, [10, 11], f"Expected 10 or 11 True results, got {true_count}"
        )
        self.assertIn(
            false_count, [9, 10], f"Expected 9 or 10 False results, got {false_count}"
        )

    def test_cron_reenabled_after_disable_allows_triggers(self):
        """Test that re-enabling cron allows jobs to trigger again"""
        # Create a job that triggers every minute
        job = JobModel(
            name="test_cron_reenable",
            command="echo 'Cron re-enabled test'",
            cron="* * * * *",
        )
        self.controller.add_job(job)

        # Disable cron
        self.controller.toggle_cron()
        self.assertFalse(self.controller.cron_enabled)

        # Wait a bit to ensure no trigger
        time.sleep(2)
        initial_log_count = len(job.logs)

        # Re-enable cron
        self.controller.toggle_cron()
        self.assertTrue(self.controller.cron_enabled)

        # Wait for next minute boundary (up to 65 seconds)
        triggered = self.wait_for_condition(
            lambda: "Cron triggered" in "\n".join(job.logs), timeout=65
        )

        self.assertTrue(triggered, "Job should trigger after cron is re-enabled")

        # Verify the job actually ran
        final_log_count = len(job.logs)
        self.assertGreater(
            final_log_count,
            initial_log_count,
            "Job logs should have increased after re-enabling cron",
        )


def run_tests():
    """Run all tests with verbose output"""
    # Create test suite
    loader = unittest.TestLoader()
    suite = loader.loadTestsFromTestCase(TestJobOrchestrator)

    # Run with verbose output
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    # Print summary
    print("\n" + "=" * 70)
    print("TEST SUMMARY")
    print("=" * 70)
    print(f"Tests run: {result.testsRun}")
    print(f"Successes: {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    print("=" * 70)

    return result.wasSuccessful()


if __name__ == "__main__":
    import sys

    success = run_tests()
    sys.exit(0 if success else 1)
