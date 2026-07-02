from services.text_attribute_pairs import build_paired_text_attributes, build_text_evidence_candidates


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
    assert left_attrs[0]["dataPriority"] is True
    assert right_attrs[0]["sourceIds"] == ["right-s-1-1"]
    assert alignments == [
        {
            "left": left_attrs[0],
            "right": right_attrs[0],
            "label": "Historical emergence",
        }
    ]


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
