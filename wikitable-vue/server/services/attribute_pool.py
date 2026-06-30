from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, TimeoutError
import re
from typing import Any


TEXT_ATTRIBUTE_EXECUTOR = ThreadPoolExecutor(max_workers=4)
MAX_TEXT_ATTRIBUTE_TIMEOUT_SECONDS = 20.0


def build_attribute_pool(article: dict[str, Any], side: str, llm_client: Any) -> list[dict[str, Any]]:
    pool = _infobox_attributes(article, side)
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

    text_index = 1
    for raw_attribute in text_attributes:
        attribute = _text_attribute(raw_attribute, side, paragraphs_by_id, text_index)
        if attribute is None:
            continue
        pool.append(attribute)
        text_index += 1

    return pool


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
    for row in article.get("infobox", []):
        if not isinstance(row, dict):
            continue
        source_id = _clean_text(row.get("id"))
        key = _clean_text(row.get("key"))
        value_text = _clean_text(row.get("valueText"))
        if not source_id or not key or not value_text:
            continue
        index = len(attributes) + 1
        attributes.append(
            {
                "id": f"{side}-attr-infobox-{index}",
                "side": side,
                "key": key,
                "valueText": value_text,
                "source": "infobox",
                "sourceIds": [source_id],
                "section": row.get("section"),
            }
        )
    return attributes


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

    return {
        "id": f"{side}-attr-main-text-{index}",
        "side": side,
        "key": key,
        "valueText": value_text,
        "source": "main_text",
        "sourceIds": sentence_ids,
        "paragraphId": paragraph_id,
        "confidence": raw_attribute.get("confidence"),
    }


def _clean_text(value: Any) -> str:
    if value is None:
        return ""
    cleaned = str(value)
    cleaned = re.sub(r"\[\s*(?:\d+|[a-z])\s*\]", " ", cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r"\bedit\b", " ", cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r"\s+([,.;:%)])", r"\1", cleaned)
    cleaned = re.sub(r"([(])\s+", r"\1", cleaned)
    return " ".join(cleaned.split())
