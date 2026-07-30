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
SIGNED_PAREN_YEAR_VALUE_RE = re.compile(
    rf"(?<![\w.])([-+]?)\s*[$€£¥]?\s*([-+]?(?:\d{{1,3}}(?:,\d{{3}})+|\d+)(?:\.\d+)?)(?:\s*(%|percent|{MAGNITUDE_PATTERN}))?\s*\(([^)]*\b((?:18|19|20|21)\d{{2}})\w*[^)]*)\)",
    re.IGNORECASE,
)
PAREN_LABEL_VALUE_RE = re.compile(
    rf"(?<![\w.])[$€£¥]?\s*([-+]?(?:\d{{1,3}}(?:,\d{{3}})+|\d+)(?:\.\d+)?)(?:st|nd|rd|th)?(?:\s*(%|percent|{MAGNITUDE_PATTERN}))?\s*\(([^)]*)\)",
    re.IGNORECASE,
)
COLON_METRIC_YEAR_VALUE_RE = re.compile(
    rf"([A-Za-z][A-Za-z /&-]*(?:\s+per\s+\d+\s+[A-Za-z /&-]+)?):\s*([-+]?)\s*[$€£¥]?\s*([-+]?(?:\d{{1,3}}(?:,\d{{3}})+|\d+)(?:\.\d+)?)(?:\s*(%|percent|{MAGNITUDE_PATTERN}))?\s*\([^)]*\b((?:18|19|20|21)\d{{2}})\w*[^)]*\)",
    re.IGNORECASE,
)
CHAINED_COLON_VALUE_RE = re.compile(
    rf"(?<![A-Za-z0-9])([A-Za-z][A-Za-z0-9 /&-]{{0,60}}?):\s*[$€£¥]?\s*([-+]?(?:\d{{1,3}}(?:,\d{{3}})+|\d+)(?:\.\d+)?)(?:\s*(%|percent|{MAGNITUDE_PATTERN}))?",
    re.IGNORECASE,
)
AGE_RANGE_COLON_VALUE_RE = re.compile(
    rf"(?<![\w.])((?:\d+\s*(?:to|-|–|—)\s*\d+\s*(?:years?|yrs?)|\d+\s*(?:years?|yrs?)\s+(?:(?:and|or)\s+)?(?:over|older|above)|(?:under|below)\s+\d+\s*(?:years?|yrs?)))\s*:\s*[$€£¥]?\s*([-+]?(?:\d{{1,3}}(?:,\d{{3}})+|\d+)(?:\.\d+)?)(?:\s*(%|percent|{MAGNITUDE_PATTERN}))?",
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
DEMOGRAPHIC_AGE_RANGE_RE = re.compile(
    r"\b(?:ages?|aged|women|men|female|male|people|persons|children)\s+\d+\s*(?:to|-|–|—)\s*\d+\b",
    re.IGNORECASE,
)
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
TEMPORAL_METADATA_KEYS = {
    "commenced operations",
    "date",
    "established",
    "formation",
    "founded",
    "introduced",
    "launched",
    "released",
}
TEXT_METADATA_KEYS = {
    "administrative divisions",
    "broadcast media",
    "capital",
    "citizenship",
    "diplomatic representation in the us",
    "disease",
    "executive branch",
    "geographic coordinates",
    "headquarters",
    "industry",
    "judicial branch",
    "military deployments",
    "military and security forces",
    "natural hazards",
    "owner",
    "pathogen",
    "suffrage",
    "traded as",
    "updated",
    "website",
}
TEMPORAL_METADATA_TERMS = {
    "aired",
    "announced",
    "appearance",
    "detected",
    "flight",
    "opened",
    "premiered",
    "reported",
}


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
    if _extract_colon_metric_year_value_series(text):
        return "Numerical"
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

    age_range_values = _extract_age_range_labeled_value_series(text)
    if age_range_values:
        return age_range_values

    chained_colon_values = _extract_chained_colon_labeled_value_series(text)
    if chained_colon_values:
        return chained_colon_values

    colon_labeled_values = _extract_colon_labeled_value_series(text)
    if colon_labeled_values:
        return colon_labeled_values

    colon_metric_year_values = _extract_colon_metric_year_value_series(text)
    if colon_metric_year_values:
        return colon_metric_year_values

    labeled_percentage_values = _extract_labeled_percentage_series(text)
    if labeled_percentage_values:
        return labeled_percentage_values

    named_numeric_values = (
        _extract_ports_value_series(text)
        or _extract_elevation_value_series(text)
        or _extract_dash_labeled_value_series(text)
        or _extract_leading_value_labeled_series(text)
    )
    if named_numeric_values:
        return named_numeric_values

    total_value = _extract_total_colon_value(text)
    if total_value:
        return total_value

    parenthetical_values = _extract_parenthetical_year_value_pairs(text)
    parenthetical_label_values = _extract_parenthetical_label_value_pairs(text)
    parenthetical_spans = _parenthetical_value_spans(text)

    year_values = _extract_year_value_pairs(text)
    if year_values:
        candidate_values = list(parenthetical_values) + list(parenthetical_label_values)
        if candidate_values and len(candidate_values) > len(year_values):
            return _apply_contextual_value_labels(_deduplicate_numeric_values(candidate_values), text)
        return year_values

    years = [int(match.group(1)) for match in YEAR_RE.finditer(text)]
    age_range_spans = [match.span() for match in AGE_RANGE_RE.finditer(text)] + [
        match.span() for match in DEMOGRAPHIC_AGE_RANGE_RE.finditer(text)
    ]
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
        if _is_embedded_number_token(text, match):
            continue
        if _is_rate_denominator_token(text, match):
            continue
        if _is_inside_spans(match, parenthetical_spans):
            continue
        if _is_date_number(text, match):
            continue
        if _is_compact_year_suffix_token(text, match):
            continue
        if _is_age_context_number(text, match):
            continue
        if _is_inside_spans(match, age_range_spans):
            continue
        if _is_secondary_gdp_share(text, match, unit):
            continue
        if _is_secondary_magnitude_count(text, match, unit):
            continue
        if is_year:
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
    used_exact_keys: set[str] = set()

    right_by_key: dict[str, list[dict[str, Any]]] = {}
    for attribute in right_pool:
        key = _alignment_key(attribute.get("key"))
        if not key:
            continue
        right_by_key.setdefault(key, []).append(attribute)
    for left_attribute in left_pool:
        key = _alignment_key(left_attribute.get("key"))
        right_attribute = _best_exact_key_match(
            left_attribute,
            right_by_key.get(key) or [],
            used_right_ids,
        )
        if not key or right_attribute is None:
            continue
        if key in used_exact_keys or right_attribute.get("id") in used_right_ids:
            continue
        alignments.append(
            {
                "left": left_attribute,
                "right": right_attribute,
                "label": left_attribute.get("key") or right_attribute.get("key") or key,
            }
        )
        used_right_ids.add(right_attribute.get("id"))
        if len(right_by_key.get(key) or []) <= 1:
            used_exact_keys.add(key)

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


def _best_exact_key_match(
    left_attribute: dict[str, Any],
    right_candidates: list[dict[str, Any]],
    used_right_ids: set[Any],
) -> dict[str, Any] | None:
    unused_candidates = [
        candidate
        for candidate in right_candidates
        if candidate.get("id") not in used_right_ids
    ]
    if not unused_candidates:
        return None
    left_shape = _value_shape(left_attribute.get("valueText"))
    for candidate in unused_candidates:
        if _value_shape(candidate.get("valueText")) == left_shape:
            return candidate
    return unused_candidates[0]


def _value_shape(value: Any) -> str:
    text = str(value or "").lower()
    if re.search(r"\bmale(?:\(s\))?\s*/\s*female\b|\bmale\s+to\s+female\b", text):
        return "sex_ratio"
    if "%" in text or re.search(r"\bpercent\b", text):
        return "percentage"
    return "other"


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
    data_role = left_attr.get("dataRole") or right_attr.get("dataRole")
    left_provided_values = _provided_numeric_values(left_attr)
    right_provided_values = _provided_numeric_values(right_attr)
    left_rule_values = extract_numeric_values(left_text)
    right_rule_values = extract_numeric_values(right_text)
    left_values = _recover_labeled_rule_values(left_provided_values, left_rule_values) if left_provided_values else left_rule_values
    right_values = _recover_labeled_rule_values(right_provided_values, right_rule_values) if right_provided_values else right_rule_values
    left_type = classify_value_rule(left_text)
    right_type = classify_value_rule(right_text)
    if left_provided_values:
        left_type = _data_type_for_role(data_role, left_values, left_type)
    if right_provided_values:
        right_type = _data_type_for_role(data_role, right_values, right_type)
    row_label = str(label or left_attr.get("key") or right_attr.get("key") or "").strip()
    left_structured_candidates = _structured_values(left_attr) or _inferred_structured_values(left_attr)
    right_structured_candidates = _structured_values(right_attr) or _inferred_structured_values(right_attr)
    if not left_provided_values:
        left_values = _refine_values_with_model(
            value_refiner,
            key=str(left_attr.get("key") or row_label),
            value_text=left_text,
            rule_values=left_values,
            data_type=left_type,
        )
    if not right_provided_values:
        right_values = _refine_values_with_model(
            value_refiner,
            key=str(right_attr.get("key") or row_label),
            value_text=right_text,
            rule_values=right_values,
            data_type=right_type,
        )
    left_gdp_share_values = _extract_gdp_share_values(left_text) or _extract_contextual_gdp_share_year_values(left_text)
    right_gdp_share_values = _extract_gdp_share_values(right_text) or _extract_contextual_gdp_share_year_values(right_text)
    if left_gdp_share_values and right_gdp_share_values:
        left_values = left_gdp_share_values
        right_values = right_gdp_share_values
        if _is_year_series(left_values) or _is_year_series(right_values):
            left_type = "Trend"
            right_type = "Trend"
        else:
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
    if (
        _is_temporal_metadata_role(data_role)
        or _is_temporal_metadata_attribute(row_label, left_attr, right_attr)
        or _is_text_metadata_attribute(row_label, left_attr, right_attr)
        or _is_incomplete_main_text_data_pair(left_attr, right_attr, data_role, left_values, right_values)
        or _has_incompatible_single_point_main_text_years(left_attr, right_attr, data_role, left_values, right_values)
        or (
        _is_generic_main_text_pair(left_attr, right_attr, data_role)
        and not _has_explicit_main_text_visual_signal(
            left_type,
            right_type,
            left_values,
            right_values,
        )
        )
    ):
        left_values = []
        right_values = []
        left_type = "Text"
        right_type = "Text"
        left_structured_values = []
        right_structured_values = []
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

    chart_type = (
        "text"
        if (left_structured_values or right_structured_values)
        else _chart_type_for_values(
            data_type,
            point_count,
            left_values,
            right_values,
            row_label=row_label,
            left_text=left_text,
            right_text=right_text,
        )
    )

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
        "dataPriority": False if _is_temporal_metadata_role(data_role) else bool(left_attr.get("dataPriority") or right_attr.get("dataPriority")),
        "dataRole": data_role,
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


def _provided_numeric_values(attr: dict[str, Any]) -> list[NumericValue]:
    raw_values = attr.get("extractedValues")
    if not isinstance(raw_values, list):
        return []
    return _validated_refined_values(raw_values)


def _recover_labeled_rule_values(
    provided_values: list[NumericValue],
    rule_values: list[NumericValue],
) -> list[NumericValue]:
    if not provided_values or not rule_values:
        return provided_values
    provided_label_count = sum(1 for value in provided_values if value.get("label"))
    rule_label_count = sum(1 for value in rule_values if value.get("label"))
    if provided_label_count >= 2 or rule_label_count < 2:
        return provided_values
    if not _rule_values_cover_provided_numbers(provided_values, rule_values):
        return provided_values
    return rule_values


def _rule_values_cover_provided_numbers(
    provided_values: list[NumericValue],
    rule_values: list[NumericValue],
) -> bool:
    remaining = [float(value["value"]) for value in rule_values if "value" in value]
    for provided in provided_values:
        if "value" not in provided:
            continue
        provided_number = float(provided["value"])
        match_index = next(
            (
                index
                for index, rule_number in enumerate(remaining)
                if math.isclose(provided_number, rule_number, rel_tol=1e-9, abs_tol=1e-9)
            ),
            None,
        )
        if match_index is None:
            return False
        remaining.pop(match_index)
    return True


def _data_type_for_role(data_role: Any, values: list[NumericValue], fallback: str) -> str:
    role = str(data_role or "").strip().lower()
    if len(values) >= 2 and any("year" in value for value in values):
        return "Trend"
    if role == "proportion":
        return "Proportional"
    if role == "ranking":
        return "Ordinal"
    if role in {"quantity", "scale"}:
        return "Numerical"
    return fallback


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
        if item.get("unit") not in (None, ""):
            unit = str(item["unit"]).strip()
            if unit:
                clean_item["unit"] = unit
        if item.get("valueKind") not in (None, ""):
            value_kind = str(item["valueKind"]).strip()
            if value_kind in {"aggregate", "component", "rate", "share", "point"}:
                clean_item["valueKind"] = value_kind
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
    disambiguated_rows = _disambiguate_duplicate_metric_row_labels(rows)
    indexed_rows = [
        (index, _row_with_rank_score(row))
        for index, row in enumerate(disambiguated_rows)
        if not _is_demoted_main_text_visual_data_row(row)
        and not _is_temporal_metadata_text_row(row)
    ]
    ranked_rows = [
        row
        for _, row in sorted(
            indexed_rows,
            key=lambda item: _row_sort_key(item[0], item[1]),
        )
    ]
    return _deduplicate_ranked_rows(ranked_rows)


def _disambiguate_duplicate_metric_row_labels(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    label_counts: dict[str, int] = {}
    for row in rows:
        label_key = _normalized_label(row.get("label"))
        if label_key:
            label_counts[label_key] = label_counts.get(label_key, 0) + 1

    disambiguated: list[dict[str, Any]] = []
    for row in rows:
        label = str(row.get("label") or "").strip()
        label_key = _normalized_label(label)
        if not label_key or label_counts.get(label_key, 0) <= 1:
            disambiguated.append(row)
            continue

        suffix = _metric_row_semantic_suffix(row, label)
        if not suffix or _normalized_label(label).endswith(f": {_normalized_label(suffix)}"):
            disambiguated.append(row)
            continue

        updated = dict(row)
        updated_label = f"{label}: {suffix}"
        updated["label"] = updated_label
        updated["id"] = _row_id(
            row.get("leftAttributeId") or row.get("leftId"),
            row.get("rightAttributeId") or row.get("rightId"),
            updated_label,
        )
        disambiguated.append(updated)

    return disambiguated


def _metric_row_semantic_suffix(row: dict[str, Any], base_label: str) -> str:
    labels = _shared_value_labels_for_row(row)
    if not labels:
        return ""
    total_labels = [label for label in labels if _is_total_metric_label(label, base_label)]
    component_labels = [label for label in labels if not _is_total_metric_label(label, base_label)]
    if total_labels and not component_labels:
        return total_labels[0]
    if len(component_labels) >= 2 and not total_labels:
        return _component_metric_label(base_label)
    if len(component_labels) == 1 and not total_labels:
        return component_labels[0]
    return ""


def _shared_value_labels_for_row(row: dict[str, Any]) -> list[str]:
    visualization = row.get("visualization") if isinstance(row.get("visualization"), dict) else {}
    left_side = visualization.get("left") if isinstance(visualization.get("left"), dict) else {}
    right_side = visualization.get("right") if isinstance(visualization.get("right"), dict) else {}
    left_values = left_side.get("values") if isinstance(left_side.get("values"), list) else []
    right_values = right_side.get("values") if isinstance(right_side.get("values"), list) else []
    return _ordered_shared_metric_labels(left_values, right_values)


def split_mixed_unit_metric_rows(row: dict[str, Any]) -> list[dict[str, Any]]:
    visualization = row.get("visualization") if isinstance(row.get("visualization"), dict) else {}
    left_side = visualization.get("left") if isinstance(visualization.get("left"), dict) else {}
    right_side = visualization.get("right") if isinstance(visualization.get("right"), dict) else {}
    left_values = left_side.get("values") if isinstance(left_side.get("values"), list) else []
    right_values = right_side.get("values") if isinstance(right_side.get("values"), list) else []
    shared_labels = _ordered_shared_metric_labels(left_values, right_values)
    if row.get("dataType") == "Trend" and _is_single_shared_metric_year_series(
        left_values,
        right_values,
        shared_labels,
    ):
        return [row]
    aggregate_component_rows = _split_aggregate_component_metric_rows(row, left_side, right_side, shared_labels)
    if aggregate_component_rows:
        return aggregate_component_rows
    shared_label_row = _row_for_shared_metric_labels(row, left_side, right_side, shared_labels)
    if shared_label_row is not None:
        return [shared_label_row]
    if not _should_split_mixed_unit_metric_labels(shared_labels):
        return [row]

    split_rows: list[dict[str, Any]] = []
    base_label = str(row.get("label") or "").strip()
    for label in shared_labels:
        left_value = _first_value_for_label(left_values, label)
        right_value = _first_value_for_label(right_values, label)
        if left_value is None or right_value is None:
            continue
        split_label = f"{base_label}: {label}" if base_label else label
        split_row = dict(row)
        split_row["id"] = _row_id(
            row.get("leftAttributeId"),
            row.get("rightAttributeId"),
            split_label,
        )
        split_row["label"] = split_label
        split_data_type = "Proportional" if _is_relative_metric_label(label) else "Numerical"
        split_row["dataType"] = split_data_type
        split_row["chartType"] = _chart_type_for_values(
            split_data_type,
            2,
            [left_value],
            [right_value],
            row_label=split_label,
        )
        split_row["score"] = _score_pair(split_data_type, [left_value], [right_value])
        split_row["comparisonQuality"] = "direct"
        split_row["visualization"] = {
            "left": _visual_side_with_single_value(left_side, left_value),
            "right": _visual_side_with_single_value(right_side, right_value),
        }
        split_rows.append(split_row)
    return split_rows or [row]


def _row_for_shared_metric_labels(
    row: dict[str, Any],
    left_side: dict[str, Any],
    right_side: dict[str, Any],
    shared_labels: list[str],
) -> dict[str, Any] | None:
    if not shared_labels:
        return None
    left_values = left_side.get("values") or []
    right_values = right_side.get("values") or []
    if max(len(left_values), len(right_values)) <= len(shared_labels):
        if len(shared_labels) == 1 and _is_total_metric_label(shared_labels[0]):
            base_label = str(row.get("label") or "").strip()
            return _row_with_values(
                row,
                f"{base_label}: {shared_labels[0]}" if base_label else shared_labels[0],
                "Numerical",
                choose_chart_type("Numerical", 2),
                _values_for_labels(left_values, shared_labels),
                _values_for_labels(right_values, shared_labels),
                left_side,
                right_side,
            )
        return None
    if row.get("dataType") == "Proportional":
        return None
    left_shared = _values_for_labels(left_values, shared_labels)
    right_shared = _values_for_labels(right_values, shared_labels)
    if not left_shared or not right_shared:
        return None
    label = str(row.get("label") or "").strip()
    if len(shared_labels) == 1 and _is_total_metric_label(shared_labels[0]):
        label = f"{label}: {shared_labels[0]}" if label else shared_labels[0]
    return _row_with_values(
        row,
        label,
        row.get("dataType") or "Numerical",
        row.get("chartType") or choose_chart_type("Numerical", len(left_shared) + len(right_shared)),
        left_shared,
        right_shared,
        left_side,
        right_side,
    )


def _split_aggregate_component_metric_rows(
    row: dict[str, Any],
    left_side: dict[str, Any],
    right_side: dict[str, Any],
    shared_labels: list[str],
) -> list[dict[str, Any]]:
    base_label = str(row.get("label") or "").strip()
    if not _should_split_aggregate_component_labels(shared_labels, base_label):
        return []

    total_label = next((label for label in shared_labels if _is_total_metric_label(label, base_label)), "")
    component_labels = [label for label in shared_labels if not _is_total_metric_label(label, base_label)]
    if not total_label or len(component_labels) < 2:
        return []

    total_left = _first_value_for_label(left_side.get("values") or [], total_label)
    total_right = _first_value_for_label(right_side.get("values") or [], total_label)
    if total_left is None or total_right is None:
        return []

    component_left = _values_for_labels(left_side.get("values") or [], component_labels)
    component_right = _values_for_labels(right_side.get("values") or [], component_labels)
    if len(component_left) < 2 or len(component_right) < 2:
        return []

    total_row = _row_with_values(
        row,
        f"{base_label}: {total_label}" if base_label else total_label,
        "Numerical",
        choose_chart_type("Numerical", 2),
        [total_left],
        [total_right],
        left_side,
        right_side,
    )
    component_label = _component_metric_label(base_label)
    component_row = _row_with_values(
        row,
        f"{base_label}: {component_label}" if base_label else component_label,
        "Numerical",
        "bar",
        component_left,
        component_right,
        left_side,
        right_side,
    )
    return [total_row, component_row]


def _row_with_values(
    row: dict[str, Any],
    label: str,
    data_type: str,
    chart_type: str,
    left_values: list[dict[str, Any]],
    right_values: list[dict[str, Any]],
    left_side: dict[str, Any],
    right_side: dict[str, Any],
) -> dict[str, Any]:
    split_row = dict(row)
    split_row["id"] = _row_id(
        row.get("leftAttributeId"),
        row.get("rightAttributeId"),
        label,
    )
    split_row["label"] = label
    split_row["dataType"] = data_type
    split_row["chartType"] = chart_type
    split_row["score"] = _score_pair(data_type, left_values, right_values)
    split_row["comparisonQuality"] = "shared_labels" if max(len(left_values), len(right_values)) > 1 else "direct"
    split_row["visualization"] = {
        "left": _visual_side_with_values(left_side, left_values),
        "right": _visual_side_with_values(right_side, right_values),
    }
    return split_row


def _should_split_aggregate_component_labels(labels: list[str], base_label: str = "") -> bool:
    if len(labels) < 3:
        return False
    has_total = any(_is_total_metric_label(label, base_label) for label in labels)
    component_count = sum(1 for label in labels if not _is_total_metric_label(label, base_label))
    return has_total and component_count >= 2


def _is_total_metric_label(label: Any, base_label: str = "") -> bool:
    normalized = _normalized_label(label)
    if normalized in {"total", "overall", "all"}:
        return True
    base_normalized = _normalized_label(base_label)
    return bool(base_normalized and normalized == base_normalized)


def _values_for_labels(values: list[dict[str, Any]], labels: list[str]) -> list[dict[str, Any]]:
    result = []
    for label in labels:
        value = _first_value_for_label(values, label)
        if value is not None:
            result.append(value)
    return result


def _component_metric_label(base_label: str) -> str:
    if re.search(r"\balcohol\b", base_label, re.IGNORECASE):
        return "beverage categories"
    return "component categories"


def _ordered_shared_metric_labels(
    left_values: list[dict[str, Any]],
    right_values: list[dict[str, Any]],
) -> list[str]:
    right_labels = {
        _normalized_label(value.get("label"))
        for value in right_values
        if value.get("label")
    }
    labels: list[str] = []
    seen: set[str] = set()
    for value in left_values:
        label = str(value.get("label") or "").strip()
        normalized = _normalized_label(label)
        if not label or normalized not in right_labels or normalized in seen:
            continue
        seen.add(normalized)
        labels.append(label)
    return labels


def _is_single_shared_metric_year_series(
    left_values: list[dict[str, Any]],
    right_values: list[dict[str, Any]],
    shared_labels: list[str],
) -> bool:
    if len(shared_labels) != 1:
        return False
    shared_label = _normalized_label(shared_labels[0])
    return all(
        _is_year_series(values)
        and all(_normalized_label(value.get("label")) == shared_label for value in values)
        for values in (left_values, right_values)
    )


def _should_split_mixed_unit_metric_labels(labels: list[str]) -> bool:
    if len(labels) < 2:
        return False
    has_relative_label = any(_is_relative_metric_label(label) for label in labels)
    has_absolute_label = any(not _is_relative_metric_label(label) for label in labels)
    return has_relative_label and has_absolute_label


def _is_rate_metric_label(label: Any) -> bool:
    return bool(
        re.search(
            r"\bper\s+(?:\d+|capita|person|people|inhabitants?|population)\b",
            str(label or ""),
            re.IGNORECASE,
        )
    )


def _is_relative_metric_label(label: Any) -> bool:
    text = str(label or "").strip().lower()
    if _is_rate_metric_label(text):
        return True
    return bool(re.search(r"\b(?:percent|percentage|share|rate)\b|%", text))


def _first_value_for_label(
    values: list[dict[str, Any]],
    label: str,
) -> dict[str, Any] | None:
    normalized = _normalized_label(label)
    for value in values:
        if _normalized_label(value.get("label")) == normalized:
            return dict(value)
    return None


def _visual_side_with_single_value(
    side: dict[str, Any],
    value: dict[str, Any],
) -> dict[str, Any]:
    return _visual_side_with_values(side, [value])


def _visual_side_with_values(
    side: dict[str, Any],
    values: list[dict[str, Any]],
) -> dict[str, Any]:
    split_side = dict(side)
    split_side["values"] = [dict(value) for value in values]
    return split_side


def _row_sort_key(index: int, row: dict[str, Any]) -> tuple[Any, ...]:
    return (
        _visual_rank_bucket(row),
        -_weighted_score(row),
        str(row.get("label") or row.get("id") or ""),
        index,
    )


def _deduplicate_ranked_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    deduplicated = []
    seen_labels = set()
    for row in rows:
        label_key = _normalized_label(row.get("label"))
        if label_key and label_key in seen_labels:
            continue
        if label_key:
            seen_labels.add(label_key)
        deduplicated.append(row)
    return deduplicated


def _extract_labeled_percentage_series(text: str) -> list[NumericValue]:
    matches = [
        match
        for match in NUMBER_RE.finditer(text)
        if (match.group(2) or "").lower() in {"%", "percent"}
        and not re.match(r"\s*:", text[match.end():])
        and not _is_percentage_bucket_context_number(text, match)
    ]
    if len(matches) < 2:
        return []

    values: list[NumericValue] = []
    previous_end = 0
    all_years = [int(match.group(1)) for match in YEAR_RE.finditer(text)]
    for index, match in enumerate(matches):
        next_match_start = matches[index + 1].start() if index + 1 < len(matches) else len(text)
        label = _percentage_series_label(text, previous_end, match.start())
        previous_end = match.end()
        if not label:
            return []
        number = _parse_number(match.group(1))
        if number is None:
            return []
        item: NumericValue = {"value": number, "label": label}
        year_match = YEAR_RE.search(text[match.end():next_match_start])
        if year_match:
            item["year"] = int(year_match.group(1))
        elif len(all_years) == 1:
            item["year"] = all_years[0]
        values.append(item)
    return values


def _is_percentage_bucket_context_number(text: str, match: re.Match) -> bool:
    number = _parse_number(match.group(1))
    if number is None:
        return False
    prefix = text[max(0, match.start() - 32):match.start()]
    suffix = text[match.end():match.end() + 24]
    if number == 10 and re.search(r"\b(?:lowest|highest)\s*$", prefix, re.IGNORECASE):
        return True
    if number == 10 and re.match(r"\s+of\s+population\b", suffix, re.IGNORECASE):
        return True
    return False


def _percentage_series_label(text: str, previous_end: int, match_start: int) -> str | None:
    prefix = text[max(0, previous_end):match_start]
    colon_label_match = re.search(r"([A-Za-z][A-Za-z0-9 /&%-]{0,54}):\s*$", prefix)
    if colon_label_match:
        return _clean_series_label(colon_label_match.group(1))

    boundary = max(
        prefix.rfind(separator)
        for separator in (")", ";", ".", "\n")
    )
    candidate = prefix[boundary + 1:]
    if ":" in candidate:
        candidate = candidate.rsplit(":", 1)[-1]
    candidate = re.sub(r"\([^)]*\)", " ", candidate)
    return _clean_series_label(candidate)


def _extract_total_colon_value(text: str) -> list[NumericValue]:
    match = re.search(
        rf"\btotal\s*:\s*[$€£¥]?\s*([-+]?(?:\d{{1,3}}(?:,\d{{3}})+|\d+)(?:\.\d+)?)(?:\s*(%|percent|{MAGNITUDE_PATTERN}))?",
        text,
        re.IGNORECASE,
    )
    if not match:
        return []
    number = _parse_number(match.group(1))
    if number is None:
        return []
    item: NumericValue = {"value": _scale_number(number, (match.group(2) or "").lower()), "label": "total"}
    year_match = YEAR_RE.search(text[match.end():match.end() + 80])
    if year_match:
        item["year"] = int(year_match.group(1))
    return [item]


def _extract_dash_labeled_value_series(text: str) -> list[NumericValue]:
    values: list[NumericValue] = []
    for match in re.finditer(
        rf"([^;:\n]+?)\s+-\s*([-+]?(?:\d{{1,3}}(?:,\d{{3}})+|\d+)(?:\.\d+)?)(?:\s*(%|percent|{MAGNITUDE_PATTERN}|km|m|sq km))?",
        text,
        re.IGNORECASE,
    ):
        label_text = re.sub(r"\([^)]*\)", " ", match.group(1))
        if ":" in label_text:
            label_text = label_text.rsplit(":", 1)[-1]
        label = _clean_series_label(label_text)
        number = _parse_number(match.group(2))
        if not label or number is None:
            continue
        unit = (match.group(3) or "").lower()
        values.append({"value": _scale_number(number, unit), "label": label})
    if len(values) >= 2:
        return values
    if values and re.search(r"\bmajor lakes?\b", text, re.IGNORECASE):
        return values
    return []


def _extract_leading_value_labeled_series(text: str) -> list[NumericValue]:
    if not re.search(r"\bmajor urban areas\b|\bpopulation\b", text, re.IGNORECASE):
        return []
    years = [int(match.group(1)) for match in YEAR_RE.finditer(text)]
    values: list[NumericValue] = []
    for match in re.finditer(
        rf"(?<![\w.])([-+]?(?:\d{{1,3}}(?:,\d{{3}})+|\d+)(?:\.\d+)?)\s+({MAGNITUDE_PATTERN})\s+([^,;()]+)",
        text,
        re.IGNORECASE,
    ):
        number = _parse_number(match.group(1))
        label = _clean_series_label(match.group(3))
        if number is None or not label:
            continue
        item: NumericValue = {
            "value": _scale_number(number, (match.group(2) or "").lower()),
            "label": label,
        }
        if len(years) == 1:
            item["year"] = years[0]
        values.append(item)
    return values if len(values) >= 2 else []


def _extract_ports_value_series(text: str) -> list[NumericValue]:
    if not re.search(r"^\s*ports\s*:", text, re.IGNORECASE):
        return []
    years = [int(match.group(1)) for match in YEAR_RE.finditer(text)]
    label_pattern = (
        "ports with oil terminals|total ports|very small|size unknown|large|medium|small"
    )
    values: list[NumericValue] = []
    for match in re.finditer(
        rf"\b({label_pattern})\s+([-+]?(?:\d{{1,3}}(?:,\d{{3}})+|\d+)(?:\.\d+)?)\b",
        text,
        re.IGNORECASE,
    ):
        label = _clean_series_label(match.group(1))
        number = _parse_number(match.group(2))
        if not label or number is None:
            continue
        item: NumericValue = {"value": number, "label": label}
        if len(years) == 1:
            item["year"] = years[0]
        values.append(item)
    return values if len(values) >= 2 else []


def _extract_elevation_value_series(text: str) -> list[NumericValue]:
    if not re.search(r"^\s*elevation\s*:", text, re.IGNORECASE):
        return []
    values: list[NumericValue] = []
    for label in ("highest point", "lowest point", "mean elevation"):
        match = re.search(
            rf"\b{re.escape(label)}\s*:\s*.*?([-+]?(?:\d{{1,3}}(?:,\d{{3}})+|\d+)(?:\.\d+)?)\s*m\b",
            text,
            re.IGNORECASE,
        )
        if not match:
            continue
        number = _parse_number(match.group(1))
        if number is None:
            continue
        values.append({"value": number, "label": label})
    return values if len(values) >= 2 else []


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


def _extract_age_range_labeled_value_series(text: str) -> list[NumericValue]:
    matches = list(AGE_RANGE_COLON_VALUE_RE.finditer(text))
    if len(matches) < 2:
        return []
    years = [int(match.group(1)) for match in YEAR_RE.finditer(text)]
    values: list[NumericValue] = []
    for index, match in enumerate(matches):
        label = _clean_series_label(match.group(1))
        number = _parse_number(match.group(2))
        if not label or number is None:
            continue
        item: NumericValue = {
            "value": _scale_number(number, (match.group(3) or "").lower()),
            "label": label,
        }
        next_start = matches[index + 1].start() if index + 1 < len(matches) else len(text)
        segment_years = [
            int(year_match.group(1))
            for year_match in YEAR_RE.finditer(text[match.end():next_start])
        ]
        if segment_years:
            item["year"] = segment_years[-1]
        elif len(years) == 1:
            item["year"] = years[0]
        values.append(item)
    return values if len(values) >= 2 else []


def _extract_chained_colon_labeled_value_series(text: str) -> list[NumericValue]:
    matches = list(CHAINED_COLON_VALUE_RE.finditer(text))
    if len(matches) < 2:
        return []
    years = [int(match.group(1)) for match in YEAR_RE.finditer(text)]
    values: list[NumericValue] = []
    for index, match in enumerate(matches):
        label = _clean_series_label(match.group(1))
        if not label:
            continue
        raw_number = match.group(2)
        if _is_year_token(raw_number) or _is_date_number(text, match):
            continue
        number = _parse_number(raw_number)
        if number is None:
            continue
        unit = (match.group(3) or "").lower()
        item: NumericValue = {
            "value": _scale_number(number, unit),
            "label": label,
        }
        next_start = matches[index + 1].start() if index + 1 < len(matches) else len(text)
        segment_years = [int(year_match.group(1)) for year_match in YEAR_RE.finditer(text[match.end():next_start])]
        if segment_years:
            item["year"] = segment_years[-1]
        elif len(years) == 1:
            item["year"] = years[0]
        values.append(item)
    return values if len(values) >= 2 else []


def _extract_colon_metric_year_value_series(text: str) -> list[NumericValue]:
    values: list[NumericValue] = []
    for match in COLON_METRIC_YEAR_VALUE_RE.finditer(text):
        label = _clean_metric_label(match.group(1))
        if not label:
            continue
        unit = (match.group(4) or "").lower()
        number = _parse_number(match.group(3))
        if number is None:
            continue
        if match.group(2) == "-" and number > 0:
            number = -number
        values.append(
            {
                "value": _scale_number(number, unit),
                "year": int(match.group(5)),
                "label": label,
            }
        )
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
    matches = list(SIGNED_PAREN_YEAR_VALUE_RE.finditer(text))
    currency_labels = _currency_labels_in_text(text, matches)
    use_currency_labels = len(currency_labels) >= 2
    for index, match in enumerate(matches):
        unit = (match.group(3) or "").lower()
        if _is_signed_rate_denominator_token(text, match, match.group(2)):
            continue
        if _is_secondary_gdp_share(text, match, unit):
            continue
        if _is_secondary_magnitude_count(text, match, unit):
            continue
        number = _parse_number(match.group(2))
        if number is None:
            continue
        if match.group(1) == "-" and number > 0:
            number = -number
        item: NumericValue = {
            "value": _scale_number(number, unit),
            "year": int(match.group(5)),
        }
        label = _label_for_match(
            text,
            match,
            parenthetical_context=match.group(4),
            use_currency_labels=use_currency_labels,
            next_match_start=matches[index + 1].start() if index + 1 < len(matches) else len(text),
        )
        if label:
            item["label"] = label
        values.append(item)
    return values


def _is_signed_rate_denominator_token(text: str, match: re.Match, raw_number: str) -> bool:
    if raw_number.replace(",", "") not in {"100", "1000", "100000"}:
        return False
    start, _end = match.span(2)
    prefix = text[:start].lower()
    return bool(re.search(r"(?:/|\bper\s+)$", prefix))


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
        if _is_rate_denominator_token(text, match):
            continue
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
    matches = list(NUMBER_RE.finditer(text))
    non_year_matches = [
        match for match in matches if not _is_year_token(match.group(1))
    ]
    for index, match in enumerate(non_year_matches):
        if _is_year_token(match.group(1)):
            continue
        unit = (match.group(2) or "").lower()
        if unit not in {"%", "percent"}:
            continue
        if not GDP_SHARE_AFTER_RE.search(text[match.end():]):
            continue
        number = _parse_number(match.group(1))
        if number is None:
            continue
        item: NumericValue = {"value": number}
        previous_end = non_year_matches[index - 1].end() if index > 0 else 0
        next_start = non_year_matches[index + 1].start() if index + 1 < len(non_year_matches) else len(text)
        year = _nearest_year_for_metric_value(text, match, previous_end, next_start)
        if year is not None:
            item["year"] = year
        item["label"] = "% of GDP"
        values.append(item)
    return values


def _extract_contextual_gdp_share_year_values(text: str) -> list[NumericValue]:
    if not re.search(r"\(\s*%\s+of\s+GDP\s*\)|%\s+of\s+GDP|percent\s+of\s+GDP", text, re.IGNORECASE):
        return []
    matches = [
        match for match in NUMBER_RE.finditer(text)
        if not _is_year_token(match.group(1))
    ]
    values: list[NumericValue] = []
    for index, match in enumerate(matches):
        unit = (match.group(2) or "").lower()
        if unit in MAGNITUDES:
            continue
        number = _parse_number(match.group(1))
        if number is None:
            continue
        previous_end = matches[index - 1].end() if index > 0 else 0
        next_start = matches[index + 1].start() if index + 1 < len(matches) else len(text)
        year = _nearest_year_for_metric_value(text, match, previous_end, next_start)
        if year is None:
            continue
        values.append({
            "value": number,
            "year": year,
            "label": "% of GDP",
        })
    return values if len(values) >= 2 else []


def _nearest_year_for_metric_value(
    text: str,
    match: re.Match,
    previous_value_end: int,
    next_value_start: int,
) -> int | None:
    suffix_segment = text[match.end():next_value_start]
    suffix_before_next_item = re.split(r";", suffix_segment, maxsplit=1)[0]
    suffix_years = [
        int(year_match.group(1))
        for year_match in YEAR_RE.finditer(suffix_before_next_item)
    ]
    if suffix_years:
        return suffix_years[0]

    prefix_segment = text[previous_value_end:match.start()]
    prefix_years = [
        int(year_match.group(1))
        for year_match in YEAR_RE.finditer(prefix_segment)
    ]
    if prefix_years:
        return prefix_years[-1]

    return None


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
    return [match.span() for match in SIGNED_PAREN_YEAR_VALUE_RE.finditer(text)]


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


def _is_embedded_number_token(text: str, match: re.Match) -> bool:
    start, end = match.span(1)
    before = text[start - 1] if start > 0 else ""
    before_before = text[start - 2] if start > 1 else ""
    after = text[end] if end < len(text) else ""
    after_after = text[end + 1] if end + 1 < len(text) else ""
    if before.isalpha() or after.isalpha():
        return True
    if before in {"-", "_"} and before_before.isalpha():
        return True
    if after in {"-", "_"} and after_after.isalpha():
        return True
    return False


def _is_rate_denominator_token(text: str, match: re.Match) -> bool:
    raw_number = match.group(1)
    if raw_number.replace(",", "") not in {"100", "1000", "100000"}:
        return False
    start, _end = match.span(1)
    prefix = text[:start].lower()
    return bool(re.search(r"(?:/|\bper\s+)$", prefix))


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
    contextual_label = _contextual_measurement_label(text, match)
    if contextual_label:
        return contextual_label
    suffix_label = _suffix_label(text, match.end(), next_match_start or len(text))
    if suffix_label:
        return suffix_label
    return None


def _contextual_measurement_label(text: str, match: re.Match) -> str | None:
    prefix = text[max(0, match.start() - 90):match.start()]
    suffix = text[match.end():match.end() + 90]
    context = f"{prefix} {suffix}"
    if re.search(r"\bsales\b", prefix, re.IGNORECASE) and re.match(
        r"\s*(?:units?|vehicles?|cars?|registrations?)\b",
        suffix,
        re.IGNORECASE,
    ):
        return "sales"
    if re.search(r"\bmarket share\b", context, re.IGNORECASE):
        return "market share"
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


def _clean_metric_label(raw_label: str | None) -> str | None:
    label = re.sub(r"\s+", " ", str(raw_label or "").strip(" :;,.()-"))
    if not label:
        return None
    lower = label.lower()
    if lower in {"est", "estimate", "estimated", "forecast", "f", "proj", "projected", "monthly", "annual"}:
        return None
    if YEAR_RE.fullmatch(label.strip()) or MONTH_RE.search(label):
        return None
    if re.search(r"\d", label) and not re.search(r"\bper\s+\d+\b", label, re.IGNORECASE):
        return None
    if len(label) > 60:
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


def _is_compact_year_suffix_token(text: str, match: re.Match) -> bool:
    raw_number = match.group(1).replace(",", "")
    if not re.fullmatch(r"\d{2}", raw_number):
        return False
    start, _end = match.span(1)
    prefix = text[max(0, start - 8):start]
    return bool(re.search(r"\b(?:18|19|20|21)\d{2}\s*/\s*$", prefix))


def _is_age_context_number(text: str, match: re.Match) -> bool:
    raw_number = match.group(1).replace(",", "")
    if not re.fullmatch(r"\d{1,3}", raw_number):
        return False
    prefix = text[max(0, match.start() - 32):match.start()]
    suffix = text[match.end():match.end() + 32]
    return bool(
        re.search(r"\bages?\s*$", prefix, re.IGNORECASE)
        and re.match(r"\s*(?:or\s+older|and\s+over|to|-|–|—)", suffix, re.IGNORECASE)
        or re.search(r"\bunder\s+the\s+age\s+of\s*$", prefix, re.IGNORECASE)
        and re.match(r"\s*years?\b", suffix, re.IGNORECASE)
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
    if _is_sales_unit_count(text, match):
        return False
    return "%" in text or re.search(r"\bpercent\b", text, re.IGNORECASE)


def _is_sales_unit_count(text: str, match: re.Match) -> bool:
    prefix = text[max(0, match.start() - 90):match.start()]
    suffix = text[match.end():match.end() + 32]
    return bool(
        re.search(r"\bsales\b", prefix, re.IGNORECASE)
        and re.match(r"\s*(?:units?|vehicles?|cars?|registrations?)\b", suffix, re.IGNORECASE)
    )


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


def _chart_type_for_values(
    data_type: str,
    point_count: int,
    left_values: list[NumericValue],
    right_values: list[NumericValue],
    row_label: str = "",
    left_text: str = "",
    right_text: str = "",
) -> str:
    if data_type == "Proportional":
        if (
            _is_part_whole_percentage_pair(left_values, right_values)
            and not _is_non_exhaustive_share_context(row_label, left_text, right_text, left_values, right_values)
        ):
            side_count = max(len(left_values), len(right_values))
            return "pie" if side_count <= 4 else "stacked"
        return "line" if _is_year_series(left_values) or _is_year_series(right_values) else "bar"
    return choose_chart_type(data_type, point_count)


def _is_year_series(values: list[NumericValue]) -> bool:
    years = {
        int(value["year"])
        for value in values
        if value.get("year") is not None
    }
    return len(values) >= 2 and len(years) >= 2


def _is_part_whole_percentage_pair(
    left_values: list[NumericValue],
    right_values: list[NumericValue],
) -> bool:
    sides = [values for values in (left_values, right_values) if values]
    return bool(sides) and all(_is_part_whole_percentage_values(values) for values in sides)


def _is_part_whole_percentage_values(values: list[NumericValue]) -> bool:
    if len(values) < 2 or _is_year_series(values):
        return False
    labels = [
        _normalized_label(value.get("label"))
        for value in values
        if value.get("label")
    ]
    if len(set(labels)) < 2:
        return False
    numbers = []
    for value in values:
        try:
            number = float(value.get("value"))
        except (TypeError, ValueError):
            return False
        if not math.isfinite(number) or number < 0 or number > 100:
            return False
        numbers.append(number)
    total = sum(numbers)
    return 95 <= total <= 105


def _is_non_exhaustive_share_context(
    row_label: str,
    left_text: str,
    right_text: str,
    left_values: list[NumericValue],
    right_values: list[NumericValue],
) -> bool:
    context = f"{row_label} {left_text} {right_text}".lower()
    if not re.search(r"\bpartners?\b", context):
        return False
    labels = {
        _normalized_label(value.get("label"))
        for value in left_values + right_values
        if value.get("label")
    }
    return not any(label in {"other", "others", "remaining", "rest"} for label in labels)


def _source_kind(left_source: str | None, right_source: str | None) -> str:
    sources = {str(source or "").lower() for source in (left_source, right_source)}
    if "infobox" in sources and "main_text" in sources:
        return "Both"
    if "infobox" in sources:
        return "Infobox"
    if sources == {"main_text"}:
        return "main_text"
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
    if _is_data_priority_main_text_row(row):
        return 0
    return 0 if _is_chartable_row(row) else 1


def _is_data_priority_main_text_row(row: dict[str, Any]) -> bool:
    if not row.get("dataPriority") or row.get("sourceKind") != "main_text" or not row.get("dataRole"):
        return False
    if _is_temporal_metadata_role(row.get("dataRole")):
        return False
    visualization = row.get("visualization") if isinstance(row.get("visualization"), dict) else {}
    left = visualization.get("left") if isinstance(visualization.get("left"), dict) else {}
    right = visualization.get("right") if isinstance(visualization.get("right"), dict) else {}
    return bool(left.get("values") and right.get("values"))


def _is_demoted_main_text_visual_data_row(row: dict[str, Any]) -> bool:
    if row.get("sourceKind") != "main_text" or not row.get("dataPriority"):
        return False
    if not _is_visual_data_role_name(row.get("dataRole")):
        return False
    if _is_chartable_row(row):
        return False
    visualization = row.get("visualization") if isinstance(row.get("visualization"), dict) else {}
    left = visualization.get("left") if isinstance(visualization.get("left"), dict) else {}
    right = visualization.get("right") if isinstance(visualization.get("right"), dict) else {}
    return not (left.get("values") and right.get("values"))


def _is_temporal_metadata_text_row(row: dict[str, Any]) -> bool:
    if _is_chartable_row(row):
        return False
    return _is_temporal_metadata_label(_normalized_label(row.get("label")))


def _is_chartable_row(row: dict[str, Any]) -> bool:
    chart_type = str(row.get("chartType") or "").strip().lower()
    if chart_type:
        return chart_type != "text"
    return row.get("dataType") in {"Trend", "Numerical", "Proportional"}


def _is_temporal_metadata_role(data_role: Any) -> bool:
    return str(data_role or "").strip().lower() == "emergence_time"


def _is_temporal_metadata_attribute(
    row_label: Any,
    left_attr: dict[str, Any],
    right_attr: dict[str, Any],
) -> bool:
    labels = {
        _normalized_label(row_label),
        _normalized_label(left_attr.get("key")),
        _normalized_label(right_attr.get("key")),
    }
    return any(_is_temporal_metadata_label(label) for label in labels)


def _is_text_metadata_attribute(
    row_label: Any,
    left_attr: dict[str, Any],
    right_attr: dict[str, Any],
) -> bool:
    labels = {
        _normalized_label(row_label),
        _normalized_label(left_attr.get("key")),
        _normalized_label(right_attr.get("key")),
    }
    return bool(TEXT_METADATA_KEYS.intersection(labels))


def _is_temporal_metadata_label(label: str) -> bool:
    if not label:
        return False
    if label in TEMPORAL_METADATA_KEYS:
        return True
    tokens = set(re.findall(r"[a-z0-9]+", label))
    if "date" in tokens:
        return True
    if "first" in tokens and tokens.intersection(TEMPORAL_METADATA_TERMS):
        return True
    return False


def _is_generic_main_text_pair(
    left_attr: dict[str, Any],
    right_attr: dict[str, Any],
    data_role: Any,
) -> bool:
    if data_role:
        return False
    return (
        str(left_attr.get("source") or "").lower() == "main_text"
        and str(right_attr.get("source") or "").lower() == "main_text"
        and not left_attr.get("dataPriority")
        and not right_attr.get("dataPriority")
    )


def _is_incomplete_main_text_data_pair(
    left_attr: dict[str, Any],
    right_attr: dict[str, Any],
    data_role: Any,
    left_values: list[dict[str, Any]],
    right_values: list[dict[str, Any]],
) -> bool:
    if not data_role or not _is_visual_data_role_name(data_role):
        return False
    if not (
        str(left_attr.get("source") or "").lower() == "main_text"
        and str(right_attr.get("source") or "").lower() == "main_text"
    ):
        return False
    return not (left_values and right_values)


def _has_incompatible_single_point_main_text_years(
    left_attr: dict[str, Any],
    right_attr: dict[str, Any],
    data_role: Any,
    left_values: list[dict[str, Any]],
    right_values: list[dict[str, Any]],
) -> bool:
    if not data_role or not _is_visual_data_role_name(data_role):
        return False
    if not (
        str(left_attr.get("source") or "").lower() == "main_text"
        and str(right_attr.get("source") or "").lower() == "main_text"
    ):
        return False
    if len(left_values) != 1 or len(right_values) != 1:
        return False
    left_year = left_values[0].get("year")
    right_year = right_values[0].get("year")
    if left_year is None and right_year is None:
        return False
    return left_year != right_year


def _is_visual_data_role_name(data_role: Any) -> bool:
    return str(data_role or "").strip().lower() in {"proportion", "ranking", "scale", "quantity"}


def _has_explicit_main_text_visual_signal(
    left_type: str,
    right_type: str,
    left_values: list[dict[str, Any]],
    right_values: list[dict[str, Any]],
) -> bool:
    if left_type == "Trend" and right_type == "Trend":
        return True
    return bool(_shared_labeled_value_pairs(left_values, right_values))
