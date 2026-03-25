# job_model.py
# Data model for jobs

import queue
import subprocess
from dataclasses import dataclass, field
from typing import Optional, List


@dataclass
class JobModel:
    name: str
    command: str
    cron: str
    status: str = "idle"
    last_run: Optional[str] = None
    last_result: Optional[str] = None
    restart_count: int = 0
    logs: List[str] = field(default_factory=list)
    process: Optional[subprocess.Popen] = None
    stdin_queue: queue.Queue = field(
        default_factory=queue.Queue
    )  # Thread-safe queue for async stdin writes
