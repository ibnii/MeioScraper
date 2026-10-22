from __future__ import annotations

from typing import List, Optional
from urllib.parse import urlparse

from bs4 import BeautifulSoup

from .http import HttpClient, HttpError
from .models import Chapter, ChapterContent, CoverImage, Novel
from .parser import parse_chapter, parse_chapter_list, parse_novel

DEFAULT_SITE = "https://meionovels.com"
MAX_CHAPTER_PAGES = 100
MAX_COVER_BYTES = 10 * 1024 * 1024

MEDIA_TYPES = {
    "image/jpeg": "jpg",
    "image/jpg": "jpg",
    "image/png": "png",
    "image/webp": "webp",
    "image/gif": "gif",
}


class MeionovelsScraper:
    def __init__(
        self,
        client: Optional[HttpClient] = None,
        site: str = DEFAULT_SITE,
    ) -> None:
        self.client = client or HttpClient()
        self.site = site.rstrip("/")

    def normalize_url(self, value: str) -> str:
        return normalize_novel_url(value, self.site)

    def fetch_novel(self, url_or_slug: str) -> Novel:
        url = self.normalize_url(url_or_slug)
        response = self.client.get(url)
        return parse_novel(response.text, url)

    def fetch_chapters(self, novel: Novel) -> List[Chapter]:
        endpoint = f"{novel.url.rstrip('/')}/ajax/chapters/"
        headers = {
            "Referer": novel.url,
            "X-Requested-With": "XMLHttpRequest",
        }

        collected: List[Chapter] = []
        seen = set()
        page = 1

        while page <= MAX_CHAPTER_PAGES:
            response = self.client.post(f"{endpoint}?t={page}", data=None, headers=headers)
            batch = parse_chapter_list(response.text, base_url=novel.url)
            fresh = [chapter for chapter in batch if chapter.url not in seen]
            if not fresh:
                break

            collected.extend(fresh)
            seen.update(chapter.url for chapter in fresh)

            last_page = _last_page_number(response.text)
            if last_page <= page:
                break
            page += 1

        if not collected:
            raise HttpError(
                "Daftar chapter tidak ditemukan. Struktur situs mungkin berubah.",
                url=endpoint,
            )

        return order_chapters(collected)

    def fetch_chapter(self, chapter: Chapter) -> ChapterContent:
        response = self.client.get(chapter.url)
        return parse_chapter(response.text, chapter)

    def download_cover(self, novel: Novel) -> Optional[CoverImage]:
        if not novel.cover_url:
            return None

        try:
            response = self.client.get(novel.cover_url)
        except HttpError:
            return None

        if len(response.content) > MAX_COVER_BYTES:
            return None

        content_type = (response.headers.get("Content-Type") or "").split(";")[0].strip().lower()
        extension = MEDIA_TYPES.get(content_type)
        if extension is None:
            suffix = urlparse(novel.cover_url).path.rsplit(".", 1)[-1].lower()
            if suffix in {"jpg", "jpeg", "png", "webp", "gif"}:
                extension = "jpg" if suffix == "jpeg" else suffix
                content_type = {
                    "jpg": "image/jpeg",
                    "png": "image/png",
                    "webp": "image/webp",
                    "gif": "image/gif",
                }[extension]
        if extension is None:
            return None

        return CoverImage(data=response.content, media_type=content_type, extension=extension)


def normalize_novel_url(value: str, site: str = DEFAULT_SITE) -> str:
    value = value.strip()
    if not value:
        raise ValueError("URL atau slug novel kosong")

    if not value.startswith(("http://", "https://")):
        slug = value.strip("/")
        if not slug:
            raise ValueError("Slug novel kosong")
        return f"{site}/novel/{slug}/"

    parsed = urlparse(value)
    if "meionovels.com" not in parsed.netloc.lower():
        raise ValueError("Hanya URL meionovels.com yang didukung")

    parts = [part for part in parsed.path.split("/") if part]
    if "novel" in parts:
        position = parts.index("novel")
        if position + 1 < len(parts):
            return f"{site}/novel/{parts[position + 1]}/"

    raise ValueError(f"URL bukan halaman novel: {value}")


def normalize_chapter_url(value: str, site: str = DEFAULT_SITE) -> str:
    value = value.strip()
    if not value:
        raise ValueError("URL chapter kosong")

    parsed = urlparse(value)
    if parsed.scheme not in ("http", "https"):
        raise ValueError("URL chapter harus http atau https")
    if "meionovels.com" not in parsed.netloc.lower():
        raise ValueError("Hanya URL meionovels.com yang didukung")

    parts = [part for part in parsed.path.split("/") if part]
    if len(parts) < 3 or parts[0] != "novel":
        raise ValueError(f"URL bukan halaman chapter: {value}")
    return value


def order_chapters(chapters: List[Chapter]) -> List[Chapter]:
    ordered = list(reversed(chapters))
    for index, chapter in enumerate(ordered, start=1):
        chapter.index = index
    return ordered


def _last_page_number(html: str) -> int:
    soup = BeautifulSoup(html, "html.parser")
    pages = []
    for link in soup.select(".pagination [data-page]"):
        value = (link.get("data-page") or "").strip()
        if value.isdigit():
            pages.append(int(value))
    return max(pages) if pages else 1
