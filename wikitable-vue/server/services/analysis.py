from __future__ import annotations

import json
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
) -> dict[str, Any]:
    label = _row_label(row)
    left_value = _side_value(row, "left")
    right_value = _side_value(row, "right")
    summary = f"{label}: left is {_display_value(left_value)}; right is {_display_value(right_value)}."
    citations = _citation_dicts(
        [Citation(f"cite-{row.get('id') or 'attribute'}", f"Sources: {label}", "both", _row_source_ids(row))],
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
) -> dict[str, Any]:
    source_ids = _row_source_ids(row)
    source_context = _source_context(source_map, source_ids)
    result = llm_client.chat_json(
        [
            {
                "role": "system",
                "content": (
                    "You are WikiCompare's comparison assistant. Use only the supplied "
                    "row data and source snippets. Return JSON only."
                ),
            },
            {
                "role": "user",
                "content": (
                    "Write a concise comparison for this aligned Wikipedia attribute. "
                    "Return an object with keys: summary, citations. citations must be "
                    "an array of objects with id, label, side, sourceIds. sourceIds must "
                    "come only from the provided sourceContext IDs.\n\n"
                    f"row: {json.dumps(_compact_row(row), ensure_ascii=False)}\n"
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
        "summary": summary,
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
