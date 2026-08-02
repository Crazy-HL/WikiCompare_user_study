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

    def test_admin_generate_questions_saves_next_version(self):
        login = self.post_json("/api/admin/login", {"password": "secret"})
        token = json.loads(login.body)["token"]
        raw_questions = {
            "material_id": "M1",
            "questions": [
                {"question_id": f"Q{index}", "question_text": f"Question {index}", "gold_atoms": []}
                for index in range(1, 6)
            ],
        }

        response = self.post_json(
            "/api/admin/questions/generate",
            {"materialId": "M1", "rawQuestions": raw_questions},
            headers={"X-Admin-Token": token},
        )

        assert response.code == 200
        generated = json.loads(response.body)
        assert generated["material_id"] == "M1"
        assert generated["version"] == 1
        assert generated["frozen"] is False
        assert [item["question_id"] for item in generated["questions"]] == ["Q1", "Q2", "Q3", "Q4", "Q5"]

        questions_response = self.fetch("/api/experiment/questions?materialId=M1")
        assert questions_response.code == 200
        persisted = json.loads(questions_response.body)
        assert persisted["version"] == 1
        assert persisted["questions"][0]["question_text"] == "Question 1"

    def test_participant_questions_redact_generated_answer_keys(self):
        login = self.post_json("/api/admin/login", {"password": "secret"})
        token = json.loads(login.body)["token"]
        raw_questions = {
            "material_id": "M1",
            "questions": [
                {
                    "question_id": f"Q{index}",
                    "question_type": "单维事实比较",
                    "question_text": f"Question {index}",
                    "answer_format": "free text",
                    "understanding_target": "visible learning target",
                    "answer_options": ["A", "B"],
                    "gold_atoms": [
                        {
                            "atom_id": f"Q{index}-A1",
                            "requirement": "hidden scoring requirement",
                            "canonical_answer": "hidden canonical answer",
                            "accepted_variants": ["hidden accepted variant"],
                            "source_ids": ["L-P001", "R-P001"],
                            "source_evidence": "hidden evidence excerpt",
                        }
                    ],
                    "canonical_answer": "hidden top-level answer",
                    "accepted_variants": ["hidden top-level variant"],
                    "source_evidence": "hidden top-level evidence",
                }
                for index in range(1, 6)
            ],
        }

        generate_response = self.post_json(
            "/api/admin/questions/generate",
            {"materialId": "M1", "rawQuestions": raw_questions},
            headers={"X-Admin-Token": token},
        )
        assert generate_response.code == 200
        admin_payload = json.loads(generate_response.body)
        assert "gold_atoms" in admin_payload["questions"][0]

        questions_response = self.fetch("/api/experiment/questions?materialId=M1")
        assert questions_response.code == 200
        participant_payload = json.loads(questions_response.body)
        assert participant_payload["material_id"] == "M1"
        assert participant_payload["version"] == 1
        first_question = participant_payload["questions"][0]
        assert first_question == {
            "question_id": "Q1",
            "question_type": "单维事实比较",
            "question_text": "Question 1",
            "answer_format": "free text",
            "understanding_target": "visible learning target",
            "answer_options": ["A", "B"],
        }

        forbidden_keys = {
            "gold_atoms",
            "canonical_answer",
            "accepted_variants",
            "source_ids",
            "source_evidence",
            "sourceEvidence",
        }

        def assert_no_forbidden_keys(value):
            if isinstance(value, dict):
                assert forbidden_keys.isdisjoint(value.keys())
                for child in value.values():
                    assert_no_forbidden_keys(child)
            elif isinstance(value, list):
                for child in value:
                    assert_no_forbidden_keys(child)

        assert_no_forbidden_keys(participant_payload)

    def test_admin_generate_questions_rejects_invalid_raw_questions_as_json_error(self):
        login = self.post_json("/api/admin/login", {"password": "secret"})
        token = json.loads(login.body)["token"]

        response = self.post_json(
            "/api/admin/questions/generate",
            {"materialId": "M1", "rawQuestions": "not valid json"},
            headers={"X-Admin-Token": token},
        )

        assert response.code == 400
        payload = json.loads(response.body)
        assert "rawQuestions" in payload["error"]

    def test_admin_generate_questions_requires_authentication(self):
        response = self.post_json(
            "/api/admin/questions/generate",
            {"materialId": "M1", "rawQuestions": {"questions": []}},
        )

        assert response.code == 401
        assert json.loads(response.body)["error"] == "Admin authentication required"

