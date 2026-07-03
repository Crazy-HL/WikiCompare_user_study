from services.pipeline import (
    align_attribute_pools,
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


def test_align_attribute_pools_matches_semantic_concept_dimensions():
    left_pool = [
        {"id": "left-definition", "key": "Definition", "valueText": "AI is intelligence in machines."},
        {"id": "left-applications", "key": "Applications", "valueText": "AI is used in search and robotics."},
        {"id": "left-history", "key": "History", "valueText": "AI was founded as a field in 1956."},
    ]
    right_pool = [
        {"id": "right-overview", "key": "Overview", "valueText": "Machine learning is a field of study in AI."},
        {"id": "right-uses", "key": "Uses", "valueText": "Machine learning is used in language and vision."},
        {"id": "right-background", "key": "Background", "valueText": "Machine learning grew from pattern recognition."},
    ]

    alignments = align_attribute_pools(left_pool, right_pool)

    assert [(item["left"]["id"], item["right"]["id"], item["label"]) for item in alignments] == [
        ("left-definition", "right-overview", "Definition / Overview"),
        ("left-applications", "right-uses", "Applications / Uses"),
        ("left-history", "right-background", "History / Background"),
    ]


def test_normalize_attribute_pair_produces_visualization():
    row = normalize_attribute_pair(
        {"id": "left-a", "key": "GDP growth", "valueText": "2.3% (2024)", "source": "infobox", "sourceIds": ["left-info-1"]},
        {"id": "right-a", "key": "GDP growth", "valueText": "0.8% (2024)", "source": "infobox", "sourceIds": ["right-info-1"]},
        "GDP growth",
    )

    assert row["label"] == "GDP growth"
    assert row["dataType"] == "Proportional"
    assert row["visualization"]["left"]["values"][0]["value"] == 2.3


def test_normalize_attribute_pair_preserves_related_source_ids():
    row = normalize_attribute_pair(
        {
            "id": "left-a",
            "key": "GDP growth",
            "valueText": "2.3% (2024)",
            "source": "infobox",
            "sourceIds": ["left-info-1"],
            "relatedSourceIds": ["left-s-1-1"],
        },
        {
            "id": "right-a",
            "key": "GDP growth",
            "valueText": "0.8% (2024)",
            "source": "infobox",
            "sourceIds": ["right-info-1"],
            "relatedSourceIds": ["right-s-1-1", "right-p-1"],
        },
        "GDP growth",
    )

    assert row["leftSourceIds"] == ["left-info-1"]
    assert row["rightSourceIds"] == ["right-info-1"]
    assert row["leftRelatedSourceIds"] == ["left-s-1-1"]
    assert row["rightRelatedSourceIds"] == ["right-s-1-1", "right-p-1"]


def test_normalize_attribute_pair_preserves_data_first_text_metadata():
    row = normalize_attribute_pair(
        {
            "id": "left-history",
            "key": "Historical emergence",
            "valueText": "The field emerged in 1956.",
            "source": "main_text",
            "sourceIds": ["left-s-1"],
            "dataPriority": True,
            "dataRole": "emergence_time",
            "comparisonQuestion": "When did it emerge?",
        },
        {
            "id": "right-history",
            "key": "Historical emergence",
            "valueText": "The field emerged in 1950.",
            "source": "main_text",
            "sourceIds": ["right-s-1"],
        },
        "Historical emergence",
    )

    assert row["dataPriority"] is True
    assert row["dataRole"] == "emergence_time"
    assert row["comparisonQuestion"] == "When did it emerge?"


def test_normalize_attribute_pair_structures_currency_name_code_and_symbol():
    row = normalize_attribute_pair(
        {
            "id": "left-currency",
            "key": "Currency",
            "valueText": "South Korean won (KRW, ₩)",
            "source": "infobox",
            "sourceIds": ["left-info-1"],
        },
        {
            "id": "right-currency",
            "key": "Currency",
            "valueText": "Japanese yen (JPY, ¥)",
            "source": "infobox",
            "sourceIds": ["right-info-1"],
        },
        "Currency",
    )

    assert row["dataType"] == "Categorical"
    assert row["chartType"] == "text"
    assert row["comparisonQuality"] == "structured_values"
    assert row["score"] == 1.0
    assert row["visualization"]["left"]["structuredValues"] == [
        {"label": "Name", "value": "South Korean won", "kind": "entity_name"},
        {"label": "Code", "value": "KRW", "kind": "currency_code"},
        {"label": "Symbol", "value": "₩", "kind": "currency_symbol"},
    ]
    assert row["visualization"]["right"]["structuredValues"] == [
        {"label": "Name", "value": "Japanese yen", "kind": "entity_name"},
        {"label": "Code", "value": "JPY", "kind": "currency_code"},
        {"label": "Symbol", "value": "¥", "kind": "currency_symbol"},
    ]


def test_normalize_attribute_pair_uses_numeric_values_before_list_structure():
    row = normalize_attribute_pair(
        {
            "id": "left-gdp",
            "key": "GDP",
            "valueText": "$1.87 trillion (nominal; 2025) $3.36 trillion (PPP; 2025)",
            "structuredValues": [
                {"label": "$1.87 trillion (nominal; 2025)", "value": "$1.87 trillion (nominal; 2025)", "kind": "list_item"},
                {"label": "$3.36 trillion (PPP; 2025)", "value": "$3.36 trillion (PPP; 2025)", "kind": "list_item"},
            ],
            "source": "infobox",
            "sourceIds": ["left-info-1"],
        },
        {
            "id": "right-gdp",
            "key": "GDP",
            "valueText": "$4.379 trillion (nominal; 2026f) $7.262 trillion (PPP; 2026f)",
            "structuredValues": [
                {"label": "$4.379 trillion (nominal; 2026f)", "value": "$4.379 trillion (nominal; 2026f)", "kind": "list_item"},
                {"label": "$7.262 trillion (PPP; 2026f)", "value": "$7.262 trillion (PPP; 2026f)", "kind": "list_item"},
            ],
            "source": "infobox",
            "sourceIds": ["right-info-1"],
        },
        "GDP",
    )

    assert row["dataType"] == "Numerical"
    assert row["comparisonQuality"] == "shared_labels"
    assert "structuredValues" not in row["visualization"]["left"]
    assert "structuredValues" not in row["visualization"]["right"]
    assert row["visualization"]["left"]["values"] == [
        {"value": 1870000000000.0, "year": 2025, "label": "nominal"},
        {"value": 3360000000000.0, "year": 2025, "label": "PPP"},
    ]


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


def test_rank_rows_places_text_rows_after_chartable_rows():
    rows = [
        {"id": "currency", "label": "Currency", "score": 1.0, "dataType": "Categorical", "chartType": "text"},
        {"id": "import-goods", "label": "Import goods", "score": 0.22, "dataType": "Proportional", "chartType": "stacked"},
        {"id": "gdp-rank", "label": "GDP rank", "score": 0.9, "dataType": "Ordinal", "chartType": "text"},
        {"id": "revenue", "label": "Revenue", "score": 0.04, "dataType": "Numerical", "chartType": "bar"},
    ]

    ranked = rank_rows(rows)

    assert [row["id"] for row in ranked] == ["import-goods", "revenue", "currency", "gdp-rank"]
    assert ranked[0]["rankScore"] == 0.066
    assert ranked[2]["rankScore"] == 0.2


def test_rank_rows_prioritizes_paired_data_text_over_generic_text():
    rows = [
        {
            "id": "overview",
            "label": "Overview",
            "dataType": "Text",
            "chartType": "text",
            "score": 0.8,
            "sourceKind": "main_text",
            "comparisonQuality": "text",
            "visualization": {"left": {"rawText": "A is a concept."}, "right": {"rawText": "B is a concept."}},
        },
        {
            "id": "history",
            "label": "Historical emergence",
            "dataType": "Numerical",
            "chartType": "bar",
            "score": 0.4,
            "sourceKind": "main_text",
            "comparisonQuality": "paired_text_data",
            "dataPriority": True,
            "visualization": {"left": {"values": [{"value": 1956}]}, "right": {"values": [{"value": 1950}]}},
        },
    ]

    ranked = rank_rows(rows)

    assert [row["label"] for row in ranked] == ["Historical emergence", "Overview"]


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


def test_extract_numeric_values_infers_inward_fdi_before_abroad_stock():
    values = extract_numeric_values("$230.6 billion (31 December 2017 est.) Abroad: $344.7 billion (31 December 2017 est.)")

    assert values == [
        {"value": 230600000000.0, "year": 2017, "label": "Inward"},
        {"value": 344700000000.0, "year": 2017, "label": "Abroad"},
    ]


def test_extract_numeric_values_labels_named_parenthetical_series():
    values = extract_numeric_values("$1.87 trillion (nominal; 2025) $3.36 trillion (PPP; 2025)")

    assert values == [
        {"value": 1870000000000.0, "year": 2025, "label": "nominal"},
        {"value": 3360000000000.0, "year": 2025, "label": "PPP"},
    ]


def test_normalize_attribute_pair_classifies_export_goods_as_stacked_proportional():
    left = (
        "Integrated circuits 15.35% Machinery 12.81% Vehicles and their parts 11.34% "
        "Mineral fuels 7.01% Plastics 5.86% Iron and steel 4.23% "
        "Instruments and apparatus 4.16% Organic chemicals 3.85% Others 35.39% (2019)"
    )
    right = (
        "Transport equipment 21% Machinery 19.9% Electrical machinery 18.7% "
        "Others 13.8% Chemicals 12.4% Manufactured goods 10.4% "
        "Raw materials 1.7% Foodstuff 1.3% Mineral fuels 0.8%"
    )

    row = normalize_attribute_pair(
        {"id": "left-export-goods", "key": "Export goods", "valueText": left, "source": "infobox", "sourceIds": ["left-info-1"]},
        {"id": "right-export-goods", "key": "Export goods", "valueText": right, "source": "infobox", "sourceIds": ["right-info-1"]},
        "Export goods",
    )

    assert row["dataType"] == "Proportional"
    assert row["chartType"] == "stacked"
    assert row["comparisonQuality"] == "shared_labels"
    assert "structuredValues" not in row["visualization"]["left"]
    assert row["visualization"]["left"]["values"][0] == {
        "value": 15.35,
        "label": "Integrated circuits",
        "year": 2019,
    }


def test_extract_numeric_values_deduplicates_forecast_parenthetical_series():
    assert extract_numeric_values("$4.379 trillion (nominal; 2026f) $7.262 trillion (PPP; 2026f)") == [
        {"value": 4378999999999.9995, "year": 2026, "label": "nominal"},
        {"value": 7262000000000.0, "year": 2026, "label": "PPP"},
    ]


def test_extract_numeric_values_labels_ordinal_parenthetical_series():
    values = extract_numeric_values("13th (nominal); 14th (PPP)")

    assert values == [
        {"value": 13.0, "label": "nominal"},
        {"value": 14.0, "label": "PPP"},
    ]

    row = normalize_attribute_pair(
        {"id": "left-rank", "key": "GDP rank", "valueText": "13th (nominal); 14th (PPP)", "source": "infobox", "sourceIds": ["left-info-1"]},
        {"id": "right-rank", "key": "GDP rank", "valueText": "4th (nominal); 4th (PPP)", "source": "infobox", "sourceIds": ["right-info-1"]},
        "GDP rank",
    )

    assert row["dataType"] == "Ordinal"
    assert row["chartType"] == "text"
    assert row["visualization"]["left"]["values"] == [
        {"value": 13.0, "label": "nominal"},
        {"value": 14.0, "label": "PPP"},
    ]
    assert row["visualization"]["right"]["values"] == [
        {"value": 4.0, "label": "nominal"},
        {"value": 4.0, "label": "PPP"},
    ]


def test_extract_numeric_values_labels_adjacent_ordinal_parenthetical_series():
    assert extract_numeric_values("14th (nominal; 2025) 14th (PPP; 2025)") == [
        {"value": 14.0, "year": 2025, "label": "nominal"},
        {"value": 14.0, "year": 2025, "label": "PPP"},
    ]

    assert extract_numeric_values("4th (nominal; 2026 5th (PPP; 2026") == [
        {"value": 4.0, "year": 2026, "label": "nominal"},
        {"value": 5.0, "year": 2026, "label": "PPP"},
    ]


def test_extract_numeric_values_labels_corruption_index_score_and_rank():
    assert extract_numeric_values("64 out of 100 points (2024, 30th rank)") == [
        {"value": 64.0, "year": 2024, "label": "score", "rawText": "64 out of 100 points"},
        {"value": 30.0, "year": 2024, "label": "rank", "rawText": "30th rank"},
    ]

    assert extract_numeric_values("71 out of 100 points (2025) (rank 18th)") == [
        {"value": 71.0, "year": 2025, "label": "score", "rawText": "71 out of 100 points"},
        {"value": 18.0, "year": 2025, "label": "rank", "rawText": "rank 18th"},
    ]


def test_extract_numeric_values_labels_hdi_index_and_rank():
    values = extract_numeric_values("0.929 very high (2023) (19th)")

    assert values == [
        {"value": 0.929, "year": 2023, "label": "index", "rawText": "0.929 very high (2023)"},
        {"value": 19.0, "year": 2023, "label": "rank", "rawText": "19th"},
    ]

    row = normalize_attribute_pair(
        {"id": "left-hdi", "key": "Human Development Index", "valueText": "0.929 very high (2023) (19th)", "source": "infobox", "sourceIds": ["left-info-1"]},
        {"id": "right-hdi", "key": "Human Development Index", "valueText": "0.925 very high (2023) (24th)", "source": "infobox", "sourceIds": ["right-info-1"]},
        "Human Development Index",
    )

    assert row["dataType"] == "Ordinal"
    assert row["chartType"] == "text"
    assert row["comparisonQuality"] == "shared_labels"
    assert row["visualization"]["left"]["values"] == [
        {"value": 0.929, "year": 2023, "label": "index", "rawText": "0.929 very high (2023)"},
        {"value": 19.0, "year": 2023, "label": "rank", "rawText": "19th"},
    ]


def test_extract_numeric_values_labels_hdi_and_ihdi_series():
    assert extract_numeric_values("0.937 very high (2023) (20th) 0.857 very high IHDI (2023, 18th)") == [
        {"value": 0.937, "year": 2023, "label": "HDI index", "rawText": "0.937 very high (2023)"},
        {"value": 20.0, "year": 2023, "label": "HDI rank", "rawText": "20th"},
        {"value": 0.857, "year": 2023, "label": "IHDI index", "rawText": "0.857 very high IHDI (2023)"},
        {"value": 18.0, "year": 2023, "label": "IHDI rank", "rawText": "18th"},
    ]

    assert extract_numeric_values("0.925 very high (2023) (23rd) 0.845 very high IHDI (20th) (2023)") == [
        {"value": 0.925, "year": 2023, "label": "HDI index", "rawText": "0.925 very high (2023)"},
        {"value": 23.0, "year": 2023, "label": "HDI rank", "rawText": "23rd"},
        {"value": 0.845, "year": 2023, "label": "IHDI index", "rawText": "0.845 very high IHDI (2023)"},
        {"value": 20.0, "year": 2023, "label": "IHDI rank", "rawText": "20th"},
    ]


def test_extract_numeric_values_labels_prefixed_amounts():
    values = extract_numeric_values("Inward: $25 billion (2021) Outward: $147 billion (2021)")

    assert values == [
        {"value": 25000000000.0, "year": 2021, "label": "Inward"},
        {"value": 147000000000.0, "year": 2021, "label": "Outward"},
    ]


def test_extract_numeric_values_labels_colon_amount_series():
    assert extract_numeric_values("exports: $577.4 billion; imports: $457.5 billion (2020 est.)") == [
        {"value": 577400000000.0, "year": 2020, "label": "exports"},
        {"value": 457500000000.0, "year": 2020, "label": "imports"},
    ]

    assert extract_numeric_values("revenues: $351.8 billion; expenditures: $367.6 billion (2020 est.)") == [
        {"value": 351800000000.0, "year": 2020, "label": "revenues"},
        {"value": 367600000000.0, "year": 2020, "label": "expenditures"},
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

    assert extract_numeric_values("export partners: China 25.1%, United States 12.2%, Vietnam 8.4% (2022)") == [
        {"value": 25.1, "year": 2022, "label": "China"},
        {"value": 12.2, "year": 2022, "label": "United States"},
        {"value": 8.4, "year": 2022, "label": "Vietnam"},
    ]


def test_extract_numeric_values_labels_space_separated_percentage_goods():
    assert extract_numeric_values("Transport equipment 21.0% Machinery 19.9% Others: 13.8%") == [
        {"value": 21.0, "label": "Transport equipment"},
        {"value": 19.9, "label": "Machinery"},
        {"value": 13.8, "label": "Others"},
    ]


def test_extract_numeric_values_labels_colon_percentage_categories_without_semicolons():
    assert extract_numeric_values("Agriculture: 1.0% Industry: 26.9% Services: 71.4% (2022 est.)") == [
        {"value": 1.0, "year": 2022, "label": "Agriculture"},
        {"value": 26.9, "year": 2022, "label": "Industry"},
        {"value": 71.4, "year": 2022, "label": "Services"},
    ]


def test_extract_numeric_values_labels_percentile_colon_series():
    assert extract_numeric_values("lowest 10%: 2.7%; highest 10%: 24.5% (2016)") == [
        {"value": 2.7, "year": 2016, "label": "lowest 10%"},
        {"value": 24.5, "year": 2016, "label": "highest 10%"},
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


def test_normalize_attribute_pair_can_refine_rule_values_with_llm():
    calls = []

    def refiner(*, key, value_text, rule_values, data_type):
        calls.append((key, value_text, rule_values, data_type))
        if "13th" in value_text:
            return [
                {"value": 13.0, "label": "nominal", "rawText": "13th (nominal)", "confidence": 0.94},
                {"value": 14.0, "label": "PPP", "rawText": "14th (PPP)", "confidence": 0.94},
            ]
        return [
            {"value": 4.0, "label": "nominal", "rawText": "4th (nominal)", "confidence": 0.94},
            {"value": 4.0, "label": "PPP", "rawText": "4th (PPP)", "confidence": 0.94},
        ]

    row = normalize_attribute_pair(
        {"id": "left-rank", "key": "GDP rank", "valueText": "13th (nominal); 14th (PPP)", "source": "infobox", "sourceIds": ["left-info-1"]},
        {"id": "right-rank", "key": "GDP rank", "valueText": "4th (nominal); 4th (PPP)", "source": "infobox", "sourceIds": ["right-info-1"]},
        "GDP rank",
        value_refiner=refiner,
    )

    assert len(calls) == 2
    assert row["comparisonQuality"] == "shared_labels"
    assert row["visualization"]["left"]["values"] == [
        {"value": 13.0, "label": "nominal", "rawText": "13th (nominal)", "confidence": 0.94},
        {"value": 14.0, "label": "PPP", "rawText": "14th (PPP)", "confidence": 0.94},
    ]


def test_normalize_attribute_pair_ignores_invalid_llm_value_refinement():
    def refiner(**_kwargs):
        return [{"label": "bad"}, {"value": "not numeric"}]

    row = normalize_attribute_pair(
        {"id": "left-a", "key": "Exports", "valueText": "exports: $577.4 billion; imports: $457.5 billion (2020 est.)", "source": "infobox", "sourceIds": ["left-info-1"]},
        {"id": "right-a", "key": "Exports", "valueText": "exports: $700 billion; imports: $600 billion (2020 est.)", "source": "infobox", "sourceIds": ["right-info-1"]},
        "Exports",
        value_refiner=refiner,
    )

    assert row["visualization"]["left"]["values"] == [
        {"value": 577400000000.0, "label": "exports", "year": 2020},
        {"value": 457500000000.0, "label": "imports", "year": 2020},
    ]


def test_extract_numeric_values_ignores_dates_and_age_ranges():
    assert extract_numeric_values("1 April – 31 March") == []
    assert extract_numeric_values("$230.6 billion (31 December 2017 est.) Abroad: $344.7 billion (31 December 2017 est.)") == [
        {"value": 230600000000.0, "year": 2017, "label": "Inward"},
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


def test_normalize_attribute_pair_preserves_structured_text_values():
    row = normalize_attribute_pair(
        {
            "id": "left-industries",
            "key": "Main industries",
            "valueText": "Electronics Telecommunications Shipbuilding",
            "structuredValues": [
                {"label": "Electronics", "value": "Electronics", "kind": "list_item"},
                {"label": "Telecommunications", "value": "Telecommunications", "kind": "list_item"},
                {"label": "Shipbuilding", "value": "Shipbuilding", "kind": "list_item"},
            ],
            "source": "infobox",
            "sourceIds": ["left-info-1"],
        },
        {
            "id": "right-industries",
            "key": "Main industries",
            "valueText": "High technology Motor vehicles Electronics Steel",
            "structuredValues": [
                {"label": "High technology", "value": "High technology", "kind": "list_item"},
                {"label": "Motor vehicles", "value": "Motor vehicles", "kind": "list_item"},
                {"label": "Electronics", "value": "Electronics", "kind": "list_item"},
                {"label": "Steel", "value": "Steel", "kind": "list_item"},
            ],
            "source": "infobox",
            "sourceIds": ["right-info-1"],
        },
        "Main industries",
    )

    assert row["dataType"] == "Categorical"
    assert row["chartType"] == "text"
    assert row["comparisonQuality"] == "structured_values"
    assert row["visualization"]["left"]["structuredValues"][0]["value"] == "Electronics"
    assert row["visualization"]["right"]["structuredValues"][2]["value"] == "Electronics"
