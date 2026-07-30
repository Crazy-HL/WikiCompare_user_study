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
    assert parsed.display_url == (
        "https://en.wikipedia.org/w/index.php?title=Economy_of_Japan&oldid=1297943898"
    )


def test_parse_url_normalizes_spaces_to_underscores():
    parsed = parse_english_wikipedia_url("https://en.wikipedia.org/wiki/Economy of Japan")

    assert parsed.title == "Economy_of_Japan"
    assert parsed.normalized_url == "https://en.wikipedia.org/wiki/Economy_of_Japan"


def test_parse_url_quotes_normalized_url():
    parsed = parse_english_wikipedia_url("https://en.wikipedia.org/wiki/S%C3%A3o Paulo")

    assert parsed.title == "São_Paulo"
    assert parsed.normalized_url == "https://en.wikipedia.org/wiki/S%C3%A3o_Paulo"


def test_parse_accepts_http_urls():
    parsed = parse_english_wikipedia_url("http://en.wikipedia.org/wiki/Economy_of_Japan")

    assert parsed.title == "Economy_of_Japan"
    assert parsed.normalized_url == "https://en.wikipedia.org/wiki/Economy_of_Japan"


def test_parse_accepts_uppercase_host():
    parsed = parse_english_wikipedia_url("https://EN.WIKIPEDIA.ORG/wiki/Economy_of_Japan")

    assert parsed.title == "Economy_of_Japan"
    assert parsed.normalized_url == "https://en.wikipedia.org/wiki/Economy_of_Japan"


def test_parse_accepts_default_ports():
    https_parsed = parse_english_wikipedia_url("https://en.wikipedia.org:443/wiki/Economy_of_Japan")
    http_parsed = parse_english_wikipedia_url("http://en.wikipedia.org:80/wiki/Economy_of_Japan")

    assert https_parsed.title == "Economy_of_Japan"
    assert http_parsed.title == "Economy_of_Japan"


def test_reject_non_english_wikipedia():
    with pytest.raises(WikiUrlError, match="Only en.wikipedia.org"):
        parse_english_wikipedia_url("https://zh.wikipedia.org/wiki/人工智能")


def test_reject_non_wikipedia():
    with pytest.raises(WikiUrlError, match="Only en.wikipedia.org"):
        parse_english_wikipedia_url("https://example.com/wiki/Economy_of_Japan")


def test_reject_unsupported_scheme():
    with pytest.raises(WikiUrlError):
        parse_english_wikipedia_url("ftp://en.wikipedia.org/wiki/Economy_of_Japan")


def test_reject_unsupported_path():
    with pytest.raises(WikiUrlError, match="Unsupported English Wikipedia URL format"):
        parse_english_wikipedia_url("https://en.wikipedia.org/api/rest_v1/page/summary/Economy_of_Japan")


def test_reject_empty_article_title():
    with pytest.raises(WikiUrlError, match="Wikipedia article URL must include a title"):
        parse_english_wikipedia_url("https://en.wikipedia.org/wiki/")


@pytest.mark.parametrize(
    "url",
    [
        "https://en.wikipedia.org:444/wiki/Economy_of_Japan",
        "http://en.wikipedia.org:8080/wiki/Economy_of_Japan",
    ],
)
def test_reject_non_default_ports(url):
    with pytest.raises(WikiUrlError, match="Only en.wikipedia.org"):
        parse_english_wikipedia_url(url)
