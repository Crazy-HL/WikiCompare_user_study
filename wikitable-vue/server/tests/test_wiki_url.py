import pytest

from services.wiki_url import parse_english_wikipedia_url, WikiUrlError


def test_parse_article_url():
    parsed = parse_english_wikipedia_url("https://en.wikipedia.org/wiki/Economy_of_Japan")

    assert parsed.title == "Economy_of_Japan"
    assert parsed.normalized_url == "https://en.wikipedia.org/wiki/Economy_of_Japan"
    assert parsed.revision is None


def test_parse_oldid_revision_url():
    parsed = parse_english_wikipedia_url(
        "https://en.wikipedia.org/w/index.php?title=Economy_of_Japan&oldid=1297943898"
    )

    assert parsed.title == "Economy_of_Japan"
    assert parsed.revision == "1297943898"


def test_reject_non_english_wikipedia():
    with pytest.raises(WikiUrlError, match="Only en.wikipedia.org"):
        parse_english_wikipedia_url("https://zh.wikipedia.org/wiki/人工智能")


def test_reject_non_wikipedia():
    with pytest.raises(WikiUrlError, match="Only en.wikipedia.org"):
        parse_english_wikipedia_url("https://example.com/wiki/Economy_of_Japan")
