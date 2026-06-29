from __future__ import annotations

import hashlib
import re
from typing import Any


MAGNITUDES = {
    "thousand": 1_000,
    "million": 1_000_000,
    "billion": 1_000_000_000,
    "trillion": 1_000_000_000_000,
}

NUMBER_RE = re.compile(
    r"(?<![\w.])[$€£¥]?\s*([-+]?(?:\d{1,3}(?:,\d{3})+|\d+)(?:\.\d+)?)(?:\s*(%|percent|thousand|million|billion|trillion))?",
    re.IGNORECASE,
)
YEAR_VALUE_RE = re.compile(
    r"\b((?:18|19|20|21)\d{2})\b\s*[:=]\s*[$€£¥]?\s*([-+]?(?:\d{1,3}(?:,\d{3})+|\d+)(?:\.\d+)?)(?:\s*(%|percent|thousand|million|billion|trillion))?",
    re.IGNORECASE,
)
ORDINAL_RE = re.compile(r"\b\d+(?:st|nd|rd|th)\b", re.IGNORECASE)
COORDINATE_RE = re.compile(
    r"(\b\d+(?:\.\d+)?\s*°\s*[NS]\b.*\b\d+(?:\.\d+)?\s*°\s*[EW]\b|\b\d+(?:\.\d+)?\s*°\s*[EW]\b.*\b\d+(?:\.\d+)?\s*°\s*[NS]\b)",
    re.IGNORECASE,
)
YEAR_RE = re.compile(r"\b((?:18|19|20|21)\d{2})\b")
YEAR_RANGE_RE = re.compile(r"\b(?:18|19|20|21)\d{2}\s*[-–—]\s*(?:18|19|20|21)\d{2}\b")


def choose_chart_type(data_type: str, point_count: int) -> str:
    normalized_type = (data_type or "").strip().lower()
    count = max(int(point_count or 0), 0)

    if normalized_type == "numerical":
        return "bar" if count <= 3 else "scatter"
    if normalized_type == "proportional":
        return "pie" if count <= 4 else "stacked"
    if normalized_type == "trend":
        return "bar" if count <= 2 else "line"
    if normalized_type == "categorical":
        return "text" if count <= 2 else "stacked"
    return "text"


def classify_value_rule(value_text: str | None) -> str:
    text = str(value_text or "").strip()
    lower = text.lower()
    if not text:
        return "Text"
    if COORDINATE_RE.search(text):
        return "Geographical"
    if _has_trend_shape(text):
        return "Trend"
    if "%" in text or re.search(r"\bpercent\b", lower):
        return "Proportional"
    if ORDINAL_RE.search(text) or re.search(r"\brank(?:ed|ing)?\b", lower):
        return "Ordinal"
    if extract_numeric_values(text):
        return "Numerical"
    if _looks_like_list(text):
        return "Categorical"
    return "Text"


def extract_numeric_values(value_text: str | None) -> list[dict[str, float | int]]:
    text = str(value_text or "").strip()
    if not text:
        return []
    if _is_plain_year_range(text):
        return []

    year_values = _extract_year_value_pairs(text)
    if year_values:
        return year_values

    years = [int(match.group(1)) for match in YEAR_RE.finditer(text)]
    values: list[dict[str, float | int]] = []
    has_non_year_number = any(
        not _is_year_token(match.group(1))
        for match in NUMBER_RE.finditer(text)
    )
    for match in NUMBER_RE.finditer(text):
        raw_number = match.group(1)
        is_year = _is_year_token(raw_number)
        if is_year and (
            has_non_year_number
            or not _is_standalone_year_attribute(text, raw_number)
        ):
            continue
        number = _parse_number(raw_number)
        if number is None:
            continue
        unit = (match.group(2) or "").lower()
        value = _scale_number(number, unit)
        item: dict[str, float | int] = {"value": value}
        if len(years) == 1 and not is_year:
            item["year"] = years[0]
        values.append(item)
    return values


def validate_alignments(
    left_pool: list[dict[str, Any]],
    right_pool: list[dict[str, Any]],
    alignments: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    left_ids = {item.get("id") for item in left_pool if isinstance(item, dict)}
    right_ids = {item.get("id") for item in right_pool if isinstance(item, dict)}
    valid = []
    for alignment in alignments:
        if not isinstance(alignment, dict):
            continue
        left_id = alignment.get("leftId")
        right_id = alignment.get("rightId")
        if left_id not in left_ids or right_id not in right_ids:
            continue
        clean = {"leftId": left_id, "rightId": right_id}
        if alignment.get("label"):
            clean["label"] = str(alignment["label"]).strip()
        valid.append(clean)
    return valid


def normalize_attribute_pair(
    left_attr: dict[str, Any],
    right_attr: dict[str, Any],
    label: str | None,
) -> dict[str, Any]:
    left_values = extract_numeric_values(left_attr.get("valueText"))
    right_values = extract_numeric_values(right_attr.get("valueText"))
    data_type = _combine_data_types(
        classify_value_rule(left_attr.get("valueText")),
        classify_value_rule(right_attr.get("valueText")),
    )
    point_count = _point_count(data_type, left_values, right_values)
    row_label = str(label or left_attr.get("key") or right_attr.get("key") or "").strip()

    row = {
        "id": _row_id(left_attr.get("id"), right_attr.get("id"), row_label),
        "label": row_label,
        "leftAttributeId": left_attr.get("id"),
        "rightAttributeId": right_attr.get("id"),
        "leftSourceIds": list(left_attr.get("sourceIds") or []),
        "rightSourceIds": list(right_attr.get("sourceIds") or []),
        "sourceKind": _source_kind(left_attr.get("source"), right_attr.get("source")),
        "dataType": data_type,
        "chartType": choose_chart_type(data_type, point_count),
        "score": _score_pair(data_type, left_values, right_values),
        "visualization": {
            "left": _visual_side(left_attr, left_values),
            "right": _visual_side(right_attr, right_values),
        },
    }
    return row


def rank_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    indexed_rows = list(enumerate(rows))
    return [
        row
        for _, row in sorted(
            indexed_rows,
            key=lambda item: (
                -_weighted_score(item[1]),
                str(item[1].get("label") or item[1].get("id") or ""),
                item[0],
            ),
        )
    ]


def _extract_year_value_pairs(text: str) -> list[dict[str, float | int]]:
    values = []
    for match in YEAR_VALUE_RE.finditer(text):
        if match.group(0).strip().startswith(f"{match.group(1)}-"):
            continue
        year = int(match.group(1))
        number = _parse_number(match.group(2))
        if number is None:
            continue
        values.append({"year": year, "value": _scale_number(number, (match.group(3) or "").lower())})
    return values


def _is_plain_year_range(text: str) -> bool:
    return bool(YEAR_RANGE_RE.fullmatch(text.strip()))


def _is_standalone_year_attribute(text: str, raw_number: str) -> bool:
    if not _is_year_token(raw_number):
        return False
    years = YEAR_RE.findall(text)
    if len(years) != 1:
        return False
    return not _extract_year_value_pairs(text)


def _has_trend_shape(text: str) -> bool:
    if len(_extract_year_value_pairs(text)) >= 2:
        return True
    years = YEAR_RE.findall(text)
    return len(set(years)) >= 2 and len(extract_numeric_values(text)) >= 2


def _looks_like_list(text: str) -> bool:
    if ";" in text:
        return True
    return len([part for part in text.split(",") if part.strip()]) >= 3


def _parse_number(raw_number: str) -> float | None:
    try:
        return float(raw_number.replace(",", ""))
    except (TypeError, ValueError):
        return None


def _scale_number(number: float, unit: str) -> float:
    unit = unit.lower()
    if unit == "percent":
        unit = "%"
    if unit in MAGNITUDES:
        return number * MAGNITUDES[unit]
    return number


def _is_year_token(raw_number: str) -> bool:
    try:
        number = int(raw_number.replace(",", ""))
    except (TypeError, ValueError):
        return False
    return 1800 <= number <= 2199


def _combine_data_types(left_type: str, right_type: str) -> str:
    order = [
        "Trend",
        "Proportional",
        "Numerical",
        "Ordinal",
        "Geographical",
        "Categorical",
        "Text",
    ]
    for data_type in order:
        if data_type in {left_type, right_type}:
            return data_type
    return "Text"


def _point_count(
    data_type: str,
    left_values: list[dict[str, float | int]],
    right_values: list[dict[str, float | int]],
) -> int:
    if data_type == "Trend":
        years = {
            value["year"]
            for value in left_values + right_values
            if "year" in value
        }
        return len(years) if years else max(len(left_values), len(right_values), 2)
    return max(len(left_values) + len(right_values), 1)


def _source_kind(left_source: str | None, right_source: str | None) -> str:
    sources = {str(source or "").lower() for source in (left_source, right_source)}
    if "infobox" in sources and "main_text" in sources:
        return "Both"
    if "infobox" in sources:
        return "Infobox"
    return "Text"


def _score_pair(
    data_type: str,
    left_values: list[dict[str, float | int]],
    right_values: list[dict[str, float | int]],
) -> float:
    if not left_values and not right_values:
        return 0.0
    if not left_values or not right_values:
        return 0.2
    if data_type == "Trend":
        return _trend_difference(left_values, right_values)
    return _value_difference(left_values, right_values)


def _trend_difference(
    left_values: list[dict[str, float | int]],
    right_values: list[dict[str, float | int]],
) -> float:
    left_by_year = {
        value["year"]: float(value["value"])
        for value in left_values
        if "year" in value and "value" in value
    }
    right_by_year = {
        value["year"]: float(value["value"])
        for value in right_values
        if "year" in value and "value" in value
    }
    shared_years = sorted(set(left_by_year) & set(right_by_year))
    if not shared_years:
        return _value_difference(left_values, right_values)
    diffs = [
        _normalized_difference(left_by_year[year], right_by_year[year])
        for year in shared_years
    ]
    level_difference = sum(diffs) / len(diffs)
    slope_difference = 0.0
    if len(shared_years) >= 2:
        first_year = shared_years[0]
        last_year = shared_years[-1]
        left_slope = left_by_year[last_year] - left_by_year[first_year]
        right_slope = right_by_year[last_year] - right_by_year[first_year]
        slope_difference = _normalized_difference(left_slope, right_slope)
    return round(min(1.0, (level_difference * 0.6) + (slope_difference * 0.4)), 6)


def _value_difference(
    left_values: list[dict[str, float | int]],
    right_values: list[dict[str, float | int]],
) -> float:
    pair_count = min(len(left_values), len(right_values))
    if pair_count == 0:
        return 0.0
    diffs = [
        _normalized_difference(
            float(left_values[index]["value"]),
            float(right_values[index]["value"]),
        )
        for index in range(pair_count)
        if "value" in left_values[index] and "value" in right_values[index]
    ]
    if not diffs:
        return 0.0
    return round(sum(diffs) / len(diffs), 6)


def _normalized_difference(left: float, right: float) -> float:
    denominator = max(abs(left), abs(right), 1e-9)
    return min(1.0, abs(left - right) / denominator)


def _visual_side(
    attr: dict[str, Any],
    values: list[dict[str, float | int]],
) -> dict[str, Any]:
    return {
        "attributeId": attr.get("id"),
        "label": attr.get("key"),
        "raw": attr.get("valueText"),
        "values": values,
    }


def _row_id(left_id: Any, right_id: Any, label: str) -> str:
    seed = f"{left_id or ''}|{right_id or ''}|{label}"
    digest = hashlib.sha1(seed.encode("utf-8")).hexdigest()[:12]
    return f"row-{digest}"


def _weighted_score(row: dict[str, Any]) -> float:
    score = float(row.get("score") or 0)
    data_type = row.get("dataType")
    if data_type == "Trend":
        return score * 0.5
    if data_type in {"Numerical", "Proportional"}:
        return score * 0.3
    return score * 0.2
