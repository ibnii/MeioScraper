import pytest

from novelin.utils import novel_slug, parse_chapter_range, safe_filename


def test_novel_slug_from_novel_url():
    assert novel_slug("https://meionovels.com/novel/akulah-dewa/") == "akulah-dewa"


def test_novel_slug_from_chapter_url():
    url = "https://meionovels.com/novel/akulah-dewa/htl/chapter-63/"
    assert novel_slug(url) == "akulah-dewa"


def test_safe_filename_replaces_forbidden_characters():
    assert safe_filename('judul: "uji"/test?') == "judul_ _uji__test_"
    assert safe_filename("   ") == "novel"


def test_parse_chapter_range_simple():
    assert parse_chapter_range("1-3,5", total=10) == {1, 2, 3, 5}


def test_parse_chapter_range_open_ended():
    assert parse_chapter_range("7-", total=10) == {7, 8, 9, 10}


def test_parse_chapter_range_filters_beyond_total():
    assert parse_chapter_range("1-20", total=10) == set(range(1, 11))


def test_parse_chapter_range_returns_none_for_empty():
    assert parse_chapter_range(None) is None
    assert parse_chapter_range("  ") is None


@pytest.mark.parametrize("value", ["abc", "0", "5-2"])
def test_parse_chapter_range_rejects_invalid(value):
    with pytest.raises(ValueError):
        parse_chapter_range(value, total=10)
