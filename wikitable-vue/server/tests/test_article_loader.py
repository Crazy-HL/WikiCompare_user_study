import json
from pathlib import Path

import requests
from bs4 import BeautifulSoup

from services.article_loader import fetch_article_html, parse_article_html, split_sentences


FIXTURE_DIR = Path(__file__).parent / "fixtures"


def test_fetch_article_html_sends_wikipedia_user_agent(monkeypatch):
    calls = []

    class FakeResponse:
        text = "<html></html>"

        def raise_for_status(self):
            return None

    def fake_get(url, **kwargs):
        calls.append((url, kwargs))
        return FakeResponse()

    monkeypatch.setattr(requests, "get", fake_get)

    assert fetch_article_html("Economy_of_South_Korea") == "<html></html>"

    assert calls[0][0] == "https://en.wikipedia.org/api/rest_v1/page/html/Economy_of_South_Korea"
    assert "WikiCompare" in calls[0][1]["headers"]["User-Agent"]


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


def test_parse_article_html_preserves_textless_inline_elements():
    article = parse_article_html(
        html='<html><body><p>First fact.<br/><img alt="chart" src="chart.png"/> Second fact.</p></body></html>',
        side="left",
        title="InlineMedia",
        url="https://en.wikipedia.org/wiki/InlineMedia",
        revision=None,
    )

    soup = BeautifulSoup(article["html"], "lxml")
    assert soup.select_one("br") is not None
    assert soup.select_one('img[alt="chart"][src="chart.png"]') is not None
    assert soup.select_one('[data-source-id="left-s-1-2"]').get_text(" ", strip=True) == "Second fact."


def test_parse_article_html_does_not_duplicate_inline_ids():
    article = parse_article_html(
        html='<html><body><p><span id="legacy">First fact. Second fact.</span></p></body></html>',
        side="left",
        title="InlineIds",
        url="https://en.wikipedia.org/wiki/InlineIds",
        revision=None,
    )

    assert article["html"].count('id="legacy"') <= 1


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


def test_parse_article_html_returns_readable_article_fragment_without_wikipedia_boilerplate():
    article = parse_article_html(
        html="""
        <html>
          <head><title>Ignore me</title></head>
          <body>
            <header>Site chrome</header>
            <main id="content">
              <section class="mw-parser-output">
                <h1>Example</h1>
                <p>Population reached 10 million.<sup class="reference">[1]</sup></p>
                <table class="navbox"><tr><td>Navigation noise</td></tr></table>
                <div class="metadata">Maintenance noise</div>
                <ol class="references"><li>Reference noise</li></ol>
              </section>
            </main>
          </body>
        </html>
        """,
        side="left",
        title="Example",
        url="https://en.wikipedia.org/wiki/Example",
        revision=None,
    )

    assert "<html" not in article["html"]
    assert "<body" not in article["html"]
    assert "Site chrome" not in article["html"]
    assert "Navigation noise" not in article["html"]
    assert "Maintenance noise" not in article["html"]
    assert "Reference noise" not in article["html"]
    assert "[1]" not in article["paragraphs"][0]["text"]
    assert "Population reached 10 million." in article["paragraphs"][0]["text"]


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


def test_split_sentences_keeps_abbreviation_before_uppercase_phrase():
    assert split_sentences("The U.S. Army grew. It deployed units.") == [
        "The U.S. Army grew.",
        "It deployed units.",
    ]
