import pytest

from novelin.models import Novel
from novelin.scraper import MeionovelsScraper, normalize_chapter_url


class FakeResponse:
    def __init__(self, text="", content=b"", headers=None):
        self.text = text
        self.content = content
        self.headers = headers or {}


class FakeClient:
    def __init__(self, get_map=None, post_map=None):
        self.get_map = get_map or {}
        self.post_map = post_map or {}
        self.has_cookie = False

    def get(self, url, **kwargs):
        return self.get_map[url]

    def post(self, url, data=None, headers=None):
        return self.post_map[url]


def _chapter_html(number):
    return (
        f'<li class="wp-manga-chapter">'
        f'<a href="https://meionovels.com/novel/novel-uji/htl/chapter-{number}/">'
        f"Chapter {number}</a>"
        f'<small class="mck-label">[Gratis]</small>'
        f"</li>"
    )


def test_normalize_url_accepts_slug():
    scraper = MeionovelsScraper(client=FakeClient())
    assert scraper.normalize_url("novel-uji") == "https://meionovels.com/novel/novel-uji/"


def test_normalize_url_accepts_chapter_url():
    scraper = MeionovelsScraper(client=FakeClient())
    url = "https://meionovels.com/novel/novel-uji/htl/chapter-3/"
    assert scraper.normalize_url(url) == "https://meionovels.com/novel/novel-uji/"


def test_normalize_chapter_url_accepts_chapter_paths():
    url = "https://meionovels.com/novel/novel-uji/htl/chapter-3/"
    assert normalize_chapter_url(url) == url


@pytest.mark.parametrize(
    "url",
    [
        "",
        "https://example.com/novel/novel-uji/chapter-1/",
        "https://meionovels.com/novel/novel-uji/",
        "javascript:alert(1)",
    ],
)
def test_normalize_chapter_url_rejects_invalid_values(url):
    with pytest.raises(ValueError):
        normalize_chapter_url(url)


def test_normalize_url_rejects_other_domains():
    scraper = MeionovelsScraper(client=FakeClient())
    with pytest.raises(ValueError):
        scraper.normalize_url("https://example.com/novel/novel-uji/")


def test_fetch_chapters_orders_and_indexes_pages():
    novel = Novel(
        url="https://meionovels.com/novel/novel-uji/",
        slug="novel-uji",
        title="Novel Uji",
    )
    page_one = (
        "<ul>"
        + _chapter_html(4)
        + _chapter_html(3)
        + '</ul><div class="pagination"><a data-page="1">1</a><a data-page="2">2</a></div>'
    )
    page_two = "<ul>" + _chapter_html(2) + _chapter_html(1) + "</ul>"

    client = FakeClient(
        post_map={
            "https://meionovels.com/novel/novel-uji/ajax/chapters/?t=1": FakeResponse(page_one),
            "https://meionovels.com/novel/novel-uji/ajax/chapters/?t=2": FakeResponse(page_two),
        }
    )
    chapters = MeionovelsScraper(client=client).fetch_chapters(novel)

    assert [chapter.index for chapter in chapters] == [1, 2, 3, 4]
    assert [chapter.title for chapter in chapters] == [
        "Chapter 1",
        "Chapter 2",
        "Chapter 3",
        "Chapter 4",
    ]


def test_download_cover_reads_content_type():
    novel = Novel(
        url="https://meionovels.com/novel/novel-uji/",
        slug="novel-uji",
        title="Novel Uji",
        cover_url="https://meionovels.com/cover.png",
    )
    client = FakeClient(
        get_map={
            "https://meionovels.com/cover.png": FakeResponse(
                content=b"png-bytes", headers={"Content-Type": "image/png"}
            )
        }
    )
    cover = MeionovelsScraper(client=client).download_cover(novel)

    assert cover is not None
    assert cover.data == b"png-bytes"
    assert cover.media_type == "image/png"
    assert cover.extension == "png"
