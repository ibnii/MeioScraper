import json
import xml.etree.ElementTree as ET
import zipfile

from novelin.exporters import export_epub, export_json, export_txt
from novelin.models import Chapter, ChapterContent, CoverImage, Novel


def _novel():
    return Novel(
        url="https://meionovels.com/novel/novel-uji/",
        slug="novel-uji",
        title="Novel Uji & Rekan",
        author="Penulis Uji",
        artist="Artis Uji",
        genres=["Fantasy", "Adventure"],
        status="OnGoing",
        synopsis="Sinopsis uji.",
    )


def _contents():
    first = Chapter(index=1, title="Chapter 1", url="https://example.test/1")
    second = Chapter(index=2, title="Chapter 2", url="https://example.test/2")
    return [
        ChapterContent(
            chapter=first,
            title="Chapter 1",
            html="<p>Paragraf satu.</p><p>Paragraf <strong>dua</strong>.</p>",
            text="Paragraf satu.\n\nParagraf dua.",
        ),
        ChapterContent(
            chapter=second,
            title="Chapter 2",
            html="<p>Paragraf tiga.</p>",
            text="Paragraf tiga.",
        ),
    ]


def test_export_txt(tmp_path):
    path = export_txt(_novel(), _contents(), tmp_path / "buku.txt")
    text = path.read_text(encoding="utf-8")

    assert "Novel Uji & Rekan" in text
    assert "Author: Penulis Uji" in text
    assert "[1] Chapter 1" in text
    assert "Paragraf satu." in text
    assert "Paragraf tiga." in text


def test_export_json(tmp_path):
    path = export_json(_novel(), _contents(), tmp_path / "buku.json")
    payload = json.loads(path.read_text(encoding="utf-8"))

    assert payload["novel"]["title"] == "Novel Uji & Rekan"
    assert len(payload["chapters"]) == 2
    assert payload["chapters"][0]["index"] == 1
    assert payload["chapters"][1]["content"] == "Paragraf tiga."


def test_export_epub_structure(tmp_path):
    path = export_epub(
        _novel(),
        _contents(),
        tmp_path / "buku.epub",
        cover=CoverImage(data=b"fake-image", media_type="image/png", extension="png"),
    )

    with zipfile.ZipFile(path) as archive:
        infos = archive.infolist()
        assert infos[0].filename == "mimetype"
        assert infos[0].compress_type == zipfile.ZIP_STORED
        assert archive.read("mimetype") == b"application/epub+zip"

        names = archive.namelist()
        assert "META-INF/container.xml" in names
        assert "OEBPS/content.opf" in names
        assert "OEBPS/nav.xhtml" in names
        assert "OEBPS/toc.ncx" in names
        assert "OEBPS/images/cover.png" in names
        assert "OEBPS/text/chapter-0001.xhtml" in names
        assert "OEBPS/text/chapter-0002.xhtml" in names

        for name in names:
            if name.endswith((".xml", ".opf", ".ncx", ".xhtml")):
                ET.fromstring(archive.read(name))

        nav = archive.read("OEBPS/nav.xhtml").decode("utf-8")
        assert "text/chapter-0001.xhtml" in nav
        assert "Chapter 1" in nav

        opf = archive.read("OEBPS/content.opf").decode("utf-8")
        assert 'properties="cover-image"' in opf
        assert 'media-type="application/xhtml+xml"' in opf
        assert "<dc:creator>Penulis Uji</dc:creator>" in opf
        assert "<dc:subject>Fantasy</dc:subject>" in opf
