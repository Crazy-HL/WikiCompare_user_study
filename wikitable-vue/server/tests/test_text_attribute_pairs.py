from services.text_attribute_pairs import build_text_evidence_candidates


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
