from __future__ import annotations

import re
from typing import Optional, Set
from urllib.parse import urlparse


def novel_slug(url: str) -> str:
    path = [part for part in urlparse(url).path.split("/") if part]
    if "novel" in path:
        position = path.index("novel")
        if position + 1 < len(path):
            return path[position + 1]
    return path[-1] if path else ""


def safe_filename(name: str) -> str:
    cleaned = re.sub(r'[\\/:*?"<>|\x00-\x1f]', "_", name)
    cleaned = cleaned.strip(" .")
    return cleaned or "novel"


def parse_chapter_range(spec: Optional[str], total: Optional[int] = None) -> Optional[Set[int]]:
    if spec is None or not spec.strip():
        return None

    selected: Set[int] = set()
    for raw_part in spec.split(","):
        part = raw_part.strip()
        if not part:
            continue

        if "-" in part:
            start_text, _, end_text = part.partition("-")
            try:
                start = int(start_text) if start_text.strip() else 1
                if end_text.strip():
                    end = int(end_text)
                elif total is not None:
                    end = total
                else:
                    raise ValueError("rentang terbuka membutuhkan jumlah chapter")
            except ValueError as exc:
                raise ValueError(f"Rentang chapter tidak valid: {part!r}") from exc

            if start < 1 or end < start:
                raise ValueError(f"Rentang chapter tidak valid: {part!r}")
            selected.update(range(start, end + 1))
            continue

        try:
            number = int(part)
        except ValueError as exc:
            raise ValueError(f"Nomor chapter tidak valid: {part!r}") from exc

        if number < 1:
            raise ValueError(f"Nomor chapter tidak valid: {part!r}")
        selected.add(number)

    if total is not None:
        selected = {number for number in selected if number <= total}
    return selected
