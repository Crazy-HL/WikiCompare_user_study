from __future__ import annotations

import re
from typing import Any


NUMBER_RE = re.compile(
    r"([-+]?(?:\d{1,3}(?:,\d{3})+|\d+)(?:\.\d+)?)\s*(%|percent|million|billion|trillion)?",
    re.I,
)
MONEY_RE = re.compile(r"[$€£¥₩]\s*[-+]?(?:\d{1,3}(?:,\d{3})+|\d+)(?:\.\d+)?", re.I)
ORDINAL_RE = re.compile(r"\b\d+(?:st|nd|rd|th)\b", re.I)
DATA_CONTEXT_RE = re.compile(
    r"\b(founded|introduced|launched|released|created|developed|grew|emerged|"
    r"accuracy|rate|share|percent|rank|score|revenue|population|users|models|cases|"
    r"growth|decline|increase|decrease|duration)\b",
    re.I,
)
CLAIM_CUE_RE = re.compile(
    r"\b(is|are|refers to|used|uses|include|includes|applications|methods|"
    r"techniques|consists|types|risks|limitations|impact|effects)\b",
    re.I,
)
PUBLICATION_NOISE_RE = re.compile(r"\b(published|paper|study|article|journal|conference)\b", re.I)
EMERGENCE_CONTEXT_RE = re.compile(
    r"\b(founded|introduced|launched|released|created|developed|grew|emerged)\b",
    re.I,
)
PROPORTION_CONTEXT_RE = re.compile(r"\b(accuracy|share|rate|percent)\b", re.I)
RANKING_CONTEXT_RE = re.compile(r"\brank\b", re.I)
SCALE_UNITS = {"million", "billion", "trillion"}


def build_text_evidence_candidates(article: dict[str, Any], side: str, limit: int = 24) -> list[dict[str, Any]]:
    if limit <= 0:
        return []
    candidates: list[dict[str, Any]] = []
    for paragraph in article.get("paragraphs", []) or []:
        if not isinstance(paragraph, dict):
            continue
        for sentence in paragraph.get("sentences", []) or []:
            candidate = _sentence_candidate(sentence, paragraph, side)
            if candidate is not None:
                candidates.append(candidate)
            if len(candidates) >= limit:
                return candidates
    return candidates


def _sentence_candidate(sentence: Any, paragraph: dict[str, Any], side: str) -> dict[str, Any] | None:
    if not isinstance(sentence, dict):
        return None
    sentence_id = sentence.get("id")
    text = _clean_text(sentence.get("text"))
    if not isinstance(sentence_id, str) or not sentence_id or not text:
        return None
    data_items = _data_items(text)
    if data_items:
        return {
            "side": side,
            "kind": "data",
            "claimText": text,
            "sentenceIds": [sentence_id],
            "paragraphId": paragraph.get("id"),
            "section": paragraph.get("section"),
            "semanticCue": _semantic_cue(text),
            "dataItems": data_items,
        }
    if CLAIM_CUE_RE.search(text):
        return {
            "side": side,
            "kind": "claim",
            "claimText": text,
            "sentenceIds": [sentence_id],
            "paragraphId": paragraph.get("id"),
            "section": paragraph.get("section"),
            "semanticCue": _semantic_cue(text),
            "dataItems": [],
        }
    return None


def _data_items(text: str) -> list[dict[str, Any]]:
    if not DATA_CONTEXT_RE.search(text) and not MONEY_RE.search(text) and not ORDINAL_RE.search(text):
        return []
    items: list[dict[str, Any]] = []
    for match in NUMBER_RE.finditer(text):
        raw = match.group(1)
        unit = (match.group(2) or "").lower()
        if _is_publication_context_year(raw, unit, text):
            continue
        try:
            value = float(raw.replace(",", ""))
        except ValueError:
            continue
        role = _data_role(text, unit)
        item: dict[str, Any] = {"value": int(value) if value.is_integer() else value, "role": role}
        if unit:
            item["unit"] = unit
        items.append(item)
    return items


def _data_role(text: str, unit: str) -> str:
    if MONEY_RE.search(text) or unit in SCALE_UNITS:
        return "scale"
    if unit in {"%", "percent"} or PROPORTION_CONTEXT_RE.search(text):
        return "proportion"
    if EMERGENCE_CONTEXT_RE.search(text):
        return "emergence_time"
    if RANKING_CONTEXT_RE.search(text) or ORDINAL_RE.search(text):
        return "ranking"
    return "quantity"


def _is_publication_context_year(raw: str, unit: str, text: str) -> bool:
    if unit or not PUBLICATION_NOISE_RE.search(text):
        return False
    try:
        value = int(raw.replace(",", ""))
    except ValueError:
        return False
    return 1800 <= value <= 2100 and len(raw.replace(",", "")) == 4


def _semantic_cue(text: str) -> str:
    lower = text.lower()
    for label, pattern in [
        ("applications", r"\b(application|applications|used|uses|include|includes)\b"),
        ("methods", r"\b(method|methods|technique|techniques|algorithm|model)\b"),
        ("limitations", r"\b(risk|risks|limitation|limitations|criticism)\b"),
        ("definition", r"\b(is|are|refers to)\b"),
        ("history", r"\b(founded|introduced|launched|developed|grew|emerged)\b"),
    ]:
        if re.search(pattern, lower):
            return label
    return ""


def _clean_text(value: Any) -> str:
    return " ".join(str(value or "").split())
