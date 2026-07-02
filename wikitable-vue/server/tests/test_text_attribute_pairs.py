from services.text_attribute_pairs import build_text_evidence_candidates


def test_build_text_evidence_candidates_marks_data_roles():
    article = {
        "paragraphs": [
            {
                "id": "left-p-1",
                "section": "History",
                "sentences": [
                    {
                        "id": "left-s-1-1",
                        "text": "The field was founded as an academic discipline in 1956.",
                    },
                    {
                        "id": "left-s-1-2",
                        "text": "Applications include search engines and robotics.",
                    },
                ],
            }
        ]
    }

    candidates = build_text_evidence_candidates(article, "left")

    assert candidates[0]["side"] == "left"
    assert candidates[0]["sentenceIds"] == ["left-s-1-1"]
    assert candidates[0]["kind"] == "data"
    assert candidates[0]["dataItems"][0]["role"] == "emergence_time"
    assert candidates[0]["dataItems"][0]["value"] == 1956
    assert candidates[1]["kind"] == "claim"
    assert candidates[1]["semanticCue"] == "applications"


def test_build_text_evidence_candidates_ignores_noise_years():
    article = {
        "paragraphs": [
            {
                "id": "left-p-1",
                "sentences": [
                    {"id": "left-s-1-1", "text": "Smith published a paper in 2019."},
                    {"id": "left-s-1-2", "text": "The model reached 95% accuracy."},
                ],
            }
        ]
    }

    candidates = build_text_evidence_candidates(article, "left")

    assert [candidate["sentenceIds"] for candidate in candidates] == [["left-s-1-2"]]
    assert candidates[0]["dataItems"][0]["role"] == "proportion"


def test_build_text_evidence_candidates_treats_generated_revenue_as_scale():
    article = {
        "paragraphs": [
            {
                "id": "left-p-1",
                "sentences": [
                    {
                        "id": "left-s-1-1",
                        "text": "The company generated $5 million in revenue.",
                    },
                ],
            }
        ]
    }

    candidates = build_text_evidence_candidates(article, "left")

    assert candidates[0]["dataItems"][0]["role"] == "scale"
    assert candidates[0]["dataItems"][0]["value"] == 5
    assert candidates[0]["dataItems"][0]["unit"] == "million"


def test_build_text_evidence_candidates_keeps_measurements_in_publication_sentences():
    article = {
        "paragraphs": [
            {
                "id": "left-p-1",
                "sentences": [
                    {"id": "left-s-1-1", "text": "A 2020 study reported 42 cases."},
                ],
            }
        ]
    }

    candidates = build_text_evidence_candidates(article, "left")

    assert [item["value"] for item in candidates[0]["dataItems"]] == [42]
    assert candidates[0]["dataItems"][0]["role"] == "quantity"


def test_build_text_evidence_candidates_parses_comma_grouped_numbers_once():
    article = {
        "paragraphs": [
            {
                "id": "left-p-1",
                "sentences": [
                    {"id": "left-s-1-1", "text": "The population reached 1,234,567 users."},
                ],
            }
        ]
    }

    candidates = build_text_evidence_candidates(article, "left")

    assert [item["value"] for item in candidates[0]["dataItems"]] == [1234567]


def test_build_text_evidence_candidates_honors_zero_limit():
    article = {
        "paragraphs": [
            {
                "id": "left-p-1",
                "sentences": [
                    {"id": "left-s-1-1", "text": "The model reached 95% accuracy."},
                ],
            }
        ]
    }

    assert build_text_evidence_candidates(article, "left", limit=0) == []


def test_build_text_evidence_candidates_keeps_year_like_case_counts():
    article = {
        "paragraphs": [
            {
                "id": "left-p-1",
                "sentences": [
                    {"id": "left-s-1-1", "text": "A 2020 study reported 2,019 cases."},
                ],
            }
        ]
    }

    candidates = build_text_evidence_candidates(article, "left")

    assert [item["value"] for item in candidates[0]["dataItems"]] == [2019]
    assert candidates[0]["dataItems"][0]["role"] == "quantity"


def test_build_text_evidence_candidates_keeps_year_like_currency_values():
    article = {
        "paragraphs": [
            {
                "id": "left-p-1",
                "sentences": [
                    {"id": "left-s-1-1", "text": "The journal article reported $2,019 in revenue."},
                ],
            }
        ]
    }

    candidates = build_text_evidence_candidates(article, "left")

    assert [item["value"] for item in candidates[0]["dataItems"]] == [2019]
    assert candidates[0]["dataItems"][0]["role"] == "scale"


def test_build_text_evidence_candidates_classifies_founding_and_quantity_items_locally():
    article = {
        "paragraphs": [
            {
                "id": "left-p-1",
                "sentences": [
                    {
                        "id": "left-s-1-1",
                        "text": "The field was founded in 1956 and had 200 employees.",
                    },
                ],
            }
        ]
    }

    candidates = build_text_evidence_candidates(article, "left")

    assert candidates[0]["dataItems"] == [
        {"value": 1956, "role": "emergence_time"},
        {"value": 200, "role": "quantity"},
    ]


def test_build_text_evidence_candidates_classifies_accuracy_and_sample_items_locally():
    article = {
        "paragraphs": [
            {
                "id": "left-p-1",
                "sentences": [
                    {
                        "id": "left-s-1-1",
                        "text": "The system reached 95% accuracy with 1,000 samples.",
                    },
                ],
            }
        ]
    }

    candidates = build_text_evidence_candidates(article, "left")

    assert candidates[0]["dataItems"] == [
        {"value": 95, "role": "proportion", "unit": "%"},
        {"value": 1000, "role": "quantity"},
    ]


def test_build_text_evidence_candidates_keeps_standalone_employee_measurements():
    article = {
        "paragraphs": [
            {
                "id": "left-p-1",
                "sentences": [
                    {"id": "left-s-1-1", "text": "The company had 200 employees."},
                ],
            }
        ]
    }

    candidates = build_text_evidence_candidates(article, "left")

    assert candidates[0]["dataItems"] == [{"value": 200, "role": "quantity"}]


def test_build_text_evidence_candidates_keeps_standalone_sample_measurements():
    article = {
        "paragraphs": [
            {
                "id": "left-p-1",
                "sentences": [
                    {"id": "left-s-1-1", "text": "The dataset included 1,000 samples."},
                ],
            }
        ]
    }

    candidates = build_text_evidence_candidates(article, "left")

    assert candidates[0]["dataItems"] == [{"value": 1000, "role": "quantity"}]
