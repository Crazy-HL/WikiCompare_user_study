from __future__ import annotations

import hashlib
import math
import re
from typing import Any, Callable

NumericValue = dict[str, Any]

MAGNITUDES = {
    "thousand": 1_000,
    "million": 1_000_000,
    "billion": 1_000_000_000,
    "trillion": 1_000_000_000_000,
    "quadrillion": 1_000_000_000_000_000,
}
MAGNITUDE_PATTERN = "thousand|million|billion|trillion|quadrillion"

NUMBER_RE = re.compile(
    rf"(?<![\w.])[$€£¥]?\s*([-+]?(?:\d{{1,3}}(?:,\d{{3}})+|\d+)(?:\.\d+)?)(?:\s*(%|percent|{MAGNITUDE_PATTERN}))?",
    re.IGNORECASE,
)
YEAR_VALUE_RE = re.compile(
    rf"\b((?:18|19|20|21)\d{{2}})\b\s*[:=]\s*[$€£¥]?\s*([-+]?(?:\d{{1,3}}(?:,\d{{3}})+|\d+)(?:\.\d+)?)(?:\s*(%|percent|{MAGNITUDE_PATTERN}))?",
    re.IGNORECASE,
)
PAREN_YEAR_VALUE_RE = re.compile(
    rf"(?<![\w.])[$€£¥]?\s*([-+]?(?:\d{{1,3}}(?:,\d{{3}})+|\d+)(?:\.\d+)?)(?:\s*(%|percent|{MAGNITUDE_PATTERN}))?\s*\(([^)]*\b((?:18|19|20|21)\d{{2}})\w*[^)]*)\)",
    re.IGNORECASE,
)
PAREN_LABEL_VALUE_RE = re.compile(
    rf"(?<![\w.])[$€£¥]?\s*([-+]?(?:\d{{1,3}}(?:,\d{{3}})+|\d+)(?:\.\d+)?)(?:st|nd|rd|th)?(?:\s*(%|percent|{MAGNITUDE_PATTERN}))?\s*\(([^)]*)\)",
    re.IGNORECASE,
)
INDEX_RATING_RANK_RE = re.compile(
    r"^\s*((?:0|1)(?:\.\d+)?)\s+((?:very\s+)?(?:high|medium|low))\s*\(([^)]*\b((?:18|19|20|21)\d{2})\w*[^)]*)\)\s*\((\d+)(st|nd|rd|th)\)\s*$",
    re.IGNORECASE,
)
HDI_INDEX_RE = re.compile(
    r"((?:0|1)(?:\.\d+)?)\s+((?:very\s+)?(?:high|medium|low))(?:\s+(IHDI))?",
    re.IGNORECASE,
)
ORDINAL_CONTEXT_RE = re.compile(
    r"(\d+)(st|nd|rd|th)\s*\((.*?)(?=(?:\)\s*)?\d+(?:st|nd|rd|th)\s*\(|$)",
    re.IGNORECASE,
)
CPI_SCORE_RANK_RE = re.compile(
    r"^\s*(\d+(?:\.\d+)?)\s+out\s+of\s+100\s+points\s*\(([^)]*\b((?:18|19|20|21)\d{2})[^)]*)\)(?:\s*\((rank\s+(\d+)(st|nd|rd|th))\))?\s*$",
    re.IGNORECASE,
)
CPI_SCORE_INLINE_RANK_RE = re.compile(
    r"^\s*(\d+(?:\.\d+)?)\s+out\s+of\s+100\s+points\s*\(([^)]*\b((?:18|19|20|21)\d{2})\s*,\s*((\d+)(st|nd|rd|th)\s+rank)[^)]*)\)\s*$",
    re.IGNORECASE,
)
ORDINAL_RE = re.compile(r"\b\d+(?:st|nd|rd|th)\b", re.IGNORECASE)
COORDINATE_RE = re.compile(
    r"(\b\d+(?:\.\d+)?\s*°\s*[NS]\b.*\b\d+(?:\.\d+)?\s*°\s*[EW]\b|\b\d+(?:\.\d+)?\s*°\s*[EW]\b.*\b\d+(?:\.\d+)?\s*°\s*[NS]\b)",
    re.IGNORECASE,
)
YEAR_RE = re.compile(r"\b((?:18|19|20|21)\d{2})\b")
YEAR_RANGE_RE = re.compile(r"\b(?:18|19|20|21)\d{2}\s*[-–—]\s*(?:18|19|20|21)\d{2}\b")
MONTH_RE = re.compile(
    r"\b(?:January|February|March|April|May|June|July|August|September|October|November|December)\b",
    re.IGNORECASE,
)
AGE_RANGE_RE = re.compile(r"\b\d+\s*(?:to|-|–|—)\s*\d+\s*[- ]?year", re.IGNORECASE)
GDP_SHARE_AFTER_RE = re.compile(r"^\s*(?:%|percent)?\s*of\s+GDP\b", re.IGNORECASE)
CURRENCY_SYMBOLS = "$€£¥₩₹₽₺₫₴₪₦₱฿₡₲₵"
SEMANTIC_ALIGNMENT_GROUPS = [
    ("Definition / Overview", {"definition", "overview", "description", "concept", "meaning", "scope"}),
    ("History / Background", {"history", "background", "origin", "origins", "development", "timeline"}),
    ("Applications / Uses", {"application", "applications", "use", "uses", "usage", "applied", "deployment"}),
    ("Methods / Techniques", {"method", "methods", "technique", "techniques", "approach", "approaches", "algorithm", "algorithms"}),
    ("Subfields / Types", {"subfield", "subfields", "type", "types", "category", "categories", "branches"}),
    ("Impact / Issues", {"impact", "impacts", "issue", "issues", "risk", "risks", "ethics", "limitations", "criticism"}),
]


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
    values = extract_numeric_values(text)
    if not text:
        return "Text"
    if COORDINATE_RE.search(text):
        return "Geographical"
    if _has_trend_shape(text):
        return "Trend"
    if ("%" in text or re.search(r"\bpercent\b", lower)) and not _has_amount_with_secondary_gdp_share(text):
        return "Proportional"
    if ORDINAL_RE.search(text) or re.search(r"\brank(?:ed|ing)?\b", lower):
        return "Ordinal"
    if values:
        return "Numerical"
    if _looks_like_list(text):
        return "Categorical"
    return "Text"


def extract_numeric_values(value_text: str | None) -> list[NumericValue]:
    text = str(value_text or "").strip()
    if not text:
        return []
    if _contains_year_range(text):
        return []

    hdi_series_values = _extract_hdi_series_values(text)
    if hdi_series_values:
        return hdi_series_values

    index_rating_rank_values = _extract_index_rating_rank_values(text)
    if index_rating_rank_values:
        return index_rating_rank_values

    cpi_values = _extract_cpi_score_rank_values(text)
    if cpi_values:
        return cpi_values

    ordinal_context_values = _extract_ordinal_context_values(text)
    if ordinal_context_values:
        return ordinal_context_values

    colon_labeled_values = _extract_colon_labeled_value_series(text)
    if colon_labeled_values:
        return colon_labeled_values

    labeled_percentage_values = _extract_labeled_percentage_series(text)
    if labeled_percentage_values:
        return labeled_percentage_values

    parenthetical_values = _extract_parenthetical_year_value_pairs(text)
    parenthetical_label_values = _extract_parenthetical_label_value_pairs(text)
    parenthetical_spans = _parenthetical_value_spans(text)

    year_values = _extract_year_value_pairs(text)
    if year_values:
        return year_values

    years = [int(match.group(1)) for match in YEAR_RE.finditer(text)]
    age_range_spans = [match.span() for match in AGE_RANGE_RE.finditer(text)]
    values: list[NumericValue] = list(parenthetical_values) + list(parenthetical_label_values)
    number_matches = list(NUMBER_RE.finditer(text))
    has_non_year_number = any(
        not _is_year_token(match.group(1))
        for match in number_matches
    )
    currency_labels = _currency_labels_in_text(text, number_matches)
    use_currency_labels = len(currency_labels) >= 2
    for index, match in enumerate(number_matches):
        raw_number = match.group(1)
        is_year = _is_year_token(raw_number)
        unit = (match.group(2) or "").lower()
        next_match_start = number_matches[index + 1].start() if index + 1 < len(number_matches) else len(text)
        if _is_inside_spans(match, parenthetical_spans):
            continue
        if _is_date_number(text, match):
            continue
        if _is_inside_spans(match, age_range_spans):
            continue
        if _is_secondary_gdp_share(text, match, unit):
            continue
        if _is_secondary_magnitude_count(text, match, unit):
            continue
        if is_year and (
            has_non_year_number
            or not _is_standalone_year_attribute(text, raw_number)
        ):
            continue
        number = _parse_number(raw_number)
        if number is None:
            continue
        value = _scale_number(number, unit)
        item: NumericValue = {"value": value}
        if len(years) == 1 and not is_year:
            item["year"] = years[0]
        label = _label_for_match(
            text,
            match,
            use_currency_labels=use_currency_labels,
            next_match_start=next_match_start,
        )
        if label:
            item["label"] = label
        values.append(item)
    return _apply_contextual_value_labels(_deduplicate_numeric_values(values), text)


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


def align_attribute_pools(
    left_pool: list[dict[str, Any]],
    right_pool: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    alignments: list[dict[str, Any]] = []
    used_right_ids: set[Any] = set()

    right_by_key = {
        _alignment_key(attribute.get("key")): attribute
        for attribute in right_pool
        if _alignment_key(attribute.get("key"))
    }
    for left_attribute in left_pool:
        key = _alignment_key(left_attribute.get("key"))
        right_attribute = right_by_key.get(key)
        if not key or right_attribute is None:
            continue
        alignments.append(
            {
                "left": left_attribute,
                "right": right_attribute,
                "label": left_attribute.get("key") or right_attribute.get("key") or key,
            }
        )
        used_right_ids.add(right_attribute.get("id"))

    for left_attribute in left_pool:
        if any(item["left"].get("id") == left_attribute.get("id") for item in alignments):
            continue
        left_group = _semantic_alignment_group(left_attribute.get("key"))
        if left_group is None:
            continue
        label, _terms = left_group
        right_attribute = next(
            (
                attribute
                for attribute in right_pool
                if attribute.get("id") not in used_right_ids
                and _semantic_alignment_group(attribute.get("key")) is not None
                and _semantic_alignment_group(attribute.get("key"))[0] == label
            ),
            None,
        )
        if right_attribute is None:
            continue
        left_key = str(left_attribute.get("key") or "").strip()
        right_key = str(right_attribute.get("key") or "").strip()
        alignments.append(
            {
                "left": left_attribute,
                "right": right_attribute,
                "label": left_key if left_key == right_key else f"{left_key} / {right_key}",
            }
        )
        used_right_ids.add(right_attribute.get("id"))

    return alignments


def _semantic_alignment_group(key: Any):
    tokens = set(re.findall(r"[a-z0-9]+", str(key or "").lower()))
    if not tokens:
        return None
    for label, terms in SEMANTIC_ALIGNMENT_GROUPS:
        if tokens.intersection(terms):
            return label, terms
    return None


def _alignment_key(value: Any) -> str:
    return str(value or "").strip().lower()


def normalize_attribute_pair(
    left_attr: dict[str, Any],
    right_attr: dict[str, Any],
    label: str | None,
    value_refiner: Callable[..., Any] | None = None,
) -> dict[str, Any]:
    left_text = str(left_attr.get("valueText") or "")
    right_text = str(right_attr.get("valueText") or "")
    left_values = extract_numeric_values(left_text)
    right_values = extract_numeric_values(right_text)
    left_type = classify_value_rule(left_text)
    right_type = classify_value_rule(right_text)
    row_label = str(label or left_attr.get("key") or right_attr.get("key") or "").strip()
    left_structured_candidates = _structured_values(left_attr) or _inferred_structured_values(left_attr)
    right_structured_candidates = _structured_values(right_attr) or _inferred_structured_values(right_attr)
    left_values = _refine_values_with_model(
        value_refiner,
        key=str(left_attr.get("key") or row_label),
        value_text=left_text,
        rule_values=left_values,
        data_type=left_type,
    )
    right_values = _refine_values_with_model(
        value_refiner,
        key=str(right_attr.get("key") or row_label),
        value_text=right_text,
        rule_values=right_values,
        data_type=right_type,
    )
    left_gdp_share_values = _extract_gdp_share_values(left_text)
    right_gdp_share_values = _extract_gdp_share_values(right_text)
    if left_gdp_share_values and right_gdp_share_values:
        left_values = left_gdp_share_values
        right_values = right_gdp_share_values
        left_type = "Proportional"
        right_type = "Proportional"
    use_structured_values = _should_use_structured_values(
        left_values,
        right_values,
        left_structured_candidates,
        right_structured_candidates,
    )
    left_structured_values = left_structured_candidates if use_structured_values else []
    right_structured_values = right_structured_candidates if use_structured_values else []
    if use_structured_values:
        left_type = "Categorical"
        right_type = "Categorical"
    data_type = _combine_data_types(left_type, right_type)
    comparison_quality = _comparison_quality(
        left_text,
        right_text,
        left_values,
        right_values,
        data_type,
        left_structured_values,
        right_structured_values,
    )
    point_count = _point_count(data_type, left_values, right_values, left_structured_values, right_structured_values)

    chart_type = "text" if (left_structured_values or right_structured_values) else choose_chart_type(data_type, point_count)

    row = {
        "id": _row_id(left_attr.get("id"), right_attr.get("id"), row_label),
        "label": row_label,
        "leftAttributeId": left_attr.get("id"),
        "rightAttributeId": right_attr.get("id"),
        "leftSourceIds": list(left_attr.get("sourceIds") or []),
        "rightSourceIds": list(right_attr.get("sourceIds") or []),
        "leftRelatedSourceIds": _source_id_list(left_attr.get("relatedSourceIds")),
        "rightRelatedSourceIds": _source_id_list(right_attr.get("relatedSourceIds")),
        "sourceKind": _source_kind(left_attr.get("source"), right_attr.get("source")),
        "dataType": data_type,
        "chartType": chart_type,
        "score": _score_pair(data_type, left_values, right_values, left_structured_values, right_structured_values),
        "comparisonQuality": comparison_quality,
        "dataPriority": bool(left_attr.get("dataPriority") or right_attr.get("dataPriority")),
        "dataRole": left_attr.get("dataRole") or right_attr.get("dataRole"),
        "comparisonQuestion": left_attr.get("comparisonQuestion") or right_attr.get("comparisonQuestion"),
        "visualization": {
            "left": _visual_side(left_attr, left_values, left_structured_values),
            "right": _visual_side(right_attr, right_values, right_structured_values),
        },
    }
    return row


def _source_id_list(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    seen: set[str] = set()
    ids: list[str] = []
    for item in value:
        if not isinstance(item, str) or not item:
            continue
        if item in seen:
            continue
        seen.add(item)
        ids.append(item)
    return ids


def _refine_values_with_model(
    value_refiner: Callable[..., Any] | None,
    *,
    key: str,
    value_text: str,
    rule_values: list[NumericValue],
    data_type: str,
) -> list[NumericValue]:
    if value_refiner is None or not rule_values:
        return rule_values
    try:
        refined = value_refiner(
            key=key,
            value_text=value_text,
            rule_values=rule_values,
            data_type=data_type,
        )
    except Exception:
        return rule_values
    return _validated_refined_values(refined) or rule_values


def _validated_refined_values(refined: Any) -> list[NumericValue]:
    if not isinstance(refined, list) or not refined:
        return []
    values: list[NumericValue] = []
    for item in refined:
        if not isinstance(item, dict):
            return []
        try:
            value = float(item.get("value"))
        except (TypeError, ValueError):
            return []
        if not math.isfinite(value):
            return []
        clean_item: NumericValue = {"value": value}
        if item.get("label") not in (None, ""):
            label = str(item["label"]).strip()
            if label:
                clean_item["label"] = label
        if item.get("year") not in (None, ""):
            try:
                clean_item["year"] = int(item["year"])
            except (TypeError, ValueError):
                return []
        if item.get("rawText") not in (None, ""):
            clean_item["rawText"] = str(item["rawText"]).strip()
        if item.get("confidence") not in (None, ""):
            try:
                confidence = float(item["confidence"])
            except (TypeError, ValueError):
                return []
            if not 0 <= confidence <= 1:
                return []
            clean_item["confidence"] = confidence
        values.append(clean_item)
    return values


def rank_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    indexed_rows = [
        (index, _row_with_rank_score(row))
        for index, row in enumerate(rows)
    ]
    return [
        row
        for _, row in sorted(
            indexed_rows,
            key=lambda item: (
                _visual_rank_bucket(item[1]),
                -_weighted_score(item[1]),
                str(item[1].get("label") or item[1].get("id") or ""),
                item[0],
            ),
        )
    ]


def _extract_labeled_percentage_series(text: str) -> list[NumericValue]:
    matches = [match for match in NUMBER_RE.finditer(text) if (match.group(2) or "").lower() in {"%", "percent"}]
    if len(matches) < 2:
        return []

    years = [int(match.group(1)) for match in YEAR_RE.finditer(text)]
    values: list[NumericValue] = []
    previous_end = 0
    for match in matches:
        label = _clean_series_label(text[previous_end:match.start()])
        previous_end = match.end()
        if not label:
            return []
        number = _parse_number(match.group(1))
        if number is None:
            return []
        item: NumericValue = {"value": number, "label": label}
        if len(years) == 1:
            item["year"] = years[0]
        values.append(item)
    return values


def _extract_colon_labeled_value_series(text: str) -> list[NumericValue]:
    segments = re.split(r"\s*;\s*|\n+", text)
    years = [int(match.group(1)) for match in YEAR_RE.finditer(text)]
    values: list[NumericValue] = []
    for segment in segments:
        if ":" not in segment:
            continue
        label_text, value_text = segment.split(":", 1)
        label = _clean_series_label(label_text)
        if not label:
            continue
        number_match = NUMBER_RE.search(value_text)
        if not number_match:
            continue
        raw_number = number_match.group(1)
        if _is_year_token(raw_number) or _is_date_number(value_text, number_match):
            continue
        unit = (number_match.group(2) or "").lower()
        number = _parse_number(raw_number)
        if number is None:
            continue
        item: NumericValue = {"value": _scale_number(number, unit), "label": label}
        segment_years = [int(match.group(1)) for match in YEAR_RE.finditer(value_text)]
        if segment_years:
            item["year"] = segment_years[-1]
        elif len(years) == 1:
            item["year"] = years[0]
        values.append(item)
    return values if len(values) >= 2 else []


def _extract_index_rating_rank_values(text: str) -> list[NumericValue]:
    match = INDEX_RATING_RANK_RE.match(text)
    if not match:
        return []
    index_value = _parse_number(match.group(1))
    rank_value = _parse_number(match.group(5))
    if index_value is None or rank_value is None:
        return []
    rating = re.sub(r"\s+", " ", match.group(2).strip())
    year_context = match.group(3).strip()
    year = int(match.group(4))
    rank_raw = f"{match.group(5)}{match.group(6)}"
    return [
        {
            "value": index_value,
            "year": year,
            "label": "index",
            "rawText": f"{match.group(1)} {rating} ({year_context})",
        },
        {
            "value": rank_value,
            "year": year,
            "label": "rank",
            "rawText": rank_raw,
        },
    ]


def _extract_hdi_series_values(text: str) -> list[NumericValue]:
    index_matches = list(HDI_INDEX_RE.finditer(text))
    if len(index_matches) < 2 and "IHDI" not in text:
        return []

    values: list[NumericValue] = []
    for index, match in enumerate(index_matches):
        segment_end = index_matches[index + 1].start() if index + 1 < len(index_matches) else len(text)
        segment = text[match.start():segment_end]
        index_value = _parse_number(match.group(1))
        if index_value is None:
            return []
        year_match = YEAR_RE.search(segment)
        rank_match = ORDINAL_RE.search(segment)
        if not year_match:
            return []
        year = int(year_match.group(1))
        label_prefix = "IHDI" if match.group(3) else "HDI"
        rating = re.sub(r"\s+", " ", match.group(2).strip())
        rating_suffix = f" {label_prefix}" if label_prefix == "IHDI" else ""
        values.append(
            {
                "value": index_value,
                "year": year,
                "label": f"{label_prefix} index",
                "rawText": f"{match.group(1)} {rating}{rating_suffix} ({year})",
            }
        )
        if rank_match:
            rank_value = _parse_number(re.match(r"\d+", rank_match.group(0)).group(0))
            if rank_value is None:
                return []
            values.append(
                {
                    "value": rank_value,
                    "year": year,
                    "label": f"{label_prefix} rank",
                    "rawText": rank_match.group(0),
                }
            )
    return values if len(values) >= 4 else []


def _extract_cpi_score_rank_values(text: str) -> list[NumericValue]:
    inline_rank_match = CPI_SCORE_INLINE_RANK_RE.match(text)
    trailing_rank_match = CPI_SCORE_RANK_RE.match(text)
    match = inline_rank_match or trailing_rank_match
    if not match:
        return []

    score_value = _parse_number(match.group(1))
    year = int(match.group(3))
    if score_value is None:
        return []

    if inline_rank_match:
        rank_raw = match.group(4)
        rank_number = match.group(5)
    else:
        rank_raw = match.group(4)
        rank_number = match.group(5)
    if not rank_raw or not rank_number:
        return []
    rank_value = _parse_number(rank_number)
    if rank_value is None:
        return []
    return [
        {
            "value": score_value,
            "year": year,
            "label": "score",
            "rawText": f"{match.group(1)} out of 100 points",
        },
        {
            "value": rank_value,
            "year": year,
            "label": "rank",
            "rawText": rank_raw,
        },
    ]


def _extract_ordinal_context_values(text: str) -> list[NumericValue]:
    values: list[NumericValue] = []
    for match in ORDINAL_CONTEXT_RE.finditer(text):
        number = _parse_number(match.group(1))
        if number is None:
            return []
        context = match.group(3).strip(" )")
        label = _parenthetical_label(context)
        if not label:
            return []
        item: NumericValue = {"value": number, "label": label}
        year_match = YEAR_RE.search(context)
        if year_match:
            item["year"] = int(year_match.group(1))
        values.append(item)
    return values if len(values) >= 2 else []


def _extract_parenthetical_year_value_pairs(text: str) -> list[NumericValue]:
    values = []
    matches = list(PAREN_YEAR_VALUE_RE.finditer(text))
    currency_labels = _currency_labels_in_text(text, matches)
    use_currency_labels = len(currency_labels) >= 2
    for index, match in enumerate(matches):
        unit = (match.group(2) or "").lower()
        if _is_secondary_gdp_share(text, match, unit):
            continue
        if _is_secondary_magnitude_count(text, match, unit):
            continue
        number = _parse_number(match.group(1))
        if number is None:
            continue
        item: NumericValue = {
            "value": _scale_number(number, unit),
            "year": int(match.group(4)),
        }
        label = _label_for_match(
            text,
            match,
            parenthetical_context=match.group(3),
            use_currency_labels=use_currency_labels,
            next_match_start=matches[index + 1].start() if index + 1 < len(matches) else len(text),
        )
        if label:
            item["label"] = label
        values.append(item)
    return values


def _extract_parenthetical_label_value_pairs(text: str) -> list[NumericValue]:
    values = []
    for match in PAREN_LABEL_VALUE_RE.finditer(text):
        context = match.group(3)
        if YEAR_RE.search(context):
            continue
        label = _parenthetical_label(context)
        if not label:
            continue
        unit = (match.group(2) or "").lower()
        if _is_secondary_gdp_share(text, match, unit):
            continue
        if _is_secondary_magnitude_count(text, match, unit):
            continue
        number = _parse_number(match.group(1))
        if number is None:
            continue
        values.append({
            "value": _scale_number(number, unit),
            "label": label,
        })
    return values


def _extract_gdp_share_values(text: str) -> list[NumericValue]:
    values = []
    for match in NUMBER_RE.finditer(text):
        unit = (match.group(2) or "").lower()
        if unit not in {"%", "percent"}:
            continue
        if not GDP_SHARE_AFTER_RE.search(text[match.end():]):
            continue
        number = _parse_number(match.group(1))
        if number is None:
            continue
        item: NumericValue = {"value": number}
        year_match = YEAR_RE.search(text[match.end(): match.end() + 80])
        if year_match:
            item["year"] = int(year_match.group(1))
        item["label"] = "% of GDP"
        values.append(item)
    return values


def _deduplicate_numeric_values(values: list[NumericValue]) -> list[NumericValue]:
    with_year_keys = {
        (_normalized_label(value.get("label")), _numeric_identity(value.get("value")))
        for value in values
        if value.get("year") is not None and value.get("value") is not None
    }
    seen = set()
    deduplicated = []
    for value in values:
        key = (
            _normalized_label(value.get("label")),
            _numeric_identity(value.get("value")),
            value.get("year"),
        )
        if key in seen:
            continue
        no_year_duplicate_key = (
            _normalized_label(value.get("label")),
            _numeric_identity(value.get("value")),
        )
        if value.get("year") is None and no_year_duplicate_key in with_year_keys:
            continue
        seen.add(key)
        deduplicated.append(value)
    return deduplicated


def _numeric_identity(value: Any) -> float | None:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    return round(number, 6)


def _parenthetical_year_value_spans(text: str) -> list[tuple[int, int]]:
    return [match.span() for match in PAREN_YEAR_VALUE_RE.finditer(text)]


def _parenthetical_label_value_spans(text: str) -> list[tuple[int, int]]:
    return [
        match.span()
        for match in PAREN_LABEL_VALUE_RE.finditer(text)
        if not YEAR_RE.search(match.group(3)) and _parenthetical_label(match.group(3))
    ]


def _parenthetical_value_spans(text: str) -> list[tuple[int, int]]:
    return _parenthetical_year_value_spans(text) + _parenthetical_label_value_spans(text)


def _extract_year_value_pairs(text: str) -> list[dict[str, float | int]]:
    values = []
    for match in YEAR_VALUE_RE.finditer(text):
        if match.group(0).strip().startswith(f"{match.group(1)}-"):
            continue
        if _is_right_edge_of_year_range(text, match.start()):
            continue
        year = int(match.group(1))
        number = _parse_number(match.group(2))
        if number is None:
            continue
        values.append({"year": year, "value": _scale_number(number, (match.group(3) or "").lower())})
    return values


def _contains_year_range(text: str) -> bool:
    return bool(YEAR_RANGE_RE.search(text.strip()))


def _is_right_edge_of_year_range(text: str, start_index: int) -> bool:
    prefix = text[:start_index]
    return bool(re.search(r"(?:18|19|20|21)\d{2}\s*[-–—]\s*$", prefix))


def _is_standalone_year_attribute(text: str, raw_number: str) -> bool:
    if not _is_year_token(raw_number):
        return False
    years = YEAR_RE.findall(text)
    if len(years) != 1:
        return False
    return not _extract_year_value_pairs(text)


def _has_trend_shape(text: str) -> bool:
    paired_years = {
        value["year"]
        for value in _extract_parenthetical_year_value_pairs(text) + _extract_year_value_pairs(text)
        if "year" in value
    }
    if len(paired_years) >= 2:
        return True
    value_years = {
        value["year"]
        for value in extract_numeric_values(text)
        if "year" in value
    }
    return len(value_years) >= 2


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


def _label_for_match(
    text: str,
    match: re.Match,
    *,
    parenthetical_context: str | None = None,
    use_currency_labels: bool = False,
    next_match_start: int | None = None,
) -> str | None:
    prefix_label = _prefix_label(text, match.start())
    if prefix_label:
        return prefix_label
    parenthetical_label = _parenthetical_label(parenthetical_context)
    if parenthetical_label:
        return parenthetical_label
    if use_currency_labels:
        currency_label = _currency_label(text, match)
        if currency_label:
            return currency_label
    suffix_label = _suffix_label(text, match.end(), next_match_start or len(text))
    if suffix_label:
        return suffix_label
    return None


def _prefix_label(text: str, start_index: int) -> str | None:
    prefix = text[:start_index]
    boundary = max(prefix.rfind(separator) for separator in (".", ";", "\n", ")"))
    candidate = prefix[boundary + 1:]
    match = re.search(r"([A-Za-z][A-Za-z /&-]{1,40}):\s*$", candidate)
    if not match:
        return None
    label = _clean_label(match.group(1))
    if not label:
        return None
    if label.lower() not in {
        "inward",
        "outward",
        "abroad",
        "domestic",
        "foreign",
        "local",
        "nominal",
        "ppp",
        "male",
        "female",
    }:
        return None
    return label


def _parenthetical_label(context: str | None) -> str | None:
    if not context:
        return None
    without_year = YEAR_RE.sub("", context)
    without_noise = re.sub(
        rf"\b(?:{'|'.join(_month_names())}|est|estimate|estimated|forecast|f|proj|projected)\b",
        "",
        without_year,
        flags=re.IGNORECASE,
    )
    for part in re.split(r"[;,/]", without_noise):
        label = _clean_label(part)
        if label:
            return label
    return None


def _suffix_label(text: str, start_index: int, end_index: int) -> str | None:
    suffix = text[start_index:min(end_index, start_index + 90)]
    youth_match = re.search(r"\byouth\s+unemployment\b|\byouth\b", suffix, re.IGNORECASE)
    if youth_match and not NUMBER_RE.search(suffix[:youth_match.start()]):
        return "youth"
    return None


def _currency_labels_in_text(text: str, matches: list[re.Match]) -> set[str]:
    return {
        label
        for match in matches
        if (label := _currency_label(text, match))
    }


def _currency_label(text: str, match: re.Match) -> str | None:
    prefix = text[max(0, match.start() - 8):match.start(1)]
    suffix = text[match.end():match.end() + 8]
    compact = prefix.replace(" ", "").upper()
    suffix_compact = suffix.replace(" ", "").upper()
    if "US$" in compact or "USD" in compact:
        return "USD"
    if "¥" in prefix or "¥" in suffix or "JPY" in compact or "JPY" in suffix_compact:
        return "JPY"
    if "₩" in prefix or "₩" in suffix or "KRW" in compact or "KRW" in suffix_compact:
        return "KRW"
    if "€" in prefix or "€" in suffix or "EUR" in compact or "EUR" in suffix_compact:
        return "EUR"
    if "£" in prefix or "£" in suffix or "GBP" in compact or "GBP" in suffix_compact:
        return "GBP"
    if "$" in prefix:
        return "USD"
    return None


def _apply_contextual_value_labels(values: list[NumericValue], text: str) -> list[NumericValue]:
    if re.search(r"\babroad\s*:", text, re.IGNORECASE):
        has_abroad = any(_normalized_label(value.get("label")) == "abroad" for value in values)
        if has_abroad:
            for value in values:
                if not value.get("label"):
                    value["label"] = "Inward"
                    break

    if not re.search(r"\bunemployment\b", text, re.IGNORECASE):
        return values
    if not any(value.get("label") == "youth" for value in values):
        return values
    for value in values:
        if "label" not in value:
            value["label"] = "overall"
            break
    return values


def _clean_label(raw_label: str | None) -> str | None:
    label = re.sub(r"\s+", " ", str(raw_label or "").strip(" :;,.()-"))
    if not label:
        return None
    if YEAR_RE.search(label) or MONTH_RE.search(label) or re.search(r"\d", label):
        return None
    lower = label.lower()
    if lower in {"est", "estimate", "estimated", "forecast", "f", "proj", "projected", "monthly", "annual"}:
        return None
    if lower == "ppp":
        return "PPP"
    if len(label) > 32:
        return None
    return label


def _clean_series_label(raw_label: str | None) -> str | None:
    text = str(raw_label or "")
    if ":" in text:
        before_colon, after_colon = text.rsplit(":", 1)
        text = after_colon if after_colon.strip() else before_colon
    label = re.sub(r"\s+", " ", text.strip(" :;,.()-"))
    if not label:
        return None
    if YEAR_RE.fullmatch(label.strip()):
        return None
    if MONTH_RE.search(label):
        return None
    lower = label.lower()
    if lower in {"est", "estimate", "estimated", "forecast", "f", "proj", "projected", "monthly", "annual"}:
        return None
    if lower == "ppp":
        return "PPP"
    if len(label) > 32:
        return None
    return label


def _month_names() -> list[str]:
    return [
        "January",
        "February",
        "March",
        "April",
        "May",
        "June",
        "July",
        "August",
        "September",
        "October",
        "November",
        "December",
    ]


def _is_date_number(text: str, match: re.Match) -> bool:
    if _is_year_token(match.group(1)):
        return False
    suffix = text[match.end(): match.end() + 18]
    prefix = text[max(0, match.start() - 18): match.start()]
    return bool(
        re.match(rf"\s*{MONTH_RE.pattern}", suffix, re.IGNORECASE)
        or re.search(rf"{MONTH_RE.pattern}\s*$", prefix, re.IGNORECASE)
    )


def _is_inside_spans(match: re.Match, spans: list[tuple[int, int]]) -> bool:
    return any(start <= match.start() and match.end() <= end for start, end in spans)


def _is_secondary_gdp_share(text: str, match: re.Match, unit: str) -> bool:
    if unit not in {"%", "percent"}:
        return False
    if not GDP_SHARE_AFTER_RE.search(text[match.end():]):
        return False
    return _has_absolute_amount(text)


def _is_secondary_magnitude_count(text: str, match: re.Match, unit: str) -> bool:
    if unit not in MAGNITUDES:
        return False
    if _match_has_currency(text, match):
        return False
    return "%" in text or re.search(r"\bpercent\b", text, re.IGNORECASE)


def _has_amount_with_secondary_gdp_share(text: str) -> bool:
    return _has_absolute_amount(text) and bool(
        re.search(r"(?:%|percent)\s+of\s+GDP\b", text, re.IGNORECASE)
    )


def _has_absolute_amount(text: str) -> bool:
    if re.search(r"[$€£¥]\s*[-+]?(?:\d{1,3}(?:,\d{3})+|\d+)(?:\.\d+)?", text):
        return True
    return bool(
        re.search(
            rf"\b[-+]?(?:\d{{1,3}}(?:,\d{{3}})+|\d+)(?:\.\d+)?\s*(?:{MAGNITUDE_PATTERN})\b",
            text,
            re.IGNORECASE,
        )
    )


def _match_has_currency(text: str, match: re.Match) -> bool:
    return bool(re.search(r"[$€£¥]", text[match.start(): match.start(1)]))


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
    left_structured_values: list[dict[str, Any]] | None = None,
    right_structured_values: list[dict[str, Any]] | None = None,
) -> int:
    structured_count = max(len(left_structured_values or []), len(right_structured_values or []))
    if structured_count:
        return structured_count
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
    left_structured_values: list[dict[str, Any]] | None = None,
    right_structured_values: list[dict[str, Any]] | None = None,
) -> float:
    if left_structured_values or right_structured_values:
        return _structured_value_difference(left_structured_values or [], right_structured_values or [])
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
    labeled_pairs = _shared_labeled_value_pairs(left_values, right_values)
    if labeled_pairs:
        diffs = [
            _normalized_difference(float(left["value"]), float(right["value"]))
            for left, right in labeled_pairs
        ]
        return round(sum(diffs) / len(diffs), 6)

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


def _comparison_quality(
    left_text: str,
    right_text: str,
    left_values: list[dict[str, float | int]],
    right_values: list[dict[str, float | int]],
    data_type: str,
    left_structured_values: list[dict[str, Any]] | None = None,
    right_structured_values: list[dict[str, Any]] | None = None,
) -> str:
    if left_structured_values or right_structured_values:
        return "structured_values"
    if _shared_labeled_value_pairs(left_values, right_values):
        return "shared_labels"
    if data_type == "Numerical" and _has_conflicting_currency_units(left_text, right_text):
        return "unit_mismatch"
    return "direct"


def _shared_labeled_value_pairs(
    left_values: list[dict[str, float | int]],
    right_values: list[dict[str, float | int]],
) -> list[tuple[dict[str, float | int], dict[str, float | int]]]:
    left_by_label = {
        _normalized_label(value.get("label")): value
        for value in left_values
        if value.get("label") and "value" in value
    }
    right_by_label = {
        _normalized_label(value.get("label")): value
        for value in right_values
        if value.get("label") and "value" in value
    }
    labels = sorted(set(left_by_label) & set(right_by_label))
    return [(left_by_label[label], right_by_label[label]) for label in labels]


def _normalized_label(label: Any) -> str:
    return re.sub(r"\s+", " ", str(label or "").strip().lower())


def _has_conflicting_currency_units(left_text: str, right_text: str) -> bool:
    left_units = _currency_units_in_text(left_text)
    right_units = _currency_units_in_text(right_text)
    return bool(left_units and right_units and left_units.isdisjoint(right_units))


def _currency_units_in_text(text: str) -> set[str]:
    units = set()
    compact = str(text or "").upper()
    if "US$" in compact or "$" in compact or "USD" in compact:
        units.add("USD")
    if "¥" in compact or "JPY" in compact:
        units.add("JPY")
    if "₩" in compact or "KRW" in compact:
        units.add("KRW")
    if "€" in compact or "EUR" in compact:
        units.add("EUR")
    if "£" in compact or "GBP" in compact:
        units.add("GBP")
    return units


def _normalized_difference(left: float, right: float) -> float:
    denominator = max(abs(left), abs(right), 1e-9)
    return min(1.0, abs(left - right) / denominator)


def _visual_side(
    attr: dict[str, Any],
    values: list[dict[str, float | int]],
    structured_values: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    side = {
        "attributeId": attr.get("id"),
        "label": attr.get("key"),
        "raw": attr.get("valueText"),
        "values": values,
    }
    if structured_values:
        side["structuredValues"] = structured_values
    return side


def _structured_values(attr: dict[str, Any]) -> list[dict[str, Any]]:
    raw_values = attr.get("structuredValues")
    if not isinstance(raw_values, list):
        return []
    values = []
    seen = set()
    for raw_value in raw_values:
        if not isinstance(raw_value, dict):
            continue
        value = str(raw_value.get("value") or raw_value.get("label") or "").strip()
        if not value:
            continue
        normalized = _normalized_label(value)
        if normalized in seen:
            continue
        seen.add(normalized)
        values.append(
            {
                "label": str(raw_value.get("label") or value).strip(),
                "value": value,
                "kind": str(raw_value.get("kind") or "item").strip(),
            }
        )
    return values


def _should_use_structured_values(
    left_values: list[NumericValue],
    right_values: list[NumericValue],
    left_structured_values: list[dict[str, Any]],
    right_structured_values: list[dict[str, Any]],
) -> bool:
    if not (left_structured_values or right_structured_values):
        return False
    return not (left_values or right_values)


def _inferred_structured_values(attr: dict[str, Any]) -> list[dict[str, Any]]:
    key = str(attr.get("key") or "")
    value_text = str(attr.get("valueText") or "")
    return _currency_structured_values(key, value_text)


def _currency_structured_values(key: str, value_text: str) -> list[dict[str, Any]]:
    text = re.sub(r"\s+", " ", str(value_text or "")).strip()
    if not text:
        return []

    match = re.match(r"^(.+?)\s*\(([^)]{2,80})\)\s*$", text)
    if not match:
        return []

    name = match.group(1).strip(" ,;")
    inner_items = [
        item.strip()
        for item in re.split(r"\s*[,;/]\s*", match.group(2))
        if item.strip()
    ]
    code = next((item for item in inner_items if re.fullmatch(r"[A-Z]{3}", item)), "")
    symbol = next(
        (
            item
            for item in inner_items
            if item != code and any(char in CURRENCY_SYMBOLS for char in item)
        ),
        "",
    )
    key_mentions_currency = "currency" in _normalized_label(key)
    if not name or not code:
        return []
    if not key_mentions_currency and not symbol:
        return []

    values = [
        {"label": "Name", "value": name, "kind": "entity_name"},
        {"label": "Code", "value": code, "kind": "currency_code"},
    ]
    if symbol:
        values.append({"label": "Symbol", "value": symbol, "kind": "currency_symbol"})
    return values


def _structured_value_difference(
    left_values: list[dict[str, Any]],
    right_values: list[dict[str, Any]],
) -> float:
    left = {_normalized_label(value.get("value") or value.get("label")) for value in left_values}
    right = {_normalized_label(value.get("value") or value.get("label")) for value in right_values}
    left.discard("")
    right.discard("")
    if not left and not right:
        return 0.0
    if not left or not right:
        return 0.2
    shared = left & right
    total = left | right
    return round(1 - (len(shared) / len(total)), 6)


def _row_id(left_id: Any, right_id: Any, label: str) -> str:
    seed = f"{left_id or ''}|{right_id or ''}|{label}"
    digest = hashlib.sha1(seed.encode("utf-8")).hexdigest()[:12]
    return f"row-{digest}"


def _weighted_score(row: dict[str, Any]) -> float:
    score = float(row.get("score") or 0)
    if row.get("comparisonQuality") == "unit_mismatch":
        return score * 0.03
    data_type = row.get("dataType")
    if data_type == "Trend":
        return score * 0.5
    if data_type in {"Numerical", "Proportional"}:
        return score * 0.3
    return score * 0.2


def _row_with_rank_score(row: dict[str, Any]) -> dict[str, Any]:
    ranked = dict(row)
    ranked["rankScore"] = round(_weighted_score(row), 6)
    return ranked


def _visual_rank_bucket(row: dict[str, Any]) -> int:
    if row.get("dataPriority") and row.get("sourceKind") == "main_text":
        return 0
    return 0 if _is_chartable_row(row) else 1


def _is_chartable_row(row: dict[str, Any]) -> bool:
    chart_type = str(row.get("chartType") or "").strip().lower()
    if chart_type:
        return chart_type != "text"
    return row.get("dataType") in {"Trend", "Numerical", "Proportional"}
