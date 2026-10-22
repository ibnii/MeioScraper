from __future__ import annotations

from pathlib import Path
from typing import List

from ..models import ChapterContent, Novel


def export_txt(novel: Novel, contents: List[ChapterContent], path: Path) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)

    lines: List[str] = [novel.title, ""]
    if novel.author:
        lines.append(f"Author: {novel.author}")
    if novel.artist:
        lines.append(f"Artist: {novel.artist}")
    if novel.status:
        lines.append(f"Status: {novel.status}")
    if novel.genres:
        lines.append(f"Genre: {', '.join(novel.genres)}")
    lines.append(f"Source: {novel.url}")

    if novel.synopsis:
        lines.extend(["", "Sinopsis:", novel.synopsis])

    for content in contents:
        lines.extend(
            [
                "",
                "",
                "=" * 60,
                f"[{content.chapter.index}] {content.title}",
                "=" * 60,
                "",
                content.text,
            ]
        )

    path.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")
    return path
