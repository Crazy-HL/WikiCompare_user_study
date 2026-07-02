import json
import os
import time
from pathlib import Path
from unittest.mock import patch

from tornado.testing import AsyncHTTPTestCase

import server


FIXTURE_DIR = Path(__file__).parent / "fixtures"


class CompareApiTest(AsyncHTTPTestCase):
    def get_app(self):
        return server.make_app()

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
        assert payload["warnings"]

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

            def extract_text_attribute_pairs(self, *, left_candidates, right_candidates, infobox_context):
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
        assert labels.index("Historical emergence") < labels.index("Applications")
        assert historical["leftSourceIds"] == ["left-s-1-2"]
        assert historical["rightSourceIds"] == ["right-s-1-2"]
        assert applications["leftSourceIds"] == ["left-s-2-1"]
        assert applications["rightSourceIds"] == ["right-s-2-1"]
        assert historical["sourceKind"] == "main_text"
        assert applications["sourceKind"] == "main_text"

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
