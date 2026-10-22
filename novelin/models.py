from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class Novel:
    url: str
    slug: str
    title: str
    post_id: Optional[int] = None
    alternative_title: Optional[str] = None
    author: Optional[str] = None
    artist: Optional[str] = None
    genres: List[str] = field(default_factory=list)
    status: Optional[str] = None
    release: Optional[str] = None
    cover_url: Optional[str] = None
    synopsis: str = ""


@dataclass
class Chapter:
    index: int
    title: str
    url: str
    locked: bool = False
    price_label: Optional[str] = None
    release_date: Optional[str] = None


@dataclass
class ChapterContent:
    chapter: Chapter
    title: str
    html: str
    text: str
    locked: bool = False
    gate_message: Optional[str] = None


@dataclass
class CoverImage:
    data: bytes
    media_type: str
    extension: str
