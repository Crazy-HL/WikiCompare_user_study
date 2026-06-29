from __future__ import annotations

from typing import Any

from services.models import Citation, CompareSession, SourceRef


def validate_citations(
    citations: list[Citation],
    source_map: dict[str, SourceRef | dict[str, Any]],
) -> list[Citation]:
    valid = []
    known_source_ids = set(source_map.keys())
    for citation in citations:
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
    return str(side_data.get("valueText") or side_data.get("value") or "").strip()


def _display_value(value: str) -> str:
    return value if value else "not available"


def _citation_side(value: Any) -> str:
    return value if value in {"left", "right", "both"} else "both"
