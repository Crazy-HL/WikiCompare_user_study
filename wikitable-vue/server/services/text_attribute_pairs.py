from __future__ import annotations

import math
import re
from typing import Any


MEASUREMENT_TERMS = (
	"algorithms|capacity|cases|deaths|employees|features|hospitalizations|members|models|participants|population|"
	"recovered|samples|sales|tests|users|revenue|accuracy"
)
MEASUREMENT_DESCRIPTORS = "active|confirmed|monthly|new|total|trained"
KNOWN_DATA_ROLES = {"emergence_time", "proportion", "ranking", "scale", "quantity"}
STRICT_CUE_ROLES = {"proportion", "scale", "quantity"}
ROLE_LABELS = {
    "emergence_time": "Historical emergence",
    "proportion": "Proportion / rate",
    "ranking": "Ranking",
    "scale": "Scale",
    "quantity": "Quantity",
}
ROLE_QUESTIONS = {
    "emergence_time": "When did it emerge or become established?",
    "proportion": "What proportion, rate, or percentage is reported?",
    "ranking": "What rank or index score is reported?",
    "scale": "What scale or monetary value is reported?",
    "quantity": "What quantity is reported?",
}
FINANCIAL_MEASUREMENT_LABELS = {
    "Revenue",
    "Operating income",
    "Net income",
    "Diluted earnings per share",
    "Microsoft Cloud revenue",
}
INFOBOX_KEY_SYNONYMS = {
    "founded": "foundation",
    "founding": "foundation",
    "foundation": "foundation",
}
NUMBER_RE = re.compile(
    r"([-+]?(?:\d{1,3}(?:,\d{3})+|\d+)(?:\.\d+)?)\s*(%|percent|million|billion|trillion)?",
    re.I,
)
VALUE_MAGNITUDES = {
    "million": 1_000_000,
    "billion": 1_000_000_000,
    "trillion": 1_000_000_000_000,
}
MONEY_RE = re.compile(r"[-+]?\s*[$€£¥₩]\s*[-+]?(?:\d{1,3}(?:,\d{3})+|\d+)(?:\.\d+)?", re.I)
ORDINAL_RE = re.compile(r"\b\d+(?:st|nd|rd|th)\b", re.I)
DATA_CONTEXT_RE = re.compile(
	r"\b(founded|introduced|launched|released|created|developed|grew|emerged|"
	r"accuracy|rate|share|percent|rank|ranked|ranking|placed|score|revenue|sales|population|users|models|cases|"
	r"gdp|economy|economic|poverty|inflation|employment|enrollment|electricity|coverage|growth|decline|increase|decrease|duration)\b",
	re.I,
)
CLAIM_CUE_RE = re.compile(
    r"\b(is|are|refers to|used|uses|include|includes|applications|methods|"
    r"techniques|consists|types|risks|limitations|impact|effects)\b",
    re.I,
)
PUBLICATION_NOISE_RE = re.compile(
    r"\b(study|paper|article|journal|conference|published|conducted)\b",
    re.I,
)
PUBLICATION_YEAR_PREFIX_RE = re.compile(
    r"(\b(study|paper|article|journal|conference)(\s+(published|conducted))?\s+(in|from)|"
    r"\b(published|conducted)(\s+\w+){0,3}\s+in)\s*$",
    re.I,
)
PUBLICATION_YEAR_SUFFIX_RE = re.compile(
    r"^\s*,?\s*(the\s+)?(?:\w+\s+){0,3}(study|paper|article|journal|conference)\b",
    re.I,
)
EMERGENCE_CONTEXT_RE = re.compile(
    r"\b(founded|introduced|launched|released|created|developed|grew|emerged)\b",
    re.I,
)
ENTITY_EMERGENCE_SUFFIX_RE = re.compile(
    r"^\s*,?\s*(?:the\s+)?(?:\w+\s+){0,3}"
    r"(?:journal|conference|field|company|service|system|model)\s+"
    r"(?:was\s+|were\s+)?(?:founded|introduced|launched|released|created|developed|emerged)\b",
    re.I,
)
PROPORTION_PREFIX_RE = re.compile(
    r"\b(accuracy|share|rate|percent)(?:\s+score)?\s+(?:of\s+)?$|\bscore\s+(?:of\s+)?$",
    re.I,
)
PROPORTION_SUFFIX_RE = re.compile(r"^\s*(accuracy|score|share|rate|percent)\b", re.I)
MEASUREMENT_CONTEXT_RE = re.compile(rf"\b({MEASUREMENT_TERMS})\b", re.I)
DIRECT_MEASUREMENT_CONTEXT_RE = re.compile(
    rf"^\s*(?:({MEASUREMENT_DESCRIPTORS})\s+){{0,3}}({MEASUREMENT_TERMS})\b",
    re.I,
)
RANKING_PREFIX_RE = re.compile(r"\b(rank|ranked|ranking|placed)\s+$", re.I)
RANKING_SUFFIX_CONTEXT_RE = re.compile(r"^\s*(?:st|nd|rd|th)\b\s*(?:overall|place|rank|ranking)\b", re.I)
ORDINAL_RANKING_SUFFIX_RE = re.compile(r"^\s*(?:st|nd|rd|th)\b", re.I)
CARDINAL_RANKING_SUFFIX_RE = re.compile(
    r"^\s*(?:$|[.,;:!?)]|among\b|in\b|of\b|out\s+of\b|overall\b|place\b|rank\b|ranking\b)",
    re.I,
)
PLACED_CARDINAL_RANKING_SUFFIX_RE = re.compile(
    r"^\s*(?:$|[.,;:!?)]|among\b|overall\b|place\b|rank\b|ranking\b|"
    r"of\b|out\s+of\b|"
    r"in\s+(?:the\s+)?(?:contest|competition|race|ranking|rankings|standings|overall|place)\b)",
    re.I,
)
RANKING_DENOMINATOR_PREFIX_RE = re.compile(
    r"\b(?:rank|ranked|ranking|placed)\s+#?"
    r"[-+]?(?:\d{1,3}(?:,\d{3})+|\d+)(?:\.\d+)?(?:st|nd|rd|th)?\s+"
    r"(?:out\s+of|of)\s+$",
    re.I,
)
LEADING_TEMPORAL_PREFIX_RE = re.compile(r"^\s*in\s+$", re.I)
CURRENCY_SYMBOL_RE = re.compile(r"[$€£¥₩]\s*$")
SCALE_UNITS = {"million", "billion", "trillion"}
CAPACITY_UNIT_RE = re.compile(r"\b(?:gw|mw|kw|gigawatts?|megawatts?|kilowatts?)\b", re.I)
MONTH_NAME_RE = re.compile(
	r"\b(?:January|February|March|April|May|June|July|August|September|October|November|December)\b",
	re.I,
)
NUMBER_WORDS = {
    "one": "1",
    "two": "2",
    "three": "3",
    "four": "4",
    "five": "5",
    "six": "6",
    "seven": "7",
    "eight": "8",
    "nine": "9",
    "ten": "10",
}


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
    return _sample_candidates_with_document_coverage(candidates, limit)


def _sample_candidates_with_document_coverage(candidates: list[dict[str, Any]], limit: int) -> list[dict[str, Any]]:
    if limit <= 0:
        return []
    if len(candidates) <= limit:
        return candidates
    if limit == 1:
        return [candidates[0]]

    head_count = max(1, limit // 2)
    selected_indices = set(range(head_count))
    remaining_slots = limit - len(selected_indices)
    if remaining_slots > 0:
        tail_start = head_count
        tail_count = len(candidates) - tail_start
        if tail_count <= remaining_slots:
            selected_indices.update(range(tail_start, len(candidates)))
        elif remaining_slots == 1:
            selected_indices.add(len(candidates) - 1)
        else:
            last_tail_index = tail_count - 1
            selected_indices.update(
                tail_start + round(position * last_tail_index / (remaining_slots - 1))
                for position in range(remaining_slots)
            )
    return [
        candidates[index]
        for index in sorted(selected_indices)[:limit]
    ]


def build_paired_text_attributes(
    left_article: dict[str, Any],
    right_article: dict[str, Any],
    pair_response: Any,
    left_infobox_pool: list[dict[str, Any]],
    right_infobox_pool: list[dict[str, Any]],
    *,
    require_extracted_values_for_visual: bool = False,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    pairs = pair_response.get("pairs") if isinstance(pair_response, dict) else pair_response
    if not isinstance(pairs, list):
        return [], [], []
    left_sources = _source_lookup(left_article)
    right_sources = _source_lookup(right_article)
    left_attrs: list[dict[str, Any]] = []
    right_attrs: list[dict[str, Any]] = []
    alignments: list[dict[str, Any]] = []
    seen_pairs: set[tuple[Any, ...]] = set()
    seen_dimensions: set[tuple[str, str]] = set()
    for raw_pair in pairs:
        clean_pair = _validated_pair(
            raw_pair,
            left_sources,
            right_sources,
            require_extracted_values_for_visual=require_extracted_values_for_visual,
        )
        if clean_pair is None:
            continue
        dimension_key = _dimension_dedupe_key(clean_pair)
        if clean_pair.get("_dedupeDimension") and dimension_key in seen_dimensions:
            continue
        pair_key = _pair_dedupe_key(clean_pair)
        if pair_key in seen_pairs:
            continue
        if _duplicates_infobox(clean_pair, left_infobox_pool, right_infobox_pool):
            continue
        seen_pairs.add(pair_key)
        if clean_pair.get("_dedupeDimension"):
            seen_dimensions.add(dimension_key)
        index = len(left_attrs) + 1
        left_attr = _attribute_from_pair_side(clean_pair, "left", index, left_sources)
        right_attr = _attribute_from_pair_side(clean_pair, "right", index, right_sources)
        left_attrs.append(left_attr)
        right_attrs.append(right_attr)
        alignments.append({"left": left_attr, "right": right_attr, "label": clean_pair["dimensionLabel"]})
    return left_attrs, right_attrs, alignments


def build_rule_paired_text_attributes(
    left_article: dict[str, Any],
    right_article: dict[str, Any],
    left_infobox_pool: list[dict[str, Any]],
    right_infobox_pool: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    left_candidates = _expanded_data_candidates(left_article, "left")
    right_candidates = _expanded_data_candidates(right_article, "right")
    pairs: list[dict[str, Any]] = []
    used_right: set[int] = set()
    used_dimensions: set[str] = set()
    for left_candidate in left_candidates:
        left_role = _primary_role(left_candidate)
        if not left_role:
            continue
        for right_index, right_candidate in enumerate(right_candidates):
            if right_index in used_right:
                continue
            if _primary_role(right_candidate) != left_role:
                continue
            if not _rule_candidates_are_compatible(left_candidate, right_candidate, left_role):
                continue
            label = _dimension_label_for_candidates(left_role, left_candidate, right_candidate)
            dimension_key = _normalized_label(label)
            if dimension_key in used_dimensions:
                continue
            used_right.add(right_index)
            used_dimensions.add(dimension_key)
            pairs.append(_rule_pair(left_candidate, right_candidate, left_role, label))
            break
    return build_paired_text_attributes(
        left_article,
        right_article,
        {"pairs": pairs},
        left_infobox_pool,
        right_infobox_pool,
    )


def _data_candidates(article: dict[str, Any], side: str) -> list[dict[str, Any]]:
    return [
        candidate
        for candidate in build_text_evidence_candidates(article, side, limit=240)
        if candidate.get("kind") == "data"
    ]


def _expanded_data_candidates(article: dict[str, Any], side: str) -> list[dict[str, Any]]:
    expanded: list[dict[str, Any]] = []
    for candidate in _data_candidates(article, side):
        views = _measurement_views(candidate)
        expanded.extend(views or [candidate])
    return expanded


def _measurement_views(candidate: dict[str, Any]) -> list[dict[str, Any]]:
    text = _clean_text(candidate.get("claimText"))
    if not text:
        return []
    if _field_metric_label(text):
        return []
    views = []
    for spec in _measurement_view_specs(text):
        view = dict(candidate)
        view["claimText"] = spec["text"]
        view["dataItems"] = [spec["dataItem"]]
        view["dimensionLabel"] = spec["label"]
        views.append(view)
    return views


def _measurement_view_specs(text: str) -> list[dict[str, Any]]:
    text = _normalize_number_words(text)
    specs: list[dict[str, Any]] = []
    for match in NUMBER_RE.finditer(text):
        unit = (match.group(2) or "").lower()
        if _is_embedded_token_number(text, match) or _is_calendar_day_or_age(text, match) or _is_year_range_suffix(text, match):
            continue
        if _is_year_like_match(match.group(1), unit):
            continue
        role = _data_role(text, unit, match)
        label = _specific_measurement_label(text, match, role)
        if not label:
            continue
        year = _year_for_measurement_label(text, match, label)
        value_text = _specific_measurement_text(text, match, label, year)
        if not value_text:
            continue
        value = _numeric_value(match.group(1), text, match)
        if value is None:
            continue
        data_item: dict[str, Any] = {
            "value": int(value) if value.is_integer() else value,
            "role": _role_for_specific_label(label, role),
        }
        if unit:
            data_item["unit"] = unit
        specs.append({"label": label, "text": value_text, "dataItem": data_item})
    return _deduplicate_measurement_specs(specs)


def _specific_measurement_label(text: str, match: re.Match, role: str) -> str:
    context = _role_context(text, match).lower()
    full_text = text.lower()
    financial_label = _financial_measurement_label(context)
    if financial_label:
        return financial_label
    if "market share" in context or re.search(r"\bshare\b", context) and (match.group(2) or "").lower() in {"%", "percent"}:
        return "Market share"
    if "cumulative sales" in context or ("cumulative sales" in full_text and match.start() >= full_text.find("cumulative sales")):
        return "Cumulative sales"
    if "milestone" in context or "sales mark" in context:
        return "Sales milestone"
    if re.search(r"\bsubsid(?:y|ies)|tax credits?|incentives?\b", context):
        return "Purchase incentive"
    if re.search(r"\bhigh-income\b|annual\s+growth\s+rate|aims?\s+to\s+grow|need\s+to\s+sustain\b", context) and re.search(r"\bgrowth|grow\b", context):
        return "Annual growth target"
    if role == "proportion" and re.search(r"\bpoverty\b", context):
        return "Poverty rate"
    if (
        re.search(r"\b(?:gdp|economy|economic)\b", context)
        and re.search(r"\bgrowth|grew|expand|expanded|expansion\b", context)
    ) or re.search(r"\bgrowth\s+(?:is\s+)?(?:expected|projected|forecast|estimated)\b|\bgrowth\s+should\b", context):
        return "Economic growth"
    if re.search(r"\binflation\b", context):
        return "Inflation"
    if re.search(r"\bhealth\b", context) and re.search(r"\bcoverage|covered|insurance\b", context):
        return "Health coverage"
    if re.search(r"\benrollment|school\b", context):
        return "School enrollment"
    if re.search(r"\belectricity\b", context) and re.search(r"\baccess|households?\b", context):
        return "Electricity access"
    if "production capacity" in context or "annual production capacity" in context:
        return "Production capacity"
    if "sales target" in context or "target" in context and "sales" in context:
        return "Sales target"
    if re.search(r"\bsales?\b|registrations|units sold", context):
        return "Annual sales"
    if "capacity" in context:
        return "Capacity"
    if role == "proportion":
        return "Share / rate"
    return ""


def _financial_measurement_label(context: str) -> str:
    if re.search(r"\bmicrosoft\s+cloud\s+revenue\b", context):
        return "Microsoft Cloud revenue"
    if re.search(r"\bdiluted\s+(?:earnings\s+per\s+share|eps)\b|\bearnings\s+per\s+share\b", context):
        return "Diluted earnings per share"
    if re.search(r"\boperating\s+income\b", context):
        return "Operating income"
    if re.search(r"\bnet\s+income\b", context):
        return "Net income"
    if re.search(r"\brevenue\b", context):
        return "Revenue"
    return ""


def _specific_measurement_text(text: str, match: re.Match, label: str, year: int | None) -> str:
    number_text = match.group(0).strip()
    year_text = f" in {year}" if year is not None else ""
    if label == "Market share":
        return f"market share{year_text} was {number_text}"
    if label == "Annual sales":
        return f"sales{year_text} totaled {number_text} units"
    if label == "Sales milestone":
        return f"sales milestone{year_text} was {number_text} units"
    if label == "Purchase incentive":
        return f"purchase incentive{year_text} was {number_text}"
    if label == "Annual growth target":
        return f"annual growth target was {number_text}"
    if label == "Economic growth":
        return f"economic growth was {number_text}"
    if label == "Poverty rate":
        return f"poverty rate was {number_text}"
    if label == "Inflation":
        return f"inflation was {number_text}"
    if label == "Health coverage":
        return f"health coverage was {number_text}"
    if label == "School enrollment":
        return f"school enrollment was {number_text}"
    if label == "Electricity access":
        return f"electricity access was {number_text}"
    if label == "Sales target":
        return f"sales target{year_text} was {number_text} vehicles"
    if label in {"Production capacity", "Capacity"}:
        return f"{label.lower()}{year_text} was {number_text}"
    if label == "Cumulative sales":
        return f"cumulative sales{year_text} totaled {number_text} units"
    if label in FINANCIAL_MEASUREMENT_LABELS:
        return f"{label.lower()}{year_text} was {number_text}"
    return _role_context(text, match)


def _role_for_specific_label(label: str, fallback_role: str) -> str:
    if label == "Market share":
        return "proportion"
    if label in {"Annual growth target", "Economic growth", "Poverty rate", "Inflation", "Health coverage", "School enrollment", "Electricity access"}:
        return "proportion"
    if label == "Purchase incentive":
        return "scale"
    if label in {"Annual sales", "Sales milestone", "Sales target", "Production capacity", "Capacity", "Cumulative sales"}:
        return "quantity"
    if label in FINANCIAL_MEASUREMENT_LABELS:
        return "scale"
    return fallback_role


def _first_explicit_year(text: str) -> int | None:
    match = re.search(r"\b((?:18|19|20|21)\d{2})\b", text)
    return int(match.group(1)) if match else None


def _first_measurement_year(text: str) -> int | None:
    for match in re.finditer(r"\b((?:18|19|20|21)\d{2})\b", text):
        prefix = text[max(0, match.start() - 16) : match.start()]
        if re.search(r"\b(?:since|from)\s+$", prefix, re.I):
            continue
        return int(match.group(1))
    return None


def _year_for_measurement_label(text: str, match: re.Match, label: str) -> int | None:
    if label in {
        "Annual growth target",
        "Economic growth",
        "Poverty rate",
        "Inflation",
        "Health coverage",
        "School enrollment",
        "Electricity access",
    }:
        return None
    prefix_text = text[max(0, match.start() - 64) : match.start()]
    suffix_text = text[match.end() : min(len(text), match.end() + 64)]
    if label == "Cumulative sales":
        prefix_year = _first_measurement_year(prefix_text)
        if prefix_year is not None:
            return prefix_year
    suffix_year = _first_measurement_year(suffix_text)
    if suffix_year is not None:
        return suffix_year
    prefix_year = _first_measurement_year(prefix_text)
    if prefix_year is not None:
        return prefix_year
    return _first_measurement_year(text)


def _deduplicate_measurement_specs(specs: list[dict[str, Any]]) -> list[dict[str, Any]]:
    deduped = []
    for spec in specs:
        key = _normalized_label(spec.get("label"))
        if not key:
            continue
        if key in {"poverty rate", "economic growth", "inflation"}:
            deduped = [
                existing
                for existing in deduped
                if _normalized_label(existing.get("label")) != key
            ]
        elif any(_normalized_label(existing.get("label")) == key for existing in deduped):
            continue
        deduped.append(spec)
    return deduped


def _rule_pair(
    left_candidate: dict[str, Any],
    right_candidate: dict[str, Any],
    role: str,
    label: str | None = None,
) -> dict[str, Any]:
    dimension_label = label or ROLE_LABELS[role]
    return {
        "dimensionLabel": dimension_label,
        "comparisonQuestion": _comparison_question(role, dimension_label),
        "left": {
            "valueText": left_candidate["claimText"],
            "sentenceIds": left_candidate["sentenceIds"],
        },
        "right": {
            "valueText": right_candidate["claimText"],
            "sentenceIds": right_candidate["sentenceIds"],
        },
        "dataPriority": _is_visual_data_role(role),
        "dataRole": role,
        "confidence": 0.62,
    }


def _primary_role(candidate: dict[str, Any]) -> str:
    data_items = candidate.get("dataItems") or []
    if not data_items:
        return ""
    valid_roles = [
        _clean_text(item.get("role"))
        for item in data_items
        if isinstance(item, dict) and _clean_text(item.get("role")) in ROLE_LABELS
    ]
    if not valid_roles:
        return ""
    role = next((item for item in valid_roles if item != "emergence_time"), valid_roles[0])
    return role if role in ROLE_LABELS else ""


def _rule_candidates_are_compatible(
    left_candidate: dict[str, Any],
    right_candidate: dict[str, Any],
    role: str,
) -> bool:
    if role not in STRICT_CUE_ROLES:
        return True
    left_label = _clean_text(left_candidate.get("dimensionLabel"))
    right_label = _clean_text(right_candidate.get("dimensionLabel"))
    if left_label and right_label and left_label != right_label:
        return False
    if left_label and right_label and left_label == right_label:
        return True
    left_cue = _measurement_cue(left_candidate.get("claimText"))
    right_cue = _measurement_cue(right_candidate.get("claimText"))
    if (left_cue == "share" or right_cue == "share") and (
        left_candidate.get("dimensionLabel") != "Market share"
        or right_candidate.get("dimensionLabel") != "Market share"
    ):
        return False
    if left_cue == "geographic coverage" and (
        _has_monetary_value(left_candidate.get("claimText")) != _has_monetary_value(right_candidate.get("claimText"))
    ):
        return False
    return bool(left_cue and right_cue and left_cue == right_cue)


def _dimension_label_for_candidates(
    role: str,
    left_candidate: dict[str, Any],
    right_candidate: dict[str, Any],
) -> str:
    left_label = _clean_text(left_candidate.get("dimensionLabel"))
    right_label = _clean_text(right_candidate.get("dimensionLabel"))
    if left_label and left_label == right_label:
        return left_label
    return _dimension_label(role, left_candidate.get("claimText"), right_candidate.get("claimText"))


def _measurement_cue(text: Any) -> str:
    normalized = _clean_text(text).lower()
    if CAPACITY_UNIT_RE.search(normalized):
        return "capacity"
    cue_groups = [
        ("accuracy", r"\baccuracy|score\b"),
        ("capacity", r"\bcapacity|installed capacity|generation capacity\b"),
        ("annual growth target", r"\bannual\s+growth\s+(?:rate|target)|high-income|aims?\s+to\s+grow|need\s+to\s+sustain\b"),
        ("poverty rate", r"\bpoverty\b"),
        ("economic growth", r"\bgdp\b|\beconom(?:y|ic)\b.*\b(?:growth|grew|expand|expanded|expansion)\b|\b(?:growth|grew|expand|expanded|expansion)\b.*\beconom(?:y|ic)\b|\bgrowth\s+(?:is\s+)?(?:expected|projected|forecast|estimated)\b|\bgrowth\s+should\b"),
        ("inflation", r"\binflation\b"),
        ("alcohol consumption per capita", r"\balcohol\b.*\b(?:consumption|per capita|liters? of pure alcohol)\b|\bliters? of pure alcohol\b"),
        ("health coverage", r"\bhealth\b.*\b(?:coverage|covered|insurance)\b|\b(?:coverage|covered|insurance)\b.*\bhealth\b"),
        ("school enrollment", r"\benrollment|school\b"),
        ("electricity access", r"\belectricity\b.*\b(?:access|households?)\b|\b(?:access|households?)\b.*\belectricity\b"),
        ("microsoft cloud revenue", r"\bmicrosoft\s+cloud\s+revenue\b"),
        ("diluted earnings per share", r"\bdiluted\s+(?:earnings\s+per\s+share|eps)\b|\bearnings\s+per\s+share\b"),
        ("operating income", r"\boperating\s+income\b"),
        ("net income", r"\bnet\s+income\b"),
        ("purchase incentive", r"\bsubsid(?:y|ies)|tax credits?|incentives?\b"),
        ("sales", r"\bsales|units sold|registrations\b"),
        ("revenue", r"\brevenue|revenues\b"),
        ("population", r"\bpopulation|inhabitants\b"),
        ("users", r"\busers|subscribers|customers\b"),
        ("employees", r"\bemployees|workers|staff\b"),
        ("samples", r"\bsamples|participants\b"),
        ("geographic coverage", r"\bprovinces?|regions?|(?<!united )states?|countries|cities|municipalities\b"),
        ("active cases", r"\bactive cases\b"),
        ("confirmed cases", r"\bconfirmed cases\b"),
        ("hospitalized cases", r"\bhospitali[sz](?:ed|ation|ations)? cases\b|\bhospitali[sz]ations\b"),
        ("recovered", r"\brecovered|recoveries\b"),
        ("deaths", r"\bdeaths|fatalities\b"),
        ("tests", r"\btests|testing\b"),
        ("cases", r"\bcases\b"),
        ("models", r"\bmodels\b"),
        ("features", r"\bfeatures\b"),
        ("growth", r"\bgrowth|grew|increase|decrease|decline\b"),
        ("margin", r"\bmargins?\b"),
        ("share", r"\bshare|rate|percent|percentage\b"),
    ]
    for label, pattern in cue_groups:
        if re.search(pattern, normalized):
            return label
    return ""


def _has_monetary_value(text: Any) -> bool:
    normalized = _clean_text(text)
    return bool(
        MONEY_RE.search(normalized)
        or re.search(r"\b(?:yuan|dollars?|euros?|pounds?|yen)\b", normalized, re.I)
    )


def _measurement_pair_is_compatible(label: str, left_text: Any, right_text: Any, role: str) -> bool:
    normalized_label = _normalized_label(label)
    if (
        normalized_label
        and normalized_label == _normalized_label(_field_metric_label(left_text))
        and normalized_label == _normalized_label(_field_metric_label(right_text))
    ):
        return True
    left_cue = _value_measurement_cue(label, left_text, role)
    right_cue = _value_measurement_cue(label, right_text, role)
    if not left_cue or not right_cue or left_cue != right_cue:
        return False
    if left_cue in {"growth", "economic growth", "annual growth target"}:
        left_years = _explicit_years(left_text)
        right_years = _explicit_years(right_text)
        if bool(left_years) != bool(right_years):
            return False
        if left_years and left_years != right_years:
            return False
    return True


def _value_measurement_cue(label: str, text: Any, role: str) -> str:
    normalized = _clean_text(text)
    cues = [
        _measurement_cue(_role_context(normalized, match))
        for match in NUMBER_RE.finditer(normalized)
        if not _is_embedded_token_number(normalized, match)
    ]
    cues = [cue for cue in cues if cue]
    if cues:
        return cues[0]
    label_cue = _measurement_cue(label)
    if label_cue:
        return label_cue
    if role == "scale" and (
        MONEY_RE.search(normalized)
        or re.search(r"\b(?:million|billion|trillion)\b", normalized, re.I)
    ):
        return "scale"
    return ""


def _explicit_years(text: Any) -> set[int]:
    return {
        int(match.group(1))
        for match in re.finditer(r"\b((?:18|19|20|21)\d{2})\b", _clean_text(text))
    }


def _validated_pair(
    raw_pair: Any,
    left_sources: dict[str, dict[str, Any]],
    right_sources: dict[str, dict[str, Any]],
    *,
    require_extracted_values_for_visual: bool = False,
) -> dict[str, Any] | None:
    if not isinstance(raw_pair, dict):
        return None
    label = _clean_string(raw_pair.get("dimensionLabel"))
    question = _clean_string(raw_pair.get("comparisonQuestion"))
    confidence = _confidence(raw_pair.get("confidence"))
    if not label or not question or confidence is None:
        return None
    left = _validated_pair_side(raw_pair.get("left"), left_sources)
    right = _validated_pair_side(raw_pair.get("right"), right_sources)
    if left is None or right is None:
        return None
    data_priority = raw_pair.get("dataPriority")
    if not isinstance(data_priority, bool):
        return None
    data_role = _clean_text(raw_pair.get("dataRole"))
    if data_priority:
        if not data_role or data_role not in KNOWN_DATA_ROLES:
            return None
    else:
        if data_role != "emergence_time":
            data_role = ""
    if data_role and not _is_visual_data_role(data_role):
        data_priority = False
    if not data_role:
        data_role = ""
    if data_priority and _is_visual_data_role(data_role) and not _measurement_pair_is_compatible(
        label,
        left["valueText"],
        right["valueText"],
        data_role,
    ):
        return None
    if require_extracted_values_for_visual and data_priority and _is_visual_data_role(data_role):
        if not left.get("values") or not right.get("values"):
            return None
    dedupe_dimension = _is_generic_dimension_label(label, data_role)
    label = _refined_dimension_label(label, data_role, left["valueText"], right["valueText"])
    return {
        "dimensionLabel": label,
        "comparisonQuestion": question,
        "left": left,
        "right": right,
        "dataPriority": data_priority,
        "dataRole": data_role,
        "confidence": confidence,
        "_dedupeDimension": dedupe_dimension,
    }


def _validated_pair_side(raw_side: Any, sources: dict[str, dict[str, Any]]) -> dict[str, Any] | None:
    if not isinstance(raw_side, dict):
        return None
    value_text = _clean_string(raw_side.get("valueText"))
    sentence_ids = raw_side.get("sentenceIds")
    if not value_text or not isinstance(sentence_ids, list) or not sentence_ids:
        return None
    clean_ids = []
    seen_ids = set()
    for sentence_id in sentence_ids:
        if not isinstance(sentence_id, str) or sentence_id not in sources:
            return None
        if sentence_id not in seen_ids:
            clean_ids.append(sentence_id)
            seen_ids.add(sentence_id)
    paragraph_keys = {str(sources[sentence_id].get("paragraphKey")) for sentence_id in clean_ids}
    if len(paragraph_keys) > 1:
        return None
    side = {"valueText": value_text, "sentenceIds": clean_ids}
    values = _validated_pair_values(raw_side.get("values"), value_text, clean_ids, sources)
    if values is None:
        return None
    if values:
        side["values"] = values
    return side


def _validated_pair_values(
    raw_values: Any,
    value_text: str,
    sentence_ids: list[str],
    sources: dict[str, dict[str, Any]],
) -> list[dict[str, Any]] | None:
    if raw_values is None:
        return []
    if not isinstance(raw_values, list):
        return None
    values: list[dict[str, Any]] = []
    source_text = " ".join(_clean_text(sources[source_id].get("text")) for source_id in sentence_ids)
    source_support_text = source_text.lower()
    support_text = _clean_text(f"{value_text} {source_text}").lower()
    for raw_value in raw_values:
        if not isinstance(raw_value, dict):
            return None
        try:
            number = float(raw_value.get("value"))
        except (TypeError, ValueError):
            return None
        if not math.isfinite(number):
            return None
        item: dict[str, Any] = {"value": number}
        if number.is_integer():
            item["value"] = int(number)
        label = _clean_text(raw_value.get("label"))
        if label:
            item["label"] = label
        unit = _clean_text(raw_value.get("unit"))
        if unit:
            item["unit"] = unit
        value_kind = _clean_text(raw_value.get("valueKind"))
        if value_kind in {"aggregate", "component", "rate", "share", "point"}:
            item["valueKind"] = value_kind
        if raw_value.get("year") not in (None, ""):
            try:
                year = int(raw_value["year"])
            except (TypeError, ValueError):
                return None
            if str(year) not in source_support_text:
                return None
            item["year"] = year
        raw_text = _clean_text(raw_value.get("rawText"))
        if raw_text:
            if raw_text.lower() not in support_text:
                return None
            if not _raw_text_supports_numeric_value(raw_text, item["value"]):
                return None
            item["rawText"] = raw_text
        if raw_value.get("confidence") not in (None, ""):
            confidence = _confidence(raw_value.get("confidence"))
            if confidence is None:
                return None
            item["confidence"] = confidence
        values.append(item)
    return values


def _raw_text_supports_numeric_value(raw_text: str, value: Any) -> bool:
    try:
        expected = float(value)
    except (TypeError, ValueError):
        return False
    candidates = []
    for match in NUMBER_RE.finditer(raw_text):
        try:
            number = float(match.group(1).replace(",", ""))
        except ValueError:
            continue
        candidates.append(number)
        unit = (match.group(2) or "").lower()
        if unit in VALUE_MAGNITUDES:
            candidates.append(number * VALUE_MAGNITUDES[unit])
    return any(_numbers_match(expected, candidate) for candidate in candidates)


def _numbers_match(left: float, right: float) -> bool:
    denominator = max(abs(left), abs(right), 1.0)
    return abs(left - right) / denominator <= 0.000001


def _attribute_from_pair_side(
    pair: dict[str, Any],
    side: str,
    index: int,
    sources: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    side_pair = pair[side]
    first_source = sources[side_pair["sentenceIds"][0]]
    attribute = {
        "id": f"{side}-attr-paired-text-{index}",
        "side": side,
        "key": pair["dimensionLabel"],
        "valueText": side_pair["valueText"],
        "source": "main_text",
        "sourceIds": side_pair["sentenceIds"],
        "paragraphId": first_source.get("paragraphId"),
        "confidence": pair["confidence"],
        "dataPriority": pair["dataPriority"],
        "comparisonQuestion": pair["comparisonQuestion"],
    }
    if side_pair.get("values"):
        attribute["extractedValues"] = side_pair["values"]
    if pair["dataRole"]:
        attribute["dataRole"] = pair["dataRole"]
    return attribute


def _source_lookup(article: dict[str, Any]) -> dict[str, dict[str, Any]]:
    lookup: dict[str, dict[str, Any]] = {}
    for paragraph_index, paragraph in enumerate(article.get("paragraphs", []) or []):
        if not isinstance(paragraph, dict):
            continue
        raw_paragraph_id = paragraph.get("id")
        paragraph_id = raw_paragraph_id if isinstance(raw_paragraph_id, str) and raw_paragraph_id.strip() else None
        paragraph_key = (
            paragraph_id
            if paragraph_id is not None
            else f"__paragraph_{paragraph_index}"
        )
        for sentence in paragraph.get("sentences", []) or []:
            if not isinstance(sentence, dict):
                continue
            sentence_id = sentence.get("id")
            if isinstance(sentence_id, str) and sentence_id:
                lookup[sentence_id] = {
                    "paragraphId": paragraph_id,
                    "paragraphKey": paragraph_key,
                    "text": sentence.get("text"),
                }
    return lookup


def _confidence(value: Any) -> float | None:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return None
    try:
        parsed = float(value)
    except (TypeError, ValueError):
        return None
    if not math.isfinite(parsed):
        return None
    if not 0.0 <= parsed <= 1.0:
        return None
    return parsed


def _duplicates_infobox(
    pair: dict[str, Any],
    left_infobox_pool: list[dict[str, Any]],
    right_infobox_pool: list[dict[str, Any]],
) -> bool:
    label = _normalized_infobox_key(pair["dimensionLabel"])
    left_keys = {
        _normalized_infobox_key(item.get("key"))
        for item in left_infobox_pool
        if item.get("source", "infobox") == "infobox"
    }
    right_keys = {
        _normalized_infobox_key(item.get("key"))
        for item in right_infobox_pool
        if item.get("source", "infobox") == "infobox"
    }
    if label == "cases":
        return _has_case_infobox_key(left_keys) and _has_case_infobox_key(right_keys)
    return label in left_keys and label in right_keys


def _has_case_infobox_key(keys: set[str]) -> bool:
    return any("cases" in key.split() for key in keys)


def _normalized_infobox_key(value: Any) -> str:
    tokens = re.sub(r"[^a-z0-9]+", " ", _clean_text(value).lower()).split()
    return " ".join(INFOBOX_KEY_SYNONYMS.get(token, token) for token in tokens)


def _pair_dedupe_key(pair: dict[str, Any]) -> tuple[Any, ...]:
    return (
        tuple(sorted(pair["left"]["sentenceIds"])),
        _normalized_evidence_text(pair["left"]["valueText"]),
        tuple(sorted(pair["right"]["sentenceIds"])),
        _normalized_evidence_text(pair["right"]["valueText"]),
    )


def _normalized_evidence_text(value: str) -> str:
    return _clean_text(value).lower()


def _clean_string(value: Any) -> str | None:
    if not isinstance(value, str):
        return None
    return _clean_text(value)


def _sentence_candidate(sentence: Any, paragraph: dict[str, Any], side: str) -> dict[str, Any] | None:
    if not isinstance(sentence, dict):
        return None
    sentence_id = sentence.get("id")
    text = _clean_text(sentence.get("text"))
    if not isinstance(sentence_id, str) or not sentence_id or not text:
        return None
    data_items = _data_items(text)
    dimension_label = _field_metric_label(text)
    if data_items:
        candidate = {
            "side": side,
            "kind": "data",
            "claimText": text,
            "sentenceIds": [sentence_id],
            "paragraphId": paragraph.get("id"),
            "section": paragraph.get("section"),
            "semanticCue": _semantic_cue(text),
            "dataItems": data_items,
        }
        if dimension_label:
            candidate["dimensionLabel"] = dimension_label
        return candidate
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


def _field_metric_label(text: Any) -> str:
    match = re.match(r"^\s*([^:]{2,90}):\s+\S", _clean_text(text))
    if not match:
        return ""
    label = re.sub(r"\s+", " ", match.group(1)).strip()
    if not re.search(r"[A-Za-z]", label):
        return ""
    return label


def _data_items(text: str) -> list[dict[str, Any]]:
    text = _normalize_number_words(text)
    if (
        not DATA_CONTEXT_RE.search(text)
        and not MEASUREMENT_CONTEXT_RE.search(text)
        and not MONEY_RE.search(text)
        and not ORDINAL_RE.search(text)
        and not _field_metric_label(text)
    ):
        return []
    items: list[dict[str, Any]] = []
    for match in NUMBER_RE.finditer(text):
        raw = match.group(1)
        unit = (match.group(2) or "").lower()
        if _is_embedded_token_number(text, match):
            continue
        if _is_year_range_suffix(text, match):
            continue
        if _is_calendar_day_or_age(text, match):
            continue
        if _is_ranking_denominator(text, match):
            continue
        if _is_publication_context_year(raw, unit, text, match):
            continue
        value = _numeric_value(raw, text, match)
        if value is None:
            continue
        role = _data_role(text, unit, match)
        item: dict[str, Any] = {"value": int(value) if value.is_integer() else value, "role": role}
        if unit:
            item["unit"] = unit
        items.append(item)
    return items


def _normalize_number_words(text: str) -> str:
    def replace(match: re.Match) -> str:
        return f"{NUMBER_WORDS[match.group(1).lower()]} {match.group(2)}"

    return re.sub(
        r"\b(one|two|three|four|five|six|seven|eight|nine|ten)\s+(percent|%)\b",
        replace,
        text,
        flags=re.I,
    )


def _data_role(text: str, unit: str, match: re.Match) -> str:
    if _has_currency_symbol(text, match) or unit in SCALE_UNITS:
        return "scale"
    if unit in {"%", "percent"}:
        return "proportion"
    if _has_local_ranking_context(text, match):
        return "ranking"
    if _has_local_proportion_context(text, match):
        return "proportion"
    if _is_year_like_match(match.group(1), unit) and _has_leading_temporal_prefix(text, match):
        return "emergence_time"
    if _has_direct_measurement_context(text, match):
        return "quantity"
    if _is_year_like_match(match.group(1), unit) and _has_local_emergence_context(text, match):
        return "emergence_time"
    return "quantity"


def _is_publication_context_year(raw: str, unit: str, text: str, match: re.Match) -> bool:
    if unit or _has_currency_symbol(text, match) or not PUBLICATION_NOISE_RE.search(text):
        return False
    if not _is_year_like_match(raw, unit):
        return False
    if _has_entity_emergence_context(text, match):
        return False
    return _has_publication_context(text, match)


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


def _numeric_value(raw: str, text: str, match: re.Match) -> float | None:
    try:
        value = float(raw.replace(",", ""))
    except ValueError:
        return None
    if value > 0 and _has_negative_currency_prefix(text, match):
        return -value
    return value


def _has_negative_currency_prefix(text: str, match: re.Match) -> bool:
    return bool(re.search(r"-\s*[$€£¥₩]\s*$", text[max(0, match.start() - 8) : match.start()]))


def _is_ranking_denominator(text: str, match: re.Match) -> bool:
    prefix = text[max(0, match.start() - 72) : match.start()]
    return bool(RANKING_DENOMINATOR_PREFIX_RE.search(prefix))


def _is_embedded_token_number(text: str, match: re.Match) -> bool:
    start, end = match.span(1)
    before = text[start - 1] if start > 0 else ""
    before_before = text[start - 2] if start > 1 else ""
    after = text[end] if end < len(text) else ""
    if after.lower() == "s" and _is_decade_like_match(match.group(1)) and _has_local_emergence_context(text, match):
        return False
    if after.isalpha() and _has_local_ranking_context(text, match):
        return False
    return bool(before.isalpha() or (before == "-" and before_before.isalpha()) or after.isalpha())


def _is_calendar_day_or_age(text: str, match: re.Match) -> bool:
    raw = match.group(1).replace(",", "")
    try:
        value = int(raw)
    except ValueError:
        return False
    prefix, suffix = _local_prefix_suffix(text, match)
    if 1 <= value <= 31 and (
        MONTH_NAME_RE.search(suffix[:24])
        or MONTH_NAME_RE.search(prefix[-24:])
    ):
        return True
    if 1800 <= value <= 2100 and MONTH_NAME_RE.search(prefix[-24:]):
        return True
    if 0 <= value <= 130 and re.match(r"\s*(?:-|–|—|\s)?\s*years?(?:-|\s)*old\b", suffix, re.I):
        return True
    return False


def _has_local_ranking_context(text: str, match: re.Match) -> bool:
    prefix, suffix = _local_prefix_suffix(text, match)
    if _has_direct_measurement_context(text, match):
        return False
    if RANKING_SUFFIX_CONTEXT_RE.search(suffix):
        return True
    prefix_context = _ranking_prefix_context(text, match)
    if prefix_context is None:
        return False
    if ORDINAL_RANKING_SUFFIX_RE.search(suffix) or _has_rank_marker_prefix(text, match):
        return True
    if prefix_context == "placed":
        return bool(PLACED_CARDINAL_RANKING_SUFFIX_RE.search(suffix))
    return bool(CARDINAL_RANKING_SUFFIX_RE.search(suffix))


def _ranking_prefix_context(text: str, match: re.Match) -> str | None:
    prefix, _ = _local_prefix_suffix(text, match)
    prefix_match = RANKING_PREFIX_RE.search(prefix)
    if prefix_match:
        return prefix_match.group(1).lower()
    start, _ = match.span(1)
    if start == 0 or text[start - 1] != "#":
        return None
    marker_prefix = text[max(0, start - 49) : start - 1]
    marker_prefix_match = RANKING_PREFIX_RE.search(marker_prefix)
    if marker_prefix_match:
        return marker_prefix_match.group(1).lower()
    return None


def _has_rank_marker_prefix(text: str, match: re.Match) -> bool:
    start, _ = match.span(1)
    return start > 0 and text[start - 1] == "#"


def _has_local_proportion_context(text: str, match: re.Match) -> bool:
    prefix, suffix = _local_prefix_suffix(text, match)
    return bool(PROPORTION_PREFIX_RE.search(prefix) or PROPORTION_SUFFIX_RE.search(suffix))


def _has_local_emergence_context(text: str, match: re.Match) -> bool:
    prefix, suffix = _local_prefix_suffix(text, match)
    return bool(EMERGENCE_CONTEXT_RE.search(prefix) or EMERGENCE_CONTEXT_RE.search(suffix))


def _has_entity_emergence_context(text: str, match: re.Match) -> bool:
    _, suffix = _local_prefix_suffix(text, match)
    return bool(ENTITY_EMERGENCE_SUFFIX_RE.search(suffix))


def _local_prefix_suffix(text: str, match: re.Match) -> tuple[str, str]:
    return text[max(0, match.start() - 48) : match.start()], text[match.end() : min(len(text), match.end() + 48)]


def _has_publication_context(text: str, match: re.Match) -> bool:
    prefix, suffix = _local_prefix_suffix(text, match)
    return bool(PUBLICATION_YEAR_PREFIX_RE.search(prefix) or PUBLICATION_YEAR_SUFFIX_RE.search(suffix))


def _has_direct_measurement_context(text: str, match: re.Match) -> bool:
    return bool(DIRECT_MEASUREMENT_CONTEXT_RE.search(text[match.end() :]))


def _has_leading_temporal_prefix(text: str, match: re.Match) -> bool:
    return bool(LEADING_TEMPORAL_PREFIX_RE.search(text[: match.start()]))


def _is_year_like_match(raw: str, unit: str) -> bool:
    if unit or "," in raw:
        return False
    try:
        value = int(raw.replace(",", ""))
    except ValueError:
        return False
    return 1800 <= value <= 2100 and len(raw.replace(",", "")) == 4


def _is_year_range_suffix(text: str, match: re.Match) -> bool:
    raw = match.group(1)
    if not str(raw).startswith("-"):
        return False
    return match.start(1) > 0 and text[match.start(1) - 1].isdigit()


def _is_decade_like_match(raw: str) -> bool:
    if "," in raw:
        return False
    try:
        value = int(raw)
    except ValueError:
        return False
    return 1800 <= value <= 2100 and value % 10 == 0 and len(raw) == 4


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


def _is_visual_data_role(role: str) -> bool:
    return role in KNOWN_DATA_ROLES and role != "emergence_time"


def _dimension_dedupe_key(pair: dict[str, Any]) -> tuple[str, str]:
    return (
        str(pair.get("dataRole") or "").strip().lower(),
        _normalized_label(pair.get("dimensionLabel")),
    )


def _dimension_label(role: str, left_text: Any, right_text: Any) -> str:
    left_cue = _measurement_cue(left_text)
    right_cue = _measurement_cue(right_text)
    cue = left_cue if left_cue and left_cue == right_cue else left_cue or right_cue
    if cue:
        return _cue_label(cue)
    return ROLE_LABELS[role]


def _refined_dimension_label(label: str, role: str, left_text: Any, right_text: Any) -> str:
    if not role or not _is_visual_data_role(role):
        return label
    if not _is_generic_dimension_label(label, role):
        return label
    return _dimension_label(role, left_text, right_text)


def _is_generic_dimension_label(label: str, role: str) -> bool:
    return _normalized_label(label) in {
        _normalized_label(ROLE_LABELS.get(role)),
        "quantity",
        "scale",
        "ranking",
        "proportion rate",
    }


def _cue_label(cue: str) -> str:
    labels = {
        "accuracy": "Accuracy",
        "capacity": "Capacity",
        "cases": "Cases",
        "confirmed cases": "Confirmed cases",
        "deaths": "Deaths",
        "employees": "Employees",
        "features": "Features",
        "growth": "Growth",
        "hospitalized cases": "Hospitalized cases",
        "microsoft cloud revenue": "Microsoft Cloud revenue",
        "diluted earnings per share": "Diluted earnings per share",
        "operating income": "Operating income",
        "net income": "Net income",
        "models": "Models",
        "margin": "Margin",
        "population": "Population",
        "purchase incentive": "Purchase incentive",
        "recovered": "Recovered",
        "revenue": "Revenue",
        "sales": "Sales",
        "samples": "Samples",
        "share": "Share / rate",
        "tests": "Tests",
        "users": "Users",
    }
    return labels.get(cue, cue.title())


def _comparison_question(role: str, label: str) -> str:
    if label and label != ROLE_LABELS.get(role):
        return f"How do the articles compare on {label.lower()}?"
    return ROLE_QUESTIONS[role]


def _normalized_label(value: Any) -> str:
    return re.sub(r"\s+", " ", str(value or "").strip().lower())
