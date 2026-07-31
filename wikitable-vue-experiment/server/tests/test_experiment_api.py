import json
import os
import tempfile

from tornado.testing import AsyncHTTPTestCase

import server


class ExperimentApiTest(AsyncHTTPTestCase):
    def setUp(self):
        self.tmpdir = tempfile.TemporaryDirectory()
        self.previous_data_dir = os.environ.get("EXPERIMENT_DATA_DIR")
        self.previous_password = os.environ.get("EXPERIMENT_ADMIN_PASSWORD")
        os.environ["EXPERIMENT_DATA_DIR"] = self.tmpdir.name
        os.environ["EXPERIMENT_ADMIN_PASSWORD"] = "secret"
        super().setUp()

    def tearDown(self):
        super().tearDown()
        if self.previous_data_dir is None:
            os.environ.pop("EXPERIMENT_DATA_DIR", None)
        else:
            os.environ["EXPERIMENT_DATA_DIR"] = self.previous_data_dir
        if self.previous_password is None:
            os.environ.pop("EXPERIMENT_ADMIN_PASSWORD", None)
        else:
            os.environ["EXPERIMENT_ADMIN_PASSWORD"] = self.previous_password
        self.tmpdir.cleanup()

    def get_app(self):
        return server.make_app()

    def post_json(self, url, payload, headers=None):
        return self.fetch(
            url,
            method="POST",
            headers={"Content-Type": "application/json", **(headers or {})},
            body=json.dumps(payload).encode("utf-8"),
        )

    def test_config_and_start_assignment(self):
        config_response = self.fetch("/api/experiment/config")
        assert config_response.code == 200
        config = json.loads(config_response.body)
        assert [item["id"] for item in config["materials"]] == ["M1", "M2"]
        assert "在阅读两篇文章" in config["q6Text"]

        start_response = self.post_json("/api/experiment/start", {"participantCode": "p2"})
        assert start_response.code == 200
        payload = json.loads(start_response.body)
        assert payload["participantCode"] == "P02"
        assert payload["assignmentGroup"] == "S2"
        assert payload["stages"][0]["condition"] == "chatgpt"

    def test_complete_submission_and_admin_list(self):
        complete_response = self.post_json("/api/experiment/complete", {
            "participantCode": "P01",
            "assignmentGroup": "S1",
            "stages": [],
        })
        assert complete_response.code == 200
        saved = json.loads(complete_response.body)
        assert saved["experimentId"].startswith("exp-")

        unauthorized = self.fetch("/api/admin/submissions")
        assert unauthorized.code == 401

        login = self.post_json("/api/admin/login", {"password": "secret"})
        assert login.code == 200
        token = json.loads(login.body)["token"]
        listing = self.fetch("/api/admin/submissions", headers={"X-Admin-Token": token})
        assert listing.code == 200
        records = json.loads(listing.body)["submissions"]
        assert records[0]["participantCode"] == "P01"

    def test_admin_export_answers_csv(self):
        login = self.post_json("/api/admin/login", {"password": "secret"})
        token = json.loads(login.body)["token"]
        response = self.fetch("/api/admin/export/answers.csv", headers={"X-Admin-Token": token})
        assert response.code == 200
        assert response.headers["Content-Type"].startswith("text/csv")
        assert b"participant_code" in response.body

    def test_questions_and_admin_freeze_unfreeze(self):
        questions_response = self.fetch("/api/experiment/questions?materialId=M1")
        assert questions_response.code == 200
        questions = json.loads(questions_response.body)
        assert questions["material_id"] == "M1"
        assert questions["frozen"] is False

        login = self.post_json("/api/admin/login", {"password": "secret"})
        assert login.code == 200
        token = json.loads(login.body)["token"]

        freeze = self.post_json(
            "/api/admin/questions/freeze",
            {"materialId": "M1"},
            headers={"X-Admin-Token": token},
        )
        assert freeze.code == 200
        assert json.loads(freeze.body)["frozen"] is True

        unfreeze = self.post_json(
            "/api/admin/questions/unfreeze",
            {"materialId": "M1"},
            headers={"X-Admin-Token": token},
        )
        assert unfreeze.code == 200
        assert json.loads(unfreeze.body)["frozen"] is False

