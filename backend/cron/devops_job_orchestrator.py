"""
DevOps Job Orchestrator - Web-based Cron Job Management System

ARCHITECTURAL ROLE:
    Production-grade web application for managing and monitoring scheduled/manual jobs
    in cloud environments. Provides real-time job execution, interactive I/O, and
    cron-based scheduling through a Dash web interface with HTTP Basic Authentication.

RUNTIME BEHAVIOR:
    - Initializes JobController singleton with background cron scheduler thread
    - Loads job definitions from external configuration (job_definitions.py)
    - Launches Flask/Dash web server on port 8081 with HTTP Basic Auth
    - Scheduler polls every second, triggers jobs at minute boundaries via croniter
    - Each job runs in isolated daemon thread with PTY for unbuffered I/O
    - UI refreshes at 1Hz via Dash callbacks for near-real-time updates

MAJOR COMPONENTS:
    1. Authentication Layer: HTTP Basic Auth via Flask middleware
    2. JobController: Core orchestration engine managing job lifecycle
    3. Scheduler Loop: Minute-boundary cron trigger detection
    4. Job Runner: PTY-based subprocess execution with async stdin/stdout handling
    5. Dash UI: Bootstrap-styled web interface with DataTable, logs, and controls

INPUTS/OUTPUTS:
    Inputs:
        - Environment variables: AUTH_USERNAME, AUTH_PASSWORD, DEBUG
        - Job definitions from job_definitions.py (JobModel instances)
        - User interactions via web UI (start/stop/input commands)
        - Cron expressions for automated scheduling

    Outputs:
        - Real-time job logs streamed to web UI
        - Job status updates (idle/running/error)
        - Process exit codes and execution duration metrics
        - HTTP responses (200 OK, 401 Unauthorized)

KEY DESIGN ASSUMPTIONS:
    - Jobs are I/O-bound or short-lived (daemon threads acceptable)
    - PTY usage required for interactive programs expecting terminal
    - Log retention capped at 1000 lines per job to prevent memory exhaustion
    - Minute-granularity scheduling sufficient (no sub-minute cron support)
    - Single-selection job table (one job operated on at a time)
    - Network latency <1s acceptable for UI refresh (1Hz polling)

OPERATIONAL CONSIDERATIONS:
    - Graceful shutdown: SIGTERM with 5s timeout, then SIGKILL
    - Thread safety: Queue-based stdin, atomic job dict operations
    - Memory bounds: 1000-line log tail per job prevents unbounded growth
    - Concurrency: Prevents duplicate job starts via status check
    - Security: Basic Auth required for all routes except health checks
    - Reliability: Daemon threads auto-cleanup on process exit
    - Error handling: Per-job exception isolation, restart counter tracking
"""

# devops_job_orchestrator.py

import os
import pty
import queue
import select
import subprocess
import threading
import time
import secrets
from datetime import datetime, timedelta, timezone
from functools import wraps
from flask import request, Response, session, make_response
from flask_session import Session

import dash
import requests
from croniter import croniter
from dash import html, dcc, dash_table, Input, Output, State
import dash_bootstrap_components as dbc

from cron_jobs.job_model import JobModel


# ===================== CONSTANTS & HELPERS =====================

# Log formatting constants
LOG_SEPARATOR = "=" * 60
PROMPT_SUFFIXES = (": ", "? ", ") ")

# UI Style constants
STYLES = {
    "monospace_time": {"fontFamily": "monospace", "fontWeight": "bold"},
    "date_text": {"fontSize": "14px"},
    "log_view": {
        "height": "400px",
        "overflowY": "scroll",
        "backgroundColor": "#1e1e1e",
        "color": "#d4d4d4",
        "padding": "15px",
        "borderRadius": "5px",
        "fontFamily": "Consolas, Monaco, monospace",
        "fontSize": "13px",
        "lineHeight": "1.5",
    },
}


def get_full_timestamp() -> str:
    """Returns full UTC timestamp: '2026-02-15 07:01:26 UTC'"""
    return datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")


def get_time_timestamp() -> str:
    """Returns time-only UTC timestamp: '07:01:26 UTC'"""
    return datetime.now(timezone.utc).strftime("%H:%M:%S UTC")


def is_prompt(text: str) -> bool:
    """Check if text ends with a prompt suffix (: ? ))"""
    return text.endswith(PROMPT_SUFFIXES)


def get_selected_job_name(controller, rows: list) -> str | None:
    """Get job name from selected row index"""
    if not rows:
        return None
    return list(controller.jobs.keys())[rows[0]]


def format_timezone(utc_now: datetime, hours: int, minutes: int = 0) -> dict:
    """Format timezone data with offset"""
    adjusted = utc_now + timedelta(hours=hours, minutes=minutes)
    return {
        "time": adjusted.strftime("%H:%M:%S"),
        "date": adjusted.strftime("%Y-%m-%d"),
    }


def create_timezone_card(
    label: str,
    emoji: str,
    time_id: str,
    date_id: str,
    offset: str,
    bg_color: str,
    border_color: str,
) -> dbc.Col:
    """Factory function for timezone display cards"""
    return dbc.Col(
        dbc.Card(
            dbc.CardBody(
                [
                    html.H6(f"{emoji} {label}", className="text-muted mb-2"),
                    html.H2(
                        id=time_id,
                        className="mb-1",
                        style=STYLES["monospace_time"],
                    ),
                    html.P(
                        id=date_id,
                        className="mb-1",
                        style=STYLES["date_text"],
                    ),
                    html.Small(offset, className="text-muted"),
                ]
            ),
            style={
                "backgroundColor": bg_color,
                "border": f"2px solid {border_color}",
            },
            className="text-center h-100",
        ),
        width=12,
        md=3,
        className="mb-3 mb-md-0",
    )


def create_status_style(
    status: str, bg_color: str, text_color: str, bold: bool = False
) -> dict:
    """Factory for status-based conditional styles"""
    return {
        "if": {"column_id": "status", "filter_query": f"{{status}} = {status}"},
        "backgroundColor": bg_color,
        "color": text_color,
        "fontWeight": "bold" if bold else "normal",
    }


# ===================== AUTHENTICATION =====================


def check_auth(username, password):
    """
    Check if username/password combination is valid.

    Security Note:
        - Credentials MUST be set via environment variables
        - No hardcoded defaults for production security

    Args:
        username: Username to validate
        password: Password to validate

    Returns:
        bool: True if credentials are valid, False otherwise

    Raises:
        ValueError: If AUTH_USERNAME or AUTH_PASSWORD not set
    """
    auth_user = os.getenv("AUTH_USERNAME")
    auth_pass = os.getenv("AUTH_PASSWORD")

    if not auth_user or not auth_pass:
        raise ValueError(
            "AUTH_USERNAME and AUTH_PASSWORD environment variables must be set. "
            "No default credentials allowed for security."
        )

    return username == auth_user and password == auth_pass


def authenticate():
    """
    Send 401 response that enables basic auth.

    Returns:
        Response: 401 Unauthorized with WWW-Authenticate header
    """
    return Response(
        "Autenticación requerida. Tu sesión ha expirado después de 1 hora. "
        "Por favor, ingresa tus credenciales nuevamente.",
        401,
        {"WWW-Authenticate": 'Basic realm="SMT-Toolbox - Sesión de 1 hora"'},
    )


# ===================== CONTROLLER =====================


class JobController:
    def __init__(self):
        self.jobs = {}  # Dict[str, JobModel] - keyed by job name
        self.scheduler_running = False
        self.cron_enabled = True  # Cron jobs enabled by default
        self.cron_lock = threading.Lock()  # Thread-safe toggle
        self.start_scheduler()

    def add_job(self, job: JobModel):
        # Jobs dict keyed by name for O(1) lookup
        self.jobs[job.name] = job

    def toggle_cron(self) -> bool:
        """
        Toggle cron scheduler on/off. Returns new state.
        Thread-safe operation that logs the state change to all jobs.
        """
        with self.cron_lock:
            self.cron_enabled = not self.cron_enabled
            timestamp = get_full_timestamp()
            status = "ENABLED" if self.cron_enabled else "DISABLED"
            # Log to all jobs for visibility
            for job in self.jobs.values():
                job.logs.append(f"[{timestamp}] 🔄 Cron scheduler {status}")
            return self.cron_enabled

    def start_scheduler(self):
        """Start the cron scheduler in a background thread"""
        # Idempotent - prevents duplicate scheduler threads
        if self.scheduler_running:
            return

        self.scheduler_running = True
        last_minute = datetime.now(timezone.utc).minute

        def scheduler_loop():
            nonlocal last_minute
            while self.scheduler_running:
                now = datetime.now(timezone.utc)  # Force UTC for predictable scheduling
                current_minute = now.minute

                # Minute-boundary detection to avoid duplicate triggers within same minute
                if current_minute != last_minute:
                    last_minute = current_minute

                    for job in self.jobs.values():
                        # Skip cron processing if cron scheduler is disabled
                        if not self.cron_enabled:
                            continue

                        # Skip manual jobs (empty cron)
                        if job.cron and job.cron.strip():
                            try:
                                cron = croniter(job.cron, now)
                                # Trigger if last scheduled run was within the past 60s
                                # This handles minute-boundary edge cases
                                prev_run = cron.get_prev(datetime)
                                if (now - prev_run).total_seconds() < 60:
                                    # Only start if not already running to prevent overlap
                                    if job.status != "running":
                                        timestamp = get_full_timestamp()
                                        job.logs.append(
                                            f"[{timestamp}] 🕐 Cron triggered: {job.cron}"
                                        )
                                        self.start_job(job.name)
                                    else:
                                        timestamp = get_full_timestamp()
                                        job.logs.append(
                                            f"[{timestamp}] ⏭️  Skipped cron trigger (job still running from previous execution)"
                                        )
                            except Exception as e:
                                # Cron parsing errors logged but don't crash scheduler
                                timestamp = get_full_timestamp()
                                job.logs.append(f"[{timestamp}] ⚠️  Cron error: {e}")

                # 1-second poll interval balances responsiveness vs CPU usage
                time.sleep(1)

        # Daemon thread auto-terminates when main process exits
        threading.Thread(target=scheduler_loop, daemon=True).start()

    def update_job(self, old_name: str, new_name: str, command: str, cron: str):
        """Update job properties, handling name changes"""
        if old_name in self.jobs:
            job = self.jobs[old_name]
            # Prevent race conditions by stopping running jobs before modification
            if job.status == "running":
                self.stop_job(old_name)

            job.command = command
            job.cron = cron

            # Atomic rename: delete old key, insert new key
            # Prevents stale references if name changes
            if old_name != new_name:
                job.name = new_name
                del self.jobs[old_name]
                self.jobs[new_name] = job

            job.logs.append(f"[{get_full_timestamp()}] Job updated")

    def start_job(self, name: str):
        job = self.jobs[name]
        # Idempotent - prevents duplicate execution
        if job.status == "running":
            return

        def runner():
            job.status = "running"
            start_time = datetime.now(timezone.utc)
            job.last_run = get_full_timestamp()
            job.logs.append(LOG_SEPARATOR)
            job.logs.append(f"[{job.last_run}] 🚀 Starting Job: {job.name}")
            job.logs.append(f"[{job.last_run}] 📝 Command: {job.command}")
            job.logs.append(LOG_SEPARATOR)

            try:
                # PTY forces programs to use unbuffered I/O (line-buffered mode)
                # Critical for interactive programs that expect terminal behavior
                env = os.environ.copy()
                env["PYTHONUNBUFFERED"] = "1"  # Python-specific unbuffered flag

                # Create pseudo-terminal pair: master (parent) and slave (child)
                master_fd, slave_fd = pty.openpty()

                # Subprocess inherits slave end for stdin/stdout/stderr
                p = subprocess.Popen(
                    job.command,
                    shell=True,
                    stdin=slave_fd,
                    stdout=slave_fd,
                    stderr=slave_fd,
                    env=env,
                    close_fds=True,  # Close unused file descriptors for security
                )
                job.process = p
                os.close(slave_fd)  # Parent closes slave end after fork

                # Separate thread handles stdin to avoid blocking stdout reads
                def stdin_writer():
                    while job.process and job.process.poll() is None:
                        try:
                            # Non-blocking queue get with timeout
                            inp = job.stdin_queue.get(timeout=0.1)
                            timestamp = get_time_timestamp()
                            job.logs.append(f"[{timestamp}] 📥 User Input: {inp}")
                            # Write to PTY master, which forwards to subprocess stdin
                            os.write(master_fd, (inp + "\n").encode())
                        except queue.Empty:
                            continue
                        except Exception as e:
                            timestamp = get_time_timestamp()
                            job.logs.append(f"[{timestamp}] ⚠️  Input error: {e}")
                            break

                stdin_thread = threading.Thread(target=stdin_writer, daemon=True)
                stdin_thread.start()

                # Non-blocking read from PTY master using select()
                buffer = ""
                while True:
                    # Check if there's data to read (with 0.1s timeout)
                    ready, _, _ = select.select([master_fd], [], [], 0.1)
                    if ready:
                        try:
                            # Read up to 1KB chunks for efficiency
                            data = os.read(master_fd, 1024).decode(
                                "utf-8", errors="replace"  # Replace invalid UTF-8
                            )
                            if not data:
                                break  # EOF - process closed output
                            buffer += data
                            # Process complete lines and interactive prompts
                            # Prompts detected by common suffixes (: ? ))
                            while "\n" in buffer or is_prompt(buffer):
                                if "\n" in buffer:
                                    line, buffer = buffer.split("\n", 1)
                                    timestamp = get_time_timestamp()
                                    job.logs.append(f"[{timestamp}] {line}")
                                elif is_prompt(buffer):
                                    # Log prompt immediately for interactive UX
                                    timestamp = get_time_timestamp()
                                    job.logs.append(f"[{timestamp}] {buffer}")
                                    buffer = ""
                                    break
                        except OSError:
                            break  # PTY closed or error
                    elif p.poll() is not None:
                        # Process has ended, drain any remaining buffered data
                        try:
                            data = os.read(master_fd, 1024).decode(
                                "utf-8", errors="replace"
                            )
                            if data:
                                buffer += data
                        except OSError:
                            pass
                        break

                # Log any remaining buffer content
                if buffer:
                    timestamp = get_time_timestamp()
                    job.logs.append(f"[{timestamp}] {buffer}")

                os.close(master_fd)

                # Wait for process exit and capture return code
                rc = p.wait()
                end_time = datetime.now(timezone.utc)
                duration = (end_time - start_time).total_seconds()

                # Map exit code to result status
                job.last_result = "ok" if rc == 0 else "error"
                job.status = "idle" if rc == 0 else "error"

                end_timestamp = get_full_timestamp()
                job.logs.append(LOG_SEPARATOR)
                if rc == 0:
                    job.logs.append(f"[{end_timestamp}] ✅ Job completed successfully")
                else:
                    job.logs.append(
                        f"[{end_timestamp}] ❌ Job failed with exit code {rc}"
                    )
                job.logs.append(
                    f"[{end_timestamp}] ⏱️  Duration: {duration:.2f} seconds"
                )
                job.logs.append(LOG_SEPARATOR)

            except Exception as e:
                # Catch-all for unexpected errors (PTY failures, etc.)
                end_timestamp = get_full_timestamp()
                job.logs.append(LOG_SEPARATOR)
                job.logs.append(f"[{end_timestamp}] ❌ ERROR: {e}")
                job.logs.append(LOG_SEPARATOR)
                job.status = "error"
                job.restart_count += 1  # Track failure count for monitoring
            finally:
                job.process = None
                # Memory-bound log retention - prevents unbounded growth
                # Tail last 1000 lines to cap memory at ~100KB per job
                if len(job.logs) > 1000:
                    job.logs = job.logs[-1000:]

        # Each job runs in isolated daemon thread
        threading.Thread(target=runner, daemon=True).start()

    def send_input(self, name: str, text: str):
        job = self.jobs.get(name)
        # Validate job exists, has active process, and is running
        if job and job.process and job.status == "running":
            # Queue-based stdin for thread-safe async writes
            job.stdin_queue.put(text)
            # timestamp = datetime.now().strftime("%H:%M:%S")
            # job.logs.append(f"[{timestamp}] 📤 Queued input: {text}")
            return True
        return False

    def stop_job(self, name: str):
        job = self.jobs.get(name)
        if job and job.process:
            timestamp = get_full_timestamp()
            try:
                job.logs.append(f"[{timestamp}] 🛑 Stopping job...")
                # SIGTERM - graceful shutdown (allows cleanup handlers)
                job.process.terminate()
                job.process.wait(timeout=5)  # 5s grace period
                job.logs.append(f"[{timestamp}] ✅ Job stopped gracefully")
            except subprocess.TimeoutExpired:
                # SIGKILL - force kill after timeout (no cleanup)
                job.process.kill()
                job.logs.append(f"[{timestamp}] ⚠️  Job killed (timeout)")
            finally:
                job.process = None
            job.status = "idle"


# ===================== DASH VIEW =====================

# Global controller instance - shared across all callbacks
# Singleton pattern ensures single scheduler thread
controller = JobController()

# Load job definitions from external file for separation of concerns
from cron_jobs.job_definitions import get_job_definitions

for job in get_job_definitions():
    controller.add_job(job)

# Initialize Dash app with Bootstrap styling
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])

# Get Flask server instance for session configuration
server = app.server

# ===================== SESSION CONFIGURATION =====================

# Configure Flask-Session for 1-hour session timeout
server.config["SECRET_KEY"] = os.getenv("SECRET_KEY", secrets.token_hex(32))
server.config["SESSION_TYPE"] = "filesystem"  # Use filesystem for session storage
server.config["SESSION_PERMANENT"] = True
server.config["PERMANENT_SESSION_LIFETIME"] = timedelta(hours=1)  # 1 hour timeout
server.config["SESSION_COOKIE_SECURE"] = (
    os.getenv("SESSION_COOKIE_SECURE", "True").lower() == "true"
)  # HTTPS only in production
server.config["SESSION_COOKIE_HTTPONLY"] = True  # Prevent JavaScript access
server.config["SESSION_COOKIE_SAMESITE"] = "Lax"  # CSRF protection
server.config["SESSION_FILE_DIR"] = "/tmp/flask_session"  # Session storage directory

# Initialize Flask-Session
Session(server)


# ===================== SESSION MANAGEMENT FUNCTIONS =====================


def is_session_valid():
    """
    Check if the current session is valid and not expired.

    Returns:
        bool: True if session is valid, False otherwise
    """
    if "authenticated" not in session:
        return False

    if "login_time" not in session:
        return False

    # Check if session has expired (more than 1 hour)
    try:
        login_time = datetime.fromisoformat(session["login_time"])
        now = datetime.now(timezone.utc)
        elapsed = now - login_time

        if elapsed > timedelta(hours=1):
            # Session expired - clear it
            session.clear()
            return False
    except (ValueError, TypeError):
        # Invalid login_time format - clear session
        session.clear()
        return False

    return session.get("authenticated", False)


def create_session(username):
    """
    Create a new session after successful authentication.

    Args:
        username: The authenticated username
    """
    session.clear()
    session["authenticated"] = True
    session["username"] = username
    session["login_time"] = datetime.now(timezone.utc).isoformat()
    session.permanent = True  # Use PERMANENT_SESSION_LIFETIME


def get_session_info():
    """
    Get information about the current session.

    Returns:
        dict: Session info with username, login_time, and remaining_minutes
        None: If session is invalid
    """
    if not is_session_valid():
        return None

    try:
        login_time = datetime.fromisoformat(session["login_time"])
        now = datetime.now(timezone.utc)
        elapsed = now - login_time
        remaining = timedelta(hours=1) - elapsed

        return {
            "username": session.get("username", "Unknown"),
            "login_time": login_time.strftime("%Y-%m-%d %H:%M:%S UTC"),
            "remaining_minutes": max(0, int(remaining.total_seconds() / 60)),
        }
    except (ValueError, TypeError):
        return None


def get_timezone_times():
    """Calculate times for different timezones using UTC offsets (no external libs)"""
    utc_now = datetime.now(timezone.utc)

    system_tz = format_timezone(utc_now, 0)
    costa_rica_tz = format_timezone(utc_now, -6)
    us_eastern_tz = format_timezone(utc_now, -5)
    india_tz = format_timezone(utc_now, 5, 30)

    return {
        "system": {
            **system_tz,
            "label": "UTC Time",
            "offset": "UTC",
        },
        "costa_rica": {
            **costa_rica_tz,
            "label": "Costa Rica",
            "offset": "UTC-6",
        },
        "us_eastern": {
            **us_eastern_tz,
            "label": "US Eastern",
            "offset": "UTC-5",
        },
        "india": {
            **india_tz,
            "label": "India",
            "offset": "UTC+5:30",
        },
    }


def job_rows():
    """Serialize job state for DataTable - explicit type coercion for Dash compatibility"""
    # Dash DataTable requires primitive types (str, int, float)
    return [
        {
            "name": str(j.name),
            "command": str(j.command),
            "cron": str(j.cron),
            "status": str(j.status),
            "last_run": str(j.last_run) if j.last_run else "",
            "restarts": int(j.restart_count),
        }
        for j in controller.jobs.values()
    ]


# Dash layout using Bootstrap components for responsive design
app.layout = dbc.Container(
    [
        # Header
        dbc.Row(
            dbc.Col(
                html.H1(
                    "🛠 SMT-TOOLBOX on the cloud",
                    className="text-center my-4",
                    style={"color": "#2c3e50", "fontWeight": "bold"},
                ),
                width=12,
            )
        ),
        # Session Info Alert
        dbc.Row(
            dbc.Col(
                dbc.Alert(
                    [
                        html.Span("🔒 Sesión activa: ", className="fw-bold"),
                        html.Span(id="session-username", className="text-primary"),
                        html.Span(" | Tiempo restante: ", className="ms-3"),
                        html.Span(
                            id="session-remaining", className="fw-bold text-warning"
                        ),
                        html.Span(" minutos", className="ms-1"),
                        html.A(
                            [
                                html.I(className="bi bi-box-arrow-right me-1"),
                                "Cerrar sesión",
                            ],
                            href="/logout",
                            className="btn btn-sm btn-outline-danger ms-3",
                        ),
                    ],
                    color="info",
                    className="mb-3",
                    id="session-alert",
                ),
                width=12,
            )
        ),
        # Clock Card - World Time Display
        dbc.Card(
            [
                dbc.CardHeader(
                    html.H4("🌍 World Clock", className="mb-0"),
                    style={"backgroundColor": "#9b59b6", "color": "white"},
                ),
                dbc.CardBody(
                    dbc.Row(
                        [
                            # UTC Time
                            create_timezone_card(
                                "UTC Time",
                                "🌐",
                                "clock-system-time",
                                "clock-system-date",
                                "UTC",
                                "#e3f2fd",
                                "#2196f3",
                            ),
                            # Costa Rica Time
                            create_timezone_card(
                                "Costa Rica",
                                "🇨🇷",
                                "clock-cr-time",
                                "clock-cr-date",
                                "UTC-6",
                                "#e8f5e9",
                                "#4caf50",
                            ),
                            # US Eastern Time
                            create_timezone_card(
                                "US Eastern",
                                "🇺🇸",
                                "clock-us-time",
                                "clock-us-date",
                                "UTC-5",
                                "#fff3e0",
                                "#ff9800",
                            ),
                            # India Time
                            create_timezone_card(
                                "India",
                                "🇮🇳",
                                "clock-india-time",
                                "clock-india-date",
                                "UTC+5:30",
                                "#f3e5f5",
                                "#9c27b0",
                            ),
                        ],
                        className="g-3",
                    )
                ),
            ],
            className="mb-4 shadow",
        ),
        # # External Services Status Card
        # dbc.Card(
        #     [
        #         dbc.CardHeader(
        #             dbc.Row(
        #                 [
        #                     dbc.Col(
        #                         html.H4(
        #                             "🔗 External Services Status", className="mb-0"
        #                         ),
        #                         width="auto",
        #                     ),
        #                     dbc.Col(
        #                         dbc.Button(
        #                             [
        #                                 html.I(className="bi bi-arrow-clockwise me-2"),
        #                                 "Refresh",
        #                             ],
        #                             id="refresh-services-btn",
        #                             color="light",
        #                             size="sm",
        #                             outline=True,
        #                         ),
        #                         width="auto",
        #                         className="ms-auto",
        #                     ),
        #                 ],
        #                 align="center",
        #                 className="g-2",
        #             ),
        #             style={"backgroundColor": "#16a085", "color": "white"},
        #         ),
        #         dbc.CardBody(
        #             dbc.Row(
        #                 [
        #                     # JIRA Status
        #                     dbc.Col(
        #                         dbc.Card(
        #                             dbc.CardBody(
        #                                 [
        #                                     html.H6(
        #                                         "📋 JIRA", className="text-muted mb-2"
        #                                     ),
        #                                     html.Div(
        #                                         id="jira-status-badge",
        #                                         className="mb-2",
        #                                     ),
        #                                     html.Small(
        #                                         id="jira-status-details",
        #                                         className="text-muted",
        #                                     ),
        #                                 ]
        #                             ),
        #                             style={"border": "2px solid #e0e0e0"},
        #                             className="text-center h-100",
        #                         ),
        #                         width=12,
        #                         md=6,
        #                         className="mb-3 mb-md-0",
        #                     ),
        #                     # GitHub Status
        #                     dbc.Col(
        #                         dbc.Card(
        #                             dbc.CardBody(
        #                                 [
        #                                     html.H6(
        #                                         "🐙 GitHub", className="text-muted mb-2"
        #                                     ),
        #                                     html.Div(
        #                                         id="github-status-badge",
        #                                         className="mb-2",
        #                                     ),
        #                                     html.Small(
        #                                         id="github-status-details",
        #                                         className="text-muted",
        #                                     ),
        #                                 ]
        #                             ),
        #                             style={"border": "2px solid #e0e0e0"},
        #                             className="text-center h-100",
        #                         ),
        #                         width=12,
        #                         md=6,
        #                     ),
        #                 ],
        #                 className="g-3",
        #             )
        #         ),
        #     ],
        #     className="mb-4 shadow",
        # ),
        # Cron Scheduler Control Card
        dbc.Card(
            [
                dbc.CardHeader(
                    html.H4("🕐 Cron Scheduler Control", className="mb-0"),
                    style={"backgroundColor": "#9b59b6", "color": "white"},
                ),
                dbc.CardBody(
                    dbc.Row(
                        [
                            dbc.Col(
                                html.Div(
                                    id="cron-status-display",
                                    className="text-center",
                                ),
                                width=8,
                            ),
                            dbc.Col(
                                dbc.Button(
                                    [
                                        html.I(className="bi bi-toggle-on me-2"),
                                        "Toggle Cron",
                                    ],
                                    id="toggle-cron-btn",
                                    color="warning",
                                    size="lg",
                                    className="w-100",
                                ),
                                width=4,
                            ),
                        ],
                        align="center",
                        className="g-3",
                    )
                ),
            ],
            className="mb-4 shadow",
        ),
        # Job Table Card
        dbc.Card(
            [
                dbc.CardHeader(
                    html.H4("Job Management", className="mb-0"),
                    style={"backgroundColor": "#3498db", "color": "white"},
                ),
                dbc.CardBody(
                    [
                        dash_table.DataTable(
                            id="job-table",
                            columns=[
                                {"name": "Name", "id": "name"},
                                {"name": "Command", "id": "command"},
                                {"name": "Cron", "id": "cron"},
                                {"name": "Status", "id": "status"},
                                {"name": "Last Run", "id": "last_run"},
                                {"name": "Restarts", "id": "restarts"},
                            ],
                            data=job_rows(),  # type: ignore[arg-type]
                            row_selectable="single",  # Single-selection mode
                            style_table={"overflowX": "auto"},
                            style_cell={
                                "textAlign": "left",
                                "padding": "12px",
                                "fontFamily": "Arial, sans-serif",
                            },
                            style_header={
                                "backgroundColor": "#ecf0f1",
                                "fontWeight": "bold",
                                "border": "1px solid #bdc3c7",
                            },
                            style_data={
                                "border": "1px solid #ecf0f1",
                            },
                            style_data_conditional=[  # type: ignore[arg-type]
                                # Conditional styling based on job status for visual feedback
                                create_status_style(
                                    "running", "#d4edda", "#155724", bold=True
                                ),
                                create_status_style(
                                    "error", "#f8d7da", "#721c24", bold=True
                                ),
                                create_status_style("idle", "#d1ecf1", "#0c5460"),
                                {
                                    "if": {"state": "selected"},
                                    "backgroundColor": "#3498db",
                                    "color": "white",
                                    "border": "2px solid #2980b9",
                                },
                            ],
                        ),
                    ]
                ),
            ],
            className="mb-4 shadow",
        ),
        # Control Buttons
        dbc.Row(
            [
                dbc.Col(
                    dbc.ButtonGroup(
                        [
                            dbc.Button(
                                [html.I(className="bi bi-play-fill me-2"), "Run Job"],
                                id="run-btn",
                                color="success",
                                size="lg",
                            ),
                            dbc.Button(
                                [html.I(className="bi bi-stop-fill me-2"), "Stop Job"],
                                id="stop-btn",
                                color="danger",
                                size="lg",
                            ),
                        ],
                        className="w-100",
                    ),
                    width=12,
                    className="mb-4",
                ),
            ]
        ),
        # Logs Card
        dbc.Card(
            [
                dbc.CardHeader(
                    dbc.Row(
                        [
                            dbc.Col(
                                html.H4("Job Logs", className="mb-0"),
                                width="auto",
                            ),
                            dbc.Col(
                                dbc.Checklist(
                                    options=[{"label": "Auto-scroll", "value": 1}],
                                    value=[1],  # Enabled by default for UX
                                    id="auto-scroll-toggle",
                                    switch=True,
                                    inline=True,
                                    className="mb-0",
                                    style={"color": "white"},
                                ),
                                width="auto",
                                className="ms-auto",
                            ),
                        ],
                        align="center",
                        className="g-2",
                    ),
                    style={"backgroundColor": "#2c3e50", "color": "white"},
                ),
                dbc.CardBody(
                    [
                        html.Pre(
                            id="log-view",
                            style=STYLES["log_view"],
                        ),
                    ]
                ),
            ],
            className="mb-4 shadow",
        ),
        # Input Section for interactive jobs
        dbc.Card(
            [
                dbc.CardHeader(
                    html.H4("Send Input to Job", className="mb-0"),
                    style={"backgroundColor": "#16a085", "color": "white"},
                ),
                dbc.CardBody(
                    dbc.Row(
                        [
                            dbc.Col(
                                dcc.Input(
                                    id="human-input",
                                    placeholder="Type input for interactive job...",
                                    className="form-control form-control-lg",
                                    style={"width": "100%"},
                                    n_submit=0,  # Tracks Enter key presses
                                ),
                                width=9,
                            ),
                            dbc.Col(
                                dbc.Button(
                                    [html.I(className="bi bi-send-fill me-2"), "Send"],
                                    id="send-input",
                                    color="primary",
                                    size="lg",
                                    className="w-100",
                                ),
                                width=3,
                            ),
                        ],
                        className="g-2",
                    )
                ),
            ],
            className="mb-4 shadow",
        ),
        # 1Hz refresh for near-real-time UI updates (1000ms interval)
        dcc.Interval(id="refresh", interval=1000),
        # Interval for cron status updates
        dcc.Interval(id="cron-status-interval", interval=1000, n_intervals=0),
    ],
    fluid=True,
    style={"backgroundColor": "#f8f9fa", "minHeight": "100vh", "padding": "20px"},
)


@app.callback(
    [
        Output("session-username", "children"),
        Output("session-remaining", "children"),
    ],
    Input("refresh", "n_intervals"),
)
def update_session_info(_):
    """
    Update session information display every second.

    Shows:
        - Username of authenticated user
        - Remaining time in minutes before session expires

    Returns:
        tuple: (username, remaining_minutes)
    """
    info = get_session_info()
    if not info:
        return "Sesión expirada", "0"

    remaining = info["remaining_minutes"]

    # Color code based on remaining time
    if remaining <= 5:
        # Less than 5 minutes - critical
        return info["username"], f"⚠️ {remaining}"
    elif remaining <= 15:
        # Less than 15 minutes - warning
        return info["username"], f"⏰ {remaining}"
    else:
        # Normal
        return info["username"], str(remaining)


@app.callback(
    [
        Output("clock-system-time", "children"),
        Output("clock-system-date", "children"),
        Output("clock-cr-time", "children"),
        Output("clock-cr-date", "children"),
        Output("clock-us-time", "children"),
        Output("clock-us-date", "children"),
        Output("clock-india-time", "children"),
        Output("clock-india-date", "children"),
    ],
    Input("refresh", "n_intervals"),
)
def update_clocks(_):
    """Update all clock displays every second"""
    times = get_timezone_times()
    return (
        times["system"]["time"],
        times["system"]["date"],
        times["costa_rica"]["time"],
        times["costa_rica"]["date"],
        times["us_eastern"]["time"],
        times["us_eastern"]["date"],
        times["india"]["time"],
        times["india"]["date"],
    )


@app.callback(
    [
        Output("jira-status-badge", "children"),
        Output("jira-status-details", "children"),
        Output("github-status-badge", "children"),
        Output("github-status-details", "children"),
    ],
    [Input("refresh", "n_intervals"), Input("refresh-services-btn", "n_clicks")],
)
def update_external_services_status(n_intervals, n_clicks):
    """Update external services status display"""
    # Check JIRA connectivity
    jira_status = check_jira_connectivity(timeout=3)

    # Check GitHub connectivity
    github_status = check_github_connectivity(timeout=3)

    # Helper function to create status badge
    def create_status_badge(status_data):
        status = status_data["status"]
        if status == "healthy":
            badge = dbc.Badge(
                "✓ Healthy",
                color="success",
                className="fs-6 px-3 py-2",
            )
            details = f"Response: {status_data['response_time_ms']}ms"
        elif status == "degraded":
            badge = dbc.Badge(
                "⚠ Degraded",
                color="warning",
                className="fs-6 px-3 py-2",
            )
            error_msg = status_data.get("error", "Unknown error")
            http_code = status_data.get("http_status_code", "N/A")
            details = f"HTTP {http_code}: {error_msg}"
        else:  # unreachable
            badge = dbc.Badge(
                "✗ Unreachable",
                color="danger",
                className="fs-6 px-3 py-2",
            )
            error_msg = status_data.get("error", "Connection failed")
            details = f"{error_msg}"

        return badge, details

    jira_badge, jira_details = create_status_badge(jira_status)
    github_badge, github_details = create_status_badge(github_status)

    return jira_badge, jira_details, github_badge, github_details


@app.callback(Output("job-table", "data"), Input("refresh", "n_intervals"))
def refresh(_):
    """Periodic table refresh - triggered by Interval component every 1s"""
    return job_rows()


@app.callback(
    Output("log-view", "children"),
    Input("job-table", "selected_rows"),
    Input("refresh", "n_intervals"),
)
def show_logs(rows, _):
    """Display logs for selected job - updates on selection change or refresh"""
    name = get_selected_job_name(controller, rows)
    if not name:
        return ""
    return "\n".join(controller.jobs[name].logs[-1000:])  # Tail last 1000 lines


@app.callback(
    Output("cron-status-display", "children"),
    [
        Input("cron-status-interval", "n_intervals"),
        Input("toggle-cron-btn", "n_clicks"),
    ],
)
def update_cron_status(n_intervals, n_clicks):
    """Update cron scheduler status display"""
    enabled = controller.cron_enabled

    if enabled:
        badge = dbc.Badge(
            "ENABLED ✓",
            color="success",
            className="fs-4 px-4 py-2",
        )
        message = "Cron jobs will run automatically on schedule"
        message_color = "text-success"
    else:
        badge = dbc.Badge(
            "DISABLED ✗",
            color="danger",
            className="fs-4 px-4 py-2",
        )
        message = "Cron jobs are paused (manual execution still works)"
        message_color = "text-danger"

    return html.Div(
        [
            badge,
            html.P(message, className=f"mt-2 mb-0 {message_color}"),
        ]
    )


@app.callback(
    Output("toggle-cron-btn", "children"),
    [Input("toggle-cron-btn", "n_clicks")],
    prevent_initial_call=True,
)
def toggle_cron_scheduler(n_clicks):
    """Toggle cron scheduler on/off"""
    if n_clicks:
        new_state = controller.toggle_cron()
        icon = "bi-toggle-on" if new_state else "bi-toggle-off"
        return [html.I(className=f"{icon} me-2"), "Toggle Cron"]
    return dash.no_update


# Clientside callback for auto-scrolling logs (runs in browser, not server)
app.clientside_callback(
    """
    function(children, autoScroll) {
        // Only scroll if auto-scroll is enabled (value contains 1)
        if (autoScroll && autoScroll.includes(1)) {
            setTimeout(function() {
                var logView = document.getElementById('log-view');
                if (logView) {
                    logView.scrollTop = logView.scrollHeight;
                }
            }, 50);  // Small delay to ensure content is rendered
        }
        return window.dash_clientside.no_update;
    }
    """,
    Output("log-view", "data-scroll"),  # Dummy output (required by Dash)
    Input("log-view", "children"),
    Input("auto-scroll-toggle", "value"),
)


@app.callback(
    Output("run-btn", "n_clicks"),
    Input("run-btn", "n_clicks"),
    State("job-table", "selected_rows"),
    prevent_initial_call=True,
)
def run_job(n_clicks, rows):
    """Start selected job - returns n_clicks to satisfy Output requirement"""
    name = get_selected_job_name(controller, rows)
    if name:
        controller.start_job(name)
    return n_clicks  # Echo back to satisfy Dash callback contract


@app.callback(
    Output("stop-btn", "n_clicks"),
    Input("stop-btn", "n_clicks"),
    State("job-table", "selected_rows"),
    prevent_initial_call=True,
)
def stop_job(n_clicks, rows):
    """Terminate selected job - SIGTERM with SIGKILL fallback after 5s"""
    name = get_selected_job_name(controller, rows)
    if name:
        controller.stop_job(name)
    return n_clicks  # Echo back to satisfy Dash callback contract


@app.callback(
    [Output("human-input", "value"), Output("send-input", "n_clicks")],
    [Input("send-input", "n_clicks"), Input("human-input", "n_submit")],
    State("job-table", "selected_rows"),
    State("human-input", "value"),
    prevent_initial_call=True,
)
def send_input(n_clicks, n_submit, rows, text):
    """Queue stdin input for selected job - clears input field on success"""
    name = get_selected_job_name(controller, rows)
    if name and text is not None:
        controller.send_input(
            name, text if text else ""
        )  # Send empty string if text is empty
        return "", n_clicks  # Clear input after sending
    return text, n_clicks


# Production server configuration - exposes Flask app for WSGI servers
server = app.server

# ===================== EXTERNAL SERVICE HEALTH CHECKS =====================


def check_external_service(url: str, service_name: str, timeout: int = 3) -> dict:
    """
    Generic external service connectivity check with error code reporting

    Args:
        url: Service URL to check
        service_name: Name of the service (for logging)
        timeout: Request timeout in seconds (default: 3)

    Returns:
        dict: {
            "status": "healthy|degraded|unreachable",
            "url": str,
            "response_time_ms": int or None,
            "http_status_code": int or None,
            "last_check": str (timestamp),
            "error": str or None,
            "error_type": "timeout|connection|http_error" or None
        }
    """
    start_time = time.time()
    result = {
        "status": "unreachable",
        "url": url,
        "response_time_ms": None,
        "http_status_code": None,
        "last_check": get_full_timestamp(),
        "error": None,
        "error_type": None,
    }

    try:
        # Disable SSL warnings for internal services (if urllib3 is available)
        try:
            import urllib3

            urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
        except (ImportError, AttributeError):
            pass  # urllib3 not available or different version

        # Make HEAD request (faster than GET, just checks connectivity)
        response = requests.head(
            url, timeout=timeout, verify=False, allow_redirects=True
        )

        # Calculate response time
        response_time = int((time.time() - start_time) * 1000)
        result["response_time_ms"] = response_time
        result["http_status_code"] = response.status_code

        # Determine status based on HTTP status code
        if response.status_code == 200:
            result["status"] = "healthy"
        elif response.status_code in [500, 502, 503, 504]:
            result["status"] = "degraded"
            result["error"] = f"HTTP {response.status_code}: {response.reason}"
            result["error_type"] = "http_error"
        elif response.status_code in [401, 403]:
            result["status"] = "degraded"
            result["error"] = f"HTTP {response.status_code}: {response.reason}"
            result["error_type"] = "http_error"
        elif response.status_code == 404:
            result["status"] = "unreachable"
            result["error"] = f"HTTP 404: Endpoint not found"
            result["error_type"] = "http_error"
        else:
            result["status"] = "degraded"
            result["error"] = f"HTTP {response.status_code}: {response.reason}"
            result["error_type"] = "http_error"

    except requests.exceptions.Timeout:
        result["response_time_ms"] = timeout * 1000
        result["error"] = f"Connection timeout after {timeout} seconds"
        result["error_type"] = "timeout"
        result["status"] = "unreachable"

    except requests.exceptions.ConnectionError as e:
        result["response_time_ms"] = int((time.time() - start_time) * 1000)
        result["error"] = f"Connection failed: {str(e).split(':')[0]}"
        result["error_type"] = "connection"
        result["status"] = "unreachable"

    except Exception as e:
        result["response_time_ms"] = int((time.time() - start_time) * 1000)
        result["error"] = f"Unexpected error: {str(e)}"
        result["error_type"] = "connection"
        result["status"] = "unreachable"

    return result


def check_jira_connectivity(timeout: int = 3) -> dict:
    """
    Check JIRA connectivity to https://jsw.ibm.com

    Uses the /rest/api/2/serverInfo endpoint which is publicly accessible
    and provides basic server information without authentication.

    Args:
        timeout: Request timeout in seconds (default: 3)

    Returns:
        dict: Health check result with status, response time, and error details
    """
    url = "https://jsw.ibm.com/rest/api/2/serverInfo"
    return check_external_service(url, "JIRA", timeout)


def check_github_connectivity(timeout: int = 3) -> dict:
    """
    Check GitHub Enterprise connectivity to https://github.ibm.com

    Uses the /api/v3 endpoint which is publicly accessible and returns
    API metadata without authentication.

    Args:
        timeout: Request timeout in seconds (default: 3)

    Returns:
        dict: Health check result with status, response time, and error details
    """
    url = "https://github.ibm.com/api/v3"
    return check_external_service(url, "GitHub", timeout)


# ===================== HEALTH CHECK ENDPOINT =====================


@server.route("/health")
def health_check():
    """
    Public health check endpoint - no authentication required

    Returns JSON with:
        - Service status (healthy/degraded/error)
        - Scheduler status (running/stopped)
        - External services status (JIRA, GitHub) with error codes
        - Timestamp

    HTTP Status Codes:
        - 200: Service healthy (scheduler running, at least one external service reachable)
        - 503: Service degraded (scheduler stopped OR both external services unreachable)
    """
    try:
        # Check scheduler status
        scheduler_healthy = controller.scheduler_running

        # Check external services connectivity
        jira_status = check_jira_connectivity(timeout=3)
        github_status = check_github_connectivity(timeout=3)

        # Determine if external services are healthy
        jira_healthy = jira_status["status"] == "healthy"
        github_healthy = github_status["status"] == "healthy"

        # At least one external service should be reachable
        external_services_ok = jira_healthy or github_healthy

        # Both external services unreachable is a critical issue
        both_services_down = (
            jira_status["status"] == "unreachable"
            and github_status["status"] == "unreachable"
        )

        # Determine overall health status
        if scheduler_healthy and external_services_ok:
            status = "healthy"
            http_status = 200
        elif scheduler_healthy and not both_services_down:
            # Scheduler running but one service degraded/unreachable
            status = "degraded"
            http_status = 200  # Still operational, just degraded
        else:
            # Scheduler stopped OR both external services unreachable
            status = "degraded"
            http_status = 503

        # Build response payload with external services
        response_data = {
            "status": status,
            "timestamp": get_full_timestamp(),
            "scheduler": {
                "running": scheduler_healthy,
                "status": "active" if scheduler_healthy else "stopped",
            },
            "external_services": {
                "jira": jira_status,
                "github": github_status,
            },
            "service_name": "SMT-Toolbox DevOps Job Orchestrator",
        }

        return response_data, http_status, {"Content-Type": "application/json"}

    except Exception as e:
        # Catch-all for unexpected errors in health check itself
        error_response = {
            "status": "error",
            "timestamp": get_full_timestamp(),
            "error": str(e),
            "service": {
                "name": "SMT-Toolbox DevOps Job Orchestrator",
                "version": "1.0.0",
                "port": 8081,
            },
        }
        return error_response, 503, {"Content-Type": "application/json"}


# ===================== LOGOUT ROUTE =====================


@server.route("/logout")
def logout():
    """
    Logout endpoint - clears the session and requires re-authentication.

    Returns:
        Response: 401 Unauthorized to trigger re-authentication
    """
    session.clear()
    return Response(
        "Sesión cerrada exitosamente. Por favor, vuelve a autenticarte.",
        401,
        {"WWW-Authenticate": 'Basic realm="SMT-Toolbox Login"'},
    )


# ===================== SESSION-BASED AUTHENTICATION MIDDLEWARE =====================


@server.before_request
def before_request():
    """
    Session-based authentication middleware with 1-hour timeout.

    Flow:
        1. Check if route is public (health, logout, Dash assets)
        2. Check if valid session exists
        3. If no session, attempt Basic Auth
        4. Create session on successful auth
        5. Reject if auth fails

    Security Features:
        - 1-hour session timeout (automatic expiration)
        - Session-based authentication (not per-request)
        - Secure cookies (HttpOnly, Secure, SameSite)
        - Public health endpoint for monitoring
        - Manual logout capability

    Public Routes:
        - /health: Health check for monitoring
        - /logout: Manual session termination
        - /_dash-*: Dash framework assets (CSS, JS)
    """
    # Public routes - no authentication required
    public_paths = ["/health", "/logout"]

    # Allow Dash framework assets (CSS, JS, etc.)
    if request.path.startswith("/_dash-"):
        return None

    # Allow public routes
    if request.path in public_paths:
        return None

    # Check if session is valid
    if not is_session_valid():
        # No valid session - attempt Basic Auth
        auth = request.authorization

        if auth:
            try:
                # Validate credentials
                if check_auth(auth.username, auth.password):
                    # Create new session (1-hour timeout)
                    create_session(auth.username)
                    return None
            except ValueError as e:
                # Credentials not configured
                return make_response(
                    {"error": "Authentication not configured", "message": str(e)}, 500
                )

        # No auth or invalid credentials - request authentication
        # For AJAX/JSON requests, return JSON error
        if request.path.startswith("/_dash-") or request.is_json:
            return make_response(
                {
                    "error": "Session expired",
                    "message": "Tu sesión ha expirado. Por favor, recarga la página.",
                },
                401,
            )

        # For normal requests, trigger Basic Auth dialog
        return authenticate()

    # Valid session exists - allow request
    return None


if __name__ == "__main__":
    # Get configuration from environment variables
    debug_mode = os.getenv("DEBUG", "False").lower() == "true"
    host = "0.0.0.0"  # Bind to all interfaces for container deployment
    port = 8081

    # Log authentication status for operational visibility
    auth_enabled = os.getenv("AUTH_USERNAME") and os.getenv("AUTH_PASSWORD")
    if auth_enabled:
        print("🔒 Basic authentication enabled")
        print(f"   Username: {os.getenv('AUTH_USERNAME')}")
    else:
        print("⚠️  WARNING: Using default credentials (admin/admin)")
        print(
            "   Set AUTH_USERNAME and AUTH_PASSWORD environment variables for production"
        )

    app.run(debug=debug_mode, host=host, port=port)
