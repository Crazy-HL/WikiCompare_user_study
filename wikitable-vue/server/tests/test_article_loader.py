import json
from pathlib import Path

from bs4 import BeautifulSoup

from services.article_loader import parse_article_html, split_sentences


FIXTURE_DIR = Path(__file__).parent / "fixtures"


def test_parse_article_html_adds_traceable_sources():
    html = (FIXTURE_DIR / "article_left.html").read_text()

    article = parse_article_html(
        html=html,
        side="left",
        title="Economy_of_Example_A",
        url="https://en.wikipedia.org/wiki/Economy_of_Example_A",
        revision=None,
    )

    assert article["title"] == "Economy_of_Example_A"
    assert article["outline"][0]["id"] == "left-heading-1"
    assert article["infobox"][0]["id"] == "left-info-1"
    assert article["paragraphs"][0]["id"] == "left-p-1"
    assert article["paragraphs"][0]["sentences"][0]["id"] == "left-s-1-1"
    assert 'data-source-id="left-info-1"' in article["html"]


def test_parse_article_html_source_map_contains_infobox_and_sentence():
    html = (FIXTURE_DIR / "article_left.html").read_text()

    article = parse_article_html(
        html=html,
        side="left",
        title="Economy_of_Example_A",
        url="https://en.wikipedia.org/wiki/Economy_of_Example_A",
        revision=None,
    )

    source_map = article["sourceMap"]
    assert source_map["left-info-1"]["sourceType"] == "infobox"
    assert source_map["left-s-1-1"]["sourceType"] == "sentence"


def test_parse_article_html_returns_json_serializable_article():
    html = (FIXTURE_DIR / "article_left.html").read_text()

    article = parse_article_html(
        html=html,
        side="left",
        title="Economy_of_Example_A",
        url="https://en.wikipedia.org/wiki/Economy_of_Example_A",
        revision=None,
    )

    json.dumps(article)


def test_parse_article_html_preserves_inline_markup():
    html = (FIXTURE_DIR / "article_left.html").read_text()

    article = parse_article_html(
        html=html,
        side="left",
        title="Economy_of_Example_A",
        url="https://en.wikipedia.org/wiki/Economy_of_Example_A",
        revision=None,
    )

    assert '<a href="/wiki/U.S.">U.S.</a>' in article["html"]
    assert article["paragraphs"][0]["sentences"][1]["id"] == "left-s-1-2"
    assert 'data-source-id="left-s-1-2"' in article["html"]
    assert article["sourceMap"]["left-s-1-2"]["sourceType"] == "sentence"


def test_parse_article_html_anchors_every_sentence_with_trailing_whitespace():
    article = parse_article_html(
        html="<html><body><p>Final sentence. </p></body></html>",
        side="left",
        title="Trailing",
        url="https://en.wikipedia.org/wiki/Trailing",
        revision=None,
    )

    soup = BeautifulSoup(article["html"], "lxml")
    for sentence in article["paragraphs"][0]["sentences"]:
        node = soup.select_one(f'[data-source-id="{sentence["id"]}"]')
        assert node is not None
        assert " ".join(node.get_text(" ", strip=True).split()) == sentence["text"]


def test_parse_article_html_anchors_sentences_inside_inline_tags():
    article = parse_article_html(
        html="<html><body><p><span>First fact. Second fact.</span></p></body></html>",
        side="left",
        title="Inline",
        url="https://en.wikipedia.org/wiki/Inline",
        revision=None,
    )

    soup = BeautifulSoup(article["html"], "lxml")
    assert [item["id"] for item in article["paragraphs"][0]["sentences"]] == [
        "left-s-1-1",
        "left-s-1-2",
    ]
    assert soup.select_one('[data-source-id="left-s-1-1"]').get_text(" ", strip=True) == "First fact."
    assert soup.select_one('[data-source-id="left-s-1-2"]').get_text(" ", strip=True) == "Second fact."


def test_parse_article_html_preserves_existing_heading_id():
    html = (FIXTURE_DIR / "article_left.html").read_text()

    article = parse_article_html(
        html=html,
        side="left",
        title="Economy_of_Example_A",
        url="https://en.wikipedia.org/wiki/Economy_of_Example_A",
        revision=None,
    )

    assert '<h2 data-source-id="left-heading-2" id="Overview">Overview</h2>' in article["html"]


def test_split_sentences_preserves_common_abbreviations():
    assert split_sentences("The U.S. economy grew. Apple Inc. expanded.") == [
        "The U.S. economy grew.",
        "Apple Inc. expanded.",
    ]


def test_split_sentences_handles_abbreviation_at_sentence_end():
    assert split_sentences("He lives in the U.S. It is large.") == [
        "He lives in the U.S.",
        "It is large.",
    ]
