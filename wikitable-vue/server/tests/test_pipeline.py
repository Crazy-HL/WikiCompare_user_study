from services.pipeline import (
    choose_chart_type,
    classify_value_rule,
    extract_numeric_values,
    normalize_attribute_pair,
    rank_rows,
    validate_alignments,
)


def test_choose_chart_type_uses_table_one_rules():
    assert choose_chart_type("Numerical", 2) == "bar"
    assert choose_chart_type("Numerical", 3) == "bar"
    assert choose_chart_type("Numerical", 4) == "scatter"
    assert choose_chart_type("Proportional", 4) == "pie"
    assert choose_chart_type("Proportional", 5) == "stacked"
    assert choose_chart_type("Trend", 2) == "bar"
    assert choose_chart_type("Trend", 3) == "line"
    assert choose_chart_type("Categorical", 2) == "text"
    assert choose_chart_type("Categorical", 3) == "stacked"
    assert choose_chart_type("Ordinal", 1) == "text"


def test_classify_value_rule_detects_common_types():
    assert classify_value_rule("1.5% (2024)") == "Proportional"
    assert classify_value_rule("2020: 100, 2024: 150") == "Trend"
    assert classify_value_rule("12th (nominal)") == "Ordinal"
    assert classify_value_rule("40°N, 116°E") == "Geographical"
    assert classify_value_rule("116°E, 40°N") == "Geographical"
    assert classify_value_rule("10 million") == "Numerical"


def test_validate_alignments_drops_unknown_attribute_ids():
    left_pool = [{"id": "left-a", "key": "GDP growth", "valueText": "2.3%", "sourceIds": ["left-info-1"]}]
    right_pool = [{"id": "right-a", "key": "GDP growth", "valueText": "0.8%", "sourceIds": ["right-info-1"]}]
    alignments = [
        {"leftId": "left-a", "rightId": "right-a", "label": "GDP growth"},
        {"leftId": "missing", "rightId": "right-a", "label": "Bad"},
    ]

    valid = validate_alignments(left_pool, right_pool, alignments)

    assert len(valid) == 1
    assert valid[0]["leftId"] == "left-a"


def test_normalize_attribute_pair_produces_visualization():
    row = normalize_attribute_pair(
        {"id": "left-a", "key": "GDP growth", "valueText": "2.3% (2024)", "source": "infobox", "sourceIds": ["left-info-1"]},
        {"id": "right-a", "key": "GDP growth", "valueText": "0.8% (2024)", "source": "infobox", "sourceIds": ["right-info-1"]},
        "GDP growth",
    )

    assert row["label"] == "GDP growth"
    assert row["dataType"] == "Proportional"
    assert row["visualization"]["left"]["values"][0]["value"] == 2.3


def test_rank_rows_orders_trend_first_scores():
    rows = [
        {"id": "a", "score": 0.2, "dataType": "Text"},
        {"id": "b", "score": 0.9, "dataType": "Trend"},
    ]

    assert [row["id"] for row in rank_rows(rows)] == ["b", "a"]


def test_rank_rows_uses_weighted_difference_not_trend_bucket_only():
    rows = [
        {"id": "tiny-trend", "score": 0.01, "dataType": "Trend"},
        {"id": "huge-numeric", "score": 0.95, "dataType": "Numerical"},
    ]

    assert [row["id"] for row in rank_rows(rows)] == ["huge-numeric", "tiny-trend"]


def test_extract_numeric_values_handles_currency_magnitude_and_years():
    values = extract_numeric_values("$1.5 billion in 2024")

    assert values == [{"value": 1500000000.0, "year": 2024}]


def test_extract_numeric_values_handles_wikipedia_infobox_year_series():
    values = extract_numeric_values("1.4% (2023) 2.0% (2024) 1.0% (2025) 1.4% (2026f)")

    assert values == [
        {"value": 1.4, "year": 2023},
        {"value": 2.0, "year": 2024},
        {"value": 1.0, "year": 2025},
        {"value": 1.4, "year": 2026},
    ]


def test_extract_numeric_values_labels_named_parenthetical_series():
    values = extract_numeric_values("$1.87 trillion (nominal; 2025) $3.36 trillion (PPP; 2025)")

    assert values == [
        {"value": 1870000000000.0, "year": 2025, "label": "nominal"},
        {"value": 3360000000000.0, "year": 2025, "label": "PPP"},
    ]


def test_extract_numeric_values_labels_prefixed_amounts():
    values = extract_numeric_values("Inward: $25 billion (2021) Outward: $147 billion (2021)")

    assert values == [
        {"value": 25000000000.0, "year": 2021, "label": "Inward"},
        {"value": 147000000000.0, "year": 2021, "label": "Outward"},
    ]


def test_extract_numeric_values_labels_youth_unemployment():
    values = extract_numeric_values("2.6% (October 2025) 6.4% youth unemployment (15 to 24-year-olds, 2024)")

    assert values == [
        {"value": 2.6, "year": 2025, "label": "overall"},
        {"value": 6.4, "label": "youth"},
    ]


def test_extract_numeric_values_labels_currency_variants():
    values = extract_numeric_values("¥545,000 (US$3,606) monthly (2023)")

    assert values == [
        {"value": 545000.0, "year": 2023, "label": "JPY"},
        {"value": 3606.0, "year": 2023, "label": "USD"},
    ]

    values = extract_numeric_values("3,835,828 ₩ / US$2,810 monthly (2024)")

    assert values == [
        {"value": 3835828.0, "year": 2024, "label": "KRW"},
        {"value": 2810.0, "year": 2024, "label": "USD"},
    ]


def test_extract_numeric_values_labels_percentage_category_lists_in_order():
    values = extract_numeric_values("China 22.5% United States 11.6% Japan 7.8% Taiwan 5.1% (2025)")

    assert values == [
        {"value": 22.5, "year": 2025, "label": "China"},
        {"value": 11.6, "year": 2025, "label": "United States"},
        {"value": 7.8, "year": 2025, "label": "Japan"},
        {"value": 5.1, "year": 2025, "label": "Taiwan"},
    ]


def test_rank_rows_downranks_mismatched_currency_amounts():
    rows = [
        {"id": "revenue", "score": 0.998, "dataType": "Numerical", "comparisonQuality": "unit_mismatch"},
        {"id": "gdp", "score": 0.55, "dataType": "Numerical"},
    ]

    assert [row["id"] for row in rank_rows(rows)] == ["gdp", "revenue"]


def test_normalize_attribute_pair_compares_shared_labeled_values_first():
    row = normalize_attribute_pair(
        {"id": "left-a", "key": "Average net salary", "valueText": "3,835,828 ₩ / US$2,810 monthly (2024)", "source": "infobox", "sourceIds": ["left-info-1"]},
        {"id": "right-a", "key": "Average net salary", "valueText": "¥352,541 / US$2,421 monthly (2024)", "source": "infobox", "sourceIds": ["right-info-1"]},
        "Average net salary",
    )

    assert row["comparisonQuality"] == "shared_labels"
    assert row["score"] == 0.138434


def test_extract_numeric_values_ignores_dates_and_age_ranges():
    assert extract_numeric_values("1 April – 31 March") == []
    assert extract_numeric_values("$230.6 billion (31 December 2017 est.) Abroad: $344.7 billion (31 December 2017 est.)") == [
        {"value": 230600000000.0, "year": 2017},
        {"value": 344700000000.0, "year": 2017, "label": "Abroad"},
    ]
    assert extract_numeric_values("2.6% (October 2025) 6.4% youth unemployment (15 to 24-year-olds, 2024)") == [
        {"value": 2.6, "year": 2025, "label": "overall"},
        {"value": 6.4, "label": "youth"},
    ]
    assert extract_numeric_values("2.3% (July 2025) 3.7% youth unemployment (15 to 24 year-olds; May 2023) 1.69 million unemployed (July 2025)") == [
        {"value": 2.3, "year": 2025, "label": "overall"},
        {"value": 3.7, "label": "youth"},
    ]


def test_normalize_attribute_pair_keeps_mixed_currency_and_gdp_share_numerical():
    row = normalize_attribute_pair(
        {"id": "left-a", "key": "Revenue", "valueText": "$428.7 billion (2020)", "source": "infobox", "sourceIds": ["left-info-1"]},
        {"id": "right-a", "key": "Revenue", "valueText": "¥236,284 billion 37.2% of GDP (2025)", "source": "infobox", "sourceIds": ["right-info-1"]},
        "Revenue",
    )

    assert row["dataType"] == "Numerical"
    assert row["chartType"] == "bar"
    assert row["visualization"]["right"]["values"] == [{"value": 236284000000000.0, "year": 2025}]


def test_extract_numeric_values_scales_quadrillion_and_skips_gdp_share_when_amount_present():
    assert extract_numeric_values("¥1.451 quadrillion 229.6% of GDP (2025)") == [
        {"value": 1451000000000000.0, "year": 2025}
    ]


def test_normalize_attribute_pair_compares_shared_gdp_share_when_available():
    row = normalize_attribute_pair(
        {"id": "left-a", "key": "Government debt", "valueText": "39.8% of GDP (2020)", "source": "infobox", "sourceIds": ["left-info-1"]},
        {"id": "right-a", "key": "Government debt", "valueText": "¥1.451 quadrillion 229.6% of GDP (2025)", "source": "infobox", "sourceIds": ["right-info-1"]},
        "Government debt",
    )

    assert row["dataType"] == "Proportional"
    assert row["visualization"]["left"]["values"] == [{"value": 39.8, "year": 2020, "label": "% of GDP"}]
    assert row["visualization"]["right"]["values"] == [{"value": 229.6, "year": 2025, "label": "% of GDP"}]


def test_classify_value_rule_does_not_treat_context_years_as_trend():
    assert classify_value_rule("2.6% (October 2025) 6.4% youth unemployment (15 to 24-year-olds, 2024)") == "Proportional"


def test_extract_numeric_values_does_not_treat_year_ranges_as_year_values():
    assert extract_numeric_values("2020-2024") == []
    assert extract_numeric_values("2020 - 2024") == []
    assert extract_numeric_values("2020–2024") == []
    assert extract_numeric_values("Years: 2020, 2024") == []
    assert extract_numeric_values("2020-2024: 12") == []
    assert extract_numeric_values("2020 - 2024: 12") == []
    assert extract_numeric_values("2020—2024: 12") == []


def test_normalize_attribute_pair_scores_actual_value_differences():
    same = normalize_attribute_pair(
        {"id": "left-a", "key": "Exports", "valueText": "2020: 100, 2024: 150", "source": "main_text", "sourceIds": ["left-s-1"]},
        {"id": "right-a", "key": "Exports", "valueText": "2020: 100, 2024: 150", "source": "main_text", "sourceIds": ["right-s-1"]},
        "Exports",
    )
    different = normalize_attribute_pair(
        {"id": "left-b", "key": "Exports", "valueText": "2020: 100, 2024: 300", "source": "main_text", "sourceIds": ["left-s-2"]},
        {"id": "right-b", "key": "Exports", "valueText": "2020: 100, 2024: 150", "source": "main_text", "sourceIds": ["right-s-2"]},
        "Exports",
    )

    assert same["score"] == 0
    assert different["score"] > same["score"]
    assert different["dataType"] == "Trend"


def test_normalize_attribute_pair_handles_standalone_year_attributes():
    row = normalize_attribute_pair(
        {"id": "left-founded", "key": "Founded", "valueText": "Founded: 1998", "source": "infobox", "sourceIds": ["left-info-1"]},
        {"id": "right-founded", "key": "Founded", "valueText": "Founded: 2001", "source": "infobox", "sourceIds": ["right-info-1"]},
        "Founded",
    )

    assert row["dataType"] == "Numerical"
    assert row["visualization"]["left"]["values"] == [{"value": 1998.0}]
    assert row["visualization"]["right"]["values"] == [{"value": 2001.0}]
    assert row["score"] > 0


def test_normalize_attribute_pair_marks_source_kind_both():
    row = normalize_attribute_pair(
        {"id": "left-a", "key": "Revenue", "valueText": "$1.5 billion in 2024", "source": "infobox", "sourceIds": ["left-info-1"]},
        {"id": "right-a", "key": "Revenue", "valueText": "$900 million in 2024", "source": "main_text", "sourceIds": ["right-s-1"]},
        "Revenue",
    )

    assert row["sourceKind"] == "Both"
    assert row["leftSourceIds"] == ["left-info-1"]
    assert row["rightSourceIds"] == ["right-s-1"]
    assert row["visualization"]["right"]["values"][0]["value"] == 900000000.0
