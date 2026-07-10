from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, TimeoutError
import re
from typing import Any


TEXT_ATTRIBUTE_EXECUTOR = ThreadPoolExecutor(max_workers=4)
MAX_TEXT_ATTRIBUTE_TIMEOUT_SECONDS = 8.0
RELATED_TEXT_LIMIT = 4
TOKEN_RE = re.compile(r"[a-z0-9]+", re.IGNORECASE)
STOPWORDS = {
    "a",
    "an",
    "and",
    "are",
    "as",
    "at",
    "by",
    "for",
    "from",
    "in",
    "is",
    "it",
    "its",
    "main",
    "of",
    "on",
    "or",
    "the",
    "to",
    "was",
    "were",
    "with",
}


def build_attribute_pool(article: dict[str, Any], side: str, llm_client: Any) -> list[dict[str, Any]]:
    pool = _infobox_attributes(article, side)
    text_index = 1
    for attribute in _body_table_attributes(article.get("bodyTables", []), side, text_index):
        pool.append(attribute)
        text_index += 1
    if not pool:
        for attribute in _rule_text_attributes(article.get("paragraphs", []), side, text_index):
            pool.append(attribute)
            text_index += 1
    if llm_client is None:
        return pool

    try:
        text_attributes = _extract_text_attributes_with_timeout(
            llm_client,
            side,
            article.get("paragraphs", []),
        )
    except Exception:
        return pool
    if not isinstance(text_attributes, list):
        return pool

    paragraphs_by_id = {
        paragraph.get("id"): paragraph
        for paragraph in article.get("paragraphs", [])
        if paragraph.get("id")
    }

    for raw_attribute in text_attributes:
        attribute = _text_attribute(raw_attribute, side, paragraphs_by_id, text_index)
        if attribute is None:
            continue
        duplicate = _find_duplicate_infobox_attribute(pool, attribute)
        if duplicate is not None:
            _merge_related_source_ids(duplicate, attribute.get("sourceIds") or [])
            continue
        pool.append(attribute)
        text_index += 1

    return pool


def _rule_text_attributes(paragraphs: Any, side: str, start_index: int) -> list[dict[str, Any]]:
    if not isinstance(paragraphs, list):
        return []
    specs = [
        ("Overview", _is_overview_sentence),
        ("History", _is_history_sentence),
        ("Applications", _is_application_sentence),
        ("Methods", _is_method_sentence),
    ]
    attributes: list[dict[str, Any]] = []
    used_sentence_ids: set[str] = set()
    for key, matcher in specs:
        sentence = _first_matching_sentence(paragraphs, matcher, used_sentence_ids)
        if sentence is None:
            continue
        source_id = sentence["id"]
        used_sentence_ids.add(source_id)
        attributes.append(
            {
                "id": f"{side}-attr-rule-text-{start_index + len(attributes)}",
                "side": side,
                "key": key,
                "valueText": sentence["text"],
                "source": "main_text",
                "sourceIds": [source_id],
                "paragraphId": sentence.get("paragraphId"),
                "confidence": 0.72,
            }
        )
    return attributes


def _body_table_attributes(body_tables: Any, side: str, start_index: int) -> list[dict[str, Any]]:
    if not isinstance(body_tables, list):
        return []
    attributes = []
    for row in body_tables:
        if not isinstance(row, dict):
            continue
        source_id = _clean_text(row.get("id"))
        key = _clean_text(row.get("key"))
        value_text = _clean_text(row.get("valueText"))
        if not source_id or not key or not value_text:
            continue
        attributes.append(
            {
                "id": f"{side}-attr-body-table-{start_index + len(attributes)}",
                "side": side,
                "key": key,
                "valueText": value_text,
                "source": "main_text",
                "sourceIds": [source_id],
                "section": row.get("section"),
                "dataPriority": True,
                "dataRole": "quantity",
            }
        )
    return attributes


def _first_matching_sentence(paragraphs: list[dict[str, Any]], matcher, used_sentence_ids: set[str]) -> dict[str, Any] | None:
    for paragraph_index, paragraph in enumerate(paragraphs):
        if not isinstance(paragraph, dict):
            continue
        sentences = paragraph.get("sentences")
        if not isinstance(sentences, list):
            continue
        for sentence_index, sentence in enumerate(sentences):
            if not isinstance(sentence, dict):
                continue
            source_id = sentence.get("id")
            text = _clean_text(sentence.get("text"))
            if not source_id or source_id in used_sentence_ids or not text:
                continue
            if matcher(text, paragraph_index, sentence_index):
                return {"id": source_id, "text": text, "paragraphId": paragraph.get("id")}
    return None


def _is_overview_sentence(text: str, paragraph_index: int, sentence_index: int) -> bool:
    lower = text.lower()
    return paragraph_index == 0 and sentence_index == 0 and (
        " is " in f" {lower} " or " are " in f" {lower} "
    )


def _is_history_sentence(text: str, _paragraph_index: int, _sentence_index: int) -> bool:
    lower = text.lower()
    return any(word in lower for word in ["history", "founded", "origin", "developed", "introduced", "coined", "grew from"])


def _is_application_sentence(text: str, _paragraph_index: int, _sentence_index: int) -> bool:
    lower = text.lower()
    return any(word in lower for word in ["application", "applications", "used", "uses", "include", "including"])


def _is_method_sentence(text: str, _paragraph_index: int, _sentence_index: int) -> bool:
    lower = text.lower()
    return any(word in lower for word in ["method", "methods", "algorithm", "algorithms", "technique", "techniques", "model", "models"])


def _extract_text_attributes_with_timeout(
    llm_client: Any,
    side: str,
    paragraphs: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    timeout = _text_attribute_timeout(llm_client)
    future = TEXT_ATTRIBUTE_EXECUTOR.submit(
        llm_client.extract_text_attributes,
        side,
        paragraphs,
    )
    try:
        return future.result(timeout=timeout)
    except TimeoutError:
        future.cancel()
        return []


def _text_attribute_timeout(llm_client: Any) -> float:
    configured = getattr(getattr(llm_client, "config", None), "timeout_seconds", None)
    try:
        timeout = float(configured)
    except (TypeError, ValueError):
        timeout = MAX_TEXT_ATTRIBUTE_TIMEOUT_SECONDS
    if timeout <= 0:
        return MAX_TEXT_ATTRIBUTE_TIMEOUT_SECONDS
    return min(timeout, MAX_TEXT_ATTRIBUTE_TIMEOUT_SECONDS)


def _infobox_attributes(article: dict[str, Any], side: str) -> list[dict[str, Any]]:
    attributes = []
    paragraphs = article.get("paragraphs", [])
    parent_key = ""
    for row in article.get("infobox", []):
        if not isinstance(row, dict):
            continue
        source_id = _clean_text(row.get("id"))
        raw_key = _clean_text(row.get("key"))
        key = _infobox_display_key(raw_key, parent_key)
        value_text = _clean_text(row.get("valueText"))
        if not source_id or not key or not value_text:
            continue
        if not _is_infobox_subrow_key(raw_key):
            parent_key = raw_key
        index = len(attributes) + 1
        attribute = {
            "id": f"{side}-attr-infobox-{index}",
            "side": side,
            "key": key,
            "valueText": value_text,
            "source": "infobox",
            "sourceIds": [source_id],
            "section": row.get("section"),
        }
        structured_values = _structured_values(row.get("structuredValues"))
        if structured_values:
            attribute["structuredValues"] = structured_values
        related_source_ids = _related_text_source_ids(key, value_text, paragraphs)
        if related_source_ids:
            attribute["relatedSourceIds"] = related_source_ids
        attributes.append(attribute)
    return attributes


def _infobox_display_key(key: str, parent_key: str) -> str:
    if not _is_infobox_subrow_key(key) or not parent_key:
        return key
    child_key = re.sub(r"^[•\-\u2013\u2014]+\s*", "", key).strip()
    if not child_key:
        return key
    return f"{parent_key}: {child_key}"


def _is_infobox_subrow_key(key: str) -> bool:
    return bool(re.match(r"^\s*[•\-\u2013\u2014]\s*", key or ""))


def _text_attribute(
    raw_attribute: Any,
    side: str,
    paragraphs_by_id: dict[str, dict[str, Any]],
    index: int,
) -> dict[str, Any] | None:
    if not isinstance(raw_attribute, dict):
        return None

    key = _clean_text(raw_attribute.get("key"))
    value_text = _clean_text(raw_attribute.get("valueText"))
    paragraph_id = raw_attribute.get("paragraphId")
    sentence_ids = raw_attribute.get("sentenceIds")

    if not key or not value_text:
        return None
    if not isinstance(paragraph_id, str) or paragraph_id not in paragraphs_by_id:
        return None
    if not isinstance(sentence_ids, list) or not sentence_ids:
        return None
    if not all(isinstance(sentence_id, str) and sentence_id for sentence_id in sentence_ids):
        return None

    valid_sentence_ids = {
        sentence.get("id")
        for sentence in paragraphs_by_id[paragraph_id].get("sentences", [])
        if sentence.get("id")
    }
    if not all(sentence_id in valid_sentence_ids for sentence_id in sentence_ids):
        return None

    attribute = {
        "id": f"{side}-attr-main-text-{index}",
        "side": side,
        "key": key,
        "valueText": value_text,
        "source": "main_text",
        "sourceIds": sentence_ids,
        "paragraphId": paragraph_id,
        "confidence": raw_attribute.get("confidence"),
    }
    structured_values = _structured_values(raw_attribute.get("structuredValues"))
    if structured_values:
        attribute["structuredValues"] = structured_values
    return attribute


def _structured_values(raw_values: Any) -> list[dict[str, Any]]:
    if not isinstance(raw_values, list):
        return []
    values = []
    for raw_value in raw_values:
        if not isinstance(raw_value, dict):
            continue
        value = _clean_text(raw_value.get("value") or raw_value.get("label"))
        if not value:
            continue
        item = {
            "label": _clean_text(raw_value.get("label")) or value,
            "value": value,
            "kind": _clean_text(raw_value.get("kind")) or "item",
        }
        values.append(item)
    return values


def _find_duplicate_infobox_attribute(
    pool: list[dict[str, Any]],
    text_attribute: dict[str, Any],
) -> dict[str, Any] | None:
    text_key = _normal_key(text_attribute.get("key"))
    text_value = _normal_value(text_attribute.get("valueText"))
    if not text_key or not text_value:
        return None
    for attribute in pool:
        if attribute.get("source") != "infobox":
            continue
        if _normal_key(attribute.get("key")) != text_key:
            continue
        if _structured_values_add_new_items(attribute, text_attribute):
            continue
        if _values_overlap(attribute.get("valueText"), text_attribute.get("valueText")):
            return attribute
    return None


def _structured_values_add_new_items(
    infobox_attribute: dict[str, Any],
    text_attribute: dict[str, Any],
) -> bool:
    text_values = {
        _normal_value(item.get("value") or item.get("label"))
        for item in text_attribute.get("structuredValues") or []
        if isinstance(item, dict)
    }
    if not text_values:
        return False
    infobox_values = {
        _normal_value(item.get("value") or item.get("label"))
        for item in infobox_attribute.get("structuredValues") or []
        if isinstance(item, dict)
    }
    return bool(text_values - infobox_values)


def _merge_related_source_ids(attribute: dict[str, Any], source_ids: list[str]) -> None:
    related = list(attribute.get("relatedSourceIds") or [])
    seen = set(related)
    for source_id in source_ids:
        if not isinstance(source_id, str) or not source_id or source_id in seen:
            continue
        related.append(source_id)
        seen.add(source_id)
    if related:
        attribute["relatedSourceIds"] = related


def _related_text_source_ids(key: str, value_text: str, paragraphs: Any) -> list[str]:
    if not isinstance(paragraphs, list):
        return []

    related: list[str] = []
    seen: set[str] = set()
    for paragraph in paragraphs:
        if not isinstance(paragraph, dict):
            continue
        sentences = paragraph.get("sentences")
        candidates = sentences if isinstance(sentences, list) and sentences else [paragraph]
        for candidate in candidates:
            if not isinstance(candidate, dict):
                continue
            source_id = candidate.get("id")
            text = candidate.get("text")
            if not isinstance(source_id, str) or not source_id or source_id in seen:
                continue
            if not _text_matches_infobox_attribute(key, value_text, text):
                continue
            related.append(source_id)
            seen.add(source_id)
            if len(related) >= RELATED_TEXT_LIMIT:
                return related
    return related


def _text_matches_infobox_attribute(key: str, value_text: str, text: Any) -> bool:
    text_normal = _normal_key(text)
    if not text_normal:
        return False

    text_tokens = set(text_normal.split())
    key_tokens = _significant_tokens(key)
    value_tokens = _significant_tokens(value_text)
    value_numbers = set(re.findall(r"\d+(?:\.\d+)?", _normal_value(value_text)))

    key_phrase = _normal_key(key)
    if key_phrase and key_phrase in text_normal:
        return True

    acronym = _acronym(key_tokens)
    if acronym and acronym in text_tokens:
        return True

    key_hits = len(set(key_tokens).intersection(text_tokens))
    if len(key_tokens) >= 2 and key_hits >= min(2, len(key_tokens)):
        return True

    text_numbers = set(re.findall(r"\d+(?:\.\d+)?", text_normal))
    if value_numbers and value_numbers.intersection(text_numbers) and (
        key_hits >= 1 or (acronym and acronym in text_tokens)
    ):
        return True

    value_hits = len(set(value_tokens).intersection(text_tokens))
    return key_hits >= 1 and value_hits >= 1


def _significant_tokens(value: Any) -> list[str]:
    tokens = TOKEN_RE.findall(_clean_text(value).lower())
    return [
        token
        for token in tokens
        if len(token) > 2 and token not in STOPWORDS
    ]


def _acronym(tokens: list[str]) -> str:
    if len(tokens) < 2:
        return ""
    acronym = "".join(token[0] for token in tokens if token)
    return acronym if len(acronym) >= 2 else ""


def _values_overlap(left: Any, right: Any) -> bool:
    left_numbers = set(re.findall(r"\d+(?:\.\d+)?", _normal_value(left)))
    right_numbers = set(re.findall(r"\d+(?:\.\d+)?", _normal_value(right)))
    if left_numbers and right_numbers and left_numbers.intersection(right_numbers):
        return True
    left_words = set(_normal_value(left).split())
    right_words = set(_normal_value(right).split())
    return len(left_words.intersection(right_words)) >= 2


def _normal_key(value: Any) -> str:
    return re.sub(r"[^a-z0-9]+", " ", _clean_text(value).lower()).strip()


def _normal_value(value: Any) -> str:
    return re.sub(r"[^a-z0-9.]+", " ", _clean_text(value).lower()).strip()


def _clean_text(value: Any) -> str:
    if value is None:
        return ""
    cleaned = str(value)
    cleaned = re.sub(r"\[\s*(?:\d+|[a-z])\s*\]", " ", cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r"\bedit\b", " ", cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r"\s+([,.;:%)])", r"\1", cleaned)
    cleaned = re.sub(r"([(])\s+", r"\1", cleaned)
    return " ".join(cleaned.split())
