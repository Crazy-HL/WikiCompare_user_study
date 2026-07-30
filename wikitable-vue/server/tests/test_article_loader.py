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
    assert article["sourceKind"] == "wikipedia"


def test_parse_article_html_marks_public_web_source_kind():
    article = parse_article_html(
        html="""
        <html><head><title>Official report</title></head><body><main>
          <h1>Official report</h1>
          <p>Revenue was $76.4 billion in 2025.</p>
        </main></body></html>
        """,
        side="left",
        title="Microsoft FY25 Q4 earnings",
        url="https://www.microsoft.com/en-us/investor/earnings/fy-2025-q4/press-release-webcast",
        revision=None,
        source_kind="web",
    )

    assert article["title"] == "Microsoft FY25 Q4 earnings"
    assert article["sourceKind"] == "web"
    assert article["paragraphs"][0]["text"] == "Revenue was $76.4 billion in 2025."


def test_parse_article_html_converts_factbook_field_cards_to_main_text_paragraphs():
    article = parse_article_html(
        html="""
        <html><body><main>
          <div class="group/field glass-card">
            <h3>Population growth rate</h3>
            <div><p>0.72% (2025 est.)</p></div>
          </div>
          <div class="group/field glass-card">
            <h3>Religions</h3>
            <div><p>Hindu 79.8%, Muslim 14.2%, Christian 2.3% (2011 est.)</p></div>
          </div>
        </main></body></html>
        """,
        side="left",
        title="India OpenFactBook profile",
        url="https://openfactbook.org/countries/india/",
        revision=None,
        source_kind="web",
    )

    assert [paragraph["text"] for paragraph in article["paragraphs"]] == [
        "Population growth rate: 0.72% (2025 est.)",
        "Religions: Hindu 79.8%, Muslim 14.2%, Christian 2.3% (2011 est.)",
    ]
    assert article["paragraphs"][0]["section"] == "Population growth rate"
    assert article["paragraphs"][0]["sentences"][0]["text"] == "Population growth rate: 0.72% (2025 est.)"
    assert article["sourceMap"]["left-s-1-1"]["sourceType"] == "sentence"
    assert 'data-source-id="left-s-1-1"' in article["html"]


def test_parse_article_html_resolves_public_web_relative_assets():
    article = parse_article_html(
        html="""
        <html><body><main>
          <a href="/countries/india/">India</a>
          <img alt="Flag of India" src="/flags/in.svg"/>
          <img alt="Map of India" src="/maps/in.png"/>
          <img alt="Responsive flag" srcset="/flags/in.svg 1x, https://cdn.example.com/in@2x.svg 2x"/>
        </main></body></html>
        """,
        side="left",
        title="India OpenFactBook profile",
        url="https://openfactbook.org/countries/india/",
        revision=None,
        source_kind="web",
    )

    assert 'href="https://openfactbook.org/countries/india/"' in article["html"]
    assert 'src="https://openfactbook.org/flags/in.svg"' in article["html"]
    assert 'src="https://openfactbook.org/maps/in.png"' in article["html"]
    assert 'srcset="https://openfactbook.org/flags/in.svg 1x, https://cdn.example.com/in@2x.svg 2x"' in article["html"]


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


def test_parse_article_html_preserves_infobox_list_items_as_structured_values():
    article = parse_article_html(
        html="""
        <html><body><table class="infobox">
          <tr>
            <th>Main industries</th>
            <td><ul><li>Electronics</li><li>Telecommunications</li><li>Shipbuilding</li></ul></td>
          </tr>
        </table></body></html>
        """,
        side="left",
        title="List",
        url="https://en.wikipedia.org/wiki/List",
        revision=None,
    )

    assert article["infobox"][0]["valueText"] == "Electronics Telecommunications Shipbuilding"
    assert article["infobox"][0]["structuredValues"] == [
        {"label": "Electronics", "value": "Electronics", "kind": "list_item"},
        {"label": "Telecommunications", "value": "Telecommunications", "kind": "list_item"},
        {"label": "Shipbuilding", "value": "Shipbuilding", "kind": "list_item"},
    ]


def test_parse_article_html_extracts_body_wikitable_year_series_as_main_text_sources():
    article = parse_article_html(
        html="""
        <html><body><main>
          <table class="wikitable">
            <tr><th>Year</th><th>Capacity (MW)</th><th>Installed/yr</th></tr>
            <tr><td>2020</td><td>250</td><td>50</td></tr>
            <tr><td>2021</td><td>400</td><td>150</td></tr>
            <tr><td>2022</td><td>700</td><td>300</td></tr>
          </table>
        </main></body></html>
        """,
        side="left",
        title="Solar",
        url="https://en.wikipedia.org/wiki/Solar",
        revision=None,
    )

    assert article["bodyTables"] == [
        {
            "id": "left-table-1-col-2",
            "key": "Capacity",
            "valueText": "2020: 250; 2021: 400; 2022: 700",
            "section": None,
            "source": "main_text",
            "side": "left",
        },
        {
            "id": "left-table-1-col-3",
            "key": "Installed",
            "valueText": "2020: 50; 2021: 150; 2022: 300",
            "section": None,
            "source": "main_text",
            "side": "left",
        },
    ]
    assert article["sourceMap"]["left-table-1-col-2"]["sourceType"] == "body_table"
    assert 'data-source-id="left-table-1-col-2"' in article["html"]


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
