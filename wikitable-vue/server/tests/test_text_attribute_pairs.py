from services.text_attribute_pairs import (
    build_paired_text_attributes,
    build_rule_paired_text_attributes,
    build_text_evidence_candidates,
)


def _data_items_for_text(text):
    article = {
        "paragraphs": [
            {
                "id": "left-p-1",
                "sentences": [
                    {"id": "left-s-1-1", "text": text},
                ],
            }
        ]
    }

    candidates = build_text_evidence_candidates(article, "left")

    return [item for candidate in candidates for item in candidate["dataItems"]]


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


def test_build_text_evidence_candidates_samples_late_article_evidence_when_limited():
    article = {
        "paragraphs": [
            {
                "id": f"left-p-{index}",
                "sentences": [
                    {
                        "id": f"left-s-{index}-1",
                        "text": f"Revenue was ${index} million in 2024.",
                    }
                ],
            }
            for index in range(1, 41)
        ]
    }

    candidates = build_text_evidence_candidates(article, "left", limit=8)

    sentence_ids = [candidate["sentenceIds"][0] for candidate in candidates]
    assert len(candidates) == 8
    assert sentence_ids[0] == "left-s-1-1"
    assert sentence_ids[-1] == "left-s-40-1"


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


def test_build_text_evidence_candidates_ignores_calendar_days_and_ages():
    article = {
        "paragraphs": [
            {
                "id": "left-p-1",
                "sentences": [
                    {
                        "id": "left-s-1-1",
                        "text": (
                            "On 9 February, officials said the country would only have a handful "
                            "of cases. On 13 February, the first death involved a 69-year-old man."
                        ),
                    },
                    {
                        "id": "left-s-1-2",
                        "text": "As of 17 March 2023, the country has 141,988 active cases.",
                    },
                ],
            }
        ]
    }

    candidates = build_text_evidence_candidates(article, "left")

    assert [candidate["sentenceIds"] for candidate in candidates] == [["left-s-1-2"]]
    assert candidates[0]["dataItems"][-1]["value"] == 141988
    assert candidates[0]["dataItems"][-1]["role"] == "quantity"


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


def test_rule_paired_emergence_years_are_not_data_priority():
    left_article = {
        "paragraphs": [
            {
                "id": "left-p-1",
                "sentences": [
                    {
                        "id": "left-s-1-1",
                        "text": "Artificial intelligence was founded as an academic discipline in 1956.",
                    }
                ],
            }
        ]
    }
    right_article = {
        "paragraphs": [
            {
                "id": "right-p-1",
                "sentences": [
                    {
                        "id": "right-s-1-1",
                        "text": "Machine learning emerged from pattern recognition in 1959.",
                    }
                ],
            }
        ]
    }

    left_attrs, right_attrs, alignments = build_rule_paired_text_attributes(left_article, right_article, [], [])

    assert [alignment["label"] for alignment in alignments] == ["Historical emergence"]
    assert left_attrs[0]["dataPriority"] is False
    assert right_attrs[0]["dataPriority"] is False
    assert left_attrs[0]["dataRole"] == "emergence_time"
    assert right_attrs[0]["dataRole"] == "emergence_time"


def test_build_rule_paired_text_attributes_keeps_late_unique_measurements_after_many_early_candidates():
    left_article = {
        "paragraphs": [
            {
                "id": f"left-p-{index}",
                "sentences": [
                    {
                        "id": f"left-s-{index}-1",
                        "text": f"Revenue was ${index} million in 2024.",
                    }
                ],
            }
            for index in range(1, 31)
        ]
        + [
            {
                "id": "left-p-31",
                "sentences": [
                    {
                        "id": "left-s-31-1",
                        "text": "Net income was $18 million in 2024.",
                    }
                ],
            }
        ]
    }
    right_article = {
        "paragraphs": [
            {
                "id": f"right-p-{index}",
                "sentences": [
                    {
                        "id": f"right-s-{index}-1",
                        "text": f"Revenue was ${index + 1} million in 2024.",
                    }
                ],
            }
            for index in range(1, 31)
        ]
        + [
            {
                "id": "right-p-31",
                "sentences": [
                    {
                        "id": "right-s-31-1",
                        "text": "Net income was $4 million in 2024.",
                    }
                ],
            }
        ]
    }

    _left_attrs, _right_attrs, alignments = build_rule_paired_text_attributes(
        left_article,
        right_article,
        [],
        [],
    )

    labels = [alignment["label"] for alignment in alignments]
    assert "Revenue" in labels
    assert "Net income" in labels


def test_build_rule_paired_text_attributes_extracts_development_report_prose_metrics():
    left_article = {
        "paragraphs": [
            {
                "id": "left-p-1",
                "sentences": [
                    {
                        "id": "left-s-1-1",
                        "text": "To become a high-income economy by 2047, India will need to sustain an average annual growth rate of 7.8 percent.",
                    }
                ],
            },
            {
                "id": "left-p-2",
                "sentences": [
                    {
                        "id": "left-s-2-1",
                        "text": "GDP growth is estimated at 6.5 percent in FY24-25.",
                    }
                ],
            },
            {
                "id": "left-p-3",
                "sentences": [
                    {
                        "id": "left-s-3-1",
                        "text": "Extreme poverty declined to 2.3 percent in 2022-23.",
                    }
                ],
            },
        ]
    }
    right_article = {
        "paragraphs": [
            {
                "id": "right-p-1",
                "sentences": [
                    {
                        "id": "right-s-1-1",
                        "text": "The Government of Indonesia aims to grow at the brisk annual rate of 6 percent to reach high-income status by 2045.",
                    }
                ],
            },
            {
                "id": "right-p-2",
                "sentences": [
                    {
                        "id": "right-s-2-1",
                        "text": "Indonesia’s economy grew by 5 percent in the first half of 2025.",
                    }
                ],
            },
            {
                "id": "right-p-3",
                "sentences": [
                    {
                        "id": "right-s-3-1",
                        "text": "As of March 2025, the official poverty rate stood at 8.5 percent.",
                    }
                ],
            },
        ]
    }

    _left_attrs, _right_attrs, alignments = build_rule_paired_text_attributes(
        left_article,
        right_article,
        [],
        [],
    )

    labels = [alignment["label"] for alignment in alignments]
    assert labels == ["Annual growth target", "Economic growth", "Poverty rate"]


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


def test_build_text_evidence_candidates_ignores_publication_year_before_reported_cases():
    article = {
        "paragraphs": [
            {
                "id": "left-p-1",
                "sentences": [
                    {"id": "left-s-1-1", "text": "A study in 2020 reported 42 cases."},
                ],
            }
        ]
    }

    candidates = build_text_evidence_candidates(article, "left")

    assert candidates[0]["dataItems"] == [{"value": 42, "role": "quantity"}]


def test_build_text_evidence_candidates_ignores_publication_year_before_reported_samples():
    article = {
        "paragraphs": [
            {
                "id": "left-p-1",
                "sentences": [
                    {"id": "left-s-1-1", "text": "A paper from 2019 reported 1,000 samples."},
                ],
            }
        ]
    }

    candidates = build_text_evidence_candidates(article, "left")

    assert candidates[0]["dataItems"] == [{"value": 1000, "role": "quantity"}]


def test_build_text_evidence_candidates_isolates_introduced_year_from_later_accuracy():
    article = {
        "paragraphs": [
            {
                "id": "left-p-1",
                "sentences": [
                    {
                        "id": "left-s-1-1",
                        "text": "The model introduced in 2019 reached 95% accuracy.",
                    },
                ],
            }
        ]
    }

    candidates = build_text_evidence_candidates(article, "left")

    assert candidates[0]["dataItems"] == [
        {"value": 2019, "role": "emergence_time"},
        {"value": 95, "role": "proportion", "unit": "%"},
    ]


def test_build_text_evidence_candidates_ignores_rate_substrings_for_proportion():
    article = {
        "paragraphs": [
            {
                "id": "left-p-1",
                "sentences": [
                    {"id": "left-s-1-1", "text": "The ratepayer group had 200 members."},
                ],
            }
        ]
    }

    candidates = build_text_evidence_candidates(article, "left")

    assert candidates[0]["dataItems"] == [{"value": 200, "role": "quantity"}]


def test_build_text_evidence_candidates_keeps_journal_founding_years():
    article = {
        "paragraphs": [
            {
                "id": "left-p-1",
                "sentences": [
                    {"id": "left-s-1-1", "text": "The journal was founded in 1880."},
                ],
            }
        ]
    }

    candidates = build_text_evidence_candidates(article, "left")

    assert candidates[0]["dataItems"] == [{"value": 1880, "role": "emergence_time"}]


def test_build_text_evidence_candidates_keeps_conference_launch_years():
    article = {
        "paragraphs": [
            {
                "id": "left-p-1",
                "sentences": [
                    {"id": "left-s-1-1", "text": "The conference was launched in 1995."},
                ],
            }
        ]
    }

    candidates = build_text_evidence_candidates(article, "left")

    assert candidates[0]["dataItems"] == [{"value": 1995, "role": "emergence_time"}]


def test_build_text_evidence_candidates_classifies_non_percent_accuracy_scores_locally():
    article = {
        "paragraphs": [
            {
                "id": "left-p-1",
                "sentences": [
                    {
                        "id": "left-s-1-1",
                        "text": "The model introduced in 2019 reached an accuracy score of 95.",
                    },
                ],
            }
        ]
    }

    candidates = build_text_evidence_candidates(article, "left")

    assert candidates[0]["dataItems"] == [
        {"value": 2019, "role": "emergence_time"},
        {"value": 95, "role": "proportion"},
    ]


def test_build_text_evidence_candidates_ignores_leading_publication_years():
    article = {
        "paragraphs": [
            {
                "id": "left-p-1",
                "sentences": [
                    {"id": "left-s-1-1", "text": "In 2020, the study reported 42 cases."},
                ],
            }
        ]
    }

    candidates = build_text_evidence_candidates(article, "left")

    assert candidates[0]["dataItems"] == [{"value": 42, "role": "quantity"}]


def test_build_text_evidence_candidates_ignores_published_in_year_before_reported_cases():
    article = {
        "paragraphs": [
            {
                "id": "left-p-1",
                "sentences": [
                    {"id": "left-s-1-1", "text": "A paper published in 2019 reported 42 cases."},
                ],
            }
        ]
    }

    candidates = build_text_evidence_candidates(article, "left")

    assert candidates[0]["dataItems"] == [{"value": 42, "role": "quantity"}]


def test_build_text_evidence_candidates_ignores_adjectival_publication_years():
    article = {
        "paragraphs": [
            {
                "id": "left-p-1",
                "sentences": [
                    {"id": "left-s-1-1", "text": "A 2020 clinical study reported 42 cases."},
                ],
            }
        ]
    }

    candidates = build_text_evidence_candidates(article, "left")

    assert candidates[0]["dataItems"] == [{"value": 42, "role": "quantity"}]


def test_build_text_evidence_candidates_ignores_measurement_descriptor_publication_years():
    assert _data_items_for_text("A 2020 population study reported 42 cases.") == [
        {"value": 42, "role": "quantity"}
    ]


def test_build_text_evidence_candidates_ignores_revenue_descriptor_publication_years():
    assert _data_items_for_text("A 2020 revenue study reported $42 million.") == [
        {"value": 42, "role": "scale", "unit": "million"}
    ]


def test_build_text_evidence_candidates_ignores_publication_year_when_study_introduces_method():
    assert _data_items_for_text("A 2020 clinical study introduced a method with 42 cases.") == [
        {"value": 42, "role": "quantity"}
    ]


def test_build_text_evidence_candidates_ignores_leading_publication_year_when_study_introduces_method():
    assert _data_items_for_text("In 2020, the study introduced a method with 42 cases.") == [
        {"value": 42, "role": "quantity"}
    ]


def test_build_text_evidence_candidates_ignores_conducted_in_publication_years():
    article = {
        "paragraphs": [
            {
                "id": "left-p-1",
                "sentences": [
                    {"id": "left-s-1-1", "text": "A study conducted in 2020 reported 42 cases."},
                ],
            }
        ]
    }

    candidates = build_text_evidence_candidates(article, "left")

    assert candidates[0]["dataItems"] == [{"value": 42, "role": "quantity"}]


def test_build_text_evidence_candidates_classifies_direct_accuracy_values_locally():
    article = {
        "paragraphs": [
            {
                "id": "left-p-1",
                "sentences": [
                    {"id": "left-s-1-1", "text": "The model introduced in 2019 reached accuracy 95."},
                ],
            }
        ]
    }

    candidates = build_text_evidence_candidates(article, "left")

    assert candidates[0]["dataItems"] == [
        {"value": 2019, "role": "emergence_time"},
        {"value": 95, "role": "proportion"},
    ]


def test_build_text_evidence_candidates_classifies_direct_accuracy_score_values_locally():
    article = {
        "paragraphs": [
            {
                "id": "left-p-1",
                "sentences": [
                    {"id": "left-s-1-1", "text": "The model introduced in 2019 reached accuracy score 95."},
                ],
            }
        ]
    }

    candidates = build_text_evidence_candidates(article, "left")

    assert candidates[0]["dataItems"] == [
        {"value": 2019, "role": "emergence_time"},
        {"value": 95, "role": "proportion"},
    ]


def test_build_text_evidence_candidates_keeps_confirmed_case_counts_after_publication_years():
    article = {
        "paragraphs": [
            {
                "id": "left-p-1",
                "sentences": [
                    {"id": "left-s-1-1", "text": "A 2020 study reported 2,019 confirmed cases."},
                ],
            }
        ]
    }

    candidates = build_text_evidence_candidates(article, "left")

    assert candidates[0]["dataItems"] == [{"value": 2019, "role": "quantity"}]


def test_build_text_evidence_candidates_keeps_total_case_counts_after_publication_years():
    article = {
        "paragraphs": [
            {
                "id": "left-p-1",
                "sentences": [
                    {"id": "left-s-1-1", "text": "A 2020 study reported 2,019 total cases."},
                ],
            }
        ]
    }

    candidates = build_text_evidence_candidates(article, "left")

    assert candidates[0]["dataItems"] == [{"value": 2019, "role": "quantity"}]


def test_build_text_evidence_candidates_keeps_user_counts_after_introduced_years():
    article = {
        "paragraphs": [
            {
                "id": "left-p-1",
                "sentences": [
                    {"id": "left-s-1-1", "text": "The service introduced in 2019 reached 200 users."},
                ],
            }
        ]
    }

    candidates = build_text_evidence_candidates(article, "left")

    assert candidates[0]["dataItems"] == [
        {"value": 2019, "role": "emergence_time"},
        {"value": 200, "role": "quantity"},
    ]


def test_build_text_evidence_candidates_keeps_rank_values_after_introduced_years():
    article = {
        "paragraphs": [
            {
                "id": "left-p-1",
                "sentences": [
                    {"id": "left-s-1-1", "text": "The model introduced in 2019 reached rank 1."},
                ],
            }
        ]
    }

    candidates = build_text_evidence_candidates(article, "left")

    assert candidates[0]["dataItems"] == [
        {"value": 2019, "role": "emergence_time"},
        {"value": 1, "role": "ranking"},
    ]


def test_build_text_evidence_candidates_keeps_later_decline_year_after_publication_year():
    article = {
        "paragraphs": [
            {
                "id": "left-p-1",
                "sentences": [
                    {"id": "left-s-1-1", "text": "A 2020 clinical study found cases declined in 2019."},
                ],
            }
        ]
    }

    candidates = build_text_evidence_candidates(article, "left")

    assert candidates[0]["dataItems"] == [{"value": 2019, "role": "quantity"}]


def test_build_text_evidence_candidates_keeps_leading_journal_founding_years():
    assert _data_items_for_text("In 1880, the journal was founded.") == [
        {"value": 1880, "role": "emergence_time"}
    ]


def test_build_text_evidence_candidates_keeps_leading_conference_launch_years():
    assert _data_items_for_text("In 1995, the conference was launched.") == [
        {"value": 1995, "role": "emergence_time"}
    ]


def test_build_text_evidence_candidates_classifies_introduced_feature_counts_as_quantity():
    article = {
        "paragraphs": [
            {
                "id": "left-p-1",
                "sentences": [
                    {"id": "left-s-1-1", "text": "The release introduced 200 features."},
                ],
            }
        ]
    }

    candidates = build_text_evidence_candidates(article, "left")

    assert candidates[0]["dataItems"] == [{"value": 200, "role": "quantity"}]


def test_build_text_evidence_candidates_classifies_introduced_model_counts_as_quantity():
    article = {
        "paragraphs": [
            {
                "id": "left-p-1",
                "sentences": [
                    {"id": "left-s-1-1", "text": "The model introduced 2 models in 2019."},
                ],
            }
        ]
    }

    candidates = build_text_evidence_candidates(article, "left")

    assert candidates[0]["dataItems"] == [
        {"value": 2, "role": "quantity"},
        {"value": 2019, "role": "emergence_time"},
    ]


def test_build_text_evidence_candidates_classifies_active_user_counts_as_quantity():
    article = {
        "paragraphs": [
            {
                "id": "left-p-1",
                "sentences": [
                    {"id": "left-s-1-1", "text": "The service introduced 2,019 active users."},
                ],
            }
        ]
    }

    candidates = build_text_evidence_candidates(article, "left")

    assert candidates[0]["dataItems"] == [{"value": 2019, "role": "quantity"}]


def test_build_text_evidence_candidates_classifies_monthly_active_user_counts_as_quantity():
    article = {
        "paragraphs": [
            {
                "id": "left-p-1",
                "sentences": [
                    {"id": "left-s-1-1", "text": "The service introduced 2,019 monthly active users."},
                ],
            }
        ]
    }

    candidates = build_text_evidence_candidates(article, "left")

    assert candidates[0]["dataItems"] == [{"value": 2019, "role": "quantity"}]


def test_build_text_evidence_candidates_classifies_new_feature_counts_as_quantity():
    article = {
        "paragraphs": [
            {
                "id": "left-p-1",
                "sentences": [
                    {"id": "left-s-1-1", "text": "The release introduced 2,019 new features."},
                ],
            }
        ]
    }

    candidates = build_text_evidence_candidates(article, "left")

    assert candidates[0]["dataItems"] == [{"value": 2019, "role": "quantity"}]


def test_build_text_evidence_candidates_classifies_trained_model_counts_as_quantity():
    article = {
        "paragraphs": [
            {
                "id": "left-p-1",
                "sentences": [
                    {"id": "left-s-1-1", "text": "The system introduced 2,019 trained models."},
                ],
            }
        ]
    }

    candidates = build_text_evidence_candidates(article, "left")

    assert candidates[0]["dataItems"] == [{"value": 2019, "role": "quantity"}]


def test_build_text_evidence_candidates_keeps_leading_year_before_new_features_as_emergence():
    article = {
        "paragraphs": [
            {
                "id": "left-p-1",
                "sentences": [
                    {"id": "left-s-1-1", "text": "In 2019 new features were introduced."},
                ],
            }
        ]
    }

    candidates = build_text_evidence_candidates(article, "left")

    assert candidates[0]["dataItems"] == [{"value": 2019, "role": "emergence_time"}]


def test_build_text_evidence_candidates_keeps_leading_year_before_active_users_as_temporal():
    article = {
        "paragraphs": [
            {
                "id": "left-p-1",
                "sentences": [
                    {"id": "left-s-1-1", "text": "In 2019 active users grew to 2 million."},
                ],
            }
        ]
    }

    candidates = build_text_evidence_candidates(article, "left")

    assert candidates[0]["dataItems"] == [
        {"value": 2019, "role": "emergence_time"},
        {"value": 2, "role": "scale", "unit": "million"},
    ]


def test_build_text_evidence_candidates_keeps_comma_grouped_leading_case_counts_as_quantity():
    article = {
        "paragraphs": [
            {
                "id": "left-p-1",
                "sentences": [
                    {"id": "left-s-1-1", "text": "In 2,019 cases, the rate was 5%."},
                ],
            }
        ]
    }

    candidates = build_text_evidence_candidates(article, "left")

    assert candidates[0]["dataItems"] == [
        {"value": 2019, "role": "quantity"},
        {"value": 5, "role": "proportion", "unit": "%"},
    ]


def test_build_text_evidence_candidates_keeps_comma_grouped_leading_active_users_as_quantity():
    article = {
        "paragraphs": [
            {
                "id": "left-p-1",
                "sentences": [
                    {"id": "left-s-1-1", "text": "In 2,019 active users, engagement increased by 5%."},
                ],
            }
        ]
    }

    candidates = build_text_evidence_candidates(article, "left")

    assert candidates[0]["dataItems"] == [
        {"value": 2019, "role": "quantity"},
        {"value": 5, "role": "proportion", "unit": "%"},
    ]


def test_build_text_evidence_candidates_keeps_comma_grouped_participants_as_quantity():
    article = {
        "paragraphs": [
            {
                "id": "left-p-1",
                "sentences": [
                    {"id": "left-s-1-1", "text": "A study from 2,019 participants reported 95% accuracy."},
                ],
            }
        ]
    }

    candidates = build_text_evidence_candidates(article, "left")

    assert candidates[0]["dataItems"] == [
        {"value": 2019, "role": "quantity"},
        {"value": 95, "role": "proportion", "unit": "%"},
    ]


def test_build_text_evidence_candidates_ignores_hyphenated_model_token_numbers():
    article = {
        "paragraphs": [
            {
                "id": "left-p-1",
                "sentences": [
                    {"id": "left-s-1-1", "text": "GPT-4 reached 95% accuracy."},
                ],
            }
        ]
    }

    candidates = build_text_evidence_candidates(article, "left")

    assert candidates[0]["dataItems"] == [{"value": 95, "role": "proportion", "unit": "%"}]


def test_build_text_evidence_candidates_ignores_alphanumeric_token_numbers():
    article = {
        "paragraphs": [
            {
                "id": "left-p-1",
                "sentences": [
                    {"id": "left-s-1-1", "text": "XGBoost2 reached 95% accuracy."},
                ],
            }
        ]
    }

    candidates = build_text_evidence_candidates(article, "left")

    assert candidates[0]["dataItems"] == [{"value": 95, "role": "proportion", "unit": "%"}]


def test_build_text_evidence_candidates_ignores_score_name_digits():
    article = {
        "paragraphs": [
            {
                "id": "left-p-1",
                "sentences": [
                    {"id": "left-s-1-1", "text": "F1 score of 95 was reported."},
                ],
            }
        ]
    }

    candidates = build_text_evidence_candidates(article, "left")

    assert candidates[0]["dataItems"] == [{"value": 95, "role": "proportion"}]


def test_build_text_evidence_candidates_keeps_first_place_ordinals_as_rankings():
    article = {
        "paragraphs": [
            {
                "id": "left-p-1",
                "sentences": [
                    {"id": "left-s-1-1", "text": "The model ranked 1st in accuracy."},
                ],
            }
        ]
    }

    candidates = build_text_evidence_candidates(article, "left")

    assert candidates[0]["dataItems"] == [{"value": 1, "role": "ranking"}]


def test_build_text_evidence_candidates_keeps_second_place_ordinals_as_rankings():
    article = {
        "paragraphs": [
            {
                "id": "left-p-1",
                "sentences": [
                    {"id": "left-s-1-1", "text": "The system ranked 2nd overall."},
                ],
            }
        ]
    }

    candidates = build_text_evidence_candidates(article, "left")

    assert candidates[0]["dataItems"] == [{"value": 2, "role": "ranking"}]


def test_build_text_evidence_candidates_keeps_cardinal_ranked_values_as_rankings():
    article = {
        "paragraphs": [
            {
                "id": "left-p-1",
                "sentences": [
                    {"id": "left-s-1-1", "text": "The model ranked 1."},
                ],
            }
        ]
    }

    candidates = build_text_evidence_candidates(article, "left")

    assert candidates[0]["dataItems"] == [{"value": 1, "role": "ranking"}]


def test_build_text_evidence_candidates_keeps_cardinal_placed_values_as_rankings():
    article = {
        "paragraphs": [
            {
                "id": "left-p-1",
                "sentences": [
                    {"id": "left-s-1-1", "text": "The system placed 2."},
                ],
            }
        ]
    }

    candidates = build_text_evidence_candidates(article, "left")

    assert candidates[0]["dataItems"] == [{"value": 2, "role": "ranking"}]


def test_build_text_evidence_candidates_keeps_hash_marked_cardinal_rankings():
    assert _data_items_for_text("The model ranked #1.") == [{"value": 1, "role": "ranking"}]


def test_build_text_evidence_candidates_keeps_cardinal_rankings_before_accuracy_context():
    assert _data_items_for_text("The model ranked 1 in accuracy.") == [{"value": 1, "role": "ranking"}]


def test_build_text_evidence_candidates_keeps_cardinal_rankings_before_among_context():
    assert _data_items_for_text("The model ranked 1 among baselines.") == [{"value": 1, "role": "ranking"}]


def test_build_text_evidence_candidates_keeps_cardinal_placements_before_contest_context():
    assert _data_items_for_text("The model placed 2 in the contest.") == [{"value": 2, "role": "ranking"}]


def test_build_text_evidence_candidates_keeps_rankings_with_out_of_denominators():
    assert _data_items_for_text("The model ranked 1 out of 10 teams.") == [{"value": 1, "role": "ranking"}]


def test_build_text_evidence_candidates_keeps_rankings_with_of_denominators():
    assert _data_items_for_text("The model ranked 1 of 10 teams.") == [{"value": 1, "role": "ranking"}]


def test_build_text_evidence_candidates_keeps_placements_with_out_of_denominators():
    assert _data_items_for_text("The model placed 2 out of 20 contestants.") == [{"value": 2, "role": "ranking"}]


def test_build_text_evidence_candidates_classifies_placed_job_counts_as_quantity():
    assert _data_items_for_text("The program placed 2,000 in jobs.") == [{"value": 2000, "role": "quantity"}]


def test_build_text_evidence_candidates_classifies_placed_service_counts_as_quantity():
    assert _data_items_for_text("The airline placed 2 in service.") == [{"value": 2, "role": "quantity"}]


def test_build_text_evidence_candidates_classifies_placed_training_counts_as_quantity():
    assert _data_items_for_text("The company placed 200 in training.") == [{"value": 200, "role": "quantity"}]


def test_build_text_evidence_candidates_classifies_ranked_algorithm_counts_as_quantity():
    assert _data_items_for_text("The study ranked 10 algorithms.") == [{"value": 10, "role": "quantity"}]


def test_build_text_evidence_candidates_classifies_placed_employee_counts_as_quantity():
    assert _data_items_for_text("The company placed 2,000 employees on leave.") == [
        {"value": 2000, "role": "quantity"}
    ]


def test_build_text_evidence_candidates_classifies_placed_model_counts_as_quantity():
    assert _data_items_for_text("The system placed 2 models into production.") == [{"value": 2, "role": "quantity"}]


def test_build_text_evidence_candidates_ignores_century_ordinals_as_rankings():
    assert _data_items_for_text("The 21st century changed the field.") == []


def test_build_text_evidence_candidates_ignores_generation_ordinals_as_rankings():
    assert _data_items_for_text("The 3rd generation system uses neural networks.") == []


def test_build_text_evidence_candidates_ignores_edition_ordinals_as_rankings():
    assert _data_items_for_text("The 1st edition includes a glossary.") == []


def test_build_text_evidence_candidates_ignores_series_ordinals_as_rankings():
    assert _data_items_for_text("The 5th in the series uses neural networks.") == []


def test_build_text_evidence_candidates_preserves_negative_sign_before_currency():
    article = {
        "paragraphs": [
            {
                "id": "left-p-1",
                "sentences": [
                    {"id": "left-s-1-1", "text": "The company generated -$2,019 in revenue."},
                ],
            }
        ]
    }

    candidates = build_text_evidence_candidates(article, "left")

    assert candidates[0]["dataItems"] == [{"value": -2019, "role": "scale"}]


def test_build_text_evidence_candidates_preserves_negative_sign_before_currency_units():
    article = {
        "paragraphs": [
            {
                "id": "left-p-1",
                "sentences": [
                    {"id": "left-s-1-1", "text": "The company generated -$2.5 million in revenue."},
                ],
            }
        ]
    }

    candidates = build_text_evidence_candidates(article, "left")

    assert candidates[0]["dataItems"] == [{"value": -2.5, "role": "scale", "unit": "million"}]


def test_build_paired_text_attributes_rejects_invalid_sentence_ids():
    left_article = {
        "paragraphs": [
            {
                "id": "left-p-1",
                "sentences": [{"id": "left-s-1-1", "text": "AI was founded in 1956."}],
            }
        ]
    }
    right_article = {
        "paragraphs": [
            {
                "id": "right-p-1",
                "sentences": [{"id": "right-s-1-1", "text": "ML emerged in the 1950s."}],
            }
        ]
    }
    pair_response = {
        "pairs": [
            {
                "dimensionLabel": "Historical emergence",
                "comparisonQuestion": "When did it emerge?",
                "left": {"valueText": "founded in 1956", "sentenceIds": ["left-s-missing"]},
                "right": {"valueText": "emerged in the 1950s", "sentenceIds": ["right-s-1-1"]},
                "dataPriority": True,
                "dataRole": "emergence_time",
                "confidence": 0.9,
            }
        ]
    }

    left_attrs, right_attrs, alignments = build_paired_text_attributes(
        left_article,
        right_article,
        pair_response,
        [],
        [],
    )

    assert left_attrs == []
    assert right_attrs == []
    assert alignments == []


def test_build_paired_text_attributes_creates_aligned_attributes():
    left_article = {
        "paragraphs": [
            {
                "id": "left-p-1",
                "sentences": [{"id": "left-s-1-1", "text": "AI was founded in 1956."}],
            }
        ]
    }
    right_article = {
        "paragraphs": [
            {
                "id": "right-p-1",
                "sentences": [{"id": "right-s-1-1", "text": "ML emerged in the 1950s."}],
            }
        ]
    }
    pair_response = {
        "pairs": [
            {
                "dimensionLabel": "Historical emergence",
                "comparisonQuestion": "When did it emerge?",
                "left": {"valueText": "founded in 1956", "sentenceIds": ["left-s-1-1"]},
                "right": {"valueText": "emerged in the 1950s", "sentenceIds": ["right-s-1-1"]},
                "dataPriority": True,
                "dataRole": "emergence_time",
                "confidence": 0.9,
            }
        ]
    }

    left_attrs, right_attrs, alignments = build_paired_text_attributes(
        left_article,
        right_article,
        pair_response,
        [],
        [],
    )

    assert left_attrs[0]["key"] == "Historical emergence"
    assert left_attrs[0]["source"] == "main_text"
    assert left_attrs[0]["sourceIds"] == ["left-s-1-1"]
    assert left_attrs[0]["dataPriority"] is False
    assert left_attrs[0]["dataRole"] == "emergence_time"
    assert right_attrs[0]["sourceIds"] == ["right-s-1-1"]
    assert alignments == [
        {
            "left": left_attrs[0],
            "right": right_attrs[0],
            "label": "Historical emergence",
        }
    ]


def test_build_paired_text_attributes_rejects_unsupported_structured_values():
    left_article = {
        "paragraphs": [
            {
                "id": "left-p-1",
                "sentences": [{"id": "left-s-1-1", "text": "Operating margin reached 18.4% in 2024."}],
            }
        ]
    }
    right_article = {
        "paragraphs": [
            {
                "id": "right-p-1",
                "sentences": [{"id": "right-s-1-1", "text": "Operating margin reached 4.1% in 2024."}],
            }
        ]
    }
    pair_response = {
        "pairs": [
            {
                "dimensionLabel": "Operating margin",
                "comparisonQuestion": "How do margins compare?",
                "left": {
                    "valueText": "operating margin in 2024",
                    "sentenceIds": ["left-s-1-1"],
                    "values": [{"value": 99, "year": 2024, "rawText": "99%"}],
                },
                "right": {
                    "valueText": "operating margin in 2024",
                    "sentenceIds": ["right-s-1-1"],
                    "values": [{"value": 4.1, "year": 2024, "rawText": "4.1%"}],
                },
                "dataPriority": True,
                "dataRole": "proportion",
                "confidence": 0.9,
            }
        ]
    }

    left_attrs, right_attrs, alignments = build_paired_text_attributes(
        left_article,
        right_article,
        pair_response,
        [],
        [],
    )

    assert left_attrs == []
    assert right_attrs == []
    assert alignments == []


def test_build_paired_text_attributes_rejects_visual_pair_without_llm_values():
    left_article = {
        "paragraphs": [
            {
                "id": "left-p-1",
                "sentences": [{"id": "left-s-1-1", "text": "Operating margin reached 18.4% in 2024."}],
            }
        ]
    }
    right_article = {
        "paragraphs": [
            {
                "id": "right-p-1",
                "sentences": [{"id": "right-s-1-1", "text": "Operating margin reached 4.1% in 2024."}],
            }
        ]
    }
    pair_response = {
        "pairs": [
            {
                "dimensionLabel": "Operating margin",
                "comparisonQuestion": "How do margins compare?",
                "left": {
                    "valueText": "operating margin reached 18.4% in 2024",
                    "sentenceIds": ["left-s-1-1"],
                },
                "right": {
                    "valueText": "operating margin reached 4.1% in 2024",
                    "sentenceIds": ["right-s-1-1"],
                },
                "dataPriority": True,
                "dataRole": "proportion",
                "confidence": 0.9,
            }
        ]
    }

    left_attrs, right_attrs, alignments = build_paired_text_attributes(
        left_article,
        right_article,
        pair_response,
        [],
        [],
        require_extracted_values_for_visual=True,
    )

    assert left_attrs == []
    assert right_attrs == []
    assert alignments == []


def test_build_paired_text_attributes_rejects_structured_value_mismatched_with_raw_text():
    left_article = {
        "paragraphs": [
            {
                "id": "left-p-1",
                "sentences": [{"id": "left-s-1-1", "text": "Operating margin reached 18.4% in 2024."}],
            }
        ]
    }
    right_article = {
        "paragraphs": [
            {
                "id": "right-p-1",
                "sentences": [{"id": "right-s-1-1", "text": "Operating margin reached 4.1% in 2024."}],
            }
        ]
    }
    pair_response = {
        "pairs": [
            {
                "dimensionLabel": "Operating margin",
                "comparisonQuestion": "How do margins compare?",
                "left": {
                    "valueText": "operating margin in 2024",
                    "sentenceIds": ["left-s-1-1"],
                    "values": [{"value": 99, "year": 2024, "rawText": "18.4%"}],
                },
                "right": {
                    "valueText": "operating margin in 2024",
                    "sentenceIds": ["right-s-1-1"],
                    "values": [{"value": 4.1, "year": 2024, "rawText": "4.1%"}],
                },
                "dataPriority": True,
                "dataRole": "proportion",
                "confidence": 0.9,
            }
        ]
    }

    left_attrs, right_attrs, alignments = build_paired_text_attributes(
        left_article,
        right_article,
        pair_response,
        [],
        [],
    )

    assert left_attrs == []
    assert right_attrs == []
    assert alignments == []


def test_build_paired_text_attributes_accepts_scaled_structured_value_raw_text():
    left_article = {
        "paragraphs": [
            {
                "id": "left-p-1",
                "sentences": [{"id": "left-s-1-1", "text": "Sales reached 7.4 million units in 2023."}],
            }
        ]
    }
    right_article = {
        "paragraphs": [
            {
                "id": "right-p-1",
                "sentences": [{"id": "right-s-1-1", "text": "Sales reached 1,402,371 units in 2023."}],
            }
        ]
    }
    pair_response = {
        "pairs": [
            {
                "dimensionLabel": "Annual sales",
                "comparisonQuestion": "How do annual sales compare?",
                "left": {
                    "valueText": "sales in 2023",
                    "sentenceIds": ["left-s-1-1"],
                    "values": [{"value": 7400000, "year": 2023, "rawText": "7.4 million"}],
                },
                "right": {
                    "valueText": "sales in 2023",
                    "sentenceIds": ["right-s-1-1"],
                    "values": [{"value": 1402371, "year": 2023, "rawText": "1,402,371"}],
                },
                "dataPriority": True,
                "dataRole": "quantity",
                "confidence": 0.9,
            }
        ]
    }

    left_attrs, right_attrs, alignments = build_paired_text_attributes(
        left_article,
        right_article,
        pair_response,
        [],
        [],
    )

    assert left_attrs[0]["extractedValues"] == [{"value": 7400000, "year": 2023, "rawText": "7.4 million"}]
    assert right_attrs[0]["extractedValues"] == [{"value": 1402371, "year": 2023, "rawText": "1,402,371"}]
    assert alignments[0]["label"] == "Annual sales"


def test_build_paired_text_attributes_preserves_llm_standard_value_metadata():
    left_article = {
        "paragraphs": [
            {
                "id": "left-p-1",
                "sentences": [{"id": "left-s-1-1", "text": "Alcohol consumption per capita totaled 4.85 liters of pure alcohol in 2019."}],
            }
        ]
    }
    right_article = {
        "paragraphs": [
            {
                "id": "right-p-1",
                "sentences": [{"id": "right-s-1-1", "text": "Alcohol consumption per capita totaled 0.78 liters of pure alcohol in 2019."}],
            }
        ]
    }
    pair_response = {
        "pairs": [
            {
                "dimensionLabel": "Alcohol consumption per capita: total",
                "comparisonQuestion": "How does total alcohol consumption per capita compare?",
                "left": {
                    "valueText": "totaled 4.85 liters of pure alcohol in 2019",
                    "sentenceIds": ["left-s-1-1"],
                    "values": [
                        {
                            "value": 4.85,
                            "label": "total",
                            "unit": "liters of pure alcohol per capita",
                            "valueKind": "aggregate",
                            "year": 2019,
                            "rawText": "4.85 liters of pure alcohol",
                        }
                    ],
                },
                "right": {
                    "valueText": "totaled 0.78 liters of pure alcohol in 2019",
                    "sentenceIds": ["right-s-1-1"],
                    "values": [
                        {
                            "value": 0.78,
                            "label": "total",
                            "unit": "liters of pure alcohol per capita",
                            "valueKind": "aggregate",
                            "year": 2019,
                            "rawText": "0.78 liters of pure alcohol",
                        }
                    ],
                },
                "dataPriority": True,
                "dataRole": "quantity",
                "confidence": 0.93,
            }
        ]
    }

    left_attrs, right_attrs, alignments = build_paired_text_attributes(
        left_article,
        right_article,
        pair_response,
        [],
        [],
        require_extracted_values_for_visual=True,
    )

    assert left_attrs[0]["extractedValues"] == [
        {
            "value": 4.85,
            "label": "total",
            "unit": "liters of pure alcohol per capita",
            "valueKind": "aggregate",
            "year": 2019,
            "rawText": "4.85 liters of pure alcohol",
        }
    ]
    assert right_attrs[0]["extractedValues"][0]["unit"] == "liters of pure alcohol per capita"
    assert right_attrs[0]["extractedValues"][0]["valueKind"] == "aggregate"
    assert alignments[0]["label"] == "Alcohol consumption per capita: total"


def test_build_paired_text_attributes_rejects_structured_value_year_not_in_evidence():
    left_article = {
        "paragraphs": [
            {
                "id": "left-p-1",
                "sentences": [{"id": "left-s-1-1", "text": "Sales reached 7.4 million units in 2023."}],
            }
        ]
    }
    right_article = {
        "paragraphs": [
            {
                "id": "right-p-1",
                "sentences": [{"id": "right-s-1-1", "text": "Sales reached 1,402,371 units in 2023."}],
            }
        ]
    }
    pair_response = {
        "pairs": [
            {
                "dimensionLabel": "Annual sales",
                "comparisonQuestion": "How do annual sales compare?",
                "left": {
                    "valueText": "sales in 2024",
                    "sentenceIds": ["left-s-1-1"],
                    "values": [{"value": 7400000, "year": 2024, "rawText": "7.4 million"}],
                },
                "right": {
                    "valueText": "sales in 2023",
                    "sentenceIds": ["right-s-1-1"],
                    "values": [{"value": 1402371, "year": 2023, "rawText": "1,402,371"}],
                },
                "dataPriority": True,
                "dataRole": "quantity",
                "confidence": 0.9,
            }
        ]
    }

    left_attrs, right_attrs, alignments = build_paired_text_attributes(
        left_article,
        right_article,
        pair_response,
        [],
        [],
    )

    assert left_attrs == []
    assert right_attrs == []
    assert alignments == []


def test_build_paired_text_attributes_rejects_incompatible_measurement_cues():
    left_article = {
        "paragraphs": [
            {
                "id": "left-p-1",
                "sentences": [
                    {
                        "id": "left-s-1-1",
                        "text": "Overall, there have been 26,969,913 confirmed cases and 198,523 deaths.",
                    },
                    {
                        "id": "left-s-1-2",
                        "text": "Its economic growth rate reached 6.2% in 2010.",
                    },
                ],
            }
        ]
    }
    right_article = {
        "paragraphs": [
            {
                "id": "right-p-1",
                "sentences": [
                    {
                        "id": "right-s-1-1",
                        "text": "By 13 March, cases had been confirmed in all 50 provinces of the country.",
                    },
                    {
                        "id": "right-s-1-2",
                        "text": "GDP growth for that year was 2.8%, with annualised fourth quarter expansion of 5.5%.",
                    },
                ],
            }
        ]
    }
    pair_response = {
        "pairs": [
            {
                "dimensionLabel": "Cases",
                "comparisonQuestion": "How do confirmed cases compare?",
                "left": {
                    "valueText": "26,969,913 confirmed cases and 198,523 deaths",
                    "sentenceIds": ["left-s-1-1"],
                },
                "right": {
                    "valueText": "cases had been confirmed in all 50 provinces",
                    "sentenceIds": ["right-s-1-1"],
                },
                "dataPriority": True,
                "dataRole": "quantity",
                "confidence": 0.9,
            },
            {
                "dimensionLabel": "Growth",
                "comparisonQuestion": "How does growth compare?",
                "left": {
                    "valueText": "economic growth rate reached 6.2% in 2010",
                    "sentenceIds": ["left-s-1-2"],
                },
                "right": {
                    "valueText": "GDP growth was 2.8%, with annualised fourth quarter expansion of 5.5%",
                    "sentenceIds": ["right-s-1-2"],
                },
                "dataPriority": True,
                "dataRole": "proportion",
                "confidence": 0.9,
            },
        ]
    }

    left_attrs, right_attrs, alignments = build_paired_text_attributes(
        left_article,
        right_article,
        pair_response,
        [],
        [],
    )

    assert left_attrs == []
    assert right_attrs == []
    assert alignments == []


def test_build_paired_text_attributes_rejects_case_counts_paired_with_geographic_coverage():
    left_article = {
        "paragraphs": [
            {
                "id": "left-p-1",
                "sentences": [
                    {
                        "id": "left-s-1-1",
                        "text": "As of 17 March 2023, Italy has 141,988 active cases.",
                    },
                ],
            }
        ]
    }
    right_article = {
        "paragraphs": [
            {
                "id": "right-p-1",
                "sentences": [
                    {
                        "id": "right-s-1-1",
                        "text": "By 13 March, cases had been confirmed in all 50 provinces of the country.",
                    },
                ],
            }
        ]
    }
    pair_response = {
        "pairs": [
            {
                "dimensionLabel": "Cases",
                "comparisonQuestion": "How do cases compare?",
                "left": {
                    "valueText": "Italy has 141,988 active cases",
                    "sentenceIds": ["left-s-1-1"],
                },
                "right": {
                    "valueText": "cases had been confirmed in all 50 provinces",
                    "sentenceIds": ["right-s-1-1"],
                },
                "dataPriority": True,
                "dataRole": "quantity",
                "confidence": 0.9,
            }
        ]
    }

    left_attrs, right_attrs, alignments = build_paired_text_attributes(
        left_article,
        right_article,
        pair_response,
        [],
        [],
    )

    assert left_attrs == []
    assert right_attrs == []
    assert alignments == []


def test_build_paired_text_attributes_rejects_active_cases_paired_with_regional_cases():
    left_article = {
        "paragraphs": [
            {
                "id": "left-p-1",
                "sentences": [
                    {
                        "id": "left-s-1-1",
                        "text": "As of 17 March 2023, Italy has 141,988 active cases.",
                    },
                ],
            }
        ]
    }
    right_article = {
        "paragraphs": [
            {
                "id": "right-p-1",
                "sentences": [
                    {
                        "id": "right-s-1-1",
                        "text": "On 1 March, two doctors were infected, increasing the number of Andalusian cases to 12.",
                    },
                ],
            }
        ]
    }
    pair_response = {
        "pairs": [
            {
                "dimensionLabel": "Cases",
                "comparisonQuestion": "How do cases compare?",
                "left": {
                    "valueText": "Italy has 141,988 active cases",
                    "sentenceIds": ["left-s-1-1"],
                },
                "right": {
                    "valueText": "increasing the number of Andalusian cases to 12",
                    "sentenceIds": ["right-s-1-1"],
                },
                "dataPriority": True,
                "dataRole": "quantity",
                "confidence": 0.9,
            }
        ]
    }

    left_attrs, right_attrs, alignments = build_paired_text_attributes(
        left_article,
        right_article,
        pair_response,
        [],
        [],
    )

    assert left_attrs == []
    assert right_attrs == []
    assert alignments == []


def test_build_paired_text_attributes_drops_generic_cases_when_infobox_has_case_rows():
    left_article = {
        "paragraphs": [
            {
                "id": "left-p-1",
                "sentences": [{"id": "left-s-1-1", "text": "The country reported 141,988 local cases."}],
            }
        ]
    }
    right_article = {
        "paragraphs": [
            {
                "id": "right-p-1",
                "sentences": [{"id": "right-s-1-1", "text": "The country reported 12 local cases."}],
            }
        ]
    }
    pair_response = {
        "pairs": [
            {
                "dimensionLabel": "Cases",
                "comparisonQuestion": "How do cases compare?",
                "left": {"valueText": "141,988 local cases", "sentenceIds": ["left-s-1-1"]},
                "right": {"valueText": "12 local cases", "sentenceIds": ["right-s-1-1"]},
                "dataPriority": True,
                "dataRole": "quantity",
                "confidence": 0.9,
            }
        ]
    }

    left_attrs, right_attrs, alignments = build_paired_text_attributes(
        left_article,
        right_article,
        pair_response,
        [{"key": "Confirmed cases", "source": "infobox"}],
        [{"key": "Confirmed cases", "source": "infobox"}],
    )

    assert left_attrs == []
    assert right_attrs == []
    assert alignments == []


def _paired_articles_with_paragraphs():
    left_article = {
        "paragraphs": [
            {
                "id": "left-p-1",
                "sentences": [
                    {"id": "left-s-1-1", "text": "AI was founded in 1956."},
                    {"id": "left-s-1-2", "text": "AI grew from a summer workshop."},
                ],
            },
            {
                "id": "left-p-2",
                "sentences": [{"id": "left-s-2-1", "text": "AI adoption accelerated later."}],
            },
        ]
    }
    right_article = {
        "paragraphs": [
            {
                "id": "right-p-1",
                "sentences": [
                    {"id": "right-s-1-1", "text": "ML emerged in the 1950s."},
                    {"id": "right-s-1-2", "text": "ML developed from statistical methods."},
                ],
            }
        ]
    }
    return left_article, right_article


def _pair_response(label="Historical emergence", *, data_priority=True, data_role="emergence_time"):
    return {
        "pairs": [
            {
                "dimensionLabel": label,
                "comparisonQuestion": "When did it emerge?",
                "left": {"valueText": "founded in 1956", "sentenceIds": ["left-s-1-1"]},
                "right": {"valueText": "emerged in the 1950s", "sentenceIds": ["right-s-1-1"]},
                "dataPriority": data_priority,
                "dataRole": data_role,
                "confidence": 0.9,
            }
        ]
    }


def test_build_paired_text_attributes_rejects_cross_paragraph_sentence_ids():
    left_article, right_article = _paired_articles_with_paragraphs()
    pair_response = _pair_response()
    pair_response["pairs"][0]["left"]["sentenceIds"] = ["left-s-1-1", "left-s-2-1"]

    left_attrs, right_attrs, alignments = build_paired_text_attributes(
        left_article,
        right_article,
        pair_response,
        [],
        [],
    )

    assert left_attrs == []
    assert right_attrs == []
    assert alignments == []


def test_build_paired_text_attributes_accepts_multi_sentence_same_paragraph():
    left_article, right_article = _paired_articles_with_paragraphs()
    pair_response = _pair_response()
    pair_response["pairs"][0]["left"]["sentenceIds"] = ["left-s-1-1", "left-s-1-2"]

    left_attrs, _, _ = build_paired_text_attributes(
        left_article,
        right_article,
        pair_response,
        [],
        [],
    )

    assert left_attrs[0]["sourceIds"] == ["left-s-1-1", "left-s-1-2"]
    assert left_attrs[0]["paragraphId"] == "left-p-1"


def test_build_paired_text_attributes_deduplicates_repeated_sentence_ids():
    left_article, right_article = _paired_articles_with_paragraphs()
    pair_response = _pair_response()
    pair_response["pairs"][0]["left"]["sentenceIds"] = ["left-s-1-1", "left-s-1-1", "left-s-1-2"]

    left_attrs, _, _ = build_paired_text_attributes(
        left_article,
        right_article,
        pair_response,
        [],
        [],
    )

    assert left_attrs[0]["sourceIds"] == ["left-s-1-1", "left-s-1-2"]
    assert left_attrs[0]["paragraphId"] == "left-p-1"


def test_build_paired_text_attributes_drops_normalized_infobox_key_duplicates():
    left_article, right_article = _paired_articles_with_paragraphs()

    left_attrs, right_attrs, alignments = build_paired_text_attributes(
        left_article,
        right_article,
        [
            {
                "dimensionLabel": "GDP (PPP)",
                "comparisonQuestion": "What is GDP by PPP?",
                "left": {"valueText": "$1 trillion", "sentenceIds": ["left-s-1-1"]},
                "right": {"valueText": "$2 trillion", "sentenceIds": ["right-s-1-1"]},
                "dataPriority": True,
                "dataRole": "scale",
                "confidence": 0.9,
            },
            {
                "dimensionLabel": "Founded",
                "comparisonQuestion": "When was it founded?",
                "left": {"valueText": "1956", "sentenceIds": ["left-s-1-1"]},
                "right": {"valueText": "1950s", "sentenceIds": ["right-s-1-1"]},
                "dataPriority": True,
                "dataRole": "emergence_time",
                "confidence": 0.9,
            },
        ],
        [{"key": "GDP PPP"}, {"key": "Foundation"}],
        [{"key": "GDP PPP"}, {"key": "Foundation"}],
    )

    assert left_attrs == []
    assert right_attrs == []
    assert alignments == []


def test_build_paired_text_attributes_rejects_non_bool_data_priority():
    left_article, right_article = _paired_articles_with_paragraphs()
    pair_response = _pair_response(data_priority="false", data_role="emergence_time")

    left_attrs, right_attrs, alignments = build_paired_text_attributes(
        left_article,
        right_article,
        pair_response,
        [],
        [],
    )

    assert left_attrs == []
    assert right_attrs == []
    assert alignments == []


def test_build_paired_text_attributes_rejects_unknown_data_role_when_priority_true():
    left_article, right_article = _paired_articles_with_paragraphs()
    pair_response = _pair_response(data_priority=True, data_role="timeline")

    left_attrs, right_attrs, alignments = build_paired_text_attributes(
        left_article,
        right_article,
        pair_response,
        [],
        [],
    )

    assert left_attrs == []
    assert right_attrs == []
    assert alignments == []


def test_build_paired_text_attributes_allows_blank_data_role_when_priority_false():
    left_article, right_article = _paired_articles_with_paragraphs()
    pair_response = _pair_response(data_priority=False, data_role=None)

    left_attrs, right_attrs, alignments = build_paired_text_attributes(
        left_article,
        right_article,
        pair_response,
        [],
        [],
    )

    assert left_attrs[0]["dataPriority"] is False
    assert "dataRole" not in left_attrs[0]
    assert right_attrs[0]["dataPriority"] is False
    assert "dataRole" not in right_attrs[0]
    assert alignments[0]["label"] == "Historical emergence"


def test_build_paired_text_attributes_rejects_malformed_scalar_fields():
    left_article, right_article = _paired_articles_with_paragraphs()
    cases = [
        ("list label", {"dimensionLabel": ["Revenue"]}),
        ("dict label", {"dimensionLabel": {"text": "Revenue"}}),
        ("dict value", {"left": {"valueText": {"text": "1956"}, "sentenceIds": ["left-s-1-1"]}}),
        ("list value", {"left": {"valueText": ["1956"], "sentenceIds": ["left-s-1-1"]}}),
        ("non-string question", {"comparisonQuestion": ["When?"]}),
        ("blank question", {"comparisonQuestion": "   "}),
    ]

    for name, override in cases:
        pair_response = _pair_response(label=f"Malformed {name}")
        pair_response["pairs"][0].update(override)

        left_attrs, right_attrs, alignments = build_paired_text_attributes(
            left_article,
            right_article,
            pair_response,
            [],
            [],
        )

        assert (name, left_attrs, right_attrs, alignments) == (name, [], [], [])


def test_build_paired_text_attributes_rejects_bool_and_non_finite_confidence():
    left_article, right_article = _paired_articles_with_paragraphs()
    cases = [
        ("bool", True),
        ("string infinity", "Infinity"),
        ("float infinity", float("inf")),
        ("nan", float("nan")),
    ]

    for name, confidence in cases:
        pair_response = _pair_response(label=f"Bad confidence {name}")
        pair_response["pairs"][0]["confidence"] = confidence

        left_attrs, right_attrs, alignments = build_paired_text_attributes(
            left_article,
            right_article,
            pair_response,
            [],
            [],
        )

        assert (name, left_attrs, right_attrs, alignments) == (name, [], [], [])


def test_build_paired_text_attributes_rejects_out_of_range_confidence():
    left_article, right_article = _paired_articles_with_paragraphs()
    cases = [
        ("negative", -0.1),
        ("above one", 2),
    ]

    for name, confidence in cases:
        pair_response = _pair_response(label=f"Out of range confidence {name}")
        pair_response["pairs"][0]["confidence"] = confidence

        left_attrs, right_attrs, alignments = build_paired_text_attributes(
            left_article,
            right_article,
            pair_response,
            [],
            [],
        )

        assert (name, left_attrs, right_attrs, alignments) == (name, [], [], [])


def test_build_paired_text_attributes_preserves_finite_confidence_values():
    left_article, right_article = _paired_articles_with_paragraphs()
    pair_response = _pair_response()
    pair_response["pairs"][0]["confidence"] = 0.25

    left_attrs, right_attrs, _ = build_paired_text_attributes(
        left_article,
        right_article,
        pair_response,
        [],
        [],
    )

    assert left_attrs[0]["confidence"] == 0.25
    assert right_attrs[0]["confidence"] == 0.25


def test_build_paired_text_attributes_rejects_missing_paragraph_ids_from_different_paragraphs():
    left_article = {
        "paragraphs": [
            {"sentences": [{"id": "left-s-1-1", "text": "AI was founded in 1956."}]},
            {"sentences": [{"id": "left-s-2-1", "text": "AI grew from a workshop."}]},
        ]
    }
    right_article = {
        "paragraphs": [
            {"sentences": [{"id": "right-s-1-1", "text": "ML emerged in the 1950s."}]},
        ]
    }
    pair_response = _pair_response()
    pair_response["pairs"][0]["left"]["sentenceIds"] = ["left-s-1-1", "left-s-2-1"]

    left_attrs, right_attrs, alignments = build_paired_text_attributes(
        left_article,
        right_article,
        pair_response,
        [],
        [],
    )

    assert left_attrs == []
    assert right_attrs == []
    assert alignments == []


def test_build_paired_text_attributes_rejects_blank_paragraph_ids_from_different_paragraphs():
    left_article = {
        "paragraphs": [
            {"id": "", "sentences": [{"id": "left-s-1-1", "text": "AI was founded in 1956."}]},
            {"id": "", "sentences": [{"id": "left-s-2-1", "text": "AI grew from a workshop."}]},
        ]
    }
    right_article = {
        "paragraphs": [
            {"id": "", "sentences": [{"id": "right-s-1-1", "text": "ML emerged in the 1950s."}]},
        ]
    }
    pair_response = _pair_response()
    pair_response["pairs"][0]["left"]["sentenceIds"] = ["left-s-1-1", "left-s-2-1"]

    left_attrs, right_attrs, alignments = build_paired_text_attributes(
        left_article,
        right_article,
        pair_response,
        [],
        [],
    )

    assert left_attrs == []
    assert right_attrs == []
    assert alignments == []


def test_build_paired_text_attributes_handles_unhashable_paragraph_ids():
    left_article = {
        "paragraphs": [
            {"id": ["left-p-1"], "sentences": [{"id": "left-s-1-1", "text": "AI was founded in 1956."}]},
        ]
    }
    right_article = {
        "paragraphs": [
            {
                "id": {"name": "right-p-1"},
                "sentences": [{"id": "right-s-1-1", "text": "ML emerged in the 1950s."}],
            },
        ]
    }

    left_attrs, right_attrs, alignments = build_paired_text_attributes(
        left_article,
        right_article,
        _pair_response(),
        [],
        [],
    )

    assert left_attrs[0]["sourceIds"] == ["left-s-1-1"]
    assert left_attrs[0]["paragraphId"] is None
    assert right_attrs[0]["sourceIds"] == ["right-s-1-1"]
    assert right_attrs[0]["paragraphId"] is None
    assert alignments[0]["label"] == "Historical emergence"


def test_build_paired_text_attributes_keeps_distinct_pairs_with_same_label():
    left_article, right_article = _paired_articles_with_paragraphs()
    pair_response = {
        "pairs": [
            {
                "dimensionLabel": "Revenue",
                "comparisonQuestion": "What revenue was reported?",
                "left": {"valueText": "$1 million", "sentenceIds": ["left-s-1-1"]},
                "right": {"valueText": "$2 million", "sentenceIds": ["right-s-1-1"]},
                "dataPriority": True,
                "dataRole": "scale",
                "confidence": 0.9,
            },
            {
                "dimensionLabel": "Revenue",
                "comparisonQuestion": "What revenue was reported?",
                "left": {"valueText": "$3 million", "sentenceIds": ["left-s-1-2"]},
                "right": {"valueText": "$4 million", "sentenceIds": ["right-s-1-2"]},
                "dataPriority": True,
                "dataRole": "scale",
                "confidence": 0.9,
            },
        ]
    }

    left_attrs, right_attrs, alignments = build_paired_text_attributes(
        left_article,
        right_article,
        pair_response,
        [],
        [],
    )

    assert [attr["id"] for attr in left_attrs] == ["left-attr-paired-text-1", "left-attr-paired-text-2"]
    assert [attr["id"] for attr in right_attrs] == ["right-attr-paired-text-1", "right-attr-paired-text-2"]
    assert [attr["valueText"] for attr in left_attrs] == ["$1 million", "$3 million"]
    assert [alignment["label"] for alignment in alignments] == ["Revenue", "Revenue"]


def test_build_paired_text_attributes_drops_exact_duplicate_evidence_pairs():
    left_article, right_article = _paired_articles_with_paragraphs()
    pair_response = {
        "pairs": [
            {
                "dimensionLabel": "Revenue",
                "comparisonQuestion": "What revenue was reported?",
                "left": {"valueText": "$1 million", "sentenceIds": ["left-s-1-1"]},
                "right": {"valueText": "$2 million", "sentenceIds": ["right-s-1-1"]},
                "dataPriority": True,
                "dataRole": "scale",
                "confidence": 0.9,
            },
            {
                "dimensionLabel": "Market size",
                "comparisonQuestion": "What revenue was reported?",
                "left": {"valueText": "$1 million", "sentenceIds": ["left-s-1-1"]},
                "right": {"valueText": "$2 million", "sentenceIds": ["right-s-1-1"]},
                "dataPriority": True,
                "dataRole": "scale",
                "confidence": 0.9,
            },
        ]
    }

    left_attrs, right_attrs, alignments = build_paired_text_attributes(
        left_article,
        right_article,
        pair_response,
        [],
        [],
    )

    assert len(left_attrs) == 1
    assert len(right_attrs) == 1
    assert len(alignments) == 1
    assert left_attrs[0]["key"] == "Revenue"


def test_build_paired_text_attributes_deduplicates_reordered_multi_sentence_evidence():
    left_article, right_article = _paired_articles_with_paragraphs()
    pair_response = {
        "pairs": [
            {
                "dimensionLabel": "Origins",
                "comparisonQuestion": "What origin evidence is reported?",
                "left": {"valueText": "founded in 1956", "sentenceIds": ["left-s-1-1", "left-s-1-2"]},
                "right": {"valueText": "emerged in the 1950s", "sentenceIds": ["right-s-1-1", "right-s-1-2"]},
                "dataPriority": True,
                "dataRole": "emergence_time",
                "confidence": 0.9,
            },
            {
                "dimensionLabel": "Historical background",
                "comparisonQuestion": "What origin evidence is reported?",
                "left": {"valueText": "founded in 1956", "sentenceIds": ["left-s-1-2", "left-s-1-1"]},
                "right": {"valueText": "emerged in the 1950s", "sentenceIds": ["right-s-1-2", "right-s-1-1"]},
                "dataPriority": True,
                "dataRole": "emergence_time",
                "confidence": 0.9,
            },
        ]
    }

    left_attrs, right_attrs, alignments = build_paired_text_attributes(
        left_article,
        right_article,
        pair_response,
        [],
        [],
    )

    assert len(left_attrs) == 1
    assert len(right_attrs) == 1
    assert len(alignments) == 1
    assert left_attrs[0]["sourceIds"] == ["left-s-1-1", "left-s-1-2"]


def test_build_paired_text_attributes_strips_data_role_when_priority_false():
    left_article, right_article = _paired_articles_with_paragraphs()
    pair_response = _pair_response(data_priority=False, data_role="scale")

    left_attrs, right_attrs, _ = build_paired_text_attributes(
        left_article,
        right_article,
        pair_response,
        [],
        [],
    )

    assert left_attrs[0]["dataPriority"] is False
    assert "dataRole" not in left_attrs[0]
    assert right_attrs[0]["dataPriority"] is False
    assert "dataRole" not in right_attrs[0]


def test_build_rule_paired_text_attributes_pairs_compatible_data_roles():
    left_article = {
        "paragraphs": [
            {
                "id": "left-p-1",
                "sentences": [{"id": "left-s-1-1", "text": "The field was founded in 1956."}],
            }
        ]
    }
    right_article = {
        "paragraphs": [
            {
                "id": "right-p-1",
                "sentences": [{"id": "right-s-1-1", "text": "The method emerged in the 1950s."}],
            }
        ]
    }

    left_attrs, right_attrs, alignments = build_rule_paired_text_attributes(left_article, right_article, [], [])

    assert alignments[0]["label"] == "Historical emergence"
    assert left_attrs[0]["dataRole"] == "emergence_time"
    assert right_attrs[0]["dataRole"] == "emergence_time"


def test_build_rule_paired_text_attributes_does_not_pair_different_data_roles():
    left_article = {
        "paragraphs": [
            {
                "id": "left-p-1",
                "sentences": [{"id": "left-s-1-1", "text": "The model reached 95% accuracy."}],
            }
        ]
    }
    right_article = {
        "paragraphs": [
            {
                "id": "right-p-1",
                "sentences": [{"id": "right-s-1-1", "text": "The field was founded in 1956."}],
            }
        ]
    }

    left_attrs, right_attrs, alignments = build_rule_paired_text_attributes(left_article, right_article, [], [])

    assert left_attrs == []
    assert right_attrs == []
    assert alignments == []


def test_build_rule_paired_text_attributes_pairs_matching_quantity_cues():
    left_article = {
        "paragraphs": [
            {
                "id": "left-p-1",
                "sentences": [{"id": "left-s-1-1", "text": "The company had 200 employees."}],
            }
        ]
    }
    right_article = {
        "paragraphs": [
            {
                "id": "right-p-1",
                "sentences": [{"id": "right-s-1-1", "text": "The organization had 500 employees."}],
            }
        ]
    }

    left_attrs, right_attrs, alignments = build_rule_paired_text_attributes(left_article, right_article, [], [])

    assert alignments[0]["label"] == "Employees"
    assert left_attrs[0]["key"] == "Employees"
    assert right_attrs[0]["key"] == "Employees"
    assert left_attrs[0]["dataRole"] == "quantity"
    assert right_attrs[0]["dataRole"] == "quantity"


def test_build_rule_paired_text_attributes_pairs_capacity_when_country_name_mentions_states():
    left_article = {
        "paragraphs": [
            {
                "id": "left-p-1",
                "sentences": [
                    {
                        "id": "left-s-1-1",
                        "text": "Its PV capacity crossed 1,000 gigawatts in May 2025.",
                    }
                ],
            }
        ]
    }
    right_article = {
        "paragraphs": [
            {
                "id": "right-p-1",
                "sentences": [
                    {
                        "id": "right-s-1-1",
                        "text": (
                            "As of the end of 2024, the United States had 239 gigawatts "
                            "of installed photovoltaic and concentrated solar power capacity combined."
                        ),
                    }
                ],
            }
        ]
    }

    left_attrs, right_attrs, alignments = build_rule_paired_text_attributes(left_article, right_article, [], [])

    assert [alignment["label"] for alignment in alignments] == ["Capacity"]
    assert left_attrs[0]["source"] == "main_text"
    assert right_attrs[0]["source"] == "main_text"
    assert left_attrs[0]["dataPriority"] is True
    assert right_attrs[0]["dataPriority"] is True
    assert left_attrs[0]["sourceIds"] == ["left-s-1-1"]
    assert right_attrs[0]["sourceIds"] == ["right-s-1-1"]


def test_build_rule_paired_text_attributes_labels_sales_separately_from_revenue():
    left_article = {
        "paragraphs": [
            {
                "id": "left-p-1",
                "sentences": [
                    {
                        "id": "left-s-1-1",
                        "text": "Sales in 2023 totaled 7.4 million units with a market share of 30.2%.",
                    }
                ],
            }
        ]
    }
    right_article = {
        "paragraphs": [
            {
                "id": "right-p-1",
                "sentences": [
                    {
                        "id": "right-s-1-1",
                        "text": "Sales totaled 1,402,371 units in 2023, with a market share of 9.1%.",
                    }
                ],
            }
        ]
    }

    left_attrs, right_attrs, alignments = build_rule_paired_text_attributes(left_article, right_article, [], [])

    assert [alignment["label"] for alignment in alignments] == ["Annual sales", "Market share"]
    assert left_attrs[0]["key"] == "Annual sales"
    assert right_attrs[0]["key"] == "Annual sales"
    assert left_attrs[1]["key"] == "Market share"
    assert right_attrs[1]["key"] == "Market share"
    assert left_attrs[0]["source"] == "main_text"
    assert right_attrs[0]["source"] == "main_text"


def test_build_rule_paired_text_attributes_prefers_annual_sales_over_cumulative_sales():
    left_article = {
        "paragraphs": [
            {
                "id": "left-p-1",
                "sentences": [
                    {
                        "id": "left-s-1-1",
                        "text": "Sales in 2023 totaled 7.4 million units with a market share of 30.2%.",
                    },
                    {
                        "id": "left-s-1-2",
                        "text": (
                            "As sales of new energy vehicles were slower than expected, in September 2013, "
                            "the central government introduced a subsidy scheme providing a maximum of "
                            "US$9,800 toward the purchase of an all-electric passenger vehicle and "
                            "81,600 yuan for an electric bus."
                        ),
                    },
                ],
            }
        ]
    }
    right_article = {
        "paragraphs": [
            {
                "id": "right-p-1",
                "sentences": [
                    {
                        "id": "right-s-1-1",
                        "text": "As of December 2023, cumulative sales totaled 4.7 million plug-in electric cars since 2010.",
                    },
                    {
                        "id": "right-s-1-2",
                        "text": "Sales totaled 1,402,371 units in 2023, with a market share of 9.1%.",
                    },
                ],
            }
        ]
    }

    left_attrs, right_attrs, alignments = build_rule_paired_text_attributes(left_article, right_article, [], [])

    assert [alignment["label"] for alignment in alignments] == ["Annual sales", "Market share"]
    assert left_attrs[0]["sourceIds"] == ["left-s-1-1"]
    assert right_attrs[0]["sourceIds"] == ["right-s-1-2"]
    assert left_attrs[0]["dataRole"] == "quantity"
    assert right_attrs[0]["dataRole"] == "quantity"


def test_build_rule_paired_text_attributes_keeps_cumulative_sales_milestones_separate():
    left_article = {
        "paragraphs": [
            {
                "id": "left-p-1",
                "sentences": [
                    {
                        "id": "left-s-1-1",
                        "text": "Cumulative sales achieved the 500,000 unit milestone in September 2016.",
                    }
                ],
            }
        ]
    }
    right_article = {
        "paragraphs": [
            {
                "id": "right-p-1",
                "sentences": [
                    {
                        "id": "right-s-1-1",
                        "text": "As of December 2023, cumulative sales totaled 4.7 million plug-in electric cars since 2010.",
                    }
                ],
            }
        ]
    }

    left_attrs, right_attrs, alignments = build_rule_paired_text_attributes(left_article, right_article, [], [])

    assert [alignment["label"] for alignment in alignments] == ["Cumulative sales"]
    assert left_attrs[0]["valueText"] == "cumulative sales in 2016 totaled 500,000 units"
    assert right_attrs[0]["valueText"] == "cumulative sales in 2023 totaled 4.7 million units"


def test_build_rule_paired_text_attributes_rejects_monetary_incentives_as_geographic_coverage():
    left_article = {
        "paragraphs": [
            {
                "id": "left-p-1",
                "sentences": [
                    {
                        "id": "left-s-1-1",
                        "text": (
                            "On June 1, 2010, the government announced a trial program to provide "
                            "incentives for new energy vehicles of up to 60,000 yuan (~ US$9,281) "
                            "for battery electric vehicles and 50,000 yuan (~ US$7,634) for "
                            "plug-in hybrids in five cities."
                        ),
                    }
                ],
            }
        ]
    }
    right_article = {
        "paragraphs": [
            {
                "id": "right-p-1",
                "sentences": [
                    {
                        "id": "right-s-1-1",
                        "text": (
                            "and 37 states and had established incentives and tax or fee exemptions "
                            "for BEVs and PHEVs, or utility-rate breaks, and other non-monetary incentives."
                        ),
                    }
                ],
            }
        ]
    }

    left_attrs, right_attrs, alignments = build_rule_paired_text_attributes(left_article, right_article, [], [])

    assert left_attrs == []
    assert right_attrs == []
    assert alignments == []


def test_build_rule_paired_text_attributes_labels_and_deduplicates_quantity_cues():
    left_article = {
        "paragraphs": [
            {
                "id": "left-p-1",
                "sentences": [
                    {"id": "left-s-1-1", "text": "The company had 200 employees."},
                    {"id": "left-s-1-2", "text": "The company later reported 230 employees."},
                    {"id": "left-s-1-3", "text": "The outbreak had 1,000 confirmed cases."},
                ],
            }
        ]
    }
    right_article = {
        "paragraphs": [
            {
                "id": "right-p-1",
                "sentences": [
                    {"id": "right-s-1-1", "text": "The organization had 500 employees."},
                    {"id": "right-s-1-2", "text": "The organization later reported 520 employees."},
                    {"id": "right-s-1-3", "text": "The outbreak had 2,000 confirmed cases."},
                ],
            }
        ]
    }

    left_attrs, right_attrs, alignments = build_rule_paired_text_attributes(left_article, right_article, [], [])

    assert [alignment["label"] for alignment in alignments] == ["Employees", "Confirmed cases"]
    assert [attribute["key"] for attribute in left_attrs] == ["Employees", "Confirmed cases"]
    assert [attribute["key"] for attribute in right_attrs] == ["Employees", "Confirmed cases"]


def test_build_rule_paired_text_attributes_does_not_pair_mismatched_quantity_cues():
    left_article = {
        "paragraphs": [
            {
                "id": "left-p-1",
                "sentences": [{"id": "left-s-1-1", "text": "The company had 200 employees."}],
            }
        ]
    }
    right_article = {
        "paragraphs": [
            {
                "id": "right-p-1",
                "sentences": [{"id": "right-s-1-1", "text": "The experiment included 500 samples."}],
            }
        ]
    }

    left_attrs, right_attrs, alignments = build_rule_paired_text_attributes(left_article, right_article, [], [])

    assert left_attrs == []
    assert right_attrs == []
    assert alignments == []


def test_build_rule_paired_text_attributes_does_not_pair_generic_share_only_claims():
    left_article = {
        "paragraphs": [
            {
                "id": "left-p-1",
                "sentences": [
                    {
                        "id": "left-s-1-1",
                        "text": "Manufacturing industries accounted for 30 percent of GDP and 25 percent of the workforce.",
                    }
                ],
            }
        ]
    }
    right_article = {
        "paragraphs": [
            {
                "id": "right-p-1",
                "sentences": [
                    {
                        "id": "right-s-1-1",
                        "text": "The country's share of world nominal GDP was 17.8 percent.",
                    }
                ],
            }
        ]
    }

    left_attrs, right_attrs, alignments = build_rule_paired_text_attributes(left_article, right_article, [], [])

    assert left_attrs == []
    assert right_attrs == []
    assert alignments == []


def test_build_rule_paired_text_attributes_prefers_metric_role_over_context_year():
    left_article = {
        "paragraphs": [
            {
                "id": "left-p-1",
                "sentences": [{"id": "left-s-1-1", "text": "In 2019 active users grew to 2 million."}],
            }
        ]
    }
    right_article = {
        "paragraphs": [
            {
                "id": "right-p-1",
                "sentences": [{"id": "right-s-1-1", "text": "In 2020 active users grew to 5 million."}],
            }
        ]
    }

    left_attrs, right_attrs, alignments = build_rule_paired_text_attributes(left_article, right_article, [], [])

    assert alignments[0]["label"] == "Users"
    assert left_attrs[0]["dataRole"] == "scale"
    assert right_attrs[0]["dataRole"] == "scale"


def test_build_rule_paired_text_attributes_extracts_financial_prose_metrics():
    left_article = {
        "paragraphs": [
            {
                "id": "left-p-1",
                "sentences": [
                    {"id": "left-s-1-1", "text": "Revenue was $76.4 billion and increased 18%."},
                    {"id": "left-s-1-2", "text": "Operating income was $34.3 billion and increased 23%."},
                    {"id": "left-s-1-3", "text": "Net income was $27.2 billion and increased 24%."},
                    {"id": "left-s-1-4", "text": "Diluted earnings per share was $3.65 and increased 24%."},
                    {"id": "left-s-1-5", "text": "Microsoft Cloud revenue was $46.7 billion, up 27%."},
                ],
            }
        ]
    }
    right_article = {
        "paragraphs": [
            {
                "id": "right-p-1",
                "sentences": [
                    {"id": "right-s-1-1", "text": "Revenue was $64.7 billion and increased 15%."},
                    {"id": "right-s-1-2", "text": "Operating income was $27.9 billion and increased 15%."},
                    {"id": "right-s-1-3", "text": "Net income was $22.0 billion and increased 10%."},
                    {"id": "right-s-1-4", "text": "Diluted earnings per share was $2.95 and increased 10%."},
                    {"id": "right-s-1-5", "text": "Microsoft Cloud revenue was $36.8 billion, up 21%."},
                ],
            }
        ]
    }

    left_attrs, right_attrs, alignments = build_rule_paired_text_attributes(left_article, right_article, [], [])

    labels = [alignment["label"] for alignment in alignments]
    assert labels[:1] == ["Revenue"]
    assert set(labels) >= {
        "Revenue",
        "Operating income",
        "Net income",
        "Diluted earnings per share",
        "Microsoft Cloud revenue",
    }
    assert left_attrs[0]["valueText"] == "revenue was 76.4 billion"
    assert right_attrs[0]["valueText"] == "revenue was 64.7 billion"
