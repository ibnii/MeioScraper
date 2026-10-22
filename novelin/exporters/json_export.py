from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path
from typing import List

from ..models import ChapterContent, Novel


def export_json(novel: Novel, contents: List[ChapterContent], path: Path) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)

    payload = {
        "novel": asdict(novel),
        "chapters": [
            {
                "index": content.chapter.index,
                "title": content.title,
                "url": content.chapter.url,
                "release_date": content.chapter.release_date,
                "content": content.text,
            }
            for content in contents
        ],
    }

    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return path
