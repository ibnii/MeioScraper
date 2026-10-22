import xml.etree.ElementTree as ET

import pytest

from novelin.parser import (
    html_to_text,
    parse_chapter,
    parse_chapter_list,
    parse_novel,
    sanitize_content,
)
from novelin.scraper import order_chapters
from novelin.models import Chapter

NOVEL_HTML = """
<!DOCTYPE html>
<html><body>
  <div class="post-title"><span class="manga-title-badges">HTL</span><h1>Novel Uji</h1></div>
  <div class="summary_image">
    <img src="https://meionovels.com/wp-content/uploads/cover.jpg" alt="Novel Uji"/>
  </div>
  <div class="post-content">
    <div class="post-content_item">
      <div class="summary-heading">Alternative</div>
      <div class="summary-content">Judul Alternatif</div>
    </div>
    <div class="post-content_item">
      <div class="summary-heading">Author(s)</div>
      <div class="summary-content">Penulis Uji</div>
    </div>
    <div class="post-content_item">
      <div class="summary-heading">Artist(s)</div>
      <div class="summary-content">Artis Uji</div>
    </div>
    <div class="post-content_item">
      <div class="summary-heading">Genre(s)</div>
      <div class="summary-content">
        <div class="genres-content"><a href="#">Fantasy</a><a href="#">Adventure</a></div>
      </div>
    </div>
    <div class="post-content_item">
      <div class="summary-heading">Status</div>
      <div class="summary-content">OnGoing</div>
    </div>
    <div class="post-content_item">
      <div class="summary-heading">Release</div>
      <div class="summary-content">2024</div>
    </div>
  </div>
  <div class="description-summary">
    <p>Sinopsis baris pertama.</p>
    <p>Sinopsis baris kedua.</p>
    <button class="btn">Show more</button>
  </div>
  <div id="manga-chapters-holder" data-id="12345"></div>
</body></html>
"""


def test_parse_novel_metadata():
    novel = parse_novel(NOVEL_HTML, "https://meionovels.com/novel/novel-uji/")

    assert novel.title == "Novel Uji"
    assert novel.slug == "novel-uji"
    assert novel.post_id == 12345
    assert novel.alternative_title == "Judul Alternatif"
    assert novel.author == "Penulis Uji"
    assert novel.artist == "Artis Uji"
    assert novel.genres == ["Fantasy", "Adventure"]
    assert novel.status == "OnGoing"
    assert novel.release == "2024"
    assert novel.cover_url == "https://meionovels.com/wp-content/uploads/cover.jpg"
    assert novel.synopsis == "Sinopsis baris pertama.\n\nSinopsis baris kedua."


def test_parse_novel_rejects_unknown_url():
    with pytest.raises(ValueError):
        parse_novel(NOVEL_HTML, "https://meionovels.com/")


CHAPTER_LIST_HTML = """
<div class="page-content-listing">
  <ul class="main version-chap">
    <li class="wp-manga-chapter">
      <a href="https://meionovels.com/novel/novel-uji/htl/chapter-3/">Chapter 3</a>
      <span class="chapter-release-date">3 Jan</span>
      <small class="mck-label">[1 koin]</small>
    </li>
    <li class="wp-manga-chapter">
      <a href="https://meionovels.com/novel/novel-uji/htl/chapter-2/">Chapter 2</a>
      <span class="chapter-release-date">2 Jan</span>
      <small class="mck-label">[Gratis]</small>
    </li>
    <li class="wp-manga-chapter">
      <a href="https://meionovels.com/novel/novel-uji/htl/chapter-1/">Chapter 1</a>
      <span class="chapter-release-date">1 Jan</span>
      <small class="mck-label">[Gratis]</small>
    </li>
  </ul>
</div>
"""


def test_parse_chapter_list_marks_locked_chapters():
    chapters = parse_chapter_list(CHAPTER_LIST_HTML)

    assert [chapter.title for chapter in chapters] == ["Chapter 3", "Chapter 2", "Chapter 1"]
    assert chapters[0].locked is True
    assert chapters[0].price_label == "[1 koin]"
    assert chapters[1].locked is False
    assert chapters[2].release_date == "1 Jan"


def test_parse_chapter_list_ignores_foreign_hosts():
    html = (
        '<ul><li class="wp-manga-chapter">'
        '<a href="https://example.com/novel/novel-uji/chapter-1/">Chapter 1</a>'
        "</li></ul>"
    )
    chapters = parse_chapter_list(
        html, base_url="https://meionovels.com/novel/novel-uji/"
    )
    assert chapters == []


def test_order_chapters_is_chronological():
    chapters = order_chapters(parse_chapter_list(CHAPTER_LIST_HTML))

    assert [chapter.title for chapter in chapters] == ["Chapter 1", "Chapter 2", "Chapter 3"]
    assert [chapter.index for chapter in chapters] == [1, 2, 3]


FREE_CHAPTER_HTML = """
<h1 id="chapter-heading">Novel Uji - Chapter 1</h1>
<div class="reading-content">
  <div class="text-left">
    <input type="hidden" id="wp-manga-current-chap" value="chapter-1"/>
    <p>Paragraf pertama.</p>
    <p>Paragraf <strong>kedua</strong> dengan <em>penekanan</em>.</p>
    <script>alert('x')</script>
    <style>.x { color: red; }</style>
    <div class="inner"><p>Paragraf ketiga.</p></div>
    <p><img src="ilustrasi.jpg" alt="Ilustrasi"/></p>
  </div>
</div>
"""

LOCKED_CHAPTER_HTML = """
<h1 id="chapter-heading">Novel Uji - Chapter 2</h1>
<div class="reading-content">
  <input type="hidden" id="wp-manga-current-chap" value="chapter-2"/>
  <section class="mck-gate">
    <h2>Chapter terkunci</h2>
    <p>Buka chapter ini dengan 1 koin.</p>
  </section>
</div>
"""


def _chapter():
    return Chapter(index=1, title="Chapter 1", url="https://meionovels.com/novel/novel-uji/htl/chapter-1/")


def test_parse_free_chapter_sanitizes_content():
    content = parse_chapter(FREE_CHAPTER_HTML, _chapter())

    assert content.locked is False
    assert content.title == "Novel Uji - Chapter 1"
    assert "<script" not in content.html
    assert "<style" not in content.html
    assert "<input" not in content.html
    assert "<strong>kedua</strong>" in content.html
    assert "<em>penekanan</em>" in content.html
    assert "[Gambar: Ilustrasi]" in content.html
    assert "Paragraf ketiga." in content.text
    assert "\n\n" in content.text
    assert "alert" not in content.text


def test_parse_locked_chapter_returns_gate_message():
    content = parse_chapter(LOCKED_CHAPTER_HTML, _chapter())

    assert content.locked is True
    assert "Chapter terkunci" in content.gate_message
    assert content.text == ""


def test_sanitized_fragment_is_xml_well_formed():
    content = parse_chapter(FREE_CHAPTER_HTML, _chapter())
    root = ET.fromstring(f"<root>{content.html}</root>")
    assert root.tag == "root"


def test_html_to_text_collapses_blank_lines():
    text = html_to_text("<p>Satu</p><p>Dua<br/>Tiga</p>")
    assert text == "Satu\n\nDua\nTiga"


def test_sanitize_content_handles_empty_element():
    from bs4 import BeautifulSoup

    element = BeautifulSoup("<div></div>", "html.parser").div
    assert sanitize_content(element) == ""
