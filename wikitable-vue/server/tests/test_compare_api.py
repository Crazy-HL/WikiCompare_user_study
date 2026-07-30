import json
import os
import time
from pathlib import Path
from unittest.mock import patch

from tornado.testing import AsyncHTTPTestCase

import server


FIXTURE_DIR = Path(__file__).parent / "fixtures"


def test_paired_text_alignment_sends_more_than_first_24_data_candidates_to_llm():
    sentences = [
        {"id": f"left-s-1-{index}", "text": f"The service had {index + 1} million users."}
        for index in range(30)
    ]
    right_sentences = [
        {"id": f"right-s-1-{index}", "text": f"The platform had {index + 2} million users."}
        for index in range(30)
    ]
    left_article = {"paragraphs": [{"id": "left-p-1", "text": " ".join(item["text"] for item in sentences), "sentences": sentences}]}
    right_article = {"paragraphs": [{"id": "right-p-1", "text": " ".join(item["text"] for item in right_sentences), "sentences": right_sentences}]}
    captured = {}

    class CapturingLLM:
        def extract_text_attribute_pairs(self, **kwargs):
            captured["left_count"] = len(kwargs["left_candidates"])
            captured["right_count"] = len(kwargs["right_candidates"])
            return {"pairs": []}

    server._build_paired_text_alignments(left_article, right_article, [], [], CapturingLLM())

    assert captured["left_count"] == 30
    assert captured["right_count"] == 30


def test_paired_text_alignment_uses_only_llm_pairs_when_llm_extracts_values():
    left_article = {
        "paragraphs": [
            {
                "id": "left-p-1",
                "text": "Operating margin reached 18.4% in 2024. Revenue was $76.4 billion in 2024.",
                "sentences": [
                    {"id": "left-s-1-1", "text": "Operating margin reached 18.4% in 2024."},
                    {"id": "left-s-1-2", "text": "Revenue was $76.4 billion in 2024."},
                ],
            }
        ]
    }
    right_article = {
        "paragraphs": [
            {
                "id": "right-p-1",
                "text": "Operating margin reached 4.1% in 2024. Revenue was $64.7 billion in 2024.",
                "sentences": [
                    {"id": "right-s-1-1", "text": "Operating margin reached 4.1% in 2024."},
                    {"id": "right-s-1-2", "text": "Revenue was $64.7 billion in 2024."},
                ],
            }
        ]
    }

    class LLMOnlyClient:
        def extract_text_attribute_pairs(self, **_kwargs):
            return {
                "pairs": [
                    {
                        "dimensionLabel": "Operating margin",
                        "comparisonQuestion": "How do operating margins compare?",
                        "left": {
                            "valueText": "operating margin in 2024",
                            "sentenceIds": ["left-s-1-1"],
                            "values": [{"value": 18.4, "year": 2024, "rawText": "18.4%"}],
                        },
                        "right": {
                            "valueText": "operating margin in 2024",
                            "sentenceIds": ["right-s-1-1"],
                            "values": [{"value": 4.1, "year": 2024, "rawText": "4.1%"}],
                        },
                        "dataPriority": True,
                        "dataRole": "proportion",
                        "confidence": 0.93,
                    }
                ]
            }

    _left_attrs, _right_attrs, alignments = server._build_paired_text_alignments(
        left_article,
        right_article,
        [],
        [],
        LLMOnlyClient(),
    )

    assert [alignment["label"] for alignment in alignments] == ["Operating margin"]


def test_paired_text_alignment_uses_llm_reviewed_pairs_only():
    left_article = {
        "paragraphs": [
            {
                "id": "left-p-1",
                "text": (
                    "Broadband fixed subscriptions totaled 39.3 million in 2023. "
                    "There were 2 subscriptions per 100 inhabitants in 2022."
                ),
                "sentences": [
                    {"id": "left-s-1-1", "text": "Broadband fixed subscriptions totaled 39.3 million in 2023."},
                    {"id": "left-s-1-2", "text": "There were 2 subscriptions per 100 inhabitants in 2022."},
                ],
            }
        ]
    }
    right_article = {
        "paragraphs": [
            {
                "id": "right-p-1",
                "text": (
                    "Broadband fixed subscriptions totaled 13.5 million in 2023. "
                    "There were 5 subscriptions per 100 inhabitants in 2023."
                ),
                "sentences": [
                    {"id": "right-s-1-1", "text": "Broadband fixed subscriptions totaled 13.5 million in 2023."},
                    {"id": "right-s-1-2", "text": "There were 5 subscriptions per 100 inhabitants in 2023."},
                ],
            }
        ]
    }

    class ReviewingLLMClient:
        reviewed = False

        def extract_text_attribute_pairs(self, **_kwargs):
            return {
                "pairs": [
                    {
                        "dimensionLabel": "Broadband fixed subscriptions",
                        "comparisonQuestion": "How do broadband fixed subscriptions compare?",
                        "left": {
                            "valueText": "totaled 39.3 million in 2023",
                            "sentenceIds": ["left-s-1-1"],
                            "values": [{"value": 39300000, "year": 2023, "rawText": "39.3 million"}],
                        },
                        "right": {
                            "valueText": "5 subscriptions per 100 inhabitants in 2023",
                            "sentenceIds": ["right-s-1-2"],
                            "values": [{"value": 5, "year": 2023, "rawText": "5"}],
                        },
                        "dataPriority": True,
                        "dataRole": "quantity",
                        "confidence": 0.91,
                    },
                    {
                        "dimensionLabel": "Broadband fixed subscriptions per 100 inhabitants",
                        "comparisonQuestion": "How do broadband fixed subscriptions per 100 inhabitants compare?",
                        "left": {
                            "valueText": "2 subscriptions per 100 inhabitants in 2022",
                            "sentenceIds": ["left-s-1-2"],
                            "values": [{"value": 2, "year": 2022, "rawText": "2"}],
                        },
                        "right": {
                            "valueText": "5 subscriptions per 100 inhabitants in 2023",
                            "sentenceIds": ["right-s-1-2"],
                            "values": [{"value": 5, "year": 2023, "rawText": "5"}],
                        },
                        "dataPriority": True,
                        "dataRole": "quantity",
                        "confidence": 0.94,
                    },
                ]
            }

        def review_text_attribute_pairs(self, *, pair_response, **_kwargs):
            ReviewingLLMClient.reviewed = True
            return {"pairs": [pair_response["pairs"][1]]}

    _left_attrs, _right_attrs, alignments = server._build_paired_text_alignments(
        left_article,
        right_article,
        [],
        [],
        ReviewingLLMClient(),
    )

    assert ReviewingLLMClient.reviewed is True
    assert [alignment["label"] for alignment in alignments] == [
        "Broadband fixed subscriptions per 100 inhabitants"
    ]


def test_paired_text_alignment_does_not_use_rules_when_llm_review_rejects_everything():
    left_article = {
        "paragraphs": [
            {
                "id": "left-p-1",
                "text": "Revenue was $76.4 billion in 2024.",
                "sentences": [{"id": "left-s-1-1", "text": "Revenue was $76.4 billion in 2024."}],
            }
        ]
    }
    right_article = {
        "paragraphs": [
            {
                "id": "right-p-1",
                "text": "Revenue was $64.7 billion in 2024.",
                "sentences": [{"id": "right-s-1-1", "text": "Revenue was $64.7 billion in 2024."}],
            }
        ]
    }

    class RejectingReviewLLMClient:
        def extract_text_attribute_pairs(self, **_kwargs):
            return {
                "pairs": [
                    {
                        "dimensionLabel": "Financial metric",
                        "comparisonQuestion": "How do the financial metrics compare?",
                        "left": {
                            "valueText": "revenue was $76.4 billion in 2024",
                            "sentenceIds": ["left-s-1-1"],
                            "values": [{"value": 76.4, "year": 2024, "rawText": "$76.4 billion"}],
                        },
                        "right": {
                            "valueText": "revenue was $64.7 billion in 2024",
                            "sentenceIds": ["right-s-1-1"],
                            "values": [{"value": 64.7, "year": 2024, "rawText": "$64.7 billion"}],
                        },
                        "dataPriority": True,
                        "dataRole": "scale",
                        "confidence": 0.88,
                    }
                ]
            }

        def review_text_attribute_pairs(self, **_kwargs):
            return {"pairs": []}

    left_attrs, right_attrs, alignments = server._build_paired_text_alignments(
        left_article,
        right_article,
        [],
        [],
        RejectingReviewLLMClient(),
    )

    assert left_attrs == []
    assert right_attrs == []
    assert alignments == []


class CompareApiTest(AsyncHTTPTestCase):
    def get_app(self):
        return server.make_app()

    def test_compare_cache_version_tracks_main_text_chart_extraction_changes(self):
        assert server.COMPARE_CACHE_VERSION == "compare-session-v8"

    def test_compare_session_requires_urls(self):
        response = self.fetch(
            "/api/compare-session",
            method="POST",
            body=json.dumps({"leftUrl": "", "rightUrl": ""}),
            headers={"Content-Type": "application/json"},
        )

        assert response.code == 400
        assert b"leftUrl" in response.body

    def test_compare_session_rejects_invalid_utf8_json_body(self):
        response = self.fetch(
            "/api/compare-session",
            method="POST",
            body=b"\x80",
            headers={"Content-Type": "application/json"},
        )

        assert response.code == 400
        assert response.headers["Content-Type"].startswith("application/json")
        assert json.loads(response.body)["error"]

    def test_compare_session_returns_session_without_network_or_api_key(self):
        left_html = (FIXTURE_DIR / "article_left.html").read_text()
        right_html = (FIXTURE_DIR / "article_right.html").read_text()

        with patch.dict(os.environ, {"OPENAI_API_KEY": ""}, clear=False), patch.object(
            server,
            "fetch_article_html",
            side_effect=[left_html, right_html],
        ):
            response = self.fetch(
                "/api/compare-session",
                method="POST",
                body=json.dumps(
                    {
                        "leftUrl": "https://en.wikipedia.org/wiki/Economy_of_Example_A",
                        "rightUrl": "https://en.wikipedia.org/wiki/Economy_of_Example_B",
                    }
                ),
                headers={"Content-Type": "application/json"},
            )

        assert response.code == 200
        assert response.headers["Content-Type"].startswith("application/json")
        payload = json.loads(response.body)
        assert payload["sessionId"]
        assert payload["articles"]["left"]["title"] == "Economy_of_Example_A"
        assert payload["articles"]["right"]["title"] == "Economy_of_Example_B"
        assert "sourceMap" not in payload["articles"]["left"]
        assert "sourceMap" not in payload["articles"]["right"]
        assert payload["attributePools"]["left"]
        assert payload["attributePools"]["right"]
        assert payload["rankedRows"]
        assert payload["sourceMap"]

    def test_compare_session_accepts_public_web_urls_without_llm(self):
        left_html = """
        <html><body><main>
          <p>Revenue was $76.4 billion and increased 18%.</p>
          <p>Operating income was $34.3 billion and increased 23%.</p>
          <p>Net income was $27.2 billion and increased 24%.</p>
          <p>Diluted earnings per share was $3.65 and increased 24%.</p>
          <p>Microsoft Cloud revenue was $46.7 billion, up 27%.</p>
        </main></body></html>
        """
        right_html = """
        <html><body><main>
          <p>Revenue was $64.7 billion and increased 15%.</p>
          <p>Operating income was $27.9 billion and increased 15%.</p>
          <p>Net income was $22.0 billion and increased 10%.</p>
          <p>Diluted earnings per share was $2.95 and increased 10%.</p>
          <p>Microsoft Cloud revenue was $36.8 billion, up 21%.</p>
        </main></body></html>
        """

        with patch.dict(os.environ, {"OPENAI_API_KEY": ""}, clear=False), patch.object(
            server,
            "_fetch_generic_page_html",
            side_effect=[left_html, right_html],
        ):
            response = self.fetch(
                "/api/compare-session",
                method="POST",
                body=json.dumps(
                    {
                        "leftUrl": "https://www.microsoft.com/en-us/investor/earnings/fy-2025-q4/press-release-webcast",
                        "rightUrl": "https://www.microsoft.com/en-us/investor/earnings/fy-2024-q4/press-release-webcast",
                        "leftTitle": "Microsoft FY25 Q4 earnings",
                        "rightTitle": "Microsoft FY24 Q4 earnings",
                        "forceRefresh": True,
                    }
                ),
                headers={"Content-Type": "application/json"},
            )

        payload = json.loads(response.body)
        chart_rows = [
            row
            for row in payload["rankedRows"]
            if row["sourceKind"] == "main_text"
            and row["chartType"] != "text"
            and row["visualization"]["left"].get("values")
            and row["visualization"]["right"].get("values")
        ]

        assert response.code == 200
        assert payload["articles"]["left"]["title"] == "Microsoft FY25 Q4 earnings"
        assert payload["articles"]["right"]["title"] == "Microsoft FY24 Q4 earnings"
        assert payload["articles"]["left"]["sourceKind"] == "web"
        assert payload["articles"]["right"]["sourceKind"] == "web"
        assert payload["articles"]["left"]["url"].startswith("https://www.microsoft.com/")
        assert payload["articles"]["right"]["url"].startswith("https://www.microsoft.com/")
        assert len(chart_rows) >= 5
        assert {row["label"] for row in chart_rows} >= {
            "Revenue",
            "Operating income",
            "Net income",
            "Diluted earnings per share",
            "Share / rate",
        }
        assert payload["warnings"]

    def test_compare_session_accepts_manual_article_content_without_fetching_pages(self):
        server.SESSION_STORE.clear()
        server.ARTICLE_HTML_CACHE.clear()
        with patch.dict(os.environ, {"OPENAI_API_KEY": ""}, clear=False), patch.object(
            server,
            "fetch_article_html",
            side_effect=AssertionError("manual content should not fetch Wikipedia"),
        ), patch.object(
            server,
            "_fetch_generic_page_html",
            side_effect=AssertionError("manual content should not fetch public pages"),
        ):
            response = self.fetch(
                "/api/compare-session",
                method="POST",
                body=json.dumps(
                    {
                        "leftContent": (
                            "Revenue was $76.4 billion in 2024. "
                            "Operating income was $34.3 billion in 2024."
                        ),
                        "rightContent": (
                            "Revenue was $64.7 billion in 2024. "
                            "Operating income was $27.9 billion in 2024."
                        ),
                        "leftTitle": "Manual FY2025 article",
                        "rightTitle": "Manual FY2024 article",
                    }
                ),
                headers={"Content-Type": "application/json"},
            )

        payload = json.loads(response.body)
        rows_by_label = {row["label"]: row for row in payload["rankedRows"]}
        assert response.code == 200
        assert payload["articles"]["left"]["sourceKind"] == "manual"
        assert payload["articles"]["right"]["sourceKind"] == "manual"
        assert payload["articles"]["left"]["url"].startswith("manual://")
        assert payload["articles"]["right"]["url"].startswith("manual://")
        assert payload["articles"]["left"]["inputContent"].startswith("Revenue was $76.4 billion")
        assert payload["articles"]["right"]["inputContent"].startswith("Revenue was $64.7 billion")
        assert payload["articles"]["left"]["title"] == "Manual FY2025 article"
        assert payload["articles"]["right"]["title"] == "Manual FY2024 article"
        assert "Revenue" in rows_by_label
        assert rows_by_label["Revenue"]["sourceKind"] == "main_text"
        assert rows_by_label["Revenue"]["visualization"]["left"]["raw"].lower().startswith("revenue")

    def test_manual_content_falls_back_to_local_text_pairs_when_llm_returns_no_pairs(self):
        class EmptyManualLLMClient:
            def __init__(self, _config):
                pass

            def extract_text_attributes(self, _side, _paragraphs):
                return []

            def extract_text_attribute_pairs(self, **_kwargs):
                return {"pairs": []}

            def review_text_attribute_pairs(self, **_kwargs):
                return {"pairs": []}

            def refine_extracted_values(self, **_kwargs):
                return []

        server.SESSION_STORE.clear()
        server.ARTICLE_HTML_CACHE.clear()
        with patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"}, clear=False), patch.object(
            server,
            "LLMClient",
            EmptyManualLLMClient,
        ):
            response = self.fetch(
                "/api/compare-session",
                method="POST",
                body=json.dumps(
                    {
                        "leftContent": (
                            "Revenue was $76.4 billion in 2024. "
                            "Operating income was $34.3 billion in 2024."
                        ),
                        "rightContent": (
                            "Revenue was $64.7 billion in 2024. "
                            "Operating income was $27.9 billion in 2024."
                        ),
                        "leftTitle": "Manual FY2025 article",
                        "rightTitle": "Manual FY2024 article",
                        "forceRefresh": True,
                    }
                ),
                headers={"Content-Type": "application/json"},
            )

        payload = json.loads(response.body)
        labels = [row["label"] for row in payload["rankedRows"]]
        assert response.code == 200
        assert "Revenue" in labels
        assert payload["articles"]["left"]["sourceKind"] == "manual"

    def test_compare_session_preserves_revision_urls_in_payload(self):
        left_html = (FIXTURE_DIR / "article_left.html").read_text()
        right_html = (FIXTURE_DIR / "article_right.html").read_text()

        server.SESSION_STORE.clear()
        server.ARTICLE_HTML_CACHE.clear()
        with patch.dict(os.environ, {"OPENAI_API_KEY": ""}, clear=False), patch.object(
            server,
            "fetch_article_html",
            side_effect=[left_html, right_html],
        ) as fetch_article:
            response = self.fetch(
                "/api/compare-session",
                method="POST",
                body=json.dumps(
                    {
                        "leftUrl": "https://en.wikipedia.org/w/index.php?title=Economy_of_Example_A&oldid=111",
                        "rightUrl": "https://en.wikipedia.org/w/index.php?title=Economy_of_Example_B&oldid=222",
                    }
                ),
                headers={"Content-Type": "application/json"},
            )

        payload = json.loads(response.body)
        assert response.code == 200
        assert payload["articles"]["left"]["url"].endswith("title=Economy_of_Example_A&oldid=111")
        assert payload["articles"]["right"]["url"].endswith("title=Economy_of_Example_B&oldid=222")
        assert payload["articles"]["left"]["revision"] == "111"
        assert payload["articles"]["right"]["revision"] == "222"
        assert fetch_article.call_args_list[0].args == ("Economy_of_Example_A", "111")
        assert fetch_article.call_args_list[1].args == ("Economy_of_Example_B", "222")

    def test_compare_session_returns_rows_for_concept_articles_without_infobox_or_llm(self):
        left_html = """
        <html><body><main>
          <p>Artificial intelligence is intelligence exhibited by machines. The field was founded as an academic discipline in 1956.</p>
          <p>Applications include search engines, recommendation systems, and robotics.</p>
        </main></body></html>
        """
        right_html = """
        <html><body><main>
          <p>Machine learning is a field of study in artificial intelligence. Machine learning grew from pattern recognition.</p>
          <p>Uses include computer vision, speech recognition, and language processing.</p>
        </main></body></html>
        """

        server.SESSION_STORE.clear()
        server.ARTICLE_HTML_CACHE.clear()
        with patch.dict(os.environ, {"OPENAI_API_KEY": ""}, clear=False), patch.object(
            server,
            "fetch_article_html",
            side_effect=[left_html, right_html],
        ):
            response = self.fetch(
                "/api/compare-session",
                method="POST",
                body=json.dumps(
                    {
                        "leftUrl": "https://en.wikipedia.org/wiki/Artificial_intelligence",
                        "rightUrl": "https://en.wikipedia.org/wiki/Machine_learning",
                    }
                ),
                headers={"Content-Type": "application/json"},
            )

        payload = json.loads(response.body)
        labels = [row["label"] for row in payload["rankedRows"]]
        assert response.code == 200
        assert "Overview" in labels
        assert "Applications" in labels
        assert len(payload["rankedRows"]) >= 2

    def test_compare_session_uses_rule_paired_data_when_llm_disabled(self):
        left_html = """
        <html><body><main>
          <p>Artificial intelligence was founded as an academic discipline in 1956.</p>
        </main></body></html>
        """
        right_html = """
        <html><body><main>
          <p>Machine learning emerged from pattern recognition in 1959.</p>
        </main></body></html>
        """

        server.SESSION_STORE.clear()
        server.ARTICLE_HTML_CACHE.clear()
        with patch.dict(os.environ, {"OPENAI_API_KEY": ""}, clear=False), patch.object(
            server,
            "fetch_article_html",
            side_effect=[left_html, right_html],
        ):
            response = self.fetch(
                "/api/compare-session",
                method="POST",
                body=json.dumps(
                    {
                        "leftUrl": "https://en.wikipedia.org/wiki/Artificial_intelligence_rule_paired",
                        "rightUrl": "https://en.wikipedia.org/wiki/Machine_learning_rule_paired",
                    }
                ),
                headers={"Content-Type": "application/json"},
            )

        payload = json.loads(response.body)
        labels = [row["label"] for row in payload["rankedRows"]]
        assert response.code == 200
        assert "Historical emergence" in labels

    def test_compare_session_charts_main_text_sales_and_capacity_without_infobox(self):
        left_html = """
        <html><body><main>
          <p>Sales in 2023 totaled 7.4 million units with a market share of 30.2%.</p>
          <p>Its PV capacity crossed 1,000 gigawatts in May 2025.</p>
        </main></body></html>
        """
        right_html = """
        <html><body><main>
          <p>Sales totaled 1,402,371 units in 2023, with a market share of 9.1%.</p>
          <p>As of the end of 2024, the United States had 239 gigawatts of installed photovoltaic capacity.</p>
        </main></body></html>
        """

        server.SESSION_STORE.clear()
        server.ARTICLE_HTML_CACHE.clear()
        with patch.dict(os.environ, {"OPENAI_API_KEY": ""}, clear=False), patch.object(
            server,
            "fetch_article_html",
            side_effect=[left_html, right_html],
        ):
            response = self.fetch(
                "/api/compare-session",
                method="POST",
                body=json.dumps(
                    {
                        "leftUrl": "https://en.wikipedia.org/wiki/Main_text_EV_China",
                        "rightUrl": "https://en.wikipedia.org/wiki/Main_text_EV_US",
                    }
                ),
                headers={"Content-Type": "application/json"},
            )

        payload = json.loads(response.body)
        main_text_chart_rows = [
            row
            for row in payload["rankedRows"]
            if row["sourceKind"] == "main_text" and row["chartType"] != "text"
        ]
        rows_by_label = {row["label"]: row for row in main_text_chart_rows}
        assert response.code == 200
        assert set(rows_by_label) == {"Annual sales", "Market share"}
        assert all(row["dataPriority"] is True for row in main_text_chart_rows)
        assert rows_by_label["Annual sales"]["leftSourceIds"] == ["left-s-1-1"]
        assert rows_by_label["Market share"]["dataType"] == "Proportional"

    def test_compare_session_expands_body_text_ev_metrics_into_multiple_chart_rows(self):
        left_html = """
        <html><body><main>
          <p>Sales in 2023 totaled 7.4 million units with a market share of 30.2%.</p>
          <p>Sales passed the 500,000 unit milestone in March 2016.</p>
          <p>China has annual production capacity of 500,000 vehicles and a sales target of 5 million vehicles.</p>
          <p>Cumulative sales totaled 4.7 million plug-in cars since 2010.</p>
          <p>A subsidy scheme provided a maximum of US$9,800 toward the purchase of an all-electric passenger vehicle.</p>
        </main></body></html>
        """
        right_html = """
        <html><body><main>
          <p>Sales totaled 1,402,371 units in 2023, with a market share of 9.1%.</p>
          <p>The American market surpassed the 1 million sales mark.</p>
          <p>The United States had production capacity of 200,000 vehicles and a sales target of 1 million vehicles.</p>
          <p>Cumulative sales in the U.S. totaled 4.7 million plug-in electric cars since 2010.</p>
          <p>Federal tax credits for new qualified plug-in electric vehicles were worth up to US$7,500.</p>
        </main></body></html>
        """

        server.SESSION_STORE.clear()
        server.ARTICLE_HTML_CACHE.clear()
        with patch.dict(os.environ, {"OPENAI_API_KEY": ""}, clear=False), patch.object(
            server,
            "fetch_article_html",
            side_effect=[left_html, right_html],
        ):
            response = self.fetch(
                "/api/compare-session",
                method="POST",
                body=json.dumps(
                    {
                        "leftUrl": "https://en.wikipedia.org/wiki/Body_EV_China",
                        "rightUrl": "https://en.wikipedia.org/wiki/Body_EV_US",
                    }
                ),
                headers={"Content-Type": "application/json"},
            )

        payload = json.loads(response.body)
        main_text_chart_rows = [
            row
            for row in payload["rankedRows"]
            if row["sourceKind"] == "main_text" and row["chartType"] != "text"
        ]
        rows_by_label = {row["label"]: row for row in main_text_chart_rows}
        assert response.code == 200
        assert set(rows_by_label) >= {
            "Annual sales",
            "Market share",
            "Sales target",
            "Production capacity",
            "Cumulative sales",
            "Purchase incentive",
        }
        assert "Sales milestone" not in rows_by_label
        assert rows_by_label["Annual sales"]["dataType"] == "Numerical"
        assert rows_by_label["Annual sales"]["visualization"]["left"]["values"] == [
            {"value": 7400000.0, "year": 2023, "label": "sales"}
        ]
        assert rows_by_label["Market share"]["dataType"] == "Proportional"
        assert rows_by_label["Market share"]["visualization"]["left"]["values"] == [
            {"value": 30.2, "year": 2023, "label": "market share"}
        ]

    def test_compare_session_charts_body_table_year_series_as_main_text(self):
        left_html = """
        <html><body><main>
          <table class="wikitable">
            <tr><th>Year</th><th>Capacity (MW)</th><th>Installed/yr</th></tr>
            <tr><td>2020</td><td>250</td><td>50</td></tr>
            <tr><td>2021</td><td>400</td><td>150</td></tr>
            <tr><td>2022</td><td>700</td><td>300</td></tr>
          </table>
        </main></body></html>
        """
        right_html = """
        <html><body><main>
          <table class="wikitable">
            <tr><th>Year</th><th>Total (MWp)</th><th>Installed capacity (MWp)</th></tr>
            <tr><td>2020</td><td>300</td><td>80</td></tr>
            <tr><td>2021</td><td>500</td><td>200</td></tr>
            <tr><td>2022</td><td>900</td><td>400</td></tr>
          </table>
        </main></body></html>
        """

        server.SESSION_STORE.clear()
        server.ARTICLE_HTML_CACHE.clear()
        with patch.dict(os.environ, {"OPENAI_API_KEY": ""}, clear=False), patch.object(
            server,
            "fetch_article_html",
            side_effect=[left_html, right_html],
        ):
            response = self.fetch(
                "/api/compare-session",
                method="POST",
                body=json.dumps(
                    {
                        "leftUrl": "https://en.wikipedia.org/wiki/Solar_Table_A",
                        "rightUrl": "https://en.wikipedia.org/wiki/Solar_Table_B",
                    }
                ),
                headers={"Content-Type": "application/json"},
            )

        payload = json.loads(response.body)
        rows_by_label = {row["label"]: row for row in payload["rankedRows"]}
        assert response.code == 200
        assert rows_by_label["Capacity"]["sourceKind"] == "main_text"
        assert rows_by_label["Capacity"]["dataType"] == "Trend"
        assert rows_by_label["Capacity"]["chartType"] == "line"
        assert rows_by_label["Capacity"]["visualization"]["left"]["values"] == [
            {"value": 250.0, "year": 2020},
            {"value": 400.0, "year": 2021},
            {"value": 700.0, "year": 2022},
        ]
        assert rows_by_label["Installed"]["chartType"] == "line"

    def test_compare_session_aligns_repeated_infobox_keys_by_value_shape(self):
        left_html = """
        <html><body><main>
          <table class="infobox">
            <tr><th>15–64 years</th><td>67.49% (male 472,653,000/female 447,337,000) (2021 est.)</td></tr>
            <tr><th>15–64 years</th><td>1.07 male(s)/female (2023 est.)</td></tr>
            <tr><th>65 and over</th><td>6.83% (male 44,275,000/female 48,751,000) (2021 est.)</td></tr>
            <tr><th>65 and over</th><td>0.85 male(s)/female (2023)</td></tr>
          </table>
          <p>India has age and sex-ratio demographic indicators.</p>
        </main></body></html>
        """
        right_html = """
        <html><body><main>
          <table class="infobox">
            <tr><th>15–64 years</th><td>69.4% (male 504,637,819/female 476,146,909)</td></tr>
            <tr><th>15–64 years</th><td>1.06 male to female (2024 est.)</td></tr>
            <tr><th>65 and over</th><td>14.11% (male 92,426,805/female 107,035,710) (2023 est.)</td></tr>
            <tr><th>65 and over</th><td>0.86 male to female (2024 est.)</td></tr>
          </table>
          <p>China has age and sex-ratio demographic indicators.</p>
        </main></body></html>
        """

        server.SESSION_STORE.clear()
        server.ARTICLE_HTML_CACHE.clear()
        with patch.dict(os.environ, {"OPENAI_API_KEY": ""}, clear=False), patch.object(
            server,
            "fetch_article_html",
            side_effect=[left_html, right_html],
        ):
            response = self.fetch(
                "/api/compare-session",
                method="POST",
                body=json.dumps(
                    {
                        "leftUrl": "https://en.wikipedia.org/wiki/Demographics_of_Example_A",
                        "rightUrl": "https://en.wikipedia.org/wiki/Demographics_of_Example_B",
                    }
                ),
                headers={"Content-Type": "application/json"},
            )

        payload = json.loads(response.body)
        age_15_64 = next(row for row in payload["rankedRows"] if row["label"] == "15–64 years")
        age_65 = next(row for row in payload["rankedRows"] if row["label"] == "65 and over")
        assert response.code == 200
        assert "67.49%" in age_15_64["visualization"]["left"]["raw"]
        assert "69.4%" in age_15_64["visualization"]["right"]["raw"]
        assert "6.83%" in age_65["visualization"]["left"]["raw"]
        assert "14.11%" in age_65["visualization"]["right"]["raw"]

    def test_compare_session_falls_back_when_llm_returns_empty_pairs(self):
        left_html = """
        <html><body><main>
          <p>Artificial intelligence was founded as an academic discipline in 1956.</p>
        </main></body></html>
        """
        right_html = """
        <html><body><main>
          <p>Machine learning emerged from pattern recognition in 1959.</p>
        </main></body></html>
        """

        class EmptyPairLLMClient:
            def __init__(self, _config):
                pass

            def extract_text_attributes(self, _side, _paragraphs):
                return []

            def extract_text_attribute_pairs(self, **_kwargs):
                return {"pairs": []}

            def refine_extracted_values(self, **_kwargs):
                return []

        server.SESSION_STORE.clear()
        server.ARTICLE_HTML_CACHE.clear()
        with patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"}, clear=False), patch.object(
            server,
            "LLMClient",
            EmptyPairLLMClient,
        ), patch.object(
            server,
            "fetch_article_html",
            side_effect=[left_html, right_html],
        ):
            response = self.fetch(
                "/api/compare-session",
                method="POST",
                body=json.dumps(
                    {
                        "leftUrl": "https://en.wikipedia.org/wiki/Artificial_intelligence_empty_pair",
                        "rightUrl": "https://en.wikipedia.org/wiki/Machine_learning_empty_pair",
                    }
                ),
                headers={"Content-Type": "application/json"},
            )

        payload = json.loads(response.body)
        labels = [row["label"] for row in payload["rankedRows"]]
        assert response.code == 200
        assert "Historical emergence" in labels

    def test_compare_session_uses_paired_text_attributes_from_llm(self):
        left_html = """
        <html><body><main>
          <p>Artificial intelligence is intelligence exhibited by machines. The field was founded as an academic discipline in 1956.</p>
          <p>Applications include search engines, recommendation systems, and robotics.</p>
        </main></body></html>
        """
        right_html = """
        <html><body><main>
          <p>Machine learning is a field of study in artificial intelligence. Machine learning grew from pattern recognition in 1959.</p>
          <p>Applications include computer vision, speech recognition, and language processing.</p>
        </main></body></html>
        """

        class FakeLLMClient:
            def __init__(self, _config):
                pass

            def extract_text_attributes(self, _side, _paragraphs):
                return []

            def extract_text_attribute_pairs(self, *, left_body, right_body, infobox_context, left_candidates=None, right_candidates=None):
                assert left_body["paragraphs"]
                assert right_body["paragraphs"]
                assert left_candidates
                assert right_candidates
                assert "left" in infobox_context
                assert "right" in infobox_context
                return {
                    "pairs": [
                        {
                            "dimensionLabel": "Historical emergence",
                            "comparisonQuestion": "When did each field emerge?",
                            "left": {
                                "valueText": "founded as an academic discipline in 1956",
                                "sentenceIds": ["left-s-1-2"],
                            },
                            "right": {
                                "valueText": "grew from pattern recognition in 1959",
                                "sentenceIds": ["right-s-1-2"],
                            },
                            "dataPriority": True,
                            "dataRole": "emergence_time",
                            "confidence": 0.9,
                        },
                        {
                            "dimensionLabel": "Applications",
                            "comparisonQuestion": "What are common applications?",
                            "left": {
                                "valueText": "search engines, recommendation systems, and robotics",
                                "sentenceIds": ["left-s-2-1"],
                            },
                            "right": {
                                "valueText": "computer vision, speech recognition, and language processing",
                                "sentenceIds": ["right-s-2-1"],
                            },
                            "dataPriority": False,
                            "dataRole": None,
                            "confidence": 0.85,
                        },
                    ]
                }

            def refine_extracted_values(self, **_kwargs):
                return []

        server.SESSION_STORE.clear()
        server.ARTICLE_HTML_CACHE.clear()
        with patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"}, clear=False), patch.object(
            server,
            "LLMClient",
            FakeLLMClient,
        ), patch.object(
            server,
            "fetch_article_html",
            side_effect=[left_html, right_html],
        ):
            response = self.fetch(
                "/api/compare-session",
                method="POST",
                body=json.dumps(
                    {
                        "leftUrl": "https://en.wikipedia.org/wiki/Artificial_intelligence_paired",
                        "rightUrl": "https://en.wikipedia.org/wiki/Machine_learning_paired",
                    }
                ),
                headers={"Content-Type": "application/json"},
            )

        payload = json.loads(response.body)
        labels = [row["label"] for row in payload["rankedRows"]]
        historical = next(row for row in payload["rankedRows"] if row["label"] == "Historical emergence")
        applications = next(row for row in payload["rankedRows"] if row["label"] == "Applications")
        assert response.code == 200
        assert "Historical emergence" in labels
        assert "Applications" in labels
        assert labels.index("Applications") < labels.index("Historical emergence")
        assert historical["leftSourceIds"] == ["left-s-1-2"]
        assert historical["rightSourceIds"] == ["right-s-1-2"]
        assert historical["dataPriority"] is False
        assert historical["dataType"] == "Text"
        assert historical["chartType"] == "text"
        assert historical["visualization"]["left"]["values"] == []
        assert historical["visualization"]["right"]["values"] == []
        assert applications["leftSourceIds"] == ["left-s-2-1"]
        assert applications["rightSourceIds"] == ["right-s-2-1"]
        assert historical["sourceKind"] == "main_text"
        assert applications["sourceKind"] == "main_text"

    def test_compare_session_sends_full_body_to_llm_for_paragraph_chart_attributes(self):
        left_html = """
        <html><body><main>
          <p>The company operates marketplaces and cloud services.</p>
          <p>Its advertising business expanded internationally.</p>
          <p>Operating margin reached 18.4% in 2024 after logistics costs declined.</p>
        </main></body></html>
        """
        right_html = """
        <html><body><main>
          <p>The retailer operates stores and e-commerce services.</p>
          <p>Its advertising network expanded across suppliers.</p>
          <p>Operating margin reached 4.1% in 2024 after wage and supply chain costs rose.</p>
        </main></body></html>
        """

        class FullBodyLLMClient:
            def __init__(self, _config):
                pass

            def extract_text_attributes(self, _side, _paragraphs):
                return []

            def extract_text_attribute_pairs(self, *, left_body, right_body, infobox_context, left_candidates=None, right_candidates=None):
                assert "left" in infobox_context
                assert "right" in infobox_context
                assert left_candidates is not None
                assert right_candidates is not None
                assert any(
                    paragraph["id"] == "left-p-3"
                    and paragraph["sentences"][0]["id"] == "left-s-3-1"
                    and "Operating margin reached 18.4%" in paragraph["text"]
                    for paragraph in left_body["paragraphs"]
                )
                assert any(
                    paragraph["id"] == "right-p-3"
                    and paragraph["sentences"][0]["id"] == "right-s-3-1"
                    and "Operating margin reached 4.1%" in paragraph["text"]
                    for paragraph in right_body["paragraphs"]
                )
                return {
                    "pairs": [
                        {
                            "dimensionLabel": "Operating margin",
                            "comparisonQuestion": "How do operating margins compare?",
                            "left": {
                                "valueText": "operating margin in 2024 was 18.4%",
                                "sentenceIds": ["left-s-3-1"],
                                "values": [{"value": 18.4, "year": 2024, "rawText": "18.4%"}],
                            },
                            "right": {
                                "valueText": "operating margin in 2024 was 4.1%",
                                "sentenceIds": ["right-s-3-1"],
                                "values": [{"value": 4.1, "year": 2024, "rawText": "4.1%"}],
                            },
                            "dataPriority": True,
                            "dataRole": "proportion",
                            "confidence": 0.92,
                        }
                    ]
                }

            def refine_extracted_values(self, **_kwargs):
                return []

        server.SESSION_STORE.clear()
        server.ARTICLE_HTML_CACHE.clear()
        with patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"}, clear=False), patch.object(
            server,
            "LLMClient",
            FullBodyLLMClient,
        ), patch.object(
            server,
            "fetch_article_html",
            side_effect=[left_html, right_html],
        ):
            response = self.fetch(
                "/api/compare-session",
                method="POST",
                body=json.dumps(
                    {
                        "leftUrl": "https://en.wikipedia.org/wiki/Full_Body_A",
                        "rightUrl": "https://en.wikipedia.org/wiki/Full_Body_B",
                    }
                ),
                headers={"Content-Type": "application/json"},
            )

        payload = json.loads(response.body)
        rows_by_label = {row["label"]: row for row in payload["rankedRows"]}
        assert response.code == 200
        assert rows_by_label["Operating margin"]["sourceKind"] == "main_text"
        assert rows_by_label["Operating margin"]["chartType"] == "bar"
        assert rows_by_label["Operating margin"]["visualization"]["left"]["values"] == [
            {"value": 18.4, "year": 2024, "rawText": "18.4%"}
        ]
        assert rows_by_label["Operating margin"]["visualization"]["right"]["values"] == [
            {"value": 4.1, "year": 2024, "rawText": "4.1%"}
        ]

    def test_compare_session_uses_llm_structured_values_for_paragraph_charts(self):
        left_html = """
        <html><body><main>
          <p>Operating margin reached 18.4% in 2024 after logistics costs declined.</p>
        </main></body></html>
        """
        right_html = """
        <html><body><main>
          <p>Operating margin reached 4.1% in 2024 after wage and supply chain costs rose.</p>
        </main></body></html>
        """

        class StructuredValueLLMClient:
            def __init__(self, _config):
                pass

            def extract_text_attributes(self, _side, _paragraphs):
                return []

            def extract_text_attribute_pairs(self, **_kwargs):
                return {
                    "pairs": [
                        {
                            "dimensionLabel": "Operating margin",
                            "comparisonQuestion": "How do operating margins compare?",
                            "left": {
                                "valueText": "operating margin in 2024",
                                "sentenceIds": ["left-s-1-1"],
                                "values": [
                                    {"value": 18.4, "year": 2024, "rawText": "18.4%", "confidence": 0.96}
                                ],
                            },
                            "right": {
                                "valueText": "operating margin in 2024",
                                "sentenceIds": ["right-s-1-1"],
                                "values": [
                                    {"value": 4.1, "year": 2024, "rawText": "4.1%", "confidence": 0.96}
                                ],
                            },
                            "dataPriority": True,
                            "dataRole": "proportion",
                            "confidence": 0.93,
                        }
                    ]
                }

            def refine_extracted_values(self, **_kwargs):
                return []

        server.SESSION_STORE.clear()
        server.ARTICLE_HTML_CACHE.clear()
        with patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"}, clear=False), patch.object(
            server,
            "LLMClient",
            StructuredValueLLMClient,
        ), patch.object(
            server,
            "fetch_article_html",
            side_effect=[left_html, right_html],
        ):
            response = self.fetch(
                "/api/compare-session",
                method="POST",
                body=json.dumps(
                    {
                        "leftUrl": "https://en.wikipedia.org/wiki/Structured_Value_A",
                        "rightUrl": "https://en.wikipedia.org/wiki/Structured_Value_B",
                    }
                ),
                headers={"Content-Type": "application/json"},
            )

        payload = json.loads(response.body)
        rows_by_label = {row["label"]: row for row in payload["rankedRows"]}
        assert response.code == 200
        assert rows_by_label["Operating margin"]["sourceKind"] == "main_text"
        assert rows_by_label["Operating margin"]["dataType"] == "Proportional"
        assert rows_by_label["Operating margin"]["chartType"] == "bar"
        assert rows_by_label["Operating margin"]["visualization"]["left"]["values"] == [
            {"value": 18.4, "year": 2024, "rawText": "18.4%", "confidence": 0.96}
        ]
        assert rows_by_label["Operating margin"]["visualization"]["right"]["values"] == [
            {"value": 4.1, "year": 2024, "rawText": "4.1%", "confidence": 0.96}
        ]

    def test_compare_session_rejects_incompatible_llm_measurement_pair(self):
        left_html = """
        <html><body><main>
          <table class="infobox">
            <tr><th>Confirmed cases</th><td>26,969,913</td></tr>
          </table>
          <p>Overall, there have been 26,969,913 confirmed cases and 198,523 deaths.</p>
        </main></body></html>
        """
        right_html = """
        <html><body><main>
          <table class="infobox">
            <tr><th>Confirmed cases</th><td>13,980,340</td></tr>
          </table>
          <p>By 13 March, cases had been confirmed in all 50 provinces of the country.</p>
        </main></body></html>
        """

        class BadPairLLMClient:
            def __init__(self, _config):
                pass

            def extract_text_attributes(self, _side, _paragraphs):
                return []

            def extract_text_attribute_pairs(self, **_kwargs):
                return {
                    "pairs": [
                        {
                            "dimensionLabel": "Cases",
                            "comparisonQuestion": "How do cases compare?",
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
                        }
                    ]
                }

            def refine_extracted_values(self, **_kwargs):
                return []

        server.SESSION_STORE.clear()
        server.ARTICLE_HTML_CACHE.clear()
        with patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"}, clear=False), patch.object(
            server,
            "LLMClient",
            BadPairLLMClient,
        ), patch.object(
            server,
            "fetch_article_html",
            side_effect=[left_html, right_html],
        ):
            response = self.fetch(
                "/api/compare-session",
                method="POST",
                body=json.dumps(
                    {
                        "leftUrl": "https://en.wikipedia.org/wiki/COVID_Example_A",
                        "rightUrl": "https://en.wikipedia.org/wiki/COVID_Example_B",
                    }
                ),
                headers={"Content-Type": "application/json"},
            )

        payload = json.loads(response.body)
        rows_by_label = {row["label"]: row for row in payload["rankedRows"]}
        assert response.code == 200
        assert "Cases" not in rows_by_label
        assert rows_by_label["Confirmed cases"]["sourceKind"] == "Infobox"
        assert rows_by_label["Confirmed cases"]["visualization"]["right"]["raw"] == "13,980,340"

    def test_compare_session_suppresses_generic_rule_text_when_paired_text_exists(self):
        left_html = """
        <html><body><main>
          <p>Applications include rooftop systems and solar farms.</p>
          <p>After incentives were introduced in 2011, China's solar market grew dramatically.</p>
          <p>Solar power is cheaper than coal-fired power in China.</p>
        </main></body></html>
        """
        right_html = """
        <html><body><main>
          <p>Applications include solar farms and local distributed generation.</p>
          <p>These units may feed a high-capacity transmission substation.</p>
          <p>Solar is second only to onshore wind turbines in levelized cost competitiveness.</p>
        </main></body></html>
        """

        class PairLLMClient:
            def __init__(self, _config):
                pass

            def extract_text_attributes(self, _side, _paragraphs):
                return []

            def extract_text_attribute_pairs(self, **_kwargs):
                return {
                    "pairs": [
                        {
                            "dimensionLabel": "Solar cost competitiveness",
                            "comparisonQuestion": "How competitive is solar power on cost?",
                            "left": {
                                "valueText": "solar power is cheaper than coal-fired power in China",
                                "sentenceIds": ["left-s-3-1"],
                            },
                            "right": {
                                "valueText": "solar is second only to onshore wind turbines in levelized cost competitiveness",
                                "sentenceIds": ["right-s-3-1"],
                            },
                            "dataPriority": False,
                            "dataRole": None,
                            "confidence": 0.86,
                        }
                    ]
                }

            def refine_extracted_values(self, **_kwargs):
                return []

        server.SESSION_STORE.clear()
        server.ARTICLE_HTML_CACHE.clear()
        with patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"}, clear=False), patch.object(
            server,
            "LLMClient",
            PairLLMClient,
        ), patch.object(
            server,
            "fetch_article_html",
            side_effect=[left_html, right_html],
        ):
            response = self.fetch(
                "/api/compare-session",
                method="POST",
                body=json.dumps(
                    {
                        "leftUrl": "https://en.wikipedia.org/wiki/Solar_power_in_Example_A",
                        "rightUrl": "https://en.wikipedia.org/wiki/Solar_power_in_Example_B",
                    }
                ),
                headers={"Content-Type": "application/json"},
            )

        payload = json.loads(response.body)
        labels = [row["label"] for row in payload["rankedRows"]]
        assert response.code == 200
        assert labels == ["Solar cost competitiveness"]

    def test_compare_session_does_not_bulk_refine_values_with_llm(self):
        left_html = (FIXTURE_DIR / "article_left.html").read_text()
        right_html = (FIXTURE_DIR / "article_right.html").read_text()

        class FakeLLMClient:
            refine_calls = 0

            def __init__(self, _config):
                pass

            def extract_text_attributes(self, _side, _paragraphs):
                return []

            def refine_extracted_values(self, **_kwargs):
                FakeLLMClient.refine_calls += 1
                return []

        with patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"}, clear=False), patch.object(
            server,
            "LLMClient",
            FakeLLMClient,
        ), patch.object(
            server,
            "fetch_article_html",
            side_effect=[left_html, right_html],
        ):
            response = self.fetch(
                "/api/compare-session",
                method="POST",
                body=json.dumps(
                    {
                        "leftUrl": "https://en.wikipedia.org/wiki/Economy_of_Example_A",
                        "rightUrl": "https://en.wikipedia.org/wiki/Economy_of_Example_B",
                    }
                ),
                headers={"Content-Type": "application/json"},
            )

        assert response.code == 200
        assert FakeLLMClient.refine_calls == 0

    def test_compare_session_extracts_left_and_right_text_attributes_in_parallel(self):
        left_html = (FIXTURE_DIR / "article_left.html").read_text()
        right_html = (FIXTURE_DIR / "article_right.html").read_text()

        class SlowLLMClient:
            def __init__(self, _config):
                pass

            def extract_text_attributes(self, _side, _paragraphs):
                time.sleep(0.2)
                return []

            def refine_extracted_values(self, **_kwargs):
                return []

        with patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"}, clear=False), patch.object(
            server,
            "LLMClient",
            SlowLLMClient,
        ), patch.object(
            server,
            "fetch_article_html",
            side_effect=[left_html, right_html],
        ):
            started = time.monotonic()
            response = self.fetch(
                "/api/compare-session",
                method="POST",
                body=json.dumps(
                    {
                        "leftUrl": "https://en.wikipedia.org/wiki/Economy_of_Example_A",
                        "rightUrl": "https://en.wikipedia.org/wiki/Economy_of_Example_B",
                    }
                ),
                headers={"Content-Type": "application/json"},
            )

        assert response.code == 200
        assert time.monotonic() - started < 0.35

    def test_compare_session_reuses_cached_pair_without_network_or_llm(self):
        left_html = (FIXTURE_DIR / "article_left.html").read_text()
        right_html = (FIXTURE_DIR / "article_right.html").read_text()

        class CountingLLMClient:
            extraction_calls = 0

            def __init__(self, _config):
                pass

            def extract_text_attributes(self, _side, _paragraphs):
                CountingLLMClient.extraction_calls += 1
                return []

        server.SESSION_STORE.clear()
        server.ARTICLE_HTML_CACHE.clear()
        with patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"}, clear=False), patch.object(
            server,
            "LLMClient",
            CountingLLMClient,
        ), patch.object(
            server,
            "fetch_article_html",
            side_effect=[left_html, right_html],
        ) as fetch_article:
            first = self.fetch(
                "/api/compare-session",
                method="POST",
                body=json.dumps(
                    {
                        "leftUrl": "https://en.wikipedia.org/wiki/Economy_of_Cached_A",
                        "rightUrl": "https://en.wikipedia.org/wiki/Economy_of_Cached_B",
                    }
                ),
                headers={"Content-Type": "application/json"},
            )
            second = self.fetch(
                "/api/compare-session",
                method="POST",
                body=json.dumps(
                    {
                        "leftUrl": "https://en.wikipedia.org/wiki/Economy_of_Cached_A",
                        "rightUrl": "https://en.wikipedia.org/wiki/Economy_of_Cached_B",
                    }
                ),
                headers={"Content-Type": "application/json"},
            )

        first_payload = json.loads(first.body)
        second_payload = json.loads(second.body)
        assert first.code == 200
        assert second.code == 200
        assert second_payload["sessionId"] == first_payload["sessionId"]
        assert second_payload["fromCache"] is True
        assert fetch_article.call_count == 2
        assert CountingLLMClient.extraction_calls == 2

    def test_compare_session_force_refresh_bypasses_cached_pair(self):
        left_html = (FIXTURE_DIR / "article_left.html").read_text()
        right_html = (FIXTURE_DIR / "article_right.html").read_text()

        server.SESSION_STORE.clear()
        server.ARTICLE_HTML_CACHE.clear()
        with patch.dict(os.environ, {"OPENAI_API_KEY": ""}, clear=False), patch.object(
            server,
            "fetch_article_html",
            side_effect=[left_html, right_html, left_html, right_html],
        ) as fetch_article:
            first = self.fetch(
                "/api/compare-session",
                method="POST",
                body=json.dumps(
                    {
                        "leftUrl": "https://en.wikipedia.org/wiki/Economy_of_Refresh_A",
                        "rightUrl": "https://en.wikipedia.org/wiki/Economy_of_Refresh_B",
                    }
                ),
                headers={"Content-Type": "application/json"},
            )
            refreshed = self.fetch(
                "/api/compare-session",
                method="POST",
                body=json.dumps(
                    {
                        "leftUrl": "https://en.wikipedia.org/wiki/Economy_of_Refresh_A",
                        "rightUrl": "https://en.wikipedia.org/wiki/Economy_of_Refresh_B",
                        "forceRefresh": True,
                    }
                ),
                headers={"Content-Type": "application/json"},
            )

        first_payload = json.loads(first.body)
        refreshed_payload = json.loads(refreshed.body)
        assert first.code == 200
        assert refreshed.code == 200
        assert refreshed_payload["sessionId"] != first_payload["sessionId"]
        assert refreshed_payload["fromCache"] is False
        assert fetch_article.call_count == 4

    def test_compare_session_reuses_cached_article_html_across_pairs(self):
        article_a = (FIXTURE_DIR / "article_left.html").read_text()
        article_b = (FIXTURE_DIR / "article_right.html").read_text()
        article_c = article_b

        server.SESSION_STORE.clear()
        server.ARTICLE_HTML_CACHE.clear()
        with patch.dict(os.environ, {"OPENAI_API_KEY": ""}, clear=False), patch.object(
            server,
            "fetch_article_html",
            side_effect=[article_a, article_b, article_c],
        ) as fetch_article:
            first = self.fetch(
                "/api/compare-session",
                method="POST",
                body=json.dumps(
                    {
                        "leftUrl": "https://en.wikipedia.org/wiki/Economy_of_Shared_A",
                        "rightUrl": "https://en.wikipedia.org/wiki/Economy_of_Shared_B",
                    }
                ),
                headers={"Content-Type": "application/json"},
            )
            second = self.fetch(
                "/api/compare-session",
                method="POST",
                body=json.dumps(
                    {
                        "leftUrl": "https://en.wikipedia.org/wiki/Economy_of_Shared_A",
                        "rightUrl": "https://en.wikipedia.org/wiki/Economy_of_Shared_C",
                    }
                ),
                headers={"Content-Type": "application/json"},
            )

        assert first.code == 200
        assert second.code == 200
        assert fetch_article.call_count == 3

    def test_compare_session_extracts_ten_factbook_field_card_chart_rows(self):
        left_html = _factbook_card_html(
            [
                ("Population", "total: 1,419,316,933 (2025 est.)"),
                ("Population growth rate", "0.72% (2025 est.)"),
                ("Birth rate", "15.91 births/1,000 population (2025 est.)"),
                ("Death rate", "8.7 deaths/1,000 population (2025 est.)"),
                ("Net migration rate", "0.03 migrant(s)/1,000 population (2025 est.)"),
                ("Maternal mortality ratio", "80 deaths/100,000 live births (2023 est.)"),
                ("Total fertility rate", "2 children born/woman (2025 est.)"),
                ("Physician density", "0.72 physicians/1,000 population (2020)"),
                ("Hospital bed density", "1.6 beds/1,000 population (2021 est.)"),
                ("Health expenditure", "3.9% (2016)"),
                ("Religions", "Hindu 79.8%, Muslim 14.2%, Christian 2.3%, Sikh 1.7%, other 2% (2011 est.)"),
                ("Ethnic groups", "Indo-Aryan 72%, Dravidian 25%, and other 3% (2000)"),
                ("Age structure", "0-14 years: 24.5%; 15-64 years: 68.7%; 65 years and over: 6.8% (2024 est.)"),
            ]
        )
        right_html = _factbook_card_html(
            [
                ("Population", "total: 285,721,236 (2025 est.)"),
                ("Population growth rate", "0.73% (2025 est.)"),
                ("Birth rate", "14.55 births/1,000 population (2025 est.)"),
                ("Death rate", "6.82 deaths/1,000 population (2025 est.)"),
                ("Net migration rate", "-0.7 migrant(s)/1,000 population (2025 est.)"),
                ("Maternal mortality ratio", "140 deaths/100,000 live births (2023 est.)"),
                ("Total fertility rate", "1.98 children born/woman (2025 est.)"),
                ("Physician density", "0.52 physicians/1,000 population (2020)"),
                ("Hospital bed density", "1.4 beds/1,000 population (2021 est.)"),
                ("Health expenditure", "3.2% (2016)"),
                ("Religions", "Muslim 87.4%, Protestant 7.5%, Roman Catholic 3.1%, Hindu 1.7%, other 0.8% (2022 est.)"),
                ("Ethnic groups", "Javanese 40.1%, Sundanese 15.5%, Malay 3.7%, Batak 3.6%, other 37.1% (2010 est.)"),
                ("Age structure", "0-14 years: 23.7%; 15-64 years: 68.3%; 65 years and over: 8% (2024 est.)"),
            ]
        )

        server.SESSION_STORE.clear()
        server.ARTICLE_HTML_CACHE.clear()
        with patch.dict(os.environ, {"OPENAI_API_KEY": ""}, clear=False), patch.object(
            server,
            "_fetch_generic_page_html",
            side_effect=[left_html, right_html],
        ):
            response = self.fetch(
                "/api/compare-session",
                method="POST",
                body=json.dumps(
                    {
                        "leftUrl": "https://openfactbook.org/countries/india/",
                        "rightUrl": "https://openfactbook.org/countries/indonesia/",
                        "leftTitle": "India OpenFactBook profile (2026)",
                        "rightTitle": "Indonesia OpenFactBook profile (2026)",
                        "forceRefresh": True,
                    }
                ),
                headers={"Content-Type": "application/json"},
            )

        payload = json.loads(response.body)
        chart_rows = [
            row
            for row in payload["rankedRows"]
            if row["sourceKind"] == "main_text"
            and row["chartType"] != "text"
            and row["visualization"]["left"].get("values")
            and row["visualization"]["right"].get("values")
        ]
        labels = {row["label"] for row in chart_rows}
        chart_types = {row["chartType"] for row in chart_rows}

        assert response.code == 200
        assert len(chart_rows) >= 10
        assert {"bar", "pie", "stacked"}.issubset(chart_types)
        assert {
            "Population: total",
            "Population growth rate",
            "Birth rate",
            "Death rate",
            "Net migration rate",
            "Maternal mortality ratio",
            "Total fertility rate",
            "Hospital bed density",
            "Health expenditure",
            "Religions",
        }.issubset(labels)

    def test_paired_text_alignments_do_not_get_cross_matched_by_same_label(self):
        paired_alignments = [
            {
                "left": {"id": "left-paired-1", "key": "Revenue"},
                "right": {"id": "right-paired-1", "key": "Revenue"},
                "label": "Revenue",
            },
            {
                "left": {"id": "left-paired-2", "key": "Revenue"},
                "right": {"id": "right-paired-2", "key": "Revenue"},
                "label": "Revenue",
            },
        ]
        general_alignments = [
            {
                "left": {"id": "left-paired-1", "key": "Revenue"},
                "right": {"id": "right-paired-2", "key": "Revenue"},
                "label": "Revenue",
            },
            {
                "left": {"id": "left-other", "key": "GDP"},
                "right": {"id": "right-other", "key": "GDP"},
                "label": "GDP",
            },
        ]

        assert server._without_duplicate_alignments(general_alignments, paired_alignments) == [
            general_alignments[1]
        ]


def _factbook_card_html(fields):
    cards = "\n".join(
        f"""
        <div class="group/field glass-card">
          <h3>{label}</h3>
          <div><p>{value}</p></div>
        </div>
        """
        for label, value in fields
    )
    return f"<html><body><main><h1>Factbook</h1>{cards}</main></body></html>"
