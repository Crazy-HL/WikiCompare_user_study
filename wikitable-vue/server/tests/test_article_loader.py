from pathlib import Path

from services.article_loader import parse_article_html


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
    assert 'data-source-id="left-s-1-1"' in article["html"]


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
    assert source_map["left-info-1"].source_type == "infobox"
    assert source_map["left-s-1-1"].source_type == "sentence"
