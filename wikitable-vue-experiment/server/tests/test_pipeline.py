from services.pipeline import (
    align_attribute_pools,
    choose_chart_type,
    classify_value_rule,
    extract_numeric_values,
    normalize_attribute_pair,
    rank_rows,
    split_mixed_unit_metric_rows,
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
    assert classify_value_rule("Founded: 1998") == "Text"
    assert classify_value_rule("COVID-19") == "Text"
    assert classify_value_rule("SARS-CoV-2") == "Text"


def test_extract_numeric_values_keeps_sales_units_with_market_share():
    values = extract_numeric_values(
        "Sales in 2023 totaled 7.4 million units with a market share of 30.2%."
    )

    assert values == [
        {"value": 7400000.0, "year": 2023, "label": "sales"},
        {"value": 30.2, "year": 2023, "label": "market share"},
    ]


def test_extract_numeric_values_preserves_negative_currency_before_symbol():
    values = extract_numeric_values(
        "Current account balance 2024: -$32.428 billion (2024 est.) "
        "Current account balance 2023: -$31.962 billion (2023 est.) "
        "Current account balance 2022: $13.215 billion (2022 est.)"
    )

    assert values == [
        {"value": -32427999999.999996, "year": 2024},
        {"value": -31962000000.0, "year": 2023},
        {"value": 13215000000.0, "year": 2022},
    ]


def test_extract_numeric_values_labels_space_separated_percentage_components():
    values = extract_numeric_values(
        "Electricity generation sources: fossil fuels 75.5% of total installed capacity "
        "(2023 est.) nuclear 2.7% of total installed capacity (2023 est.) solar 6.6% "
        "of total installed capacity (2023 est.) wind 5.1% of total installed capacity "
        "(2023 est.) hydroelectricity 8.2% of total installed capacity (2023 est.) "
        "biomass and waste 1.9% of total installed capacity (2023 est.)"
    )

    assert values == [
        {"value": 75.5, "label": "fossil fuels", "year": 2023},
        {"value": 2.7, "label": "nuclear", "year": 2023},
        {"value": 6.6, "label": "solar", "year": 2023},
        {"value": 5.1, "label": "wind", "year": 2023},
        {"value": 8.2, "label": "hydroelectricity", "year": 2023},
        {"value": 1.9, "label": "biomass and waste", "year": 2023},
    ]


def test_extract_numeric_values_ignores_date_suffixes_and_demographic_age_ranges():
    values = extract_numeric_values(
        "Mother's mean age at first birth: 21.2 years (2019/21) "
        "note: data represents median age at first birth among women 25-49"
    )

    assert values == [{"value": 21.2, "year": 2019}]


def test_extract_numeric_values_keeps_labeled_income_share_buckets_not_bucket_numbers():
    values = extract_numeric_values(
        "Household income or consumption by percentage share: lowest 10%: 4.5% "
        "(2022 est.) highest 10%: 22.1% (2022 est.) note:% share of income "
        "accruing to lowest and highest 10% of population"
    )

    assert values == [
        {"value": 4.5, "label": "lowest 10%", "year": 2022},
        {"value": 22.1, "label": "highest 10%", "year": 2022},
    ]


def test_extract_numeric_values_labels_openfactbook_named_numeric_lists():
    assert extract_numeric_values(
        "Major rivers (by length in km): Brahmaputra (shared with China and Bangladesh) - "
        "3,969 km; Indus (shared with China and Pakistan) - 3,610 km"
    ) == [
        {"value": 3969.0, "label": "Brahmaputra"},
        {"value": 3610.0, "label": "Indus"},
    ]

    assert extract_numeric_values(
        "Major urban areas - population: 32.941 million NEW DELHI (capital), "
        "21.297 million Mumbai, 15.333 million Kolkata (2023)"
    ) == [
        {"value": 32941000.000000004, "label": "NEW DELHI", "year": 2023},
        {"value": 21297000.0, "label": "Mumbai", "year": 2023},
        {"value": 15333000.0, "label": "Kolkata", "year": 2023},
    ]


def test_extract_numeric_values_labels_ports_and_elevation_submetrics():
    assert extract_numeric_values(
        "Ports: total ports 56 (2024) large 4 medium 4 small 13 very small 30 "
        "size unknown 5 ports with oil terminals 18 key ports Calcutta, Chennai"
    ) == [
        {"value": 56.0, "label": "total ports", "year": 2024},
        {"value": 4.0, "label": "large", "year": 2024},
        {"value": 4.0, "label": "medium", "year": 2024},
        {"value": 13.0, "label": "small", "year": 2024},
        {"value": 30.0, "label": "very small", "year": 2024},
        {"value": 5.0, "label": "size unknown", "year": 2024},
        {"value": 18.0, "label": "ports with oil terminals", "year": 2024},
    ]

    assert extract_numeric_values(
        "Elevation: highest point: Kanchenjunga 8,586 m lowest point: Indian Ocean 0 m "
        "mean elevation: 160 m"
    ) == [
        {"value": 8586.0, "label": "highest point"},
        {"value": 0.0, "label": "lowest point"},
        {"value": 160.0, "label": "mean elevation"},
    ]


def test_extract_numeric_values_ignores_age_context_numbers_in_single_metrics():
    assert extract_numeric_values(
        "Labor force: 607.691 million (2024 est.) note: number of people ages 15 or older "
        "who are employed or seeking work"
    ) == [{"value": 607691000.0, "year": 2024}]

    assert extract_numeric_values(
        "Children under the age of 5 years underweight: 31.5% (2020 est.)"
    ) == [{"value": 31.5, "year": 2020}]


def test_extract_numeric_values_ignores_historical_age_notes_in_area_lists():
    assert extract_numeric_values(
        "Major lakes (area sq km): fresh water lake(s): Danau Toba - 1,150 sq km "
        "note - located in the caldera of a super volcano that erupted more than "
        "70,000 years ago"
    ) == [{"value": 1150.0, "label": "Danau Toba"}]


def test_normalize_attribute_pair_demotes_unstable_narrative_count_fields_to_text():
    for label, left_text, right_text in [
        (
            "Military deployments",
            "Military deployments: 1,100 Democratic Republic of the Congo (MONUSCO); "
            "200 Golan Heights (UNDOF); 900 Lebanon (UNIFIL); 2,400 South Sudan "
            "(UNMISS); 600 Sudan (UNISFA) (2025) note: India has over 6,000 total "
            "military and police personnel deployed on UN missions",
            "Military deployments: 250 (plus about 170 police) Central African Republic "
            "(MINUSCA); 1,025 Democratic Republic of the Congo (MONUSCO); 1,225 "
            "Lebanon (UNIFIL) (2025)",
        ),
        (
            "Administrative divisions",
            "Administrative divisions: 28 states and 8 union territories",
            "Administrative divisions: 35 provinces, 1 autonomous province, 1 special region, "
            "and 1 national capital district",
        ),
    ]:
        row = normalize_attribute_pair(
            {
                "id": f"left-{label}",
                "key": label,
                "valueText": left_text,
                "source": "main_text",
                "sourceIds": ["left-s-1"],
                "dataRole": "quantity",
                "dataPriority": True,
            },
            {
                "id": f"right-{label}",
                "key": label,
                "valueText": right_text,
                "source": "main_text",
                "sourceIds": ["right-s-1"],
                "dataRole": "quantity",
                "dataPriority": True,
            },
            label,
        )

        assert row["chartType"] == "text"
        assert row["visualization"]["left"]["values"] == []
        assert row["visualization"]["right"]["values"] == []


def test_split_mixed_unit_metric_rows_keeps_shared_total_when_components_do_not_match():
    row = normalize_attribute_pair(
        {
            "id": "left-land",
            "key": "Land boundaries",
            "valueText": (
                "Land boundaries: total: 13,888 km border countries: Bangladesh 4,142 km; "
                "Bhutan 659 km; Burma 1,468 km"
            ),
            "source": "main_text",
            "sourceIds": ["left-s-1"],
            "dataRole": "quantity",
            "dataPriority": True,
        },
        {
            "id": "right-land",
            "key": "Land boundaries",
            "valueText": (
                "Land boundaries: total: 2,958 km border countries: Malaysia 1,881 km; "
                "Papua New Guinea 824 km; Timor-Leste 253 km"
            ),
            "source": "main_text",
            "sourceIds": ["right-s-1"],
            "dataRole": "quantity",
            "dataPriority": True,
        },
        "Land boundaries",
    )

    split_rows = split_mixed_unit_metric_rows(row)

    assert len(split_rows) == 1
    assert split_rows[0]["label"] == "Land boundaries: total"
    assert split_rows[0]["visualization"]["left"]["values"] == [{"value": 13888.0, "label": "total"}]
    assert split_rows[0]["visualization"]["right"]["values"] == [{"value": 2958.0, "label": "total"}]


def test_normalize_attribute_pair_demotes_narrative_metadata_counts_to_text():
    row = normalize_attribute_pair(
        {
            "id": "left-broadcast",
            "key": "Broadcast media",
            "valueText": (
                "Broadcast media: Doordarshan operates about 20 services; cable and "
                "satellite TV offer over 850 TV channels; since 2000, privately owned "
                "FM stations have been permitted (2020)"
            ),
            "source": "main_text",
            "sourceIds": ["left-s-1"],
            "dataRole": "quantity",
            "dataPriority": True,
        },
        {
            "id": "right-broadcast",
            "key": "Broadcast media",
            "valueText": (
                "Broadcast media: mix of about a dozen national TV networks, including "
                "1 public broadcaster; more than 100 local TV stations; public radio "
                "broadcaster operates 6 national networks (2019)"
            ),
            "source": "main_text",
            "sourceIds": ["right-s-1"],
            "dataRole": "quantity",
            "dataPriority": True,
        },
        "Broadcast media",
    )

    assert row["chartType"] == "text"
    assert row["visualization"]["left"]["values"] == []
    assert row["visualization"]["right"]["values"] == []


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


def test_align_attribute_pools_deduplicates_exact_key_matches():
    left_pool = [
        {"id": "left-owner-1", "key": "Owner", "valueText": "Jeff Bezos (8.8%)"},
        {"id": "left-owner-2", "key": "Owner", "valueText": "Amazon"},
    ]
    right_pool = [
        {"id": "right-owner-1", "key": "Owner", "valueText": "Walton family (44.8%)"},
    ]

    alignments = align_attribute_pools(left_pool, right_pool)

    assert [(item["left"]["id"], item["right"]["id"], item["label"]) for item in alignments] == [
        ("left-owner-1", "right-owner-1", "Owner")
    ]


def test_align_attribute_pools_matches_repeated_keys_by_value_shape():
    left_pool = [
        {
            "id": "left-age-15-64",
            "key": "15–64 years",
            "valueText": "67.49% (male 472,653,000/female 447,337,000) (2021 est.)",
        },
        {
            "id": "left-sex-15-64",
            "key": "15–64 years",
            "valueText": "1.07 male(s)/female (2023 est.)",
        },
        {
            "id": "left-age-65",
            "key": "65 and over",
            "valueText": "6.83% (male 44,275,000/female 48,751,000) (2021 est.)",
        },
        {
            "id": "left-sex-65",
            "key": "65 and over",
            "valueText": "0.85 male(s)/female (2023)",
        },
    ]
    right_pool = [
        {
            "id": "right-age-15-64",
            "key": "15–64 years",
            "valueText": "69.4% (male 504,637,819/female 476,146,909)",
        },
        {
            "id": "right-sex-15-64",
            "key": "15–64 years",
            "valueText": "1.06 male to female (2024 est.)",
        },
        {
            "id": "right-age-65",
            "key": "65 and over",
            "valueText": "14.11% (male 92,426,805/female 107,035,710) (2023 est.)",
        },
        {
            "id": "right-sex-65",
            "key": "65 and over",
            "valueText": "0.86 male to female (2024 est.)",
        },
    ]

    alignments = align_attribute_pools(left_pool, right_pool)

    assert [(item["left"]["id"], item["right"]["id"], item["label"]) for item in alignments] == [
        ("left-age-15-64", "right-age-15-64", "15–64 years"),
        ("left-sex-15-64", "right-sex-15-64", "15–64 years"),
        ("left-age-65", "right-age-65", "65 and over"),
        ("left-sex-65", "right-sex-65", "65 and over"),
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


def test_normalize_attribute_pair_demotes_emergence_years_to_text_evidence():
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

    assert row["dataPriority"] is False
    assert row["dataRole"] == "emergence_time"
    assert row["comparisonQuestion"] == "When did it emerge?"
    assert row["sourceKind"] == "main_text"
    assert row["dataType"] == "Text"
    assert row["chartType"] == "text"
    assert row["visualization"]["left"]["values"] == []
    assert row["visualization"]["right"]["values"] == []


def test_normalize_attribute_pair_keeps_generic_main_text_claims_as_text_despite_numbers():
    row = normalize_attribute_pair(
        {
            "id": "left-applications",
            "key": "Applications",
            "valueText": "Applications include 12 pilot projects and 3 public deployments.",
            "source": "main_text",
            "sourceIds": ["left-s-1"],
        },
        {
            "id": "right-applications",
            "key": "Applications",
            "valueText": "Applications include 8 pilot projects and 2 public deployments.",
            "source": "main_text",
            "sourceIds": ["right-s-1"],
        },
        "Applications",
    )

    assert row["dataType"] == "Text"
    assert row["chartType"] == "text"
    assert row["dataPriority"] is False
    assert row["visualization"]["left"]["values"] == []
    assert row["visualization"]["right"]["values"] == []


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


def test_rank_rows_does_not_prioritize_emergence_years_as_data_visualization():
    rows = [
        {
            "id": "revenue",
            "label": "Revenue",
            "dataType": "Numerical",
            "chartType": "bar",
            "score": 0.2,
            "sourceKind": "Infobox",
            "visualization": {"left": {"values": [{"value": 100}]}, "right": {"values": [{"value": 120}]}},
        },
        {
            "id": "history",
            "label": "Historical emergence",
            "dataType": "Text",
            "chartType": "text",
            "score": 0.9,
            "sourceKind": "main_text",
            "comparisonQuality": "paired_text",
            "dataPriority": True,
            "dataRole": "emergence_time",
            "visualization": {"left": {"values": []}, "right": {"values": []}},
        },
    ]

    ranked = rank_rows(rows)

    assert [row["label"] for row in ranked] == ["Revenue", "Historical emergence"]


def test_rank_rows_prioritizes_paired_measurement_text_over_generic_text():
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
            "id": "users",
            "label": "Active users",
            "dataType": "Numerical",
            "chartType": "bar",
            "score": 0.4,
            "sourceKind": "main_text",
            "comparisonQuality": "paired_text_data",
            "dataPriority": True,
            "dataRole": "quantity",
            "visualization": {"left": {"values": [{"value": 1000}]}, "right": {"values": [{"value": 2000}]}},
        },
    ]

    ranked = rank_rows(rows)

    assert [row["label"] for row in ranked] == ["Active users", "Overview"]


def test_rank_rows_does_not_prioritize_paired_emergence_even_when_flagged_by_llm():
    rows = [
        {
            "id": "overview",
            "label": "Overview",
            "dataType": "Text",
            "chartType": "text",
            "score": 0.8,
            "sourceKind": "main_text",
            "comparisonQuality": "text",
            "visualization": {"left": {"raw": "A is a concept."}, "right": {"raw": "B is a concept."}},
        },
        {
            "id": "history",
            "label": "Historical emergence",
            "dataType": "Ordinal",
            "chartType": "text",
            "score": 0.1,
            "sourceKind": "main_text",
            "dataPriority": True,
            "dataRole": "emergence_time",
            "visualization": {"left": {"values": [{"value": 1956}]}, "right": {"values": [{"value": 1950}]}},
        },
    ]

    ranked = rank_rows(rows)

    assert [row["label"] for row in ranked] == ["Overview", "Historical emergence"]


def test_rank_rows_does_not_prioritize_generic_text_with_data_priority_flag():
    rows = [
        {
            "id": "revenue",
            "label": "Revenue",
            "dataType": "Numerical",
            "chartType": "bar",
            "score": 0.2,
            "sourceKind": "Infobox",
            "visualization": {"left": {"values": [{"value": 100}]}, "right": {"values": [{"value": 120}]}},
        },
        {
            "id": "overview",
            "label": "Overview",
            "dataType": "Text",
            "chartType": "text",
            "score": 0.9,
            "sourceKind": "main_text",
            "dataPriority": True,
            "comparisonQuality": "text",
            "visualization": {"left": {"raw": "A is a concept."}, "right": {"raw": "B is a concept."}},
        },
    ]

    ranked = rank_rows(rows)

    assert [row["label"] for row in ranked] == ["Revenue", "Overview"]


def test_rank_rows_filters_demoted_main_text_visual_data_candidates():
    rows = [
        {
            "id": "annual-sales",
            "label": "Annual sales",
            "dataType": "Numerical",
            "chartType": "bar",
            "score": 0.8,
            "sourceKind": "main_text",
            "dataPriority": True,
            "dataRole": "quantity",
            "visualization": {"left": {"values": [{"value": 7400000}]}, "right": {"values": [{"value": 1402371}]}},
        },
        {
            "id": "cumulative-sales",
            "label": "Cumulative sales",
            "dataType": "Text",
            "chartType": "text",
            "score": 0.9,
            "sourceKind": "main_text",
            "dataPriority": True,
            "dataRole": "quantity",
            "visualization": {"left": {"values": []}, "right": {"values": []}},
        },
        {
            "id": "overview",
            "label": "Overview",
            "dataType": "Text",
            "chartType": "text",
            "score": 0.7,
            "sourceKind": "main_text",
            "comparisonQuality": "text",
            "visualization": {"left": {"raw": "A is a concept."}, "right": {"raw": "B is a concept."}},
        },
    ]

    ranked = rank_rows(rows)

    assert [row["label"] for row in ranked] == ["Annual sales", "Overview"]


def test_rank_rows_filters_temporal_metadata_text_rows():
    rows = [
        {
            "id": "capacity",
            "label": "Capacity",
            "dataType": "Trend",
            "chartType": "line",
            "score": 0.4,
            "sourceKind": "main_text",
            "visualization": {
                "left": {"values": [{"value": 100, "year": 2020}]},
                "right": {"values": [{"value": 150, "year": 2020}]},
            },
        },
        {
            "id": "founded",
            "label": "Founded",
            "dataType": "Text",
            "chartType": "text",
            "score": 0,
            "sourceKind": "Infobox",
            "visualization": {"left": {"values": []}, "right": {"values": []}},
        },
        {
            "id": "arrival-date",
            "label": "Arrival date",
            "dataType": "Text",
            "chartType": "text",
            "score": 0,
            "sourceKind": "Infobox",
            "visualization": {"left": {"values": []}, "right": {"values": []}},
        },
    ]

    ranked = rank_rows(rows)

    assert [row["label"] for row in ranked] == ["Capacity"]


def test_rank_rows_deduplicates_labels_after_prioritizing_best_row():
    rows = [
        {
            "id": "growth-text",
            "label": "Growth",
            "dataType": "Text",
            "chartType": "text",
            "score": 0,
            "sourceKind": "main_text",
            "visualization": {"left": {"values": []}, "right": {"values": []}},
        },
        {
            "id": "growth-chart",
            "label": "Growth",
            "dataType": "Proportional",
            "chartType": "stacked",
            "score": 0.5,
            "sourceKind": "main_text",
            "visualization": {"left": {"values": [{"value": 6.2}]}, "right": {"values": [{"value": 2.8}]}},
        },
    ]

    ranked = rank_rows(rows)

    assert [row["id"] for row in ranked] == ["growth-chart"]


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


def test_extract_numeric_values_labels_colon_metrics_with_year_estimates():
    values = extract_numeric_values(
        "Broadband - fixed subscriptions: total: 39.3 million (2023 est.) "
        "subscriptions per 100 inhabitants: 2 (2022 est.)"
    )

    assert values == [
        {"value": 39300000.0, "year": 2023, "label": "total"},
        {"value": 2.0, "year": 2022, "label": "subscriptions per 100 inhabitants"},
    ]


def test_normalize_attribute_pair_keeps_mixed_colon_metrics_numerical_not_trend():
    row = normalize_attribute_pair(
        {
            "id": "left-broadband",
            "key": "Broadband - fixed subscriptions",
            "valueText": (
                "Broadband - fixed subscriptions: total: 39.3 million (2023 est.) "
                "subscriptions per 100 inhabitants: 2 (2022 est.)"
            ),
            "source": "main_text",
            "sourceIds": ["left-s-1"],
            "dataRole": "scale",
            "dataPriority": True,
        },
        {
            "id": "right-broadband",
            "key": "Broadband - fixed subscriptions",
            "valueText": (
                "Broadband - fixed subscriptions: total: 13.5 million (2023 est.) "
                "subscriptions per 100 inhabitants: 5 (2023 est.)"
            ),
            "source": "main_text",
            "sourceIds": ["right-s-1"],
            "dataRole": "scale",
            "dataPriority": True,
        },
        "Broadband - fixed subscriptions",
    )

    assert row["dataType"] == "Numerical"
    assert row["comparisonQuality"] == "shared_labels"
    assert row["visualization"]["left"]["values"] == [
        {"value": 39300000.0, "year": 2023, "label": "total"},
        {"value": 2.0, "year": 2022, "label": "subscriptions per 100 inhabitants"},
    ]
    assert row["visualization"]["right"]["values"] == [
        {"value": 13500000.0, "year": 2023, "label": "total"},
        {"value": 5.0, "year": 2023, "label": "subscriptions per 100 inhabitants"},
    ]


def test_split_mixed_unit_metric_rows_separates_total_from_per_capita_rate():
    row = normalize_attribute_pair(
        {
            "id": "left-broadband",
            "key": "Broadband - fixed subscriptions",
            "valueText": (
                "Broadband - fixed subscriptions: total: 39.3 million (2023 est.) "
                "subscriptions per 100 inhabitants: 2 (2022 est.)"
            ),
            "source": "main_text",
            "sourceIds": ["left-s-1"],
            "dataRole": "scale",
            "dataPriority": True,
        },
        {
            "id": "right-broadband",
            "key": "Broadband - fixed subscriptions",
            "valueText": (
                "Broadband - fixed subscriptions: total: 13.5 million (2023 est.) "
                "subscriptions per 100 inhabitants: 5 (2023 est.)"
            ),
            "source": "main_text",
            "sourceIds": ["right-s-1"],
            "dataRole": "scale",
            "dataPriority": True,
        },
        "Broadband - fixed subscriptions",
    )

    split_rows = split_mixed_unit_metric_rows(row)

    assert [item["label"] for item in split_rows] == [
        "Broadband - fixed subscriptions: total",
        "Broadband - fixed subscriptions: subscriptions per 100 inhabitants",
    ]
    assert [item["chartType"] for item in split_rows] == ["bar", "bar"]
    assert split_rows[0]["visualization"]["left"]["values"] == [
        {"value": 39300000.0, "year": 2023, "label": "total"},
    ]
    assert split_rows[0]["visualization"]["right"]["values"] == [
        {"value": 13500000.0, "year": 2023, "label": "total"},
    ]
    assert split_rows[1]["visualization"]["left"]["values"] == [
        {"value": 2.0, "year": 2022, "label": "subscriptions per 100 inhabitants"},
    ]
    assert split_rows[1]["visualization"]["right"]["values"] == [
        {"value": 5.0, "year": 2023, "label": "subscriptions per 100 inhabitants"},
    ]


def test_split_mixed_unit_metric_rows_separates_aggregate_total_from_component_categories():
    row = normalize_attribute_pair(
        {
            "id": "left-alcohol",
            "key": "Alcohol consumption per capita",
            "valueText": (
                "Alcohol consumption per capita: total: 3.09 liters of pure alcohol (2019 est.) "
                "beer: 0.23 liters of pure alcohol (2019 est.) wine: 0 liters of pure alcohol "
                "(2019 est.) spirits: 2.85 liters of pure alcohol (2019 est.) other alcohols: "
                "0 liters of pure alcohol (2019 est.)"
            ),
            "source": "main_text",
            "sourceIds": ["left-s-1"],
            "dataRole": "quantity",
            "dataPriority": True,
            "extractedValues": [
                {"value": 3.09, "year": 2019, "label": "total", "rawText": "3.09 liters of pure alcohol"},
                {"value": 0.23, "year": 2019, "label": "beer", "rawText": "0.23 liters of pure alcohol"},
                {"value": 0, "year": 2019, "label": "wine", "rawText": "0 liters of pure alcohol"},
                {"value": 2.85, "year": 2019, "label": "spirits", "rawText": "2.85 liters of pure alcohol"},
                {"value": 0, "year": 2019, "label": "other alcohols", "rawText": "0 liters of pure alcohol"},
            ],
        },
        {
            "id": "right-alcohol",
            "key": "Alcohol consumption per capita",
            "valueText": (
                "Alcohol consumption per capita: total: 0.08 liters of pure alcohol (2019 est.) "
                "beer: 0.06 liters of pure alcohol (2019 est.) wine: 0.01 liters of pure alcohol "
                "(2019 est.) spirits: 0.02 liters of pure alcohol (2019 est.) other alcohols: "
                "0 liters of pure alcohol (2019 est.)"
            ),
            "source": "main_text",
            "sourceIds": ["right-s-1"],
            "dataRole": "quantity",
            "dataPriority": True,
            "extractedValues": [
                {"value": 0.08, "year": 2019, "label": "total", "rawText": "0.08 liters of pure alcohol"},
                {"value": 0.06, "year": 2019, "label": "beer", "rawText": "0.06 liters of pure alcohol"},
                {"value": 0.01, "year": 2019, "label": "wine", "rawText": "0.01 liters of pure alcohol"},
                {"value": 0.02, "year": 2019, "label": "spirits", "rawText": "0.02 liters of pure alcohol"},
                {"value": 0, "year": 2019, "label": "other alcohols", "rawText": "0 liters of pure alcohol"},
            ],
        },
        "Alcohol consumption per capita",
    )

    split_rows = split_mixed_unit_metric_rows(row)

    assert [item["label"] for item in split_rows] == [
        "Alcohol consumption per capita: total",
        "Alcohol consumption per capita: beverage categories",
    ]
    assert [item["chartType"] for item in split_rows] == ["bar", "bar"]
    assert split_rows[0]["visualization"]["left"]["values"] == [
        {"value": 3.09, "year": 2019, "label": "total", "rawText": "3.09 liters of pure alcohol"},
    ]
    assert split_rows[1]["visualization"]["left"]["values"] == [
        {"value": 0.23, "year": 2019, "label": "beer", "rawText": "0.23 liters of pure alcohol"},
        {"value": 0, "year": 2019, "label": "wine", "rawText": "0 liters of pure alcohol"},
        {"value": 2.85, "year": 2019, "label": "spirits", "rawText": "2.85 liters of pure alcohol"},
        {"value": 0, "year": 2019, "label": "other alcohols", "rawText": "0 liters of pure alcohol"},
    ]
    assert all(
        value["label"] != "total"
        for side in ("left", "right")
        for value in split_rows[1]["visualization"][side]["values"]
    )


def test_split_mixed_unit_metric_rows_treats_base_gdp_label_as_aggregate_total():
    row = normalize_attribute_pair(
        {
            "id": "left-gdp-components",
            "key": "GDP",
            "valueText": "GDP: $1.8 trillion; agriculture: 2.0%; industry: 35.0%; services: 63.0%",
            "source": "main_text",
            "sourceIds": ["left-s-1"],
            "dataRole": "quantity",
            "dataPriority": True,
            "extractedValues": [
                {"value": 1800000000000.0, "label": "GDP", "rawText": "$1.8 trillion"},
                {"value": 2.0, "label": "agriculture", "rawText": "2.0%"},
                {"value": 35.0, "label": "industry", "rawText": "35.0%"},
                {"value": 63.0, "label": "services", "rawText": "63.0%"},
            ],
        },
        {
            "id": "right-gdp-components",
            "key": "GDP",
            "valueText": "GDP: $4.1 trillion; agriculture: 1.6%; industry: 30.0%; services: 68.4%",
            "source": "main_text",
            "sourceIds": ["right-s-1"],
            "dataRole": "quantity",
            "dataPriority": True,
            "extractedValues": [
                {"value": 4100000000000.0, "label": "GDP", "rawText": "$4.1 trillion"},
                {"value": 1.6, "label": "agriculture", "rawText": "1.6%"},
                {"value": 30.0, "label": "industry", "rawText": "30.0%"},
                {"value": 68.4, "label": "services", "rawText": "68.4%"},
            ],
        },
        "GDP",
    )

    split_rows = split_mixed_unit_metric_rows(row)

    assert [item["label"] for item in split_rows] == [
        "GDP: GDP",
        "GDP: component categories",
    ]
    assert split_rows[0]["visualization"]["left"]["values"] == [
        {"value": 1800000000000.0, "label": "GDP", "rawText": "$1.8 trillion"},
    ]
    assert split_rows[1]["visualization"]["left"]["values"] == [
        {"value": 2.0, "label": "agriculture", "rawText": "2.0%"},
        {"value": 35.0, "label": "industry", "rawText": "35.0%"},
        {"value": 63.0, "label": "services", "rawText": "63.0%"},
    ]
    assert all(
        abs(value["value"]) < 1000
        for side in ("left", "right")
        for value in split_rows[1]["visualization"][side]["values"]
    )


def test_rank_rows_preserves_llm_split_total_and_component_rows_with_same_base_label():
    rows = [
        {
            "id": "alcohol-total",
            "label": "Alcohol consumption per capita",
            "dataType": "Numerical",
            "chartType": "bar",
            "source": "main_text",
            "visualization": {
                "left": {
                    "raw": "total: 4.85 liters of pure alcohol",
                    "values": [
                        {"value": 4.85, "label": "total", "rawText": "4.85 liters of pure alcohol"},
                    ],
                },
                "right": {
                    "raw": "total: 0.78 liters of pure alcohol",
                    "values": [
                        {"value": 0.78, "label": "total", "rawText": "0.78 liters of pure alcohol"},
                    ],
                },
            },
        },
        {
            "id": "alcohol-components",
            "label": "Alcohol consumption per capita",
            "dataType": "Numerical",
            "chartType": "bar",
            "source": "main_text",
            "visualization": {
                "left": {
                    "raw": "beer: 1.9 liters wine: 0.1 liters spirits: 2.8 liters",
                    "values": [
                        {"value": 1.9, "label": "beer", "rawText": "1.9 liters of pure alcohol"},
                        {"value": 0.1, "label": "wine", "rawText": "0.1 liters of pure alcohol"},
                        {"value": 2.8, "label": "spirits", "rawText": "2.8 liters of pure alcohol"},
                    ],
                },
                "right": {
                    "raw": "beer: 0.1 liters wine: 0.01 liters spirits: 0.67 liters",
                    "values": [
                        {"value": 0.1, "label": "beer", "rawText": "0.1 liters of pure alcohol"},
                        {"value": 0.01, "label": "wine", "rawText": "0.01 liters of pure alcohol"},
                        {"value": 0.67, "label": "spirits", "rawText": "0.67 liters of pure alcohol"},
                    ],
                },
            },
        },
    ]

    ranked = rank_rows(rows)

    assert {row["label"] for row in ranked} == {
        "Alcohol consumption per capita: total",
        "Alcohol consumption per capita: beverage categories",
    }
    component_row = next(
        row for row in ranked
        if row["label"] == "Alcohol consumption per capita: beverage categories"
    )
    assert [value["label"] for value in component_row["visualization"]["left"]["values"]] == [
        "beer",
        "wine",
        "spirits",
    ]


def test_normalize_attribute_pair_recovers_openfactbook_alcohol_labels_from_raw_when_llm_values_are_unlabeled():
    row = normalize_attribute_pair(
        {
            "id": "left-alcohol",
            "key": "Alcohol consumption per capita",
            "valueText": (
                "Alcohol consumption per capita: total: 3.09 liters of pure alcohol (2019 est.) "
                "beer: 0.23 liters of pure alcohol (2019 est.) wine: 0 liters of pure alcohol "
                "(2019 est.) spirits: 2.85 liters of pure alcohol (2019 est.) other alcohols: "
                "0 liters of pure alcohol (2019 est.)"
            ),
            "source": "main_text",
            "sourceIds": ["left-s-1"],
            "dataRole": "quantity",
            "dataPriority": True,
            "extractedValues": [
                {"value": 3.09},
                {"value": 0.23},
                {"value": 0},
                {"value": 2.85},
            ],
        },
        {
            "id": "right-alcohol",
            "key": "Alcohol consumption per capita",
            "valueText": (
                "Alcohol consumption per capita: total: 0.08 liters of pure alcohol (2019 est.) "
                "beer: 0.06 liters of pure alcohol (2019 est.) wine: 0.01 liters of pure alcohol "
                "(2019 est.) spirits: 0.02 liters of pure alcohol (2019 est.) other alcohols: "
                "0 liters of pure alcohol (2019 est.)"
            ),
            "source": "main_text",
            "sourceIds": ["right-s-1"],
            "dataRole": "quantity",
            "dataPriority": True,
            "extractedValues": [
                {"value": 0.08},
                {"value": 0.06},
                {"value": 0.01},
                {"value": 0.02},
                {"value": 0},
            ],
        },
        "Alcohol consumption per capita",
    )

    split_rows = split_mixed_unit_metric_rows(row)

    assert [item["label"] for item in split_rows] == [
        "Alcohol consumption per capita: total",
        "Alcohol consumption per capita: beverage categories",
    ]
    assert split_rows[0]["visualization"]["left"]["values"] == [
        {"value": 3.09, "year": 2019, "label": "total"},
    ]
    assert split_rows[1]["visualization"]["left"]["values"] == [
        {"value": 0.23, "year": 2019, "label": "beer"},
        {"value": 0.0, "year": 2019, "label": "wine"},
        {"value": 2.85, "year": 2019, "label": "spirits"},
        {"value": 0.0, "year": 2019, "label": "other alcohols"},
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


def test_extract_numeric_values_preserves_prefixed_age_range_categories():
    assert extract_numeric_values(
        "Age structure: 0-14 years: 24.5%; 15-64 years: 68.7%; "
        "65 years and over: 6.8% (2024 est.)"
    ) == [
        {"value": 24.5, "year": 2024, "label": "0-14 years"},
        {"value": 68.7, "year": 2024, "label": "15-64 years"},
        {"value": 6.8, "year": 2024, "label": "65 years and over"},
    ]


def test_extract_numeric_values_labels_openfactbook_alcohol_categories_without_semicolons():
    assert extract_numeric_values(
        "Alcohol consumption per capita: total: 3.09 liters of pure alcohol (2019 est.) "
        "beer: 0.23 liters of pure alcohol (2019 est.) wine: 0 liters of pure alcohol "
        "(2019 est.) spirits: 2.85 liters of pure alcohol (2019 est.) other alcohols: "
        "0 liters of pure alcohol (2019 est.)"
    ) == [
        {"value": 3.09, "year": 2019, "label": "total"},
        {"value": 0.23, "year": 2019, "label": "beer"},
        {"value": 0.0, "year": 2019, "label": "wine"},
        {"value": 2.85, "year": 2019, "label": "spirits"},
        {"value": 0.0, "year": 2019, "label": "other alcohols"},
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
    assert extract_numeric_values("16.15 births/1,000 people (2023 est.)") == [
        {"value": 16.15, "year": 2023}
    ]
    assert extract_numeric_values("8.04 deaths per 1,000 (2025 est.)") == [
        {"value": 8.04, "year": 2025}
    ]
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


def test_normalize_attribute_pair_keeps_gdp_share_year_series_as_trend():
    row = normalize_attribute_pair(
        {
            "id": "left-remit",
            "key": "Remittances",
            "valueText": "Remittances: 2021: 4.8% of GDP; 2022: 5.1% of GDP; 2023: 5.4% of GDP",
            "source": "main_text",
            "sourceIds": ["left-s-1"],
            "dataRole": "quantity",
            "dataPriority": True,
        },
        {
            "id": "right-remit",
            "key": "Remittances",
            "valueText": "Remittances: 2021: 6.2% of GDP; 2022: 6.4% of GDP; 2023: 6.7% of GDP",
            "source": "main_text",
            "sourceIds": ["right-s-1"],
            "dataRole": "quantity",
            "dataPriority": True,
        },
        "Remittances",
    )

    assert row["dataType"] == "Trend"
    assert row["chartType"] == "line"
    assert row["visualization"]["left"]["values"] == [
        {"value": 4.8, "year": 2021, "label": "% of GDP"},
        {"value": 5.1, "year": 2022, "label": "% of GDP"},
        {"value": 5.4, "year": 2023, "label": "% of GDP"},
    ]
    assert row["visualization"]["right"]["values"] == [
        {"value": 6.2, "year": 2021, "label": "% of GDP"},
        {"value": 6.4, "year": 2022, "label": "% of GDP"},
        {"value": 6.7, "year": 2023, "label": "% of GDP"},
    ]


def test_split_mixed_unit_metric_rows_preserves_repeated_unit_labels_in_year_series():
    row = normalize_attribute_pair(
        {
            "id": "left-remit",
            "key": "Remittances",
            "valueText": (
                "Remittances: Remittances 2024: 3.5% of GDP (2024 est.) "
                "Remittances 2023: 3.3% of GDP (2023 est.) "
                "Remittances 2022: 3.3% of GDP (2022 est.) note: personal transfers "
                "and compensation between resident and non-resident individuals/households/entities"
            ),
            "source": "main_text",
            "sourceIds": ["left-s-1"],
            "dataRole": "quantity",
            "dataPriority": True,
        },
        {
            "id": "right-remit",
            "key": "Remittances",
            "valueText": (
                "Remittances: Remittances 2024: 1.1% of GDP (2024 est.) "
                "Remittances 2023: 1.1% of GDP (2023 est.) "
                "Remittances 2022: 1% of GDP (2022 est.) note: personal transfers "
                "and compensation between resident and non-resident individuals/households/entities"
            ),
            "source": "main_text",
            "sourceIds": ["right-s-1"],
            "dataRole": "quantity",
            "dataPriority": True,
        },
        "Remittances",
    )

    split_rows = split_mixed_unit_metric_rows(row)

    assert len(split_rows) == 1
    assert split_rows[0]["dataType"] == "Trend"
    assert split_rows[0]["chartType"] == "line"
    assert split_rows[0]["visualization"]["left"]["values"] == [
        {"value": 3.5, "year": 2024, "label": "% of GDP"},
        {"value": 3.3, "year": 2023, "label": "% of GDP"},
        {"value": 3.3, "year": 2022, "label": "% of GDP"},
    ]
    assert split_rows[0]["visualization"]["right"]["values"] == [
        {"value": 1.1, "year": 2024, "label": "% of GDP"},
        {"value": 1.1, "year": 2023, "label": "% of GDP"},
        {"value": 1.0, "year": 2022, "label": "% of GDP"},
    ]


def test_normalize_attribute_pair_keeps_parenthetical_gdp_share_year_series_complete():
    row = normalize_attribute_pair(
        {
            "id": "left-remit",
            "key": "Remittances",
            "valueText": "Remittances 4.8% of GDP (2021 est.) 5.1% of GDP (2022 est.) 5.4% of GDP (2023 est.)",
            "source": "main_text",
            "sourceIds": ["left-s-1"],
            "dataRole": "quantity",
            "dataPriority": True,
        },
        {
            "id": "right-remit",
            "key": "Remittances",
            "valueText": "Remittances 6.2% of GDP (2021 est.) 6.4% of GDP (2022 est.) 6.7% of GDP (2023 est.)",
            "source": "main_text",
            "sourceIds": ["right-s-1"],
            "dataRole": "quantity",
            "dataPriority": True,
        },
        "Remittances",
    )

    assert row["dataType"] == "Trend"
    assert row["chartType"] == "line"
    assert row["visualization"]["left"]["values"] == [
        {"value": 4.8, "year": 2021, "label": "% of GDP"},
        {"value": 5.1, "year": 2022, "label": "% of GDP"},
        {"value": 5.4, "year": 2023, "label": "% of GDP"},
    ]


def test_normalize_attribute_pair_keeps_contextual_remittances_gdp_share_series_complete():
    row = normalize_attribute_pair(
        {
            "id": "left-remit",
            "key": "Remittances",
            "valueText": "Personal remittances, received (% of GDP) was 4.8 in 2021, 5.1 in 2022, and 5.4 in 2023.",
            "source": "main_text",
            "sourceIds": ["left-s-1"],
            "dataRole": "quantity",
            "dataPriority": True,
        },
        {
            "id": "right-remit",
            "key": "Remittances",
            "valueText": "Personal remittances, received (% of GDP) was 6.2 in 2021, 6.4 in 2022, and 6.7 in 2023.",
            "source": "main_text",
            "sourceIds": ["right-s-1"],
            "dataRole": "quantity",
            "dataPriority": True,
        },
        "Remittances",
    )

    assert row["dataType"] == "Trend"
    assert row["chartType"] == "line"
    assert row["visualization"]["left"]["values"] == [
        {"value": 4.8, "year": 2021, "label": "% of GDP"},
        {"value": 5.1, "year": 2022, "label": "% of GDP"},
        {"value": 5.4, "year": 2023, "label": "% of GDP"},
    ]


def test_normalize_attribute_pair_keeps_true_percentage_parts_as_proportional():
    row = normalize_attribute_pair(
        {
            "id": "left-sector",
            "key": "GDP composition",
            "valueText": "GDP composition: agriculture 1.0%; industry 26.9%; services 71.4% (2022 est.)",
            "source": "main_text",
            "sourceIds": ["left-s-1"],
            "dataRole": "quantity",
            "dataPriority": True,
        },
        {
            "id": "right-sector",
            "key": "GDP composition",
            "valueText": "GDP composition: agriculture 11.4%; industry 30.8%; services 57.8% (2022 est.)",
            "source": "main_text",
            "sourceIds": ["right-s-1"],
            "dataRole": "quantity",
            "dataPriority": True,
        },
        "GDP composition",
    )

    assert row["dataType"] == "Proportional"
    assert row["chartType"] in {"pie", "stacked"}


def test_normalize_attribute_pair_keeps_export_partner_shares_as_bars_not_part_whole():
    row = normalize_attribute_pair(
        {
            "id": "left-export-partners",
            "key": "Exports - partners",
            "valueText": "Exports - partners: United States 55%, China 45% (2024 est.)",
            "source": "main_text",
            "sourceIds": ["left-s-1"],
            "dataRole": "proportion",
            "dataPriority": True,
        },
        {
            "id": "right-export-partners",
            "key": "Exports - partners",
            "valueText": "Exports - partners: China 60%, United States 40% (2024 est.)",
            "source": "main_text",
            "sourceIds": ["right-s-1"],
            "dataRole": "proportion",
            "dataPriority": True,
        },
        "Exports - partners",
    )

    assert row["dataType"] == "Proportional"
    assert row["chartType"] == "bar"


def test_split_mixed_unit_metric_rows_separates_amounts_from_gdp_percentages():
    row = normalize_attribute_pair(
        {
            "id": "left-military",
            "key": "Military expenditures",
            "valueText": (
                "Military expenditures: total: $83.6 billion (2024 est.) "
                "percent of GDP: 2.4% (2024 est.)"
            ),
            "source": "main_text",
            "sourceIds": ["left-s-1"],
            "dataRole": "quantity",
            "dataPriority": True,
        },
        {
            "id": "right-military",
            "key": "Military expenditures",
            "valueText": (
                "Military expenditures: total: $9.9 billion (2024 est.) "
                "percent of GDP: 0.7% (2024 est.)"
            ),
            "source": "main_text",
            "sourceIds": ["right-s-1"],
            "dataRole": "quantity",
            "dataPriority": True,
        },
        "Military expenditures",
    )

    split_rows = split_mixed_unit_metric_rows(row)

    assert [item["label"] for item in split_rows] == [
        "Military expenditures: total",
        "Military expenditures: percent of GDP",
    ]
    assert [item["dataType"] for item in split_rows] == ["Numerical", "Proportional"]
    assert split_rows[0]["visualization"]["left"]["values"] == [
        {"value": 83600000000.0, "label": "total", "year": 2024},
    ]
    assert split_rows[1]["visualization"]["left"]["values"] == [
        {"value": 2.4, "label": "percent of GDP", "year": 2024},
    ]


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

    assert row["dataType"] == "Text"
    assert row["chartType"] == "text"
    assert row["visualization"]["left"]["values"] == []
    assert row["visualization"]["right"]["values"] == []
    assert row["score"] == 0


def test_normalize_attribute_pair_keeps_founded_dates_as_text_metadata():
    row = normalize_attribute_pair(
        {
            "id": "left-founded",
            "key": "Founded",
            "valueText": "July 5, 1994; 32 years ago (1994-07-05), in Bellevue, Washington, U.S.",
            "source": "infobox",
            "sourceIds": ["left-info-1"],
        },
        {
            "id": "right-founded",
            "key": "Founded",
            "valueText": "July 2, 1962; 64 years ago (1962-07-02), in Rogers, Arkansas, U.S.",
            "source": "infobox",
            "sourceIds": ["right-info-1"],
        },
        "Founded",
    )

    assert row["dataType"] == "Text"
    assert row["chartType"] == "text"
    assert row["visualization"]["left"]["values"] == []
    assert row["visualization"]["right"]["values"] == []


def test_normalize_attribute_pair_keeps_date_named_attributes_as_text_metadata():
    row = normalize_attribute_pair(
        {
            "id": "left-opening",
            "key": "Opening date",
            "valueText": "June 12, 2010",
            "source": "infobox",
            "sourceIds": ["left-info-1"],
        },
        {
            "id": "right-opening",
            "key": "Opening date",
            "valueText": "September 3, 2018",
            "source": "infobox",
            "sourceIds": ["right-info-1"],
        },
        "Opening date",
    )

    assert row["dataType"] == "Text"
    assert row["chartType"] == "text"
    assert row["visualization"]["left"]["values"] == []
    assert row["visualization"]["right"]["values"] == []


def test_normalize_attribute_pair_keeps_first_event_dates_as_text_metadata():
    row = normalize_attribute_pair(
        {
            "id": "left-first-flight",
            "key": "First flight",
            "valueText": "July 5, 1994; 32 years ago (1994-07-05)",
            "source": "infobox",
            "sourceIds": ["left-info-1"],
        },
        {
            "id": "right-first-flight",
            "key": "First flight",
            "valueText": "July 2, 1962; 64 years ago (1962-07-02)",
            "source": "infobox",
            "sourceIds": ["right-info-1"],
        },
        "First flight",
    )

    assert row["dataType"] == "Text"
    assert row["chartType"] == "text"
    assert row["visualization"]["left"]["values"] == []
    assert row["visualization"]["right"]["values"] == []


def test_normalize_attribute_pair_keeps_entity_identifier_fields_as_text():
    row = normalize_attribute_pair(
        {
            "id": "left-traded",
            "key": "Traded as",
            "valueText": "Nasdaq: AMZN Nasdaq-100 component S&P 100 component S&P 500 component",
            "source": "infobox",
            "sourceIds": ["left-info-1"],
        },
        {
            "id": "right-traded",
            "key": "Traded as",
            "valueText": "NYSE: WMT S&P 100 component S&P 500 component",
            "source": "infobox",
            "sourceIds": ["right-info-1"],
        },
        "Traded as",
    )

    assert row["dataType"] == "Text"
    assert row["chartType"] == "text"
    assert row["visualization"]["left"]["values"] == []
    assert row["visualization"]["right"]["values"] == []


def test_normalize_attribute_pair_demotes_main_text_data_when_one_side_has_no_values():
    row = normalize_attribute_pair(
        {
            "id": "left-text",
            "key": "Share / rate",
            "valueText": "Amazon was founded as Cadabra by Jeff Bezos.",
            "source": "main_text",
            "sourceIds": ["left-s-1"],
            "dataPriority": True,
            "dataRole": "quantity",
        },
        {
            "id": "right-text",
            "key": "Share / rate",
            "valueText": "The first stock split occurred in May 1971 for $47 per share.",
            "source": "main_text",
            "sourceIds": ["right-s-1"],
            "dataPriority": True,
            "dataRole": "quantity",
        },
        "Share / rate",
    )

    assert row["dataType"] == "Text"
    assert row["chartType"] == "text"
    assert row["visualization"]["left"]["values"] == []
    assert row["visualization"]["right"]["values"] == []


def test_normalize_attribute_pair_demotes_single_point_main_text_data_with_mismatched_years():
    row = normalize_attribute_pair(
        {
            "id": "left-cumulative-sales",
            "key": "Cumulative sales",
            "valueText": "cumulative sales in 2016 totaled 500,000 units",
            "source": "main_text",
            "sourceIds": ["left-s-1"],
            "dataPriority": True,
            "dataRole": "quantity",
        },
        {
            "id": "right-cumulative-sales",
            "key": "Cumulative sales",
            "valueText": "cumulative sales in 2023 totaled 4.7 million units",
            "source": "main_text",
            "sourceIds": ["right-s-1"],
            "dataPriority": True,
            "dataRole": "quantity",
        },
        "Cumulative sales",
    )

    assert row["dataType"] == "Text"
    assert row["chartType"] == "text"
    assert row["visualization"]["left"]["values"] == []
    assert row["visualization"]["right"]["values"] == []


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


def test_import_partner_percentages_are_completed_for_pie_charts():
    row = normalize_attribute_pair(
        {
            "id": "left-import-partners",
            "key": "Main import partners",
            "valueText": "Main import partners: China 24.6% Hong Kong 5.1% United States 18.7% ASEAN 16.7% European Union 10.0% Taiwan 5.0% Japan 4.3% (2024)",
            "source": "infobox",
            "sourceIds": ["left-info-27"],
        },
        {
            "id": "right-import-partners",
            "key": "Main import partners",
            "valueText": "Main import partners: China 25.8% United States 10.9% Australia 9.1% Taiwan 8.6% South Korea 7.8% ASEAN 15.8% European Union 9.1% (2023)",
            "source": "infobox",
            "sourceIds": ["right-info-27"],
        },
        "Main import partners",
    )

    assert row["dataType"] == "Proportional"
    assert row["chartType"] == "pie"
    assert row["visualization"]["left"]["values"][-1]["label"] == "Other"
    assert row["visualization"]["right"]["values"][-1]["label"] == "Other"
    assert round(sum(item["value"] for item in row["visualization"]["left"]["values"]), 1) == 100.0
    assert round(sum(item["value"] for item in row["visualization"]["right"]["values"]), 1) == 100.0


def test_single_metric_main_text_debt_values_remain_chartable():
    row = normalize_attribute_pair(
        {
            "id": "left-debt",
            "key": "Gross external debt",
            "valueText": "Gross external debt: $620.9 billion (2023 est.)",
            "source": "main_text",
            "sourceIds": ["left-s-1"],
        },
        {
            "id": "right-debt",
            "key": "Gross external debt",
            "valueText": "Gross external debt: $420.8 billion (2023 est.)",
            "source": "main_text",
            "sourceIds": ["right-s-1"],
        },
        "Gross external debt",
    )

    assert row["dataType"] == "Numerical"
    assert row["chartType"] == "bar"
    assert row["visualization"]["left"]["values"] == [{"value": 620900000000.0, "year": 2023}]
    assert row["visualization"]["right"]["values"] == [{"value": 420800000000.0, "year": 2023}]
