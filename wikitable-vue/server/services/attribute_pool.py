from __future__ import annotations

from typing import Any


def build_attribute_pool(article: dict[str, Any], side: str, llm_client: Any) -> list[dict[str, Any]]:
    pool = _infobox_attributes(article, side)
    if llm_client is None:
        return pool

    try:
        text_attributes = llm_client.extract_text_attributes(side, article.get("paragraphs", []))
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


def _infobox_attributes(article: dict[str, Any], side: str) -> list[dict[str, Any]]:
    attributes = []
    for index, row in enumerate(article.get("infobox", []), start=1):
        attributes.append(
            {
                "id": f"{side}-attr-infobox-{index}",
                "side": side,
                "key": row.get("key", ""),
                "valueText": row.get("valueText", ""),
                "source": "infobox",
                "sourceIds": [row.get("id")],
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
    return str(value).strip()
