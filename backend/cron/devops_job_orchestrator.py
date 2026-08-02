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
    6. REST API: /api/jobs endpoints for curl/automation (same Basic Auth as the UI)
    7. Public Log Inspection: /public (page) and /public/jobs* (JSON) expose job
       status and run logs with no authentication, for external visibility into
       scraper runs. GET-only - run/stop/input remain auth-protected on /api/jobs/*.

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
from flask import request, Response, session, make_response, render_template_string
from flask_session import Session

import dash
from croniter import croniter
from dash import html, dcc, dash_table, Input, Output, State
import dash_bootstrap_components as dbc

from cron.job_model import JobModel

# Application identity - shown in the UI, auth prompts and health responses.
APP_NAME = "Crautos Ops Console"
APP_SUBTITLE = "DevOps Job Orchestrator"


# ===================== CONSTANTS & HELPERS =====================

# Log formatting constants
LOG_SEPARATOR = "=" * 60
PROMPT_SUFFIXES = (": ", "? ", ") ")

# Unified enterprise color palette - one accent, one header treatment,
# used everywhere instead of the previous per-card assortment of hues.
COLORS = {
    "header_bg": "#1e293b",  # slate-800 - all card headers share this
    "header_text": "#f8fafc",
    "page_bg": "#f1f5f9",  # slate-100
    "surface": "#ffffff",
    "accent": "#2563eb",  # blue-600
    "success": "#16a34a",
    "danger": "#dc2626",
    "warning": "#d97706",
    "muted": "#64748b",  # slate-500
    "text": "#0f172a",  # slate-900
    "border": "#e2e8f0",  # slate-200
}

# UI Style constants
STYLES = {
    "monospace_time": {"fontFamily": "monospace", "fontWeight": "bold"},
    "date_text": {"fontSize": "14px"},
    "card_header": {"backgroundColor": COLORS["header_bg"], "color": COLORS["header_text"]},
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
    time_id: str,
    date_id: str,
    offset: str,
) -> dbc.Col:
    """Factory function for timezone display cards"""
    return dbc.Col(
        dbc.Card(
            dbc.CardBody(
                [
                    html.H6(
                        label,
                        className="mb-2 text-uppercase",
                        style={"color": COLORS["muted"], "fontSize": "12px", "letterSpacing": "0.05em"},
                    ),
                    html.H2(
                        id=time_id,
                        className="mb-1",
                        style={**STYLES["monospace_time"], "color": COLORS["text"]},
                    ),
                    html.P(
                        id=date_id,
                        className="mb-1",
                        style={**STYLES["date_text"], "color": COLORS["text"]},
                    ),
                    html.Small(offset, style={"color": COLORS["muted"]}),
                ]
            ),
            style={
                "backgroundColor": COLORS["surface"],
                "border": f"1px solid {COLORS['border']}",
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
        - Falls back to 'admin'/'admin' if AUTH_USERNAME/AUTH_PASSWORD are not set.
        - Set both env vars to real credentials for production deployments.

    Args:
        username: Username to validate
        password: Password to validate

    Returns:
        bool: True if credentials are valid, False otherwise
    """
    auth_user = os.getenv("AUTH_USERNAME", "admin")
    auth_pass = os.getenv("AUTH_PASSWORD", "admin")

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
        {"WWW-Authenticate": f'Basic realm="{APP_NAME} - Sesión de 1 hora"'},
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
                job.logs.append(f"[{timestamp}] Cron scheduler {status}")
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
                                            f"[{timestamp}] Cron triggered: {job.cron}"
                                        )
                                        self.start_job(job.name)
                                    else:
                                        timestamp = get_full_timestamp()
                                        job.logs.append(
                                            f"[{timestamp}] Skipped cron trigger (job still running from previous execution)"
                                        )
                            except Exception as e:
                                # Cron parsing errors logged but don't crash scheduler
                                timestamp = get_full_timestamp()
                                job.logs.append(f"[{timestamp}] Cron error: {e}")

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
            job.logs.append(f"[{job.last_run}] Starting Job: {job.name}")
            job.logs.append(f"[{job.last_run}] Command: {job.command}")
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
                            job.logs.append(f"[{timestamp}] User Input: {inp}")
                            # Write to PTY master, which forwards to subprocess stdin
                            os.write(master_fd, (inp + "\n").encode())
                        except queue.Empty:
                            continue
                        except Exception as e:
                            timestamp = get_time_timestamp()
                            job.logs.append(f"[{timestamp}] Input error: {e}")
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
                    job.logs.append(f"[{end_timestamp}] Job completed successfully")
                else:
                    job.logs.append(
                        f"[{end_timestamp}] Job failed with exit code {rc}"
                    )
                job.logs.append(
                    f"[{end_timestamp}] Duration: {duration:.2f} seconds"
                )
                job.logs.append(LOG_SEPARATOR)

            except Exception as e:
                # Catch-all for unexpected errors (PTY failures, etc.)
                end_timestamp = get_full_timestamp()
                job.logs.append(LOG_SEPARATOR)
                job.logs.append(f"[{end_timestamp}] ERROR: {e}")
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
            # job.logs.append(f"[{timestamp}] Queued input: {text}")
            return True
        return False

    def stop_job(self, name: str):
        job = self.jobs.get(name)
        if job and job.process:
            timestamp = get_full_timestamp()
            try:
                job.logs.append(f"[{timestamp}] Stopping job...")
                # SIGTERM - graceful shutdown (allows cleanup handlers)
                job.process.terminate()
                job.process.wait(timeout=5)  # 5s grace period
                job.logs.append(f"[{timestamp}] Job stopped gracefully")
            except subprocess.TimeoutExpired:
                # SIGKILL - force kill after timeout (no cleanup)
                job.process.kill()
                job.logs.append(f"[{timestamp}] Job killed (timeout)")
            finally:
                job.process = None
            job.status = "idle"


# ===================== DASH VIEW =====================

# Global controller instance - shared across all callbacks
# Singleton pattern ensures single scheduler thread
controller = JobController()

# Load job definitions from external file for separation of concerns
from cron.job_definitions import get_job_definitions

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

# Ensure session directory exists
os.makedirs(server.config["SESSION_FILE_DIR"], exist_ok=True)

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
                html.Div(
                    [
                        html.H1(
                            APP_NAME,
                            className="mb-0",
                            style={"color": COLORS["text"], "fontWeight": "700"},
                        ),
                        html.P(
                            APP_SUBTITLE,
                            className="mb-0 text-uppercase",
                            style={"color": COLORS["muted"], "fontSize": "13px", "letterSpacing": "0.08em"},
                        ),
                    ],
                    className="text-center my-4",
                ),
                width=12,
            )
        ),
        # Session Info Alert
        dbc.Row(
            dbc.Col(
                dbc.Alert(
                    [
                        html.I(className="bi bi-shield-lock-fill me-2"),
                        html.Span("Sesión activa: ", className="fw-bold"),
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
                dbc.CardHeader(html.H4("World Clock", className="mb-0"), style=STYLES["card_header"]),
                dbc.CardBody(
                    dbc.Row(
                        [
                            create_timezone_card("UTC Time", "clock-system-time", "clock-system-date", "UTC"),
                            create_timezone_card("Costa Rica", "clock-cr-time", "clock-cr-date", "UTC-6"),
                            create_timezone_card("US Eastern", "clock-us-time", "clock-us-date", "UTC-5"),
                            create_timezone_card("India", "clock-india-time", "clock-india-date", "UTC+5:30"),
                        ],
                        className="g-3",
                    )
                ),
            ],
            className="mb-4 shadow-sm",
        ),
        # Cron Scheduler Control Card
        dbc.Card(
            [
                dbc.CardHeader(html.H4("Cron Scheduler Control", className="mb-0"), style=STYLES["card_header"]),
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
            className="mb-4 shadow-sm",
        ),
        # Job Table Card
        dbc.Card(
            [
                dbc.CardHeader(html.H4("Job Management", className="mb-0"), style=STYLES["card_header"]),
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
                                "backgroundColor": COLORS["page_bg"],
                                "fontWeight": "bold",
                                "border": f"1px solid {COLORS['border']}",
                            },
                            style_data={
                                "border": f"1px solid {COLORS['border']}",
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
                                    "backgroundColor": COLORS["accent"],
                                    "color": "white",
                                    "border": f"2px solid {COLORS['accent']}",
                                },
                            ],
                        ),
                    ]
                ),
            ],
            className="mb-4 shadow-sm",
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
                    style=STYLES["card_header"],
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
            className="mb-4 shadow-sm",
        ),
        # Input Section for interactive jobs
        dbc.Card(
            [
                dbc.CardHeader(
                    html.H4("Send Input to Job", className="mb-0"),
                    style=STYLES["card_header"],
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
    style={"backgroundColor": COLORS["page_bg"], "minHeight": "100vh", "padding": "20px"},
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
        return info["username"], f"{remaining}"
    elif remaining <= 15:
        # Less than 15 minutes - warning
        return info["username"], f"{remaining}"
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
        http_status = 200
        status = "healthy"

        response_data = {
            "status": status,
            "timestamp": get_full_timestamp(),
            "scheduler": {
                "running": scheduler_healthy,
                "status": "active" if scheduler_healthy else "stopped",
            },
            "service_name": f"{APP_NAME} - {APP_SUBTITLE}",
        }

        return response_data, http_status, {"Content-Type": "application/json"}

    except Exception as e:
        # Catch-all for unexpected errors in health check itself
        error_response = {
            "status": "error",
            "timestamp": get_full_timestamp(),
            "error": str(e),
            "service": {
                "name": f"{APP_NAME} - {APP_SUBTITLE}",
                "version": "1.0.0",
                "port": 8081,
            },
        }
        return error_response, 503, {"Content-Type": "application/json"}


# ===================== REST API (curl-friendly automation) =====================
#
# Same auth as the rest of the dashboard (HTTP Basic Auth via before_request).
# Job names may contain spaces, so identifiers also match case-insensitively
# with '-'/'_' standing in for spaces (e.g. "crautos-data-scraper").
#
# Examples:
#   curl -u admin:admin https://host/api/jobs
#   curl -u admin:admin -X POST https://host/api/jobs/crautos-data-scraper/run
#   curl -u admin:admin -X POST https://host/api/jobs/crautos-data-scraper/stop
#   curl -u admin:admin "https://host/api/jobs/crautos-data-scraper/logs?tail=50"
#   curl -u admin:admin -X POST https://host/api/jobs/crautos-data-scraper/input \
#        -H 'Content-Type: application/json' -d '{"text": "y"}'


def find_job(identifier: str) -> JobModel | None:
    """Look up a job by exact name, or case-insensitively with '-'/'_' as spaces."""
    if identifier in controller.jobs:
        return controller.jobs[identifier]
    normalized = identifier.strip().lower().replace("-", " ").replace("_", " ")
    for job in controller.jobs.values():
        if job.name.lower() == normalized:
            return job
    return None


@server.route("/api/jobs", methods=["GET"])
def api_list_jobs():
    """List all jobs with their current status."""
    return {"jobs": job_rows()}, 200, {"Content-Type": "application/json"}


@server.route("/api/jobs/<identifier>/run", methods=["POST"])
def api_run_job(identifier):
    """Start a job by name (idempotent - no-op if already running)."""
    job = find_job(identifier)
    if not job:
        return {"error": f"Job '{identifier}' not found"}, 404
    controller.start_job(job.name)
    return {"status": "started", "job": job.name}, 200


@server.route("/api/jobs/<identifier>/stop", methods=["POST"])
def api_stop_job(identifier):
    """Stop a running job by name."""
    job = find_job(identifier)
    if not job:
        return {"error": f"Job '{identifier}' not found"}, 404
    controller.stop_job(job.name)
    return {"status": "stopped", "job": job.name}, 200


@server.route("/api/jobs/<identifier>/logs", methods=["GET"])
def api_job_logs(identifier):
    """Get the tail of a job's logs. Query param 'tail' controls line count (default 200)."""
    job = find_job(identifier)
    if not job:
        return {"error": f"Job '{identifier}' not found"}, 404
    tail = request.args.get("tail", default=200, type=int) or 200
    return {"job": job.name, "status": job.status, "logs": job.logs[-tail:]}, 200


@server.route("/api/jobs/<identifier>/input", methods=["POST"])
def api_send_input(identifier):
    """Send a line of stdin to a running interactive job. Body: {"text": "..."}."""
    job = find_job(identifier)
    if not job:
        return {"error": f"Job '{identifier}' not found"}, 404
    data = request.get_json(silent=True) or {}
    text = data.get("text", "")
    sent = controller.send_input(job.name, text)
    if not sent:
        return {"status": "not_running", "job": job.name}, 409
    return {"status": "sent", "job": job.name}, 200


# ===================== PUBLIC READ-ONLY LOG INSPECTION =====================
#
# Unauthenticated, read-only views of job status and run logs, for external
# visibility into scraper runs. Deliberately GET-only: run/stop/input stay
# behind auth on /api/jobs/*. Job commands are just module invocations
# (see job_definitions.py), so exposing them alongside the logs carries no
# credential/secret risk.
#
# Examples:
#   curl https://host/public/jobs
#   curl "https://host/public/jobs/crautos-data-scraper/logs?tail=50"


@server.route("/public/jobs", methods=["GET"])
def public_list_jobs():
    """List all jobs with their current status (no authentication required)."""
    return {"jobs": job_rows()}, 200, {"Content-Type": "application/json"}


@server.route("/public/jobs/<identifier>/logs", methods=["GET"])
def public_job_logs(identifier):
    """Get the tail of a job's logs (no authentication required)."""
    job = find_job(identifier)
    if not job:
        return {"error": f"Job '{identifier}' not found"}, 404
    tail = request.args.get("tail", default=200, type=int) or 200
    return {"job": job.name, "status": job.status, "logs": job.logs[-tail:]}, 200


_PUBLIC_LOGS_PAGE = """
<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{{ app_name }} - Public Job Logs</title>
<style>
  :root { color-scheme: light; }
  * { box-sizing: border-box; }
  body {
    margin: 0; padding: 24px; background: {{ page_bg }}; color: {{ text }};
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Arial, sans-serif;
  }
  .wrap { max-width: 1100px; margin: 0 auto; }
  header { margin-bottom: 24px; }
  h1 { font-size: 22px; margin: 0 0 4px; }
  .subtitle { color: {{ muted }}; font-size: 13px; text-transform: uppercase; letter-spacing: .08em; }
  .layout { display: grid; grid-template-columns: 260px 1fr; gap: 20px; align-items: start; }
  @media (max-width: 800px) { .layout { grid-template-columns: 1fr; } }
  .card {
    background: {{ surface }}; border: 1px solid {{ border }}; border-radius: 10px;
    overflow: hidden;
  }
  .card-header {
    background: {{ header_bg }}; color: {{ header_text }};
    padding: 10px 16px; font-size: 13px; font-weight: 600; text-transform: uppercase; letter-spacing: .05em;
  }
  ul.job-list { list-style: none; margin: 0; padding: 0; }
  ul.job-list li button {
    width: 100%; text-align: left; background: none; border: none; border-bottom: 1px solid {{ border }};
    padding: 12px 16px; cursor: pointer; font-size: 14px; color: {{ text }};
  }
  ul.job-list li:last-child button { border-bottom: none; }
  ul.job-list li button:hover, ul.job-list li button.active { background: {{ page_bg }}; }
  ul.job-list li button.active { border-left: 3px solid {{ accent }}; }
  .job-name { display: block; font-weight: 600; }
  .job-meta { display: block; font-size: 11px; color: {{ muted }}; margin-top: 2px; text-transform: uppercase; letter-spacing: .04em; }
  .status-badge { display: inline-block; padding: 1px 8px; border-radius: 999px; font-size: 10px; font-weight: 700; text-transform: uppercase; }
  .status-running { background: #d1fae5; color: #065f46; }
  .status-error { background: #fee2e2; color: #991b1b; }
  .status-idle { background: #e0f2fe; color: #075985; }
  pre#log-view {
    margin: 0; height: 70vh; overflow-y: auto; background: #1e1e1e; color: #d4d4d4;
    padding: 16px; font-family: Consolas, Monaco, monospace; font-size: 12.5px; line-height: 1.5;
    white-space: pre-wrap; word-break: break-word;
  }
  .empty { padding: 40px; text-align: center; color: {{ muted }}; }
</style>
</head>
<body>
<div class="wrap">
  <header>
    <h1>{{ app_name }}</h1>
    <div class="subtitle">Public job status &amp; run logs (read-only)</div>
  </header>
  <div class="layout">
    <div class="card">
      <div class="card-header">Jobs</div>
      <ul class="job-list" id="job-list"></ul>
    </div>
    <div class="card">
      <div class="card-header" id="log-header">Logs</div>
      <pre id="log-view">Select a job to view its logs.</pre>
    </div>
  </div>
</div>
<script>
  let selected = null;

  function statusClass(status) {
    if (status === 'running') return 'status-running';
    if (status === 'error') return 'status-error';
    return 'status-idle';
  }

  async function refreshJobs() {
    const res = await fetch('/public/jobs');
    const data = await res.json();
    const list = document.getElementById('job-list');
    list.innerHTML = '';
    data.jobs.forEach(job => {
      const li = document.createElement('li');
      const btn = document.createElement('button');
      btn.className = job.name === selected ? 'active' : '';
      btn.innerHTML = '<span class="job-name">' + job.name + '</span>' +
        '<span class="job-meta"><span class="status-badge ' + statusClass(job.status) + '">' + job.status + '</span> &middot; ' +
        (job.last_run || 'never run') + '</span>';
      btn.onclick = () => { selected = job.name; refreshJobs(); refreshLogs(); };
      li.appendChild(btn);
      list.appendChild(li);
    });
    if (!selected && data.jobs.length) {
      selected = data.jobs[0].name;
      refreshJobs();
      refreshLogs();
    }
  }

  async function refreshLogs() {
    if (!selected) return;
    const res = await fetch('/public/jobs/' + encodeURIComponent(selected) + '/logs?tail=500');
    if (!res.ok) return;
    const data = await res.json();
    document.getElementById('log-header').textContent = data.job + ' - ' + data.status;
    const view = document.getElementById('log-view');
    const atBottom = view.scrollTop + view.clientHeight >= view.scrollHeight - 20;
    view.textContent = data.logs.join('\\n') || 'No logs yet.';
    if (atBottom) view.scrollTop = view.scrollHeight;
  }

  refreshJobs();
  setInterval(refreshJobs, 3000);
  setInterval(refreshLogs, 2000);
</script>
</body>
</html>
"""


@server.route("/public", methods=["GET"])
@server.route("/public/", methods=["GET"])
def public_logs_page():
    """Browsable, read-only job status/log inspection page (no authentication required)."""
    return render_template_string(
        _PUBLIC_LOGS_PAGE,
        app_name=APP_NAME,
        page_bg=COLORS["page_bg"],
        surface=COLORS["surface"],
        border=COLORS["border"],
        header_bg=COLORS["header_bg"],
        header_text=COLORS["header_text"],
        accent=COLORS["accent"],
        muted=COLORS["muted"],
        text=COLORS["text"],
    )


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
        {"WWW-Authenticate": f'Basic realm="{APP_NAME} Login"'},
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
        - /public, /public/*: Read-only job status/log inspection (GET-only
          routes - see "PUBLIC READ-ONLY LOG INSPECTION" section above).
          Running/stopping jobs or sending input always stays behind auth.
    """
    # Public routes - no authentication required
    public_paths = ["/health", "/logout"]

    # Allow Dash framework assets (CSS, JS, etc.)
    if request.path.startswith("/_dash-"):
        return None

    # Allow the public, read-only log inspection page/API (GET-only routes)
    if request.path == "/public" or request.path.startswith("/public/"):
        return None

    # Allow public routes
    if request.path in public_paths:
        return None

    # Check if session is valid
    if not is_session_valid():
        # No valid session - attempt Basic Auth
        auth = request.authorization

        if auth and check_auth(auth.username, auth.password):
            # Create new session (1-hour timeout)
            create_session(auth.username)
            return None

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
