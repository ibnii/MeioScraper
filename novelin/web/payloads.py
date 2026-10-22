from __future__ import annotations

from typing import Optional


def chapter_event(
    chapter,
    status: str,
    downloaded: int,
    skipped: int,
    failed: int,
    total: int,
    message: Optional[str] = None,
) -> dict:
    event = {
        "type": "chapter",
        "index": chapter.index,
        "title": chapter.title,
        "status": status,
        "downloaded": downloaded,
        "skipped": skipped,
        "failed": failed,
        "processed": downloaded + skipped + failed,
        "total": total,
    }
    if message:
        event["message"] = message
    return event
