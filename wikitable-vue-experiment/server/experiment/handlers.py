import json
import os
import secrets
from pathlib import Path

import tornado.web

from .assignment import assignment_for_code
from .defaults import DEFAULT_MATERIALS
from .question_generation import build_question_prompt, normalize_generated_questions
from .storage import ExperimentStorage

ADMIN_TOKENS = set()


def data_dir():
    return Path(os.environ.get("EXPERIMENT_DATA_DIR") or Path(__file__).resolve().parents[1] / "experiment_data")


def storage():
    return ExperimentStorage(data_dir())


class JsonHandler(tornado.web.RequestHandler):
    def set_default_headers(self):
        self.set_header("Access-Control-Allow-Origin", "*")
        self.set_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.set_header("Access-Control-Allow-Headers", "Content-Type, X-Admin-Token")

    def options(self):
        self.set_status(204)
        self.finish()

    def read_json(self):
        if not self.request.body:
            return {}
        return json.loads(self.request.body.decode("utf-8"))

    def write_json(self, payload, status=200):
        self.set_status(status)
        self.set_header("Content-Type", "application/json; charset=utf-8")
        self.write(json.dumps(payload, ensure_ascii=False))

    def write_error_json(self, message, status=400):
        self.write_json({"error": message}, status=status)


class AdminMixin:
    def require_admin(self):
        token = self.request.headers.get("X-Admin-Token", "")
        if token not in ADMIN_TOKENS:
            self.set_status(401)
            self.set_header("Content-Type", "application/json; charset=utf-8")
            self.finish(json.dumps({"error": "Admin authentication required"}))
            return False
        return True


class ExperimentConfigHandler(JsonHandler):
    def get(self):
        self.write_json(storage().get_config())


class ExperimentStartHandler(JsonHandler):
    def post(self):
        try:
            body = self.read_json()
            assignment = assignment_for_code(body.get("participantCode"))
            payload = {
                "participantCode": assignment["participantCode"],
                "assignmentGroup": assignment["group"],
                "stages": assignment["stages"],
            }
            self.write_json(payload)
        except ValueError as error:
            self.write_error_json(str(error), status=400)


class ExperimentQuestionsHandler(JsonHandler):
    def get(self):
        material_id = self.get_argument("materialId", "")
        try:
            self.write_json(storage().load_questions(material_id))
        except ValueError as error:
            self.write_error_json(str(error), status=404)


class ExperimentCompleteHandler(JsonHandler):
    def post(self):
        try:
            saved = storage().save_submission(self.read_json())
            self.write_json(saved)
        except Exception as error:
            self.write_error_json(str(error), status=400)


class AdminLoginHandler(JsonHandler):
    def post(self):
        expected = os.environ.get("EXPERIMENT_ADMIN_PASSWORD", "admin")
        password = self.read_json().get("password", "")
        if not secrets.compare_digest(str(password), str(expected)):
            self.write_error_json("Invalid admin password", status=401)
            return
        token = secrets.token_urlsafe(24)
        ADMIN_TOKENS.add(token)
        self.write_json({"token": token})


class AdminSubmissionsHandler(JsonHandler, AdminMixin):
    def get(self):
        if not self.require_admin():
            return
        self.write_json({"submissions": storage().list_submissions()})


class AdminExportHandler(JsonHandler, AdminMixin):
    export_name = ""

    def get(self):
        if not self.require_admin():
            return
        exports = storage().write_exports()
        path = exports[self.export_name]
        self.set_header("Content-Type", "text/csv; charset=utf-8")
        self.set_header("Content-Disposition", f"attachment; filename={Path(path).name}")
        with open(path, encoding="utf-8") as handle:
            self.write(handle.read())


class AdminSummaryCsvHandler(AdminExportHandler):
    export_name = "summaryCsv"


class AdminAnswersCsvHandler(AdminExportHandler):
    export_name = "answersCsv"


class AdminQuestionGenerateHandler(JsonHandler, AdminMixin):
    def post(self):
        if not self.require_admin():
            return
        body = self.read_json()
        material_id = body.get("materialId", "")
        material = next((item for item in DEFAULT_MATERIALS if item["id"] == material_id), None)
        if not material:
            self.write_error_json(f"Unknown material id: {material_id}", status=404)
            return
        raw_questions = body.get("rawQuestions")
        if raw_questions is None:
            self.write_error_json("rawQuestions is required until material session extraction is connected", status=400)
            return
        existing = storage().load_questions(material_id)
        normalized = normalize_generated_questions(raw_questions, material_id, int(existing.get("version") or 0) + 1)
        saved = storage().save_questions(material_id, normalized)
        self.write_json(saved)


class AdminQuestionFreezeHandler(JsonHandler, AdminMixin):
    frozen = True

    def post(self):
        if not self.require_admin():
            return
        body = self.read_json()
        material_id = body.get("materialId", "")
        try:
            self.write_json(storage().freeze_questions(material_id, self.frozen))
        except ValueError as error:
            self.write_error_json(str(error), status=404)


class AdminQuestionUnfreezeHandler(AdminQuestionFreezeHandler):
    frozen = False


def experiment_routes():
    return [
        (r"/api/experiment/config", ExperimentConfigHandler),
        (r"/api/experiment/start", ExperimentStartHandler),
        (r"/api/experiment/questions", ExperimentQuestionsHandler),
        (r"/api/experiment/complete", ExperimentCompleteHandler),
        (r"/api/admin/login", AdminLoginHandler),
        (r"/api/admin/submissions", AdminSubmissionsHandler),
        (r"/api/admin/export/submissions.csv", AdminSummaryCsvHandler),
        (r"/api/admin/export/answers.csv", AdminAnswersCsvHandler),
        (r"/api/admin/questions/generate", AdminQuestionGenerateHandler),
        (r"/api/admin/questions/freeze", AdminQuestionFreezeHandler),
        (r"/api/admin/questions/unfreeze", AdminQuestionUnfreezeHandler),
    ]
