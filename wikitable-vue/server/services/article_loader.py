from __future__ import annotations

import re
from typing import Any
from urllib.parse import quote

from bs4 import BeautifulSoup

from services.models import SourceRef


WIKIPEDIA_HTML_ENDPOINT = "https://en.wikipedia.org/api/rest_v1/page/html"
COMMON_ABBREVIATIONS = (
    "U.S.",
    "U.K.",
    "Inc.",
    "Ltd.",
    "Co.",
    "Dr.",
    "Mr.",
    "Ms.",
    "Prof.",
)


def fetch_article_html(title: str, revision: str | None = None) -> str:
    import requests

    encoded_title = quote(title, safe=":_()")
    url = f"{WIKIPEDIA_HTML_ENDPOINT}/{encoded_title}"
    if revision is not None:
        url = f"{url}/{revision}"

    response = requests.get(url, timeout=20)
    response.raise_for_status()
    return response.text


def split_sentences(text: str) -> list[str]:
    normalized = " ".join(text.split())
    if not normalized:
        return []

    protected_text = normalized
    protected_abbreviations = {}
    for index, abbreviation in enumerate(COMMON_ABBREVIATIONS):
        token = f"__ABBR_{index}__"
        protected_abbreviations[token] = abbreviation
        protected_text = protected_text.replace(abbreviation, token)

    sentences = []
    for sentence in re.split(r"(?<=[.!?])\s+", protected_text):
        for token, abbreviation in protected_abbreviations.items():
            sentence = sentence.replace(token, abbreviation)
        if sentence:
            sentences.append(sentence)
    return sentences


def parse_article_html(
    html: str,
    side: str,
    title: str,
    url: str,
    revision: str | None,
) -> dict[str, Any]:
    soup = BeautifulSoup(html, "lxml")
    source_map: dict[str, SourceRef] = {}
    outline: list[dict[str, Any]] = []
    infobox: list[dict[str, Any]] = []
    paragraphs: list[dict[str, Any]] = []

    for tag in soup.select("script, style, noscript, .mw-editsection, sup.reference"):
        tag.decompose()

    for index, heading in enumerate(soup.select("h1, h2, h3, h4, h5, h6"), start=1):
        source_id = f"{side}-heading-{index}"
        text = _node_text(heading)
        if not heading.get("id"):
            heading["id"] = source_id
        heading["data-source-id"] = source_id

        outline.append(
            {
                "id": source_id,
                "level": int(heading.name[1]),
                "text": text,
                "side": side,
            }
        )
        source_map[source_id] = _source_ref(source_id, side, "heading", text)

    for index, row in enumerate(_infobox_rows(soup), start=1):
        source_id = f"{side}-info-{index}"
        key = _node_text(row.find("th"))
        value_text = _node_text(row.find("td"))
        row["data-source-id"] = source_id

        infobox.append(
            {
                "id": source_id,
                "key": key,
                "valueText": value_text,
                "section": None,
                "source": "infobox",
                "side": side,
            }
        )
        source_map[source_id] = _source_ref(
            source_id,
            side,
            "infobox",
            f"{key}: {value_text}",
        )

    for paragraph_index, paragraph in enumerate(_non_empty_paragraphs(soup), start=1):
        paragraph_id = f"{side}-p-{paragraph_index}"
        text = _node_text(paragraph)
        sentences = split_sentences(text)
        sentence_records = []

        paragraph["data-source-id"] = paragraph_id
        should_wrap_sentences = paragraph.find() is None
        if should_wrap_sentences:
            paragraph.clear()
        for sentence_index, sentence in enumerate(sentences, start=1):
            sentence_id = f"{side}-s-{paragraph_index}-{sentence_index}"
            if should_wrap_sentences:
                span = soup.new_tag("span")
                span["data-source-id"] = sentence_id
                span.string = sentence
                if sentence_index > 1:
                    paragraph.append(" ")
                paragraph.append(span)

            sentence_records.append({"id": sentence_id, "text": sentence, "side": side})
            source_map[sentence_id] = _source_ref(
                sentence_id,
                side,
                "sentence",
                sentence,
            )

        paragraphs.append(
            {
                "id": paragraph_id,
                "text": text,
                "sentences": sentence_records,
                "side": side,
            }
        )
        source_map[paragraph_id] = _source_ref(paragraph_id, side, "paragraph", text)

    return {
        "title": title,
        "url": url,
        "revision": revision,
        "html": str(soup),
        "outline": outline,
        "infobox": infobox,
        "paragraphs": paragraphs,
        "sourceMap": {
            source_id: source_ref.to_dict()
            for source_id, source_ref in source_map.items()
        },
    }


def _infobox_rows(soup: BeautifulSoup):
    for row in soup.select("table.infobox tr, table.sidebar tr, table.toccolours tr"):
        if row.find("th") and row.find("td"):
            yield row


def _non_empty_paragraphs(soup: BeautifulSoup):
    for paragraph in soup.find_all("p"):
        if _node_text(paragraph):
            yield paragraph


def _node_text(node) -> str:
    if node is None:
        return ""
    return " ".join(node.get_text(" ", strip=True).split())


def _source_ref(source_id: str, side: str, source_type: str, text: str) -> SourceRef:
    return SourceRef(
        id=source_id,
        side=side,
        source_type=source_type,
        text=text,
        selector=f'[data-source-id="{source_id}"]',
    )
