from __future__ import annotations

import json
from typing import Iterator

from .jobs import Job


def iter_events(job: Job) -> Iterator[str]:
    index = 0
    while True:
        with job.condition:
            while index >= len(job.events) and job.status in ("queued", "running"):
                notified = job.condition.wait(timeout=15)
                if not notified:
                    break
            pending = job.events[index:]
            index = len(job.events)
            terminal = job.status not in ("queued", "running")

        for event in pending:
            yield f"data: {json.dumps(event, ensure_ascii=False)}\n\n"

        if terminal and index >= len(job.events):
            break
        if not pending:
            yield ": keep-alive\n\n"
