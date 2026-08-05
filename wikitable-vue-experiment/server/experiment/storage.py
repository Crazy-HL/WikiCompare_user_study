import csv
import json
import os
import re
import tempfile
import uuid
from datetime import datetime, timezone
from pathlib import Path

from .assignment import assignment_for_code, normalize_participant_code
from .defaults import DEFAULT_MATERIALS, Q6_TEXT, QUESTION_PROMPT_VERSION

MATERIAL_IDS = {item["id"] for item in DEFAULT_MATERIALS}
EXPERIMENT_ID_PATTERN = re.compile(r"^exp-[0-9]{8}-[a-f0-9]{8}$")
EXPECTED_ANSWER_IDS = [f"Q{index}" for index in range(1, 7)]
EXPECTED_GENERATED_QUESTION_IDS = [f"Q{index}" for index in range(1, 6)]


def utc_now_iso():
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def atomic_write_json(path, payload):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp_name = tempfile.mkstemp(prefix=path.name, suffix=".tmp", dir=str(path.parent))
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            json.dump(payload, handle, ensure_ascii=False, indent=2)
            handle.write("\n")
        os.replace(tmp_name, path)
    finally:
        if os.path.exists(tmp_name):
            os.unlink(tmp_name)


def atomic_write_csv(path, fieldnames, row_iterable):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp_name = tempfile.mkstemp(prefix=path.name, suffix=".tmp", dir=str(path.parent))
    try:
        with os.fdopen(fd, "w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=fieldnames)
            writer.writeheader()
            for row in row_iterable:
                writer.writerow(row)
        os.replace(tmp_name, path)
    finally:
        if os.path.exists(tmp_name):
            os.unlink(tmp_name)


def require_material_id(material_id):
    if material_id not in MATERIAL_IDS:
        raise ValueError(f"Unknown material id: {material_id}")
    return material_id


def require_non_negative_int(payload, field_name, context):
    value = payload.get(field_name)
    if not isinstance(value, int) or value < 0:
        raise ValueError(f"{context} {field_name} must be a non-negative integer")
    return value


def require_non_empty_string(payload, field_name, context):
    value = payload.get(field_name)
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{context} {field_name} is required")
    return value


def validate_question_set_complete(payload):
    questions = payload.get("questions")
    if not isinstance(questions, list):
        raise ValueError("Questions must be a list")
    ids = [question.get("question_id") if isinstance(question, dict) else None for question in questions]
    if ids != EXPECTED_GENERATED_QUESTION_IDS:
        raise ValueError("Questions must contain Q1-Q5 in order before freezing or participant use")
    for index, question in enumerate(questions, start=1):
        if not isinstance(question, dict) or not str(question.get("question_text") or "").strip():
            raise ValueError(f"Question Q{index} is incomplete")


def generate_experiment_id():
    return f"exp-{datetime.now(timezone.utc).strftime('%Y%m%d')}-{uuid.uuid4().hex[:8]}"


def validate_experiment_id(experiment_id):
    if not isinstance(experiment_id, str) or not EXPERIMENT_ID_PATTERN.fullmatch(experiment_id):
        raise ValueError("experimentId must be a server-issued opaque id")
    if any(separator in experiment_id for separator in ("/", "\\")) or "." in experiment_id:
        raise ValueError("experimentId must not contain path separators or dots")
    return experiment_id


def validate_submission(payload):
    if not isinstance(payload, dict):
        raise ValueError("Submission payload must be an object")

    participant_code = normalize_participant_code(payload.get("participantCode"))
    expected_assignment = assignment_for_code(participant_code)
    if payload.get("assignmentGroup") != expected_assignment["group"]:
        raise ValueError("assignmentGroup does not match participantCode assignment")

    stages = payload.get("stages")
    if not isinstance(stages, list) or len(stages) != 2:
        raise ValueError("Submission must include exactly two stages")

    require_non_empty_string(payload, "startedAt", "submission")
    require_non_empty_string(payload, "completedAt", "submission")
    started_at_ms = require_non_negative_int(payload, "startedAtMs", "submission")
    completed_at_ms = require_non_negative_int(payload, "completedAtMs", "submission")
    require_non_negative_int(payload, "totalDurationMs", "submission")
    if completed_at_ms < started_at_ms:
        raise ValueError("submission completedAtMs must be greater than or equal to startedAtMs")

    for expected_stage, actual_stage in zip(expected_assignment["stages"], stages):
        context = f"stage {expected_stage['stageIndex']}"
        if not isinstance(actual_stage, dict):
            raise ValueError(f"{context} must be an object")
        for field_name in ("stageIndex", "condition", "materialId"):
            if actual_stage.get(field_name) != expected_stage[field_name]:
                raise ValueError(f"{context} {field_name} does not match participant assignment")
        stage_start = require_non_negative_int(actual_stage, "stageStartedAtMs", context)
        stage_submit = require_non_negative_int(actual_stage, "stageSubmittedAtMs", context)
        require_non_negative_int(actual_stage, "stageDurationMs", context)
        if stage_submit < stage_start:
            raise ValueError(f"{context} stageSubmittedAtMs must be greater than or equal to stageStartedAtMs")
        answers = actual_stage.get("answers")
        if not isinstance(answers, list) or len(answers) != 6:
            raise ValueError(f"{context} must include Q1-Q6 answer records in order")
        answer_ids = [answer.get("questionId") if isinstance(answer, dict) else None for answer in answers]
        if answer_ids != EXPECTED_ANSWER_IDS:
            raise ValueError(f"{context} must include Q1-Q6 answer records in order")
        for answer_index, answer in enumerate(answers, start=1):
            answer_context = f"{context} Q{answer_index} answer"
            if not isinstance(answer, dict):
                raise ValueError(f"{answer_context} must be an object")
            require_non_empty_string(answer, "questionText", answer_context)
            require_non_empty_string(answer, "answer", answer_context)
            answer_start = require_non_negative_int(answer, "answerStartedAtMs", answer_context)
            answer_submit = require_non_negative_int(answer, "submittedAtMs", answer_context)
            require_non_negative_int(answer, "durationMs", answer_context)
            if answer_submit < answer_start:
                raise ValueError(f"{answer_context} submittedAtMs must be greater than or equal to answerStartedAtMs")

    return participant_code, expected_assignment


class ExperimentStorage:
    def __init__(self, data_dir):
        self.data_dir = Path(data_dir)
        self.config_dir = self.data_dir / "config"
        self.questions_dir = self.config_dir / "questions"
        self.static_tables_dir = self.config_dir / "static_tables"
        self.sessions_dir = self.data_dir / "sessions"
        self.submissions_dir = self.data_dir / "submissions"
        self.exports_dir = self.data_dir / "exports"

    def ensure_defaults(self):
        self.questions_dir.mkdir(parents=True, exist_ok=True)
        self.static_tables_dir.mkdir(parents=True, exist_ok=True)
        self.sessions_dir.mkdir(parents=True, exist_ok=True)
        self.submissions_dir.mkdir(parents=True, exist_ok=True)
        self.exports_dir.mkdir(parents=True, exist_ok=True)
        materials_path = self.config_dir / "materials.json"
        if not materials_path.exists():
            atomic_write_json(materials_path, {"materials": DEFAULT_MATERIALS, "q6Text": Q6_TEXT})
        for material in DEFAULT_MATERIALS:
            question_path = self.questions_dir / f"{material['id']}.json"
            if not question_path.exists():
                atomic_write_json(question_path, {
                    "material_id": material["id"],
                    "version": 0,
                    "frozen": False,
                    "generated_at": "",
                    "prompt_version": QUESTION_PROMPT_VERSION,
                    "questions": [],
                })
            table_path = self.static_tables_dir / f"{material['id']}.json"
            if not table_path.exists():
                atomic_write_json(table_path, {
                    "material_id": material["id"],
                    "version": 0,
                    "frozen": False,
                    "rows": [],
                    "updated_at": "",
                    "frozen_at": "",
                })


    def _session_path(self, experiment_id):
        sessions_root = self.sessions_dir.resolve()
        target = (self.sessions_dir / f"{validate_experiment_id(experiment_id)}.json").resolve()
        if target.parent != sessions_root:
            raise ValueError("experimentId resolved outside sessions directory")
        return target

    def create_session(self, participant_code):
        self.ensure_defaults()
        expected_assignment = assignment_for_code(participant_code)
        experiment_id = generate_experiment_id()
        payload = {
            "experimentId": experiment_id,
            "participantCode": expected_assignment["participantCode"],
            "assignmentGroup": expected_assignment["group"],
            "stages": expected_assignment["stages"],
            "startedAt": utc_now_iso(),
        }
        target = self._session_path(experiment_id)
        if target.exists():
            raise ValueError("experimentId already exists; retry start")
        atomic_write_json(target, payload)
        return payload

    def load_session(self, experiment_id):
        self.ensure_defaults()
        target = self._session_path(experiment_id)
        if not target.exists():
            raise ValueError("experimentId has not been started")
        with target.open(encoding="utf-8") as handle:
            return json.load(handle)

    def validate_started_session(self, payload, participant_code, expected_assignment):
        if not payload.get("experimentId"):
            raise ValueError("experimentId is required from started experiment")
        experiment_id = validate_experiment_id(payload.get("experimentId"))
        session = self.load_session(experiment_id)
        if session.get("participantCode") != participant_code:
            raise ValueError("experimentId started for a different participantCode")
        if session.get("assignmentGroup") != expected_assignment["group"]:
            raise ValueError("experimentId assignmentGroup does not match started session")
        if session.get("stages") != expected_assignment["stages"]:
            raise ValueError("experimentId stages do not match started session")
        return experiment_id

    def get_config(self):
        self.ensure_defaults()
        with (self.config_dir / "materials.json").open(encoding="utf-8") as handle:
            return json.load(handle)

    def load_questions(self, material_id):
        self.ensure_defaults()
        require_material_id(material_id)
        path = self.questions_dir / f"{material_id}.json"
        with path.open(encoding="utf-8") as handle:
            return json.load(handle)

    def load_participant_questions(self, material_id):
        payload = self.load_questions(material_id)
        if not payload.get("frozen"):
            raise ValueError(f"Questions for {material_id} are not frozen")
        validate_question_set_complete(payload)
        return payload

    def save_questions(self, material_id, payload):
        self.ensure_defaults()
        require_material_id(material_id)
        existing = self.load_questions(material_id)
        if existing.get("frozen"):
            raise ValueError(f"Questions for {material_id} are frozen; unfreeze before saving")
        next_payload = dict(payload)
        next_payload["material_id"] = material_id
        next_payload["version"] = int(next_payload.get("version") or existing.get("version") or 0)
        next_payload["prompt_version"] = next_payload.get("prompt_version") or QUESTION_PROMPT_VERSION
        next_payload["generated_at"] = next_payload.get("generated_at") or utc_now_iso()
        next_payload["frozen"] = False
        next_payload["questions"] = list(next_payload.get("questions") or [])
        validate_question_set_complete(next_payload)
        atomic_write_json(self.questions_dir / f"{material_id}.json", next_payload)
        return next_payload

    def freeze_questions(self, material_id, frozen):
        payload = self.load_questions(material_id)
        if frozen:
            validate_question_set_complete(payload)
        payload["frozen"] = bool(frozen)
        payload["frozen_at"] = utc_now_iso() if frozen else ""
        atomic_write_json(self.questions_dir / f"{material_id}.json", payload)
        return payload

    def load_static_table(self, material_id):
        self.ensure_defaults()
        require_material_id(material_id)
        path = self.static_tables_dir / f"{material_id}.json"
        with path.open(encoding="utf-8") as handle:
            payload = json.load(handle)
        payload.setdefault("rows", [])
        payload.setdefault("version", 0)
        payload.setdefault("frozen", False)
        return payload

    def load_participant_static_table(self, material_id):
        payload = self.load_static_table(material_id)
        if not payload.get("frozen"):
            raise ValueError(f"Static table for {material_id} is not frozen")
        rows = payload.get("rows")
        if not isinstance(rows, list) or not rows:
            raise ValueError(f"Static table for {material_id} is incomplete")
        return {
            "material_id": payload["material_id"],
            "version": payload.get("version", 0),
            "rows": rows,
        }

    def save_static_table(self, material_id, rows, generation_prompts=None, markdown_table=None):
        self.ensure_defaults()
        require_material_id(material_id)
        existing = self.load_static_table(material_id)
        if existing.get("frozen"):
            raise ValueError(f"Static table for {material_id} is frozen; unfreeze before saving")
        if not isinstance(rows, list) or not rows:
            raise ValueError("Static table rows must be a non-empty list")
        for index, row in enumerate(rows, start=1):
            if not isinstance(row, dict):
                raise ValueError(f"Static table row {index} must be an object")
        payload = {
            **existing,
            "material_id": material_id,
            "version": int(existing.get("version") or 0) + 1,
            "frozen": False,
            "rows": rows,
            "updated_at": utc_now_iso(),
        }
        if isinstance(generation_prompts, dict):
            payload["generation_prompts"] = generation_prompts
        if isinstance(markdown_table, str) and markdown_table.strip():
            payload["markdown_table"] = markdown_table
        elif "markdown_table" in payload:
            payload.pop("markdown_table", None)
        atomic_write_json(self.static_tables_dir / f"{material_id}.json", payload)
        return payload

    def freeze_static_table(self, material_id, frozen):
        payload = self.load_static_table(material_id)
        if frozen and (not isinstance(payload.get("rows"), list) or not payload.get("rows")):
            raise ValueError(f"Static table for {material_id} is incomplete")
        payload["frozen"] = bool(frozen)
        payload["frozen_at"] = utc_now_iso() if frozen else ""
        atomic_write_json(self.static_tables_dir / f"{material_id}.json", payload)
        return payload

    def save_submission(self, payload, require_started_session=False):
        self.ensure_defaults()
        participant_code, expected_assignment = validate_submission(payload)
        saved = dict(payload)
        saved["participantCode"] = participant_code
        saved["assignmentGroup"] = expected_assignment["group"]
        if require_started_session:
            saved["experimentId"] = self.validate_started_session(saved, participant_code, expected_assignment)
        elif "experimentId" in saved:
            saved["experimentId"] = validate_experiment_id(saved["experimentId"])
        else:
            saved["experimentId"] = generate_experiment_id()
        saved["savedAt"] = utc_now_iso()

        submissions_root = self.submissions_dir.resolve()
        target = (self.submissions_dir / f"{saved['experimentId']}.json").resolve()
        if target.parent != submissions_root:
            raise ValueError("experimentId resolved outside submissions directory")
        if target.exists():
            raise ValueError("experimentId already exists; duplicate completion is not allowed")
        atomic_write_json(target, saved)
        self.write_exports()
        return saved

    def list_submissions(self):
        self.ensure_defaults()
        records = []
        for path in sorted(self.submissions_dir.glob("*.json")):
            with path.open(encoding="utf-8") as handle:
                records.append(json.load(handle))
        return records

    def write_exports(self):
        self.ensure_defaults()
        submissions = self.list_submissions()
        summary_path = self.exports_dir / "submissions_summary.csv"
        answers_path = self.exports_dir / "answers_detail.csv"
        atomic_write_csv(summary_path, [
            "experiment_id", "participant_code", "assignment_group", "started_at",
            "completed_at", "total_duration_ms", "stage_count",
        ], ({
            "experiment_id": record.get("experimentId", ""),
            "participant_code": record.get("participantCode", ""),
            "assignment_group": record.get("assignmentGroup", ""),
            "started_at": record.get("startedAt", ""),
            "completed_at": record.get("completedAt", ""),
            "total_duration_ms": record.get("totalDurationMs", ""),
            "stage_count": len(record.get("stages") or []),
        } for record in submissions))
        answer_rows = []
        for record in submissions:
            for stage in record.get("stages") or []:
                for answer in stage.get("answers") or []:
                    answer_rows.append({
                        "experiment_id": record.get("experimentId", ""),
                        "participant_code": record.get("participantCode", ""),
                        "assignment_group": record.get("assignmentGroup", ""),
                        "stage_index": stage.get("stageIndex", ""),
                        "condition": stage.get("condition", ""),
                        "material_id": stage.get("materialId", ""),
                        "question_id": answer.get("questionId", ""),
                        "question_text": answer.get("questionText", ""),
                        "answer": answer.get("answer", ""),
                        "primary_source": answer.get("primarySource", ""),
                        "left_evidence": answer.get("leftEvidence", ""),
                        "right_evidence": answer.get("rightEvidence", ""),
                        "duration_ms": answer.get("durationMs", ""),
                    })
        atomic_write_csv(answers_path, [
            "experiment_id", "participant_code", "assignment_group", "stage_index",
            "condition", "material_id", "question_id", "question_text", "answer",
            "primary_source", "left_evidence", "right_evidence", "duration_ms",
        ], answer_rows)
        return {"summaryCsv": str(summary_path), "answersCsv": str(answers_path)}
