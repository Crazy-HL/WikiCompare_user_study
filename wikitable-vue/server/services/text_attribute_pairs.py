from __future__ import annotations

import re
from typing import Any


MEASUREMENT_TERMS = "cases|employees|members|population|samples|users|revenue|accuracy"
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
PUBLICATION_YEAR_FOLLOW_RE = re.compile(r"^\s*(study|paper|article|journal|conference)\b", re.I)
PUBLICATION_YEAR_PRECEDE_RE = re.compile(
    r"\b(study|paper|article|journal|conference)\s+(in|from)\s*$",
    re.I,
)
EMERGENCE_CONTEXT_RE = re.compile(
    r"\b(founded|introduced|launched|released|created|developed|grew|emerged)\b",
    re.I,
)
PROPORTION_CONTEXT_RE = re.compile(r"\b(accuracy|score|share|rate|percent)\b", re.I)
PROPORTION_PREFIX_RE = re.compile(r"\b(accuracy|score|share|rate|percent)(?:\s+\w+){0,3}\s+of\s+$", re.I)
RANKING_CONTEXT_RE = re.compile(r"\brank\b", re.I)
MEASUREMENT_CONTEXT_RE = re.compile(rf"\b({MEASUREMENT_TERMS})\b", re.I)
CURRENCY_SYMBOL_RE = re.compile(r"[$€£¥₩]\s*$")
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
    if (
        not DATA_CONTEXT_RE.search(text)
        and not MEASUREMENT_CONTEXT_RE.search(text)
        and not MONEY_RE.search(text)
        and not ORDINAL_RE.search(text)
    ):
        return []
    items: list[dict[str, Any]] = []
    for match in NUMBER_RE.finditer(text):
        raw = match.group(1)
        unit = (match.group(2) or "").lower()
        if _is_publication_context_year(raw, unit, text, match):
            continue
        try:
            value = float(raw.replace(",", ""))
        except ValueError:
            continue
        role = _data_role(text, unit, match)
        item: dict[str, Any] = {"value": int(value) if value.is_integer() else value, "role": role}
        if unit:
            item["unit"] = unit
        items.append(item)
    return items


def _data_role(text: str, unit: str, match: re.Match) -> str:
    context = _role_context(text, match)
    if _has_currency_symbol(text, match) or unit in SCALE_UNITS:
        return "scale"
    if unit in {"%", "percent"}:
        return "proportion"
    if _has_local_proportion_prefix(text, match):
        return "proportion"
    if EMERGENCE_CONTEXT_RE.search(context):
        return "emergence_time"
    if PROPORTION_CONTEXT_RE.search(context):
        return "proportion"
    if RANKING_CONTEXT_RE.search(context) or ORDINAL_RE.search(context):
        return "ranking"
    return "quantity"


def _is_publication_context_year(raw: str, unit: str, text: str, match: re.Match) -> bool:
    if unit or _has_currency_symbol(text, match) or not PUBLICATION_NOISE_RE.search(text):
        return False
    try:
        value = int(raw.replace(",", ""))
    except ValueError:
        return False
    if not 1800 <= value <= 2100 or len(raw.replace(",", "")) != 4:
        return False
    if EMERGENCE_CONTEXT_RE.search(_role_context(text, match)):
        return False
    if PUBLICATION_YEAR_FOLLOW_RE.search(text[match.end() :]):
        return True
    if PUBLICATION_YEAR_PRECEDE_RE.search(text[: match.start()]):
        return True
    return not _has_measurement_context(text, match)


def _role_context(text: str, match: re.Match) -> str:
    start = match.start()
    end = match.end()
    left = _last_boundary(text, start)
    right = _next_boundary(text, end)
    return text[left:right]


def _last_boundary(text: str, index: int) -> int:
    boundary = 0
    for pattern in [r"[;,]\s*", r"\s+and\s+", r"\s+with\s+"]:
        for match in re.finditer(pattern, text[:index], re.I):
            boundary = max(boundary, match.end())
    return boundary


def _next_boundary(text: str, index: int) -> int:
    boundary = len(text)
    for pattern in [r"[;,]\s*", r"\s+and\s+", r"\s+with\s+"]:
        match = re.search(pattern, text[index:], re.I)
        if match:
            boundary = min(boundary, index + match.start())
    return boundary


def _has_currency_symbol(text: str, match: re.Match) -> bool:
    return bool(CURRENCY_SYMBOL_RE.search(text[max(0, match.start() - 4) : match.start()]))


def _has_local_proportion_prefix(text: str, match: re.Match) -> bool:
    return bool(PROPORTION_PREFIX_RE.search(text[max(0, match.start() - 48) : match.start()]))


def _has_measurement_context(text: str, match: re.Match) -> bool:
    context = text[match.end() : min(len(text), match.end() + 32)]
    return bool(MEASUREMENT_CONTEXT_RE.search(context))


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
