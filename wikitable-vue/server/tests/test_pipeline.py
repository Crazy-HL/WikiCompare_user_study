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
    assert row["dataType"] in {"Proportional", "Trend", "Numerical"}
    assert row["visualization"]["left"]["values"][0]["value"] == 2.3


def test_rank_rows_orders_trend_first_scores():
    rows = [
        {"id": "a", "score": 0.2, "dataType": "Text"},
        {"id": "b", "score": 0.9, "dataType": "Trend"},
    ]

    assert [row["id"] for row in rank_rows(rows)] == ["b", "a"]


def test_extract_numeric_values_handles_currency_magnitude_and_years():
    values = extract_numeric_values("$1.5 billion in 2024")

    assert values == [{"value": 1500000000.0, "year": 2024}]


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
