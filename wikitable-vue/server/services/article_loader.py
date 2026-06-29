from __future__ import annotations

import re
from typing import Any
from urllib.parse import quote

from bs4 import BeautifulSoup, NavigableString, Tag

from services.models import SourceRef


WIKIPEDIA_HTML_ENDPOINT = "https://en.wikipedia.org/api/rest_v1/page/html"
FLEXIBLE_ABBREVIATIONS = (
    "U.S.",
    "U.K.",
    "Inc.",
    "Ltd.",
    "Co.",
)
NON_TERMINAL_ABBREVIATIONS = (
    "Dr.",
    "Mr.",
    "Ms.",
    "Prof.",
    "e.g.",
    "i.e.",
    "vs.",
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

    sentences = []
    start = 0
    for match in re.finditer(r"[.!?](?=\s|$)", normalized):
        punctuation_end = match.end()
        next_start = punctuation_end
        while next_start < len(normalized) and normalized[next_start].isspace():
            next_start += 1

        candidate = normalized[start:punctuation_end].strip()
        if not candidate:
            start = next_start
            continue
        if _is_protected_abbreviation_boundary(candidate, normalized[next_start:]):
            continue

        sentences.append(candidate)
        start = next_start

    tail = normalized[start:].strip()
    if tail:
        sentences.append(tail)
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
        _wrap_paragraph_sentences(soup, paragraph, sentences, side, paragraph_index)
        for sentence_index, sentence in enumerate(sentences, start=1):
            sentence_id = f"{side}-s-{paragraph_index}-{sentence_index}"
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


def _wrap_paragraph_sentences(
    soup: BeautifulSoup,
    paragraph: Tag,
    sentences: list[str],
    side: str,
    paragraph_index: int,
) -> None:
    if not sentences:
        return

    text_nodes = [
        (_tag_path(paragraph, text_node), str(text_node))
        for text_node in paragraph.find_all(string=True)
    ]
    paragraph.clear()

    sentence_index = 1
    current_span = _new_sentence_span(soup, side, paragraph_index, sentence_index)
    paragraph.append(current_span)

    for path, text in text_nodes:
        for segment in _sentence_text_segments(text):
            if not segment:
                continue
            _append_segment_with_path(soup, current_span, path, segment)
            if sentence_index > len(sentences):
                continue
            if not _span_matches_sentence(current_span, sentences[sentence_index - 1]):
                continue
            sentence_index += 1
            if sentence_index <= len(sentences):
                current_span = _new_sentence_span(
                    soup,
                    side,
                    paragraph_index,
                    sentence_index,
                )
                paragraph.append(current_span)

    for empty_span in paragraph.select("span[data-source-id]"):
        if not _node_text(empty_span):
            empty_span.decompose()


def _sentence_text_segments(text: str) -> list[str]:
    segments = []
    start = 0
    for match in re.finditer(r"[.!?](?=\s|$)", text):
        end = match.end()
        segments.append(text[start:end])
        start = end
    if start < len(text):
        segments.append(text[start:])
    return segments


def _tag_path(paragraph: Tag, text_node: NavigableString) -> list[Tag]:
    path = []
    parent = text_node.parent
    while isinstance(parent, Tag) and parent is not paragraph:
        path.append(parent)
        parent = parent.parent
    return list(reversed(path))


def _append_segment_with_path(
    soup: BeautifulSoup,
    target: Tag,
    path: list[Tag],
    text: str,
) -> None:
    if not path:
        target.append(NavigableString(text))
        return

    root_clone = _clone_empty_tag(soup, path[0])
    current_clone = root_clone
    for tag in path[1:]:
        child_clone = _clone_empty_tag(soup, tag)
        current_clone.append(child_clone)
        current_clone = child_clone
    current_clone.append(NavigableString(text))
    target.append(root_clone)


def _clone_empty_tag(soup: BeautifulSoup, tag: Tag) -> Tag:
    clone = soup.new_tag(tag.name)
    for key, value in tag.attrs.items():
        clone.attrs[key] = list(value) if isinstance(value, list) else value
    return clone


def _new_sentence_span(
    soup: BeautifulSoup,
    side: str,
    paragraph_index: int,
    sentence_index: int,
) -> Tag:
    span = soup.new_tag("span")
    span["data-source-id"] = f"{side}-s-{paragraph_index}-{sentence_index}"
    return span


def _span_matches_sentence(span: Tag, sentence: str) -> bool:
    return _node_text(span) == sentence


def _is_protected_abbreviation_boundary(candidate: str, following_text: str) -> bool:
    lowered = candidate.lower()
    if any(lowered.endswith(abbreviation.lower()) for abbreviation in NON_TERMINAL_ABBREVIATIONS):
        return True
    if not any(lowered.endswith(abbreviation.lower()) for abbreviation in FLEXIBLE_ABBREVIATIONS):
        return False
    return bool(following_text[:1] and following_text[0].islower())


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
