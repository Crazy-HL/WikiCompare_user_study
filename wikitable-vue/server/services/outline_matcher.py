from __future__ import annotations

import re
from difflib import SequenceMatcher
from typing import Any


IGNORED_HEADINGS = {
    "references",
    "notes",
    "citations",
    "bibliography",
    "external links",
    "further reading",
    "see also",
    "contents",
}

RELATED_HEADINGS = {
    "history": {"historical background", "background", "early history"},
    "economy": {"economic history", "economic overview"},
    "demographics": {"population", "people"},
    "culture": {"society and culture", "arts and culture"},
    "government": {"politics", "politics and government"},
}


def build_outline_matches(
    left_outline: list[dict[str, Any]],
    right_outline: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    left_items = [_outline_item(item, "left") for item in left_outline]
    right_items = [_outline_item(item, "right") for item in right_outline]
    left_items = [item for item in left_items if item is not None]
    right_items = [item for item in right_items if item is not None]

    candidates = []
    for left_item in left_items:
        for right_item in right_items:
            score = _heading_similarity(left_item["normalized"], right_item["normalized"])
            if score < 0.72:
                continue
            candidates.append((score, left_item, right_item))

    candidates.sort(
        key=lambda item: (
            -item[0],
            abs(item[1]["level"] - item[2]["level"]),
            item[1]["index"],
            item[2]["index"],
        )
    )

    matches = []
    used_left = set()
    used_right = set()
    for score, left_item, right_item in candidates:
        if left_item["id"] in used_left or right_item["id"] in used_right:
            continue
        used_left.add(left_item["id"])
        used_right.add(right_item["id"])
        matches.append(
            {
                "leftId": left_item["id"],
                "rightId": right_item["id"],
                "label": _match_label(left_item["text"], right_item["text"]),
                "score": round(score, 3),
            }
        )

    matches.sort(key=lambda item: _outline_index(item["leftId"]))
    return matches


def _outline_item(item: dict[str, Any], side: str) -> dict[str, Any] | None:
    if not isinstance(item, dict):
        return None
    source_id = str(item.get("id") or "").strip()
    text = " ".join(str(item.get("text") or "").split())
    normalized = _normalize_heading(text)
    level = int(item.get("level") or 0)
    if not source_id or not normalized:
        return None
    if level <= 1 or normalized in IGNORED_HEADINGS:
        return None
    return {
        "id": source_id,
        "text": text,
        "normalized": normalized,
        "level": level,
        "side": side,
        "index": _outline_index(source_id),
    }


def _heading_similarity(left: str, right: str) -> float:
    if left == right:
        return 1.0
    if right in RELATED_HEADINGS.get(left, set()) or left in RELATED_HEADINGS.get(right, set()):
        return 0.9
    left_tokens = set(left.split())
    right_tokens = set(right.split())
    if not left_tokens or not right_tokens:
        return 0.0
    jaccard = len(left_tokens & right_tokens) / len(left_tokens | right_tokens)
    sequence = SequenceMatcher(None, left, right).ratio()
    contained = 0.86 if left in right or right in left else 0.0
    return max(jaccard, sequence, contained)


def _normalize_heading(text: str) -> str:
    normalized = text.lower()
    normalized = re.sub(r"\[[^\]]+\]", " ", normalized)
    normalized = re.sub(r"[^a-z0-9]+", " ", normalized)
    normalized = re.sub(r"\b(?:the|and|of|in|by|for)\b", " ", normalized)
    return " ".join(normalized.split())


def _match_label(left_text: str, right_text: str) -> str:
    return left_text if len(left_text) <= len(right_text) else right_text


def _outline_index(source_id: str) -> int:
    match = re.search(r"(\d+)$", source_id)
    return int(match.group(1)) if match else 0
