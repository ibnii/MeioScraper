from __future__ import annotations

import re
from typing import List, Optional
from urllib.parse import urljoin, urlparse

from bs4 import BeautifulSoup
from bs4.element import NavigableString
from bs4.formatter import XMLFormatter

from .models import Chapter, ChapterContent, Novel
from .utils import novel_slug

ALLOWED_TAGS = {
    "p",
    "br",
    "strong",
    "b",
    "em",
    "i",
    "u",
    "s",
    "blockquote",
    "ul",
    "ol",
    "li",
    "h2",
    "h3",
    "h4",
    "h5",
    "h6",
    "hr",
    "a",
}
DROP_TAGS = {
    "script",
    "style",
    "noscript",
    "iframe",
    "ins",
    "form",
    "input",
    "button",
    "svg",
    "video",
    "audio",
    "canvas",
    "select",
    "textarea",
}
BLOCK_TAGS = ("p", "blockquote", "li", "h2", "h3", "h4", "h5", "h6")


def _text(node) -> str:
    if node is None:
        return ""
    return re.sub(r"\s+", " ", node.get_text(" ", strip=True)).strip()


def _info_value(soup: BeautifulSoup, label: str) -> str:
    for item in soup.select(".post-content_item"):
        heading = item.select_one(".summary-heading")
        if heading and label.lower() in _text(heading).lower():
            value = item.select_one(".summary-content")
            return _text(value) if value else ""
    return ""


def _post_id(soup: BeautifulSoup, html: str) -> Optional[int]:
    holder = soup.select_one("#manga-chapters-holder[data-id]")
    if holder:
        value = (holder.get("data-id") or "").strip()
        if value.isdigit():
            return int(value)

    match = re.search(r'"manga_id"\s*:\s*"?(\d+)"?', html)
    if match:
        return int(match.group(1))
    return None


def _synopsis(soup: BeautifulSoup) -> str:
    element = soup.select_one(".description-summary")
    if element is None:
        return ""

    for unwanted in element.select("script, style, .btn, button"):
        unwanted.decompose()

    paragraphs = [_text(node) for node in element.find_all("p")]
    paragraphs = [paragraph for paragraph in paragraphs if paragraph]
    text = "\n\n".join(paragraphs) if paragraphs else _text(element)
    text = re.sub(r"\n*\s*Show more\s*$", "", text, flags=re.IGNORECASE)
    return text.strip()


def parse_novel(html: str, url: str) -> Novel:
    soup = BeautifulSoup(html, "html.parser")
    slug = novel_slug(url)
    if not slug:
        raise ValueError(f"URL novel tidak dikenali: {url}")

    title_element = soup.select_one(".post-title h1") or soup.select_one("h1")
    title = _text(title_element) or slug

    cover_url = ""
    image = soup.select_one(".summary_image img")
    if image is not None:
        source = (image.get("data-src") or image.get("src") or "").strip()
        if source.startswith("//"):
            source = "https:" + source
        if source.startswith(("http://", "https://")):
            cover_url = source

    genres = [_text(link) for link in soup.select(".genres-content a")]
    genres = [genre for genre in genres if genre]

    return Novel(
        url=url,
        slug=slug,
        title=title,
        post_id=_post_id(soup, html),
        alternative_title=_info_value(soup, "Alternative") or None,
        author=_text(soup.select_one(".author-content a"))
        or _info_value(soup, "Author")
        or None,
        artist=_text(soup.select_one(".artist-content a"))
        or _info_value(soup, "Artist")
        or None,
        genres=genres,
        status=_info_value(soup, "Status") or None,
        release=_info_value(soup, "Release") or None,
        cover_url=cover_url or None,
        synopsis=_synopsis(soup),
    )


def parse_chapter_list(html: str, base_url: str = "") -> List[Chapter]:
    soup = BeautifulSoup(html, "html.parser")
    chapters: List[Chapter] = []

    for item in soup.select(".wp-manga-chapter"):
        link = item.select_one("a[href]")
        if link is None:
            continue

        href = (link.get("href") or "").strip()
        if not href:
            continue

        chapter_url = urljoin(base_url, href)
        host = urlparse(chapter_url).netloc.lower()
        if host and "meionovels.com" not in host:
            continue

        label_element = item.select_one(".mck-label")
        label = _text(label_element)
        release_element = item.select_one(".chapter-release-date")

        chapters.append(
            Chapter(
                index=0,
                title=_text(link) or href.rstrip("/").rsplit("/", 1)[-1],
                url=chapter_url,
                locked=bool(label) and "gratis" not in label.lower(),
                price_label=label or None,
                release_date=_text(release_element) or None,
            )
        )

    return chapters


def parse_chapter(html: str, chapter: Chapter) -> ChapterContent:
    soup = BeautifulSoup(html, "html.parser")

    heading = soup.select_one("h1#chapter-heading") or soup.select_one(".chapter-heading")
    title = _text(heading) or chapter.title

    gate = soup.select_one(".mck-gate")
    if gate is not None:
        return ChapterContent(
            chapter=chapter,
            title=title,
            html="",
            text="",
            locked=True,
            gate_message=_text(gate),
        )

    content = soup.select_one(".reading-content .text-left") or soup.select_one(
        ".reading-content"
    )
    if content is None:
        raise ValueError(f"Konten chapter tidak ditemukan: {chapter.url}")

    fragment = sanitize_content(content)
    text = html_to_text(fragment)
    return ChapterContent(
        chapter=chapter,
        title=title,
        html=fragment,
        text=text,
        locked=False,
    )


def sanitize_content(element) -> str:
    clone = BeautifulSoup(str(element), "html.parser")
    root = clone.find(element.name) or clone.body or clone.find()
    if root is None:
        return ""

    for tag in list(root.find_all(DROP_TAGS)):
        tag.decompose()

    for tag in list(root.find_all(True)):
        if tag.name == "img":
            alt = (tag.get("alt") or "").strip() or _text(tag)
            tag.replace_with(NavigableString(f"[Gambar: {alt}]" if alt else "[Gambar]"))
        elif tag.name == "a":
            href = (tag.get("href") or "").strip()
            if href.startswith(("http://", "https://", "/")) and not href.startswith(
                "javascript:"
            ):
                tag.attrs = {"href": href}
            else:
                tag.attrs = {}
                tag.unwrap()
        elif tag.name in ALLOWED_TAGS:
            tag.attrs = {}
        else:
            tag.unwrap()

    for tag in list(root.find_all(["p", "li", "blockquote"])):
        if not tag.get_text(strip=True) and tag.find("br") is None:
            tag.decompose()

    return root.decode_contents(formatter=XMLFormatter()).strip()


def html_to_text(fragment: str) -> str:
    if not fragment:
        return ""

    soup = BeautifulSoup(f"<div>{fragment}</div>", "html.parser")
    for br in soup.find_all("br"):
        br.replace_with(NavigableString("\n"))

    blocks = soup.find_all(BLOCK_TAGS)
    if blocks:
        parts = [_block_text(block) for block in blocks]
        text = "\n\n".join(part for part in parts if part)
    else:
        text = _block_text(soup)

    return re.sub(r"\n{3,}", "\n\n", text).strip()


def _block_text(block) -> str:
    raw = block.get_text("", strip=False)
    lines = [re.sub(r"[ \t]+", " ", line).strip() for line in raw.splitlines()]
    lines = [line for line in lines if line]
    return "\n".join(lines)
