from __future__ import annotations

import html
import uuid
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional

from ..models import ChapterContent, CoverImage, Novel

LANGUAGE = "id"
STYLE = """body { font-family: Georgia, serif; line-height: 1.65; margin: 1.4em; }
h1.chapter-title { font-size: 1.35em; line-height: 1.3; margin: 0 0 1.2em; text-align: center; }
.chapter-content p { margin: 0 0 0.85em; text-indent: 1.1em; }
.chapter-content blockquote { margin: 0 0 0.85em 1.5em; font-style: italic; }
.chapter-content h2, .chapter-content h3, .chapter-content h4 { margin: 1.2em 0 0.6em; }
.cover { margin: 0; padding: 0; text-align: center; }
.cover img { max-width: 100%; height: auto; }
.empty { font-style: italic; text-align: center; }
"""


def _escape(value: str) -> str:
    return html.escape(value, quote=True)


def export_epub(
    novel: Novel,
    contents: List[ChapterContent],
    path: Path,
    cover: Optional[CoverImage] = None,
) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)

    identifier = f"urn:uuid:{uuid.uuid5(uuid.NAMESPACE_URL, novel.url)}"
    modified = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    manifest_items = [
        '<item id="nav" href="nav.xhtml" media-type="application/xhtml+xml" properties="nav"/>',
        '<item id="ncx" href="toc.ncx" media-type="application/x-dtbncx+xml"/>',
        '<item id="style" href="style.css" media-type="text/css"/>',
    ]
    spine_items: List[str] = []
    nav_entries: List[str] = []
    nav_points: List[str] = []
    files = {}

    if cover is not None:
        cover_name = f"cover.{cover.extension}"
        files[f"OEBPS/images/{cover_name}"] = cover.data
        files["OEBPS/cover.xhtml"] = _document(
            "Cover",
            f'<div class="cover"><img src="images/{cover_name}" alt="Cover"/></div>',
            stylesheet="style.css",
        )
        manifest_items.append(
            f'<item id="cover" href="cover.xhtml" media-type="application/xhtml+xml"/>'
        )
        manifest_items.append(
            f'<item id="cover-image" href="images/{cover_name}" '
            f'media-type="{cover.media_type}" properties="cover-image"/>'
        )
        spine_items.append('<itemref idref="cover"/>')

    for position, content in enumerate(contents, start=1):
        file_name = f"chapter-{position:04d}.xhtml"
        item_id = f"chapter-{position:04d}"
        body = (
            f'<h1 class="chapter-title">{_escape(content.title)}</h1>'
            '<div class="chapter-content">'
            + (content.html if content.html else '<p class="empty">Konten tidak tersedia.</p>')
            + "</div>"
        )
        files[f"OEBPS/text/{file_name}"] = _document(content.title, body)
        manifest_items.append(
            f'<item id="{item_id}" href="text/{file_name}" '
            'media-type="application/xhtml+xml"/>'
        )
        spine_items.append(f'<itemref idref="{item_id}"/>')
        nav_entries.append(
            f'<li><a href="text/{file_name}">{_escape(content.title)}</a></li>'
        )
        nav_points.append(
            f'<navPoint id="navPoint-{position}" playOrder="{position}">'
            f"<navLabel><text>{_escape(content.title)}</text></navLabel>"
            f'<content src="text/{file_name}"/>'
            "</navPoint>"
        )

    files["META-INF/container.xml"] = _container()
    files["OEBPS/style.css"] = STYLE
    files["OEBPS/nav.xhtml"] = _nav(novel.title, nav_entries)
    files["OEBPS/toc.ncx"] = _ncx(novel.title, identifier, nav_points)
    files["OEBPS/content.opf"] = _opf(
        novel=novel,
        identifier=identifier,
        modified=modified,
        manifest_items=manifest_items,
        spine_items=spine_items,
    )

    with zipfile.ZipFile(path, "w") as archive:
        archive.writestr(
            "mimetype",
            "application/epub+zip",
            compress_type=zipfile.ZIP_STORED,
        )
        for name in sorted(files):
            archive.writestr(name, files[name], compress_type=zipfile.ZIP_DEFLATED)

    return path


def _document(title: str, body: str, stylesheet: str = "../style.css") -> str:
    return (
        '<?xml version="1.0" encoding="utf-8"?>\n'
        "<!DOCTYPE html>\n"
        '<html xmlns="http://www.w3.org/1999/xhtml" '
        'xmlns:epub="http://www.idpf.org/2007/ops" xml:lang="id" lang="id">\n'
        "<head>\n"
        '<meta charset="utf-8"/>\n'
        f"<title>{_escape(title)}</title>\n"
        f'<link rel="stylesheet" type="text/css" href="{stylesheet}"/>\n'
        "</head>\n"
        f"<body>\n{body}\n</body>\n"
        "</html>\n"
    )


def _container() -> str:
    return (
        '<?xml version="1.0" encoding="utf-8"?>\n'
        '<container version="1.0" '
        'xmlns="urn:oasis:names:tc:opendocument:xmlns:container">\n'
        "<rootfiles>\n"
        '<rootfile full-path="OEBPS/content.opf" '
        'media-type="application/oebps-package+xml"/>\n'
        "</rootfiles>\n"
        "</container>\n"
    )


def _nav(title: str, entries: List[str]) -> str:
    items = "\n".join(entries)
    body = (
        '<nav epub:type="toc" id="toc">\n'
        f"<h1>{_escape(title)}</h1>\n"
        f"<ol>\n{items}\n</ol>\n"
        "</nav>"
    )
    return _document("Daftar Isi", body, stylesheet="style.css")


def _ncx(title: str, identifier: str, nav_points: List[str]) -> str:
    points = "\n".join(nav_points)
    return (
        '<?xml version="1.0" encoding="utf-8"?>\n'
        '<ncx xmlns="http://www.daisy.org/z3986/2005/ncx/" version="2005-1">\n'
        "<head>\n"
        f'<meta name="dtb:uid" content="{_escape(identifier)}"/>\n'
        '<meta name="dtb:depth" content="1"/>\n'
        '<meta name="dtb:totalPageCount" content="0"/>\n'
        '<meta name="dtb:maxPageNumber" content="0"/>\n'
        "</head>\n"
        f"<docTitle><text>{_escape(title)}</text></docTitle>\n"
        f"<navMap>\n{points}\n</navMap>\n"
        "</ncx>\n"
    )


def _opf(
    novel: Novel,
    identifier: str,
    modified: str,
    manifest_items: List[str],
    spine_items: List[str],
) -> str:
    metadata = [
        f'<dc:identifier id="bookid">{_escape(identifier)}</dc:identifier>',
        f"<dc:title>{_escape(novel.title)}</dc:title>",
        f"<dc:language>{LANGUAGE}</dc:language>",
        f"<dc:source>{_escape(novel.url)}</dc:source>",
    ]
    if novel.author:
        metadata.append(f"<dc:creator>{_escape(novel.author)}</dc:creator>")
    if novel.synopsis:
        metadata.append(f"<dc:description>{_escape(novel.synopsis)}</dc:description>")
    for genre in novel.genres:
        metadata.append(f"<dc:subject>{_escape(genre)}</dc:subject>")
    metadata.append(f'<meta property="dcterms:modified">{modified}</meta>')

    manifest = "\n".join(manifest_items)
    spine = "\n".join(spine_items)
    metadata_xml = "\n".join(metadata)

    return (
        '<?xml version="1.0" encoding="utf-8"?>\n'
        '<package xmlns="http://www.idpf.org/2007/opf" version="3.0" '
        'unique-identifier="bookid">\n'
        '<metadata xmlns:dc="http://purl.org/dc/elements/1.1/">\n'
        f"{metadata_xml}\n"
        "</metadata>\n"
        "<manifest>\n"
        f"{manifest}\n"
        "</manifest>\n"
        '<spine toc="ncx">\n'
        f"{spine}\n"
        "</spine>\n"
        "</package>\n"
    )
