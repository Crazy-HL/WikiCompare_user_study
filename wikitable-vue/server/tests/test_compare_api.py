import json
import os
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
            body=b"\xff\xfe",
            headers={"Content-Type": "application/json"},
        )

        assert response.code == 400
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
