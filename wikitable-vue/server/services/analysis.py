from __future__ import annotations

import json
import re
from typing import Any

from services.models import Citation, CompareSession, SourceRef


def validate_citations(
    citations: list[Any],
    source_map: dict[str, SourceRef | dict[str, Any]],
) -> list[Citation]:
    valid = []
    known_source_ids = set(source_map.keys())
    for citation in citations:
        if not isinstance(citation, Citation):
            continue
        if not str(citation.id or "").strip():
            continue
        source_ids = list(citation.source_ids or [])
        if not source_ids:
            continue
        if all(source_id in known_source_ids for source_id in source_ids):
            valid.append(citation)
    return valid


def row_context(session: CompareSession, attribute_id: str) -> dict[str, Any] | None:
    for row in session.ranked_rows:
        if isinstance(row, dict) and row.get("id") == attribute_id:
            return row
    return None


def fallback_attribute_summary(
    row: dict[str, Any],
    source_map: dict[str, SourceRef | dict[str, Any]] | None = None,
    articles: dict[str, Any] | None = None,
) -> dict[str, Any]:
    summary = _paper_style_attribute_conclusion(row, articles)
    citations = _citation_dicts(
        [Citation(f"cite-{row.get('id') or 'attribute'}", f"Sources: {_row_label(row)}", "both", _row_source_ids(row))],
        source_map,
    )
    return {"summary": summary, "citations": citations}


def fallback_answer(session: CompareSession, question: str) -> dict[str, Any]:
    if not session.ranked_rows:
        return {
            "answer": "No aligned attributes are available for this session yet.",
            "citations": [],
        }

    row = session.ranked_rows[0]
    label = _row_label(row)
    left_value = _side_value(row, "left")
    right_value = _side_value(row, "right")
    answer = (
        f"Based on the top aligned attribute, {label}: left is "
        f"{_display_value(left_value)}; right is {_display_value(right_value)}."
    )
    citations = _citation_dicts(
        [Citation(f"cite-answer-{row.get('id') or 'top-row'}", f"Sources: {label}", "both", _row_source_ids(row))],
        session.source_map,
    )
    return {"answer": answer, "citations": citations}


def llm_attribute_summary(
    llm_client: Any,
    row: dict[str, Any],
    source_map: dict[str, SourceRef | dict[str, Any]],
    articles: dict[str, Any] | None = None,
) -> dict[str, Any]:
    source_ids = _row_source_ids(row)
    source_context = _source_context(source_map, source_ids)
    left_title = _source_title(articles, "left")
    right_title = _source_title(articles, "right")
    result = llm_client.chat_json(
        [
            {
                "role": "system",
                "content": (
                    "You are a data analysis assistant specializing in generating "
                    "concise comparative summaries from structured data. Use only "
                    "the supplied row data and source snippets. Return JSON only."
                ),
            },
            {
                "role": "user",
                "content": (
                    "Task: Initial Difference Summary (The What).\n"
                    f"Compare the provided data for the attribute \"{_row_label(row)}\" "
                    "from two sources. The summary must be brief, highlight the most "
                    "significant difference or trend, and be based solely on the "
                    "provided data.\n\n"
                    "Input Data:\n"
                    f"- Source 1 Title: {left_title}\n"
                    f"Data: {json.dumps(_attribute_prompt_data(row, 'left'), ensure_ascii=False)}\n"
                    f"- Source 2 Title: {right_title}\n"
                    f"Data: {json.dumps(_attribute_prompt_data(row, 'right'), ensure_ascii=False)}\n\n"
                    "Output Constraints:\n"
                    "- Begin the summary with \"Conclusion:\".\n"
                    "- Output a concise, direct summary.\n"
                    "- Do not list the raw data or describe the analysis process.\n"
                    "- Return an object with keys: summary, citations.\n"
                    "- citations must be an array of objects with id, label, side, sourceIds.\n"
                    "- sourceIds must come only from the provided sourceContext IDs.\n\n"
                    f"rowMetadata: {json.dumps(_compact_row(row), ensure_ascii=False)}\n"
                    f"sourceContext: {json.dumps(source_context, ensure_ascii=False)}"
                ),
            },
        ]
    )
    if not isinstance(result, dict):
        raise ValueError("Expected LLM attribute response to be a JSON object")

    summary = str(result.get("summary") or "").strip()
    if not summary:
        raise ValueError("LLM attribute response omitted summary")
    citations = validate_citations(citations_from_dicts(result.get("citations") or []), source_map)
    return {
        "summary": _ensure_conclusion_prefix(summary),
        "citations": [citation.to_dict() for citation in citations],
        "llmUsed": True,
    }


def llm_answer(
    llm_client: Any,
    session: CompareSession,
    question: str,
) -> dict[str, Any]:
    ranked_rows = session.ranked_rows[:8]
    source_ids = []
    for row in ranked_rows:
        if isinstance(row, dict):
            source_ids.extend(_row_source_ids(row))

    result = llm_client.chat_json(
        [
            {
                "role": "system",
                "content": (
                    "You are WikiCompare's Q&A assistant. Answer only from the supplied "
                    "aligned attributes and source snippets. Return JSON only."
                ),
            },
            {
                "role": "user",
                "content": (
                    "Answer the user's question briefly and cite the exact source IDs "
                    "that support the answer. Return an object with keys: answer, "
                    "citations. citations must be an array of objects with id, label, "
                    "side, sourceIds. sourceIds must come only from sourceContext IDs.\n\n"
                    f"question: {question}\n"
                    f"alignedRows: {json.dumps([_compact_row(row) for row in ranked_rows if isinstance(row, dict)], ensure_ascii=False)}\n"
                    f"sourceContext: {json.dumps(_source_context(session.source_map, source_ids), ensure_ascii=False)}"
                ),
            },
        ]
    )
    if not isinstance(result, dict):
        raise ValueError("Expected LLM answer response to be a JSON object")

    answer = str(result.get("answer") or "").strip()
    if not answer:
        raise ValueError("LLM answer response omitted answer")
    citations = validate_citations(citations_from_dicts(result.get("citations") or []), session.source_map)
    return {
        "answer": answer,
        "citations": [citation.to_dict() for citation in citations],
        "llmUsed": True,
    }


def citations_from_dicts(items: list[dict[str, Any]]) -> list[Citation]:
    citations = []
    for index, item in enumerate(items):
        if not isinstance(item, dict):
            continue
        source_ids = item.get("sourceIds", item.get("source_ids", []))
        if not isinstance(source_ids, list):
            source_ids = []
        citations.append(
            Citation(
                id=str(item.get("id") or f"cite-{index + 1}"),
                label=str(item.get("label") or "Sources"),
                side=_citation_side(item.get("side")),
                source_ids=[str(source_id) for source_id in source_ids],
            )
        )
    return citations


def _compact_row(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": row.get("id"),
        "label": _row_label(row),
        "dataType": row.get("dataType"),
        "sourceKind": row.get("sourceKind"),
        "score": row.get("score"),
        "left": {
            "value": _side_value(row, "left"),
            "sourceIds": _string_list(row.get("leftSourceIds")),
            "values": _side_values(row, "left"),
        },
        "right": {
            "value": _side_value(row, "right"),
            "sourceIds": _string_list(row.get("rightSourceIds")),
            "values": _side_values(row, "right"),
        },
    }


def _attribute_prompt_data(row: dict[str, Any], side: str) -> dict[str, Any]:
    visualization = row.get("visualization")
    side_data = visualization.get(side) if isinstance(visualization, dict) else {}
    if not isinstance(side_data, dict):
        side_data = {}
    return {
        "attribute": _row_label(row),
        "dataType": row.get("dataType"),
        "chartType": row.get("chartType"),
        "raw": side_data.get("raw") or side_data.get("valueText") or side_data.get("value"),
        "values": _side_values(row, side),
        "structuredValues": side_data.get("structuredValues") if isinstance(side_data.get("structuredValues"), list) else [],
        "sourceIds": _string_list(row.get(f"{side}SourceIds")),
    }


def _paper_style_attribute_conclusion(
    row: dict[str, Any],
    articles: dict[str, Any] | None = None,
) -> str:
    label = _row_label(row)
    left_title = _source_title(articles, "left")
    right_title = _source_title(articles, "right")
    left_observations = _numeric_observations(row, "left")
    right_observations = _numeric_observations(row, "right")
    best_pair = _largest_matched_difference(left_observations, right_observations)
    if best_pair:
        left_item, right_item = best_pair
        descriptor = left_item.get("label") or right_item.get("label") or "the reported value"
        direction = "higher" if float(left_item["value"]) > float(right_item["value"]) else "lower"
        if row.get("dataType") == "Trend":
            return (
                f"Conclusion: For {label}, {left_title} reports a {direction} "
                f"{descriptor} ({left_item['display']}) than {right_title} "
                f"({right_item['display']})."
            )
        return (
            f"Conclusion: For {label}, the largest matched difference is {descriptor}: "
            f"{left_title} reports {left_item['display']}, while {right_title} "
            f"reports {right_item['display']}."
        )

    left_value = _side_value(row, "left")
    right_value = _side_value(row, "right")
    return (
        f"Conclusion: For {label}, {left_title} reports {_display_value(left_value)}, "
        f"while {right_title} reports {_display_value(right_value)}."
    )


def _numeric_observations(row: dict[str, Any], side: str) -> list[dict[str, Any]]:
    visualization = row.get("visualization")
    side_data = visualization.get(side) if isinstance(visualization, dict) else {}
    if not isinstance(side_data, dict):
        return []
    raw = str(side_data.get("raw") or side_data.get("valueText") or "")
    values = side_data.get("values")
    if not isinstance(values, list):
        return []
    observations = []
    for index, item in enumerate(values):
        if not isinstance(item, dict):
            continue
        try:
            numeric_value = float(item.get("value"))
        except (TypeError, ValueError):
            continue
        label = _observation_label(item, index)
        observations.append(
            {
                "key": _normalized_observation_key(label),
                "label": label,
                "value": numeric_value,
                "display": _observation_display(item, raw, row.get("dataType"), index),
            }
        )
    return observations


def _observation_label(item: dict[str, Any], index: int) -> str:
    if item.get("label") not in (None, ""):
        return str(item["label"]).strip()
    if item.get("year") not in (None, ""):
        return str(item["year"]).strip()
    return f"value {index + 1}"


def _largest_matched_difference(
    left_observations: list[dict[str, Any]],
    right_observations: list[dict[str, Any]],
) -> tuple[dict[str, Any], dict[str, Any]] | None:
    right_by_key = {item["key"]: item for item in right_observations if item.get("key")}
    candidates = []
    for left_item in left_observations:
        right_item = right_by_key.get(left_item.get("key"))
        if not right_item:
            continue
        difference = _normalized_numeric_difference(left_item["value"], right_item["value"])
        candidates.append((difference, left_item, right_item))
    if not candidates and left_observations and right_observations:
        candidates.append(
            (
                _normalized_numeric_difference(left_observations[0]["value"], right_observations[0]["value"]),
                left_observations[0],
                right_observations[0],
            )
        )
    if not candidates:
        return None
    _, left_item, right_item = max(candidates, key=lambda item: item[0])
    return left_item, right_item


def _normalized_numeric_difference(left_value: float, right_value: float) -> float:
    return abs(left_value - right_value) / max(abs(left_value), abs(right_value), 1.0)


def _observation_display(
    item: dict[str, Any],
    raw: str,
    data_type: Any,
    index: int,
) -> str:
    if item.get("rawText"):
        return str(item["rawText"]).strip()
    raw_value = _raw_number_for_observation(raw, item, index)
    if raw_value:
        return _with_observation_year(raw_value, item)
    value = item.get("value")
    if _looks_percentage(data_type, raw):
        return f"{_trim_number(value)}%"
    return _trim_number(value)


def _with_observation_year(display: str, item: dict[str, Any]) -> str:
    year = item.get("year")
    if year in (None, ""):
        return display
    year_text = str(year)
    if year_text in display:
        return display
    return f"{display} ({year_text})"


def _raw_number_for_observation(raw: str, item: dict[str, Any], index: int) -> str:
    source = str(raw or "")
    if not source:
        return ""
    label = str(item.get("label") or "").strip()
    if label:
        label_match = re.search(re.escape(label), source, re.IGNORECASE)
        if label_match:
            after = source[label_match.end(): label_match.end() + 90]
            after_match = _first_amount_match(after)
            if after_match:
                return after_match
            before = source[max(0, label_match.start() - 90): label_match.start()]
            before_amounts = _amount_matches(before)
            if before_amounts:
                return before_amounts[-1]
    amounts = _amount_matches(source)
    if 0 <= index < len(amounts):
        return amounts[index]
    return amounts[0] if amounts else ""


AMOUNT_RE = re.compile(
    r"(?:US\$|[$¥₩€£])\s*[-+]?\d[\d,]*(?:\.\d+)?(?:\s*(?:thousand|million|billion|trillion|quadrillion))?"
    r"|[-+]?\d[\d,]*(?:\.\d+)?\s*(?:%|percent|thousand|million|billion|trillion|quadrillion)",
    re.IGNORECASE,
)


def _amount_matches(text: str) -> list[str]:
    return [match.group(0).replace("\u00a0", " ").strip() for match in AMOUNT_RE.finditer(text)]


def _first_amount_match(text: str) -> str:
    matches = _amount_matches(text)
    return matches[0] if matches else ""


def _looks_percentage(data_type: Any, raw: str) -> bool:
    return str(data_type or "").lower() in {"proportional", "trend"} and "%" in str(raw or "")


def _trim_number(value: Any) -> str:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return str(value or "")
    if number.is_integer():
        return str(int(number))
    return f"{number:.3f}".rstrip("0").rstrip(".")


def _normalized_observation_key(label: str) -> str:
    return re.sub(r"\s+", " ", str(label or "").strip().lower())


def _source_title(articles: dict[str, Any] | None, side: str) -> str:
    article = articles.get(side) if isinstance(articles, dict) else None
    if isinstance(article, dict):
        title = str(article.get("title") or "").strip()
        if title:
            return title
    return "Source 1" if side == "left" else "Source 2"


def _ensure_conclusion_prefix(summary: str) -> str:
    text = str(summary or "").strip()
    if re.match(r"^conclusion\s*:", text, re.IGNORECASE):
        return text
    return f"Conclusion: {text}"


def _source_context(
    source_map: dict[str, SourceRef | dict[str, Any]],
    source_ids: list[str],
) -> list[dict[str, Any]]:
    context = []
    seen = set()
    for source_id in source_ids:
        if source_id in seen or source_id not in source_map:
            continue
        seen.add(source_id)
        source_ref = source_map[source_id]
        item = source_ref if isinstance(source_ref, dict) else source_ref.to_dict()
        context.append(
            {
                "id": item.get("id") or source_id,
                "side": item.get("side"),
                "sourceType": item.get("sourceType") or item.get("source_type"),
                "text": item.get("text"),
            }
        )
    return context


def _side_values(row: dict[str, Any], side: str) -> list[dict[str, Any]]:
    visualization = row.get("visualization")
    if not isinstance(visualization, dict):
        return []
    side_data = visualization.get(side)
    if not isinstance(side_data, dict):
        return []
    values = side_data.get("values")
    if not isinstance(values, list):
        return []
    return [value for value in values if isinstance(value, dict)]


def _citation_dicts(
    citations: list[Citation],
    source_map: dict[str, SourceRef | dict[str, Any]] | None,
) -> list[dict[str, Any]]:
    if source_map is None:
        return [citation.to_dict() for citation in citations if citation.source_ids]

    pruned_citations = [
        Citation(
            id=citation.id,
            label=citation.label,
            side=citation.side,
            source_ids=[source_id for source_id in citation.source_ids if source_id in source_map],
        )
        for citation in citations
    ]
    return [citation.to_dict() for citation in validate_citations(pruned_citations, source_map)]


def _row_source_ids(row: dict[str, Any]) -> list[str]:
    return _string_list(row.get("leftSourceIds")) + _string_list(row.get("rightSourceIds"))


def _string_list(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    return [str(item) for item in value if item]


def _row_label(row: dict[str, Any]) -> str:
    return str(row.get("label") or row.get("id") or "Aligned attribute")


def _side_value(row: dict[str, Any], side: str) -> str:
    visualization = row.get("visualization")
    if not isinstance(visualization, dict):
        return ""
    side_data = visualization.get(side)
    if not isinstance(side_data, dict):
        return ""
    raw_value = side_data.get("raw") or side_data.get("valueText") or side_data.get("value")
    if raw_value not in (None, ""):
        return str(raw_value).strip()
    values = side_data.get("values")
    if isinstance(values, list) and values:
        return ", ".join(_display_numeric_value(value) for value in values if isinstance(value, dict))
    return ""


def _display_numeric_value(value: dict[str, Any]) -> str:
    amount = value.get("value")
    if "year" in value:
        return f"{value['year']}: {amount}"
    return str(amount)


def _display_value(value: str) -> str:
    return value if value else "not available"


def _citation_side(value: Any) -> str:
    return value if value in {"left", "right", "both"} else "both"
