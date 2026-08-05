import json
import os
import secrets
from pathlib import Path

import tornado.web

from .defaults import DEFAULT_MATERIALS
from .question_generation import generate_questions_from_material, normalize_generated_questions
from .static_table_generation import generate_static_table_from_material
from .storage import ExperimentStorage

ADMIN_TOKENS = set()


def data_dir():
    return Path(os.environ.get("EXPERIMENT_DATA_DIR") or Path(__file__).resolve().parents[1] / "experiment_data")


def storage():
    return ExperimentStorage(data_dir())


def configured_cors_origins():
    raw = os.environ.get("EXPERIMENT_CORS_ORIGIN", "").strip()
    return {origin.strip() for origin in raw.split(",") if origin.strip()}


def insecure_admin_default_enabled():
    return os.environ.get("EXPERIMENT_ALLOW_INSECURE_ADMIN_DEFAULT", "").lower() in {"1", "true", "yes"}


def expected_admin_password():
    password = os.environ.get("EXPERIMENT_ADMIN_PASSWORD")
    if password:
        return password
    if insecure_admin_default_enabled():
        return "admin"
    return None


class JsonHandler(tornado.web.RequestHandler):
    def set_default_headers(self):
        origins = configured_cors_origins()
        request_origin = self.request.headers.get("Origin", "")
        if request_origin and (request_origin in origins or "*" in origins):
            self.set_header("Access-Control-Allow-Origin", request_origin if "*" not in origins else "*")
            self.set_header("Vary", "Origin")
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
            payload = storage().create_session(body.get("participantCode"))
            self.write_json(payload)
        except ValueError as error:
            self.write_error_json(str(error), status=400)


PARTICIPANT_QUESTION_FIELDS = {
    "question_id",
    "question_type",
    "question_text",
    "answer_format",
    "understanding_target",
    "answer_options",
}

PARTICIPANT_QUESTION_PAYLOAD_FIELDS = {
    "material_id",
    "version",
    "frozen",
}


def participant_questions_payload(payload):
    redacted = {
        key: payload[key]
        for key in PARTICIPANT_QUESTION_PAYLOAD_FIELDS
        if key in payload
    }
    redacted["questions"] = [
        {
            key: question[key]
            for key in PARTICIPANT_QUESTION_FIELDS
            if key in question
        }
        for question in payload.get("questions") or []
    ]
    return redacted


class ExperimentQuestionsHandler(JsonHandler):
    def get(self):
        material_id = self.get_argument("materialId", "")
        try:
            self.write_json(participant_questions_payload(storage().load_participant_questions(material_id)))
        except ValueError as error:
            self.write_error_json(str(error), status=400)


class ExperimentCompleteHandler(JsonHandler):
    def post(self):
        try:
            saved = storage().save_submission(self.read_json(), require_started_session=True)
            self.write_json(saved)
        except Exception as error:
            self.write_error_json(str(error), status=400)


class AdminLoginHandler(JsonHandler):
    def post(self):
        expected = expected_admin_password()
        if expected is None:
            self.write_error_json("EXPERIMENT_ADMIN_PASSWORD is required", status=503)
            return
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


class AdminQuestionsHandler(JsonHandler, AdminMixin):
    def get(self):
        if not self.require_admin():
            return
        material_id = self.get_argument("materialId", "")
        try:
            self.write_json(storage().load_questions(material_id))
        except ValueError as error:
            self.write_error_json(str(error), status=404)


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
        existing = storage().load_questions(material_id)
        next_version = int(existing.get("version") or 0) + 1
        try:
            if raw_questions is None:
                normalized = generate_questions_from_material(material, next_version)
            else:
                normalized = normalize_generated_questions(raw_questions, material_id, next_version)
        except (TypeError, ValueError, json.JSONDecodeError) as error:
            label = "question generation" if raw_questions is None else "rawQuestions"
            self.write_error_json(f"Invalid {label}: {error}", status=400)
            return
        except Exception as error:
            self.write_error_json(f"Question generation failed: {error}", status=502)
            return
        try:
            saved = storage().save_questions(material_id, normalized)
        except ValueError as error:
            self.write_error_json(str(error), status=400)
            return
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
            self.write_error_json(str(error), status=400)


class AdminQuestionUnfreezeHandler(AdminQuestionFreezeHandler):
    frozen = False


class ExperimentStaticTableHandler(JsonHandler):
    def get(self):
        material_id = self.get_argument("materialId", "")
        try:
            self.write_json(storage().load_participant_static_table(material_id))
        except ValueError as error:
            self.write_error_json(str(error), status=400)


class AdminStaticTableHandler(JsonHandler, AdminMixin):
    def get(self):
        if not self.require_admin():
            return
        material_id = self.get_argument("materialId", "")
        try:
            self.write_json(storage().load_static_table(material_id))
        except ValueError as error:
            self.write_error_json(str(error), status=404)

    def post(self):
        if not self.require_admin():
            return
        body = self.read_json()
        try:
            self.write_json(storage().save_static_table(body.get("materialId", ""), body.get("rows")))
        except ValueError as error:
            self.write_error_json(str(error), status=400)


class AdminStaticTableGenerateHandler(JsonHandler, AdminMixin):
    def post(self):
        if not self.require_admin():
            return
        body = self.read_json()
        material_id = body.get("materialId", "")
        material = next((item for item in DEFAULT_MATERIALS if item["id"] == material_id), None)
        if not material:
            self.write_error_json(f"Unknown material id: {material_id}", status=404)
            return
        try:
            generated = generate_static_table_from_material(material)
            self.write_json(storage().save_static_table(
                material_id,
                generated.get("rows"),
                generated.get("generation_prompts"),
            ))
        except ValueError as error:
            self.write_error_json(str(error), status=400)
        except Exception as error:
            self.write_error_json(f"Static table generation failed: {error}", status=502)


class AdminStaticTableFreezeHandler(JsonHandler, AdminMixin):
    frozen = True

    def post(self):
        if not self.require_admin():
            return
        body = self.read_json()
        try:
            self.write_json(storage().freeze_static_table(body.get("materialId", ""), self.frozen))
        except ValueError as error:
            self.write_error_json(str(error), status=400)


class AdminStaticTableUnfreezeHandler(AdminStaticTableFreezeHandler):
    frozen = False


def experiment_routes():
    return [
        (r"/api/experiment/config", ExperimentConfigHandler),
        (r"/api/experiment/start", ExperimentStartHandler),
        (r"/api/experiment/questions", ExperimentQuestionsHandler),
        (r"/api/experiment/static-table", ExperimentStaticTableHandler),
        (r"/api/experiment/complete", ExperimentCompleteHandler),
        (r"/api/admin/login", AdminLoginHandler),
        (r"/api/admin/submissions", AdminSubmissionsHandler),
        (r"/api/admin/export/submissions.csv", AdminSummaryCsvHandler),
        (r"/api/admin/export/answers.csv", AdminAnswersCsvHandler),
        (r"/api/admin/questions/generate", AdminQuestionGenerateHandler),
        (r"/api/admin/questions/freeze", AdminQuestionFreezeHandler),
        (r"/api/admin/questions/unfreeze", AdminQuestionUnfreezeHandler),
        (r"/api/admin/questions", AdminQuestionsHandler),
        (r"/api/admin/static-table/generate", AdminStaticTableGenerateHandler),
        (r"/api/admin/static-table/freeze", AdminStaticTableFreezeHandler),
        (r"/api/admin/static-table/unfreeze", AdminStaticTableUnfreezeHandler),
        (r"/api/admin/static-table", AdminStaticTableHandler),
    ]
