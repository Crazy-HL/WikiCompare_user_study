from __future__ import annotations

import re
from typing import Any
from urllib.parse import quote, urljoin

from bs4 import BeautifulSoup, NavigableString, Tag

from services.models import SourceRef


WIKIPEDIA_HTML_ENDPOINT = "https://en.wikipedia.org/api/rest_v1/page/html"
WIKIPEDIA_REQUEST_HEADERS = {
    "User-Agent": "WikiCompare/0.1 (https://github.com/Crazy-HL/WikiCompare)",
    "Accept": "text/html,application/xhtml+xml",
}
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
COMMON_SENTENCE_STARTERS = {
    "A",
    "After",
    "An",
    "At",
    "Before",
    "By",
    "For",
    "From",
    "He",
    "However",
    "In",
    "It",
    "Meanwhile",
    "On",
    "She",
    "That",
    "The",
    "There",
    "These",
    "They",
    "This",
    "Those",
}


def fetch_article_html(title: str, revision: str | None = None) -> str:
    import requests

    encoded_title = quote(title, safe=":_()")
    url = f"{WIKIPEDIA_HTML_ENDPOINT}/{encoded_title}"
    if revision is not None:
        url = f"{url}/{revision}"

    response = requests.get(url, headers=WIKIPEDIA_REQUEST_HEADERS, timeout=20)
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
    source_kind: str = "wikipedia",
) -> dict[str, Any]:
    soup = BeautifulSoup(html, "lxml")
    content_root = _article_content_root(soup)
    source_map: dict[str, SourceRef] = {}
    outline: list[dict[str, Any]] = []
    infobox: list[dict[str, Any]] = []
    body_tables: list[dict[str, Any]] = []
    paragraphs: list[dict[str, Any]] = []

    for tag in content_root.select(
        ",".join(
            [
                "script",
                "style",
                "noscript",
                ".mw-editsection",
                ".reference",
                ".reflist",
                ".references",
                ".navbox",
                ".metadata",
                ".ambox",
                ".hatnote",
                ".toc",
                ".shortdescription",
                ".printfooter",
                ".catlinks",
                ".authority-control",
                ".portal",
                ".succession-box",
                "link[rel='stylesheet']",
            ]
        )
    ):
        tag.decompose()

    if source_kind != "wikipedia":
        _resolve_relative_urls(content_root, url)

    for index, heading in enumerate(content_root.select("h1, h2, h3, h4, h5, h6"), start=1):
        source_id = f"{side}-heading-{index}"
        text = _node_text(heading)
        if not text:
            continue
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

    for index, row in enumerate(_infobox_rows(content_root), start=1):
        source_id = f"{side}-info-{index}"
        value_cell = row.find("td")
        key = _node_text(row.find("th"))
        value_text = _node_text(value_cell)
        if not key or not value_text:
            continue
        row["data-source-id"] = source_id

        row_record = {
            "id": source_id,
            "key": key,
            "valueText": value_text,
            "section": None,
            "source": "infobox",
            "side": side,
        }
        structured_values = _structured_values(value_cell)
        if structured_values:
            row_record["structuredValues"] = structured_values
        infobox.append(row_record)
        source_map[source_id] = _source_ref(
            source_id,
            side,
            "infobox",
            f"{key}: {value_text}",
        )

    for table_attribute in _body_table_year_series(content_root):
        source_id = f"{side}-table-{table_attribute['tableIndex']}-col-{table_attribute['columnIndex']}"
        cell = table_attribute.pop("_cell")
        cell["data-source-id"] = source_id
        body_table_record = {
            "id": source_id,
            "key": table_attribute["key"],
            "valueText": table_attribute["valueText"],
            "section": None,
            "source": "main_text",
            "side": side,
        }
        body_tables.append(body_table_record)
        source_map[source_id] = _source_ref(
            source_id,
            side,
            "body_table",
            f"{body_table_record['key']}: {body_table_record['valueText']}",
        )

    paragraph_index = 0
    for field_record in _factbook_field_paragraphs(content_root):
        paragraph_index += 1
        paragraph_id = f"{side}-p-{paragraph_index}"
        text = field_record["text"]
        sentences = split_sentences(text) or [text]
        sentence_records = []
        field_node = field_record["node"]
        field_node["data-source-id"] = f"{side}-s-{paragraph_index}-1"
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
                "section": field_record["section"],
            }
        )
        source_map[paragraph_id] = _source_ref(paragraph_id, side, "paragraph", text)

    for paragraph in _non_empty_paragraphs(content_root):
        paragraph_index += 1
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
        "sourceKind": source_kind,
        "html": _inner_html(content_root),
        "outline": outline,
        "infobox": infobox,
        "bodyTables": body_tables,
        "paragraphs": paragraphs,
        "sourceMap": {
            source_id: source_ref.to_dict()
            for source_id, source_ref in source_map.items()
        },
    }


def _article_content_root(soup: BeautifulSoup) -> Tag:
    root = soup.select_one(".mw-parser-output")
    if root is not None:
        return root
    root = soup.select_one("main")
    if root is not None:
        return root
    root = soup.select_one("#bodyContent, #mw-content-text")
    if root is not None:
        return root
    return soup.body or soup


def _inner_html(node: Tag) -> str:
    return "".join(str(child) for child in node.contents)


def _resolve_relative_urls(root: Tag, base_url: str) -> None:
    if not base_url:
        return
    for tag in root.find_all(True):
        for attr in ("href", "src", "poster"):
            value = tag.get(attr)
            if value:
                tag[attr] = _absolute_url(base_url, value)
        srcset = tag.get("srcset")
        if srcset:
            tag["srcset"] = _absolute_srcset(base_url, srcset)


def _absolute_url(base_url: str, value: str) -> str:
    value = str(value).strip()
    if not value or value.startswith(("#", "data:", "mailto:", "tel:", "javascript:")):
        return value
    return urljoin(base_url, value)


def _absolute_srcset(base_url: str, value: str) -> str:
    candidates = []
    for candidate in str(value).split(","):
        parts = candidate.strip().split()
        if not parts:
            continue
        absolute = _absolute_url(base_url, parts[0])
        candidates.append(" ".join([absolute, *parts[1:]]))
    return ", ".join(candidates)


def _infobox_rows(root: Tag):
    for row in root.select("table.infobox tr, table.sidebar tr, table.toccolours tr"):
        if row.find("th") and row.find("td"):
            yield row


def _body_table_year_series(root: Tag) -> list[dict[str, Any]]:
    attributes: list[dict[str, Any]] = []
    for table_index, table in enumerate(root.select("table.wikitable, table.sortable"), start=1):
        classes = set(table.get("class") or [])
        if classes.intersection({"infobox", "navbox", "sidebar", "metadata"}):
            continue
        rows = table.find_all("tr")
        if len(rows) < 4:
            continue
        headers = [_node_text(cell) for cell in rows[0].find_all(["th", "td"])]
        header_cells = rows[0].find_all(["th", "td"])
        if len(headers) < 2 or _normalized_table_header(headers[0]) not in {"year", "date"}:
            continue
        row_values: list[list[str]] = []
        for row in rows[1:]:
            cells = [_node_text(cell) for cell in row.find_all(["th", "td"])]
            if len(cells) < len(headers):
                continue
            year = _year_token(cells[0])
            if year is None:
                continue
            row_values.append([str(year)] + cells[1:len(headers)])
        if len(row_values) < 3:
            continue
        for column_index in range(1, len(headers)):
            points = []
            for values in row_values:
                value = _table_numeric_text(values[column_index])
                if not value:
                    continue
                points.append((values[0], value))
            if len(points) < 3:
                continue
            attributes.append(
                {
                    "_table": table,
                    "_cell": header_cells[column_index],
                    "tableIndex": table_index,
                    "columnIndex": column_index + 1,
                    "key": _clean_table_metric_header(headers[column_index], headers),
                    "valueText": "; ".join(f"{year}: {value}" for year, value in points),
                }
            )
    return attributes


def _factbook_field_paragraphs(root: Tag) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for field_node in root.find_all(_is_factbook_field_card):
        label_node = field_node.find(["h2", "h3", "h4", "h5", "h6"])
        label = _node_text(label_node)
        value = _factbook_field_value(field_node, label_node)
        if not label or not value:
            continue
        records.append(
            {
                "node": field_node,
                "section": label,
                "text": f"{label}: {value}",
            }
        )
    return records


def _is_factbook_field_card(node) -> bool:
    if not isinstance(node, Tag):
        return False
    return "group/field" in set(node.get("class") or [])


def _factbook_field_value(field_node: Tag, label_node: Tag | None) -> str:
    paragraphs = [
        _node_text(paragraph)
        for paragraph in field_node.find_all("p")
        if _node_text(paragraph)
    ]
    if paragraphs:
        return " ".join(paragraphs)

    text = _node_text(field_node)
    label = _node_text(label_node)
    if label and text.startswith(label):
        text = text[len(label):].strip()
    return text


def _normalized_table_header(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", str(value or "").lower()).strip()


def _clean_table_metric_header(value: str, table_headers: list[str] | None = None) -> str:
    raw_header = str(value or "")
    if _is_total_capacity_header(raw_header, table_headers):
        return "Capacity"
    header = re.sub(r"\([^)]*\)", " ", raw_header)
    header = re.sub(r"/\s*yr\b", "", header, flags=re.IGNORECASE)
    header = re.sub(r"\byr\b", "", header, flags=re.IGNORECASE)
    header = re.sub(r"\btotal\b", " ", header, flags=re.IGNORECASE)
    header = re.sub(r"\binstalled capacity\b", "Installed", header, flags=re.IGNORECASE)
    header = re.sub(r"\s+", " ", header).strip(" -:/")
    return header or raw_header.strip()


def _is_total_capacity_header(value: str, table_headers: list[str] | None) -> bool:
    normalized = _normalized_table_header(value)
    if not normalized.startswith("total"):
        return False
    if _has_capacity_unit(value):
        return True
    return any("capacity" in _normalized_table_header(header) for header in table_headers or [])


def _has_capacity_unit(value: str) -> bool:
    return bool(
        re.search(
            r"\b(?:kw|mw|gw|kwh|mwh|gwh|kwp|mwp|gwp|kilowatts?|megawatts?|gigawatts?)\b",
            str(value or ""),
            re.IGNORECASE,
        )
    )


def _year_token(value: str) -> int | None:
    match = re.search(r"\b((?:18|19|20|21)\d{2})\b", str(value or ""))
    return int(match.group(1)) if match else None


def _table_numeric_text(value: str) -> str:
    text = _clean_wikipedia_text(value)
    match = re.search(
        r"[-+]?(?:\d{1,3}(?:,\d{3})+|\d+)(?:\.\d+)?(?:\s*%|\s*(?:thousand|million|billion|trillion))?",
        text,
        re.IGNORECASE,
    )
    if not match:
        return ""
    return match.group(0).strip()


def _non_empty_paragraphs(root: Tag):
    for paragraph in root.find_all("p"):
        if paragraph.find_parent(_is_factbook_field_card) is not None:
            continue
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

    inline_tokens = list(_inline_tokens(paragraph, []))
    paragraph.clear()

    sentence_index = 1
    current_span = _new_sentence_span(soup, side, paragraph_index, sentence_index)
    paragraph.append(current_span)

    for token_type, path, value in inline_tokens:
        if token_type == "tag":
            _append_tag_with_path(soup, current_span, path, value)
            continue

        for segment in _sentence_text_segments(value):
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


def _inline_tokens(node: Tag, path: list[Tag]):
    for child in node.contents:
        if isinstance(child, NavigableString):
            yield ("text", path, str(child))
            continue
        if not isinstance(child, Tag):
            continue
        child_path = path + [child]
        if child.contents:
            yielded_child = False
            for token in _inline_tokens(child, child_path):
                yielded_child = True
                yield token
            if not yielded_child:
                yield ("tag", path, child)
        else:
            yield ("tag", path, child)


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


def _append_tag_with_path(
    soup: BeautifulSoup,
    target: Tag,
    path: list[Tag],
    tag: Tag,
) -> None:
    if not path:
        target.append(_clone_empty_tag(soup, tag))
        return

    root_clone = _clone_empty_tag(soup, path[0])
    current_clone = root_clone
    for ancestor in path[1:]:
        child_clone = _clone_empty_tag(soup, ancestor)
        current_clone.append(child_clone)
        current_clone = child_clone
    current_clone.append(_clone_empty_tag(soup, tag))
    target.append(root_clone)


def _clone_empty_tag(soup: BeautifulSoup, tag: Tag) -> Tag:
    clone = soup.new_tag(tag.name)
    for key, value in tag.attrs.items():
        if key == "id":
            continue
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
    if not following_text:
        return False
    if following_text[0].islower():
        return True
    next_word = re.match(r"[A-Z][A-Za-z'-]*", following_text)
    if not next_word:
        return False
    return next_word.group(0) not in COMMON_SENTENCE_STARTERS


def _node_text(node) -> str:
    if node is None:
        return ""
    return _clean_wikipedia_text(node.get_text(" ", strip=True))


def _structured_values(node) -> list[dict[str, str]]:
    if node is None:
        return []

    list_items = [_node_text(item) for item in node.find_all("li", recursive=True)]
    clean_items = _unique_nonempty(list_items)
    if len(clean_items) >= 2:
        return [
            {"label": item, "value": item, "kind": "list_item"}
            for item in clean_items
        ]
    return []


def _unique_nonempty(values: list[str]) -> list[str]:
    seen = set()
    items = []
    for value in values:
        clean = _clean_wikipedia_text(value)
        normalized = clean.lower()
        if not clean or normalized in seen:
            continue
        seen.add(normalized)
        items.append(clean)
    return items


def _clean_wikipedia_text(text: Any) -> str:
    cleaned = str(text or "")
    cleaned = re.sub(r"\[\s*(?:\d+|[a-z])\s*\]", " ", cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r"\bedit\b", " ", cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r"\s+([,.;:%)])", r"\1", cleaned)
    cleaned = re.sub(r"([(])\s+", r"\1", cleaned)
    return " ".join(cleaned.split())


def _source_ref(source_id: str, side: str, source_type: str, text: str) -> SourceRef:
    return SourceRef(
        id=source_id,
        side=side,
        source_type=source_type,
        text=text,
        selector=f'[data-source-id="{source_id}"]',
    )
