import json
import os
from unittest.mock import patch

from tornado.testing import AsyncHTTPTestCase

import server
from services.analysis import fallback_answer, fallback_attribute_summary, validate_citations
from services.models import Citation, CompareSession, SourceRef
from services.session_store import SessionStore


def test_validate_citations_drops_unknown_source_ids():
    source_map = {
        "left-info-1": SourceRef(
            "left-info-1",
            "left",
            "infobox",
            "GDP growth: 2.3%",
            '[data-source-id="left-info-1"]',
        )
    }
    citations = [
        Citation("cite-1", "Infobox: GDP growth", "left", ["left-info-1"]),
        Citation("cite-2", "Bad", "left", ["missing"]),
    ]

    valid = validate_citations(citations, source_map)

    assert [citation.id for citation in valid] == ["cite-1"]


def test_validate_citations_drops_malformed_and_blank_id_citations():
    source_map = {
        "left-info-1": SourceRef(
            "left-info-1",
            "left",
            "infobox",
            "GDP growth: 2.3%",
            '[data-source-id="left-info-1"]',
        )
    }
    citations = [
        Citation("", "Blank", "left", ["left-info-1"]),
        {"id": "dict-citation", "sourceIds": ["left-info-1"]},
        Citation("cite-1", "Infobox: GDP growth", "left", ["left-info-1"]),
    ]

    valid = validate_citations(citations, source_map)

    assert [citation.id for citation in valid] == ["cite-1"]


def test_fallback_attribute_summary_only_returns_valid_citations():
    row = {
        "id": "row-1",
        "label": "GDP growth",
        "leftSourceIds": ["left-info-1"],
        "rightSourceIds": ["missing"],
        "visualization": {
            "left": {"valueText": "2.3%"},
            "right": {"valueText": "0.6%"},
        },
    }
    source_map = {
        "left-info-1": {
            "id": "left-info-1",
            "side": "left",
            "sourceType": "infobox",
            "text": "GDP growth: 2.3%",
            "selector": '[data-source-id="left-info-1"]',
        }
    }

    result = fallback_attribute_summary(row, source_map)

    assert "GDP growth" in result["summary"]
    assert [citation["sourceIds"] for citation in result["citations"]] == [["left-info-1"]]


def test_fallback_attribute_summary_reads_pipeline_raw_values():
    row = {
        "id": "row-1",
        "label": "GDP growth",
        "leftSourceIds": ["left-info-1"],
        "rightSourceIds": ["right-info-1"],
        "visualization": {
            "left": {"raw": "2.3% (2024)", "values": [{"value": 2.3, "year": 2024}]},
            "right": {"raw": "0.8% (2024)", "values": [{"value": 0.8, "year": 2024}]},
        },
    }
    source_map = {
        "left-info-1": SourceRef(
            "left-info-1",
            "left",
            "infobox",
            "GDP growth: 2.3%",
            '[data-source-id="left-info-1"]',
        ),
        "right-info-1": SourceRef(
            "right-info-1",
            "right",
            "infobox",
            "GDP growth: 0.8%",
            '[data-source-id="right-info-1"]',
        ),
    }

    result = fallback_attribute_summary(row, source_map)

    assert result["summary"].startswith("Conclusion:")
    assert "2.3% (2024)" in result["summary"]
    assert "0.8% (2024)" in result["summary"]


def test_fallback_attribute_summary_uses_paper_conclusion_style_for_largest_difference():
    row = {
        "id": "row-fdi",
        "label": "FDI stock",
        "dataType": "Numerical",
        "leftSourceIds": ["left-info-1"],
        "rightSourceIds": ["right-info-1"],
        "visualization": {
            "left": {
                "raw": "$230.6 billion (31 December 2017 est.) Abroad: $344.7 billion (31 December 2017 est.)",
                "values": [
                    {"value": 230600000000.0, "year": 2017, "label": "Inward"},
                    {"value": 344700000000.0, "year": 2017, "label": "Abroad"},
                ],
            },
            "right": {
                "raw": "Inward: $25 billion (2021) Outward: $147 billion (2021)",
                "values": [
                    {"value": 25000000000.0, "year": 2021, "label": "Inward"},
                    {"value": 147000000000.0, "year": 2021, "label": "Outward"},
                ],
            },
        },
    }

    result = fallback_attribute_summary(
        row,
        {},
        {
            "left": {"title": "Economy of South Korea"},
            "right": {"title": "Economy of Japan"},
        },
    )

    assert result["summary"].startswith("Conclusion:")
    assert "FDI stock" in result["summary"]
    assert "Inward" in result["summary"]
    assert "Economy of South Korea" in result["summary"]
    assert "Economy of Japan" in result["summary"]
    assert "$230.6 billion" in result["summary"]
    assert "$25 billion" in result["summary"]
    assert "Abroad: $344.7 billion" not in result["summary"]


def test_llm_attribute_summary_uses_paper_prompt_and_normalizes_conclusion_prefix():
    captured = {}

    class FakeLLMClient:
        def chat_json(self, messages):
            captured["messages"] = messages
            return {
                "summary": "The left side has the stronger reported growth.",
                "citations": [
                    {
                        "id": "cite-1",
                        "label": "Infobox: GDP growth",
                        "side": "both",
                        "sourceIds": ["left-info-1", "right-info-1"],
                    }
                ],
            }

    source_map = {
        "left-info-1": SourceRef(
            "left-info-1",
            "left",
            "infobox",
            "GDP growth: 2.3%",
            '[data-source-id="left-info-1"]',
        ),
        "right-info-1": SourceRef(
            "right-info-1",
            "right",
            "infobox",
            "GDP growth: 0.8%",
            '[data-source-id="right-info-1"]',
        ),
    }
    row = {
        "id": "row-1",
        "label": "GDP growth",
        "dataType": "Trend",
        "leftSourceIds": ["left-info-1"],
        "rightSourceIds": ["right-info-1"],
        "visualization": {
            "left": {"raw": "2.3% (2024)", "values": [{"value": 2.3, "year": 2024}]},
            "right": {"raw": "0.8% (2024)", "values": [{"value": 0.8, "year": 2024}]},
        },
    }

    result = server.llm_attribute_summary(
        FakeLLMClient(),
        row,
        source_map,
        {
            "left": {"title": "Economy of South Korea"},
            "right": {"title": "Economy of Japan"},
        },
    )

    prompt = "\n".join(message["content"] for message in captured["messages"])
    assert "Initial Difference Summary" in prompt
    assert "Begin the summary with \"Conclusion:\"" in prompt
    assert "highlight the most significant difference or trend" in prompt
    assert "based solely on the provided data" in prompt
    assert "Economy of South Korea" in prompt
    assert "Economy of Japan" in prompt
    assert result["summary"].startswith("Conclusion:")


def test_fallback_answer_uses_top_ranked_row_valid_sources():
    session = CompareSession(
        session_id="session-1",
        articles={},
        ranked_rows=[
            {
                "id": "row-1",
                "label": "GDP growth",
                "leftSourceIds": ["left-info-1"],
                "rightSourceIds": ["missing"],
                "visualization": {
                    "left": {"valueText": "2.3%"},
                    "right": {"valueText": "0.6%"},
                },
            }
        ],
        source_map={
            "left-info-1": SourceRef(
                "left-info-1",
                "left",
                "infobox",
                "GDP growth: 2.3%",
                '[data-source-id="left-info-1"]',
            )
        },
    )

    result = fallback_answer(session, "How do they compare?")

    assert "GDP growth" in result["answer"]
    assert [citation["sourceIds"] for citation in result["citations"]] == [["left-info-1"]]


class AnalysisApiTest(AsyncHTTPTestCase):
    def get_app(self):
        env_patch = patch.dict(os.environ, {"OPENAI_API_KEY": ""}, clear=False)
        env_patch.start()
        self.addCleanup(env_patch.stop)
        server.SESSION_STORE = SessionStore()
        self.session = CompareSession(
            session_id="session-1",
            articles={},
            ranked_rows=[
                {
                    "id": "row-1",
                    "label": "GDP growth",
                    "leftSourceIds": ["left-info-1"],
                    "rightSourceIds": ["missing"],
                    "visualization": {
                        "left": {"valueText": "2.3%"},
                        "right": {"valueText": "0.6%"},
                    },
                }
            ],
            source_map={
                "left-info-1": SourceRef(
                    "left-info-1",
                    "left",
                    "infobox",
                    "GDP growth: 2.3%",
                    '[data-source-id="left-info-1"]',
                )
            },
        )
        server.SESSION_STORE.save(self.session)
        return server.make_app()

    def test_analyze_attribute_returns_only_valid_citation_source_ids(self):
        response = self.fetch(
            "/api/analyze-attribute",
            method="POST",
            body=json.dumps({"sessionId": "session-1", "attributeId": "row-1"}),
            headers={"Content-Type": "application/json"},
        )

        assert response.code == 200
        payload = json.loads(response.body)
        assert [citation["sourceIds"] for citation in payload["citations"]] == [["left-info-1"]]

    def test_analyze_attribute_uses_llm_when_configured(self):
        class FakeLLMClient:
            def __init__(self, config):
                self.config = config

            def chat_json(self, messages):
                return {
                    "summary": "LLM comparison: growth is higher on the left.",
                    "citations": [
                        {
                            "id": "cite-1",
                            "label": "Infobox: GDP growth",
                            "side": "left",
                            "sourceIds": ["left-info-1"],
                        }
                    ],
                }

        with patch.dict("os.environ", {"OPENAI_API_KEY": "test-key"}, clear=False), patch.object(
            server, "LLMClient", FakeLLMClient
        ):
            response = self.fetch(
                "/api/analyze-attribute",
                method="POST",
                body=json.dumps({"sessionId": "session-1", "attributeId": "row-1"}),
                headers={"Content-Type": "application/json"},
            )

        assert response.code == 200
        payload = json.loads(response.body)
        assert payload["summary"] == "Conclusion: LLM comparison: growth is higher on the left."
        assert payload["citations"][0]["sourceIds"] == ["left-info-1"]

    def test_ask_returns_only_valid_citation_source_ids(self):
        response = self.fetch(
            "/api/ask",
            method="POST",
            body=json.dumps({"sessionId": "session-1", "question": "What changed?"}),
            headers={"Content-Type": "application/json"},
        )

        assert response.code == 200
        payload = json.loads(response.body)
        assert [citation["sourceIds"] for citation in payload["citations"]] == [["left-info-1"]]

    def test_ask_uses_llm_when_configured(self):
        class FakeLLMClient:
            def __init__(self, config):
                self.config = config

            def chat_json(self, messages):
                return {
                    "answer": "LLM answer: the left article reports stronger growth.",
                    "citations": [
                        {
                            "id": "cite-1",
                            "label": "Infobox: GDP growth",
                            "side": "left",
                            "sourceIds": ["left-info-1"],
                        }
                    ],
                }

        with patch.dict("os.environ", {"OPENAI_API_KEY": "test-key"}, clear=False), patch.object(
            server, "LLMClient", FakeLLMClient
        ):
            response = self.fetch(
                "/api/ask",
                method="POST",
                body=json.dumps({"sessionId": "session-1", "question": "What changed?"}),
                headers={"Content-Type": "application/json"},
            )

        assert response.code == 200
        payload = json.loads(response.body)
        assert payload["answer"] == "LLM answer: the left article reports stronger growth."
        assert payload["citations"][0]["sourceIds"] == ["left-info-1"]
