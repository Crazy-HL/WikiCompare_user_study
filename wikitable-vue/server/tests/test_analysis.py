import json

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
