import csv
import json
import os
import tempfile
import uuid
from datetime import datetime, timezone
from pathlib import Path

from .defaults import DEFAULT_MATERIALS, Q6_TEXT, QUESTION_PROMPT_VERSION


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


class ExperimentStorage:
    def __init__(self, data_dir):
        self.data_dir = Path(data_dir)
        self.config_dir = self.data_dir / "config"
        self.questions_dir = self.config_dir / "questions"
        self.static_tables_dir = self.config_dir / "static_tables"
        self.submissions_dir = self.data_dir / "submissions"
        self.exports_dir = self.data_dir / "exports"

    def ensure_defaults(self):
        self.questions_dir.mkdir(parents=True, exist_ok=True)
        self.static_tables_dir.mkdir(parents=True, exist_ok=True)
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
                    "frozen": False,
                    "markdown_table": "",
                    "updated_at": "",
                })

    def get_config(self):
        self.ensure_defaults()
        with (self.config_dir / "materials.json").open(encoding="utf-8") as handle:
            return json.load(handle)

    def load_questions(self, material_id):
        self.ensure_defaults()
        path = self.questions_dir / f"{material_id}.json"
        if not path.exists():
            raise ValueError(f"Unknown material id: {material_id}")
        with path.open(encoding="utf-8") as handle:
            return json.load(handle)

    def save_questions(self, material_id, payload):
        self.ensure_defaults()
        if material_id not in {item["id"] for item in DEFAULT_MATERIALS}:
            raise ValueError(f"Unknown material id: {material_id}")
        existing = self.load_questions(material_id)
        next_payload = dict(payload)
        next_payload["material_id"] = material_id
        next_payload["version"] = int(next_payload.get("version") or existing.get("version") or 0)
        next_payload["prompt_version"] = next_payload.get("prompt_version") or QUESTION_PROMPT_VERSION
        next_payload["generated_at"] = next_payload.get("generated_at") or utc_now_iso()
        next_payload["frozen"] = bool(next_payload.get("frozen", False))
        next_payload["questions"] = list(next_payload.get("questions") or [])
        atomic_write_json(self.questions_dir / f"{material_id}.json", next_payload)
        return next_payload

    def freeze_questions(self, material_id, frozen):
        payload = self.load_questions(material_id)
        payload["frozen"] = bool(frozen)
        payload["frozen_at"] = utc_now_iso() if frozen else ""
        atomic_write_json(self.questions_dir / f"{material_id}.json", payload)
        return payload

    def save_submission(self, payload):
        self.ensure_defaults()
        saved = dict(payload)
        saved["experimentId"] = saved.get("experimentId") or f"exp-{datetime.now(timezone.utc).strftime('%Y%m%d')}-{uuid.uuid4().hex[:8]}"
        saved["savedAt"] = utc_now_iso()
        atomic_write_json(self.submissions_dir / f"{saved['experimentId']}.json", saved)
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
        with summary_path.open("w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=[
                "experiment_id", "participant_code", "assignment_group", "started_at",
                "completed_at", "total_duration_ms", "stage_count",
            ])
            writer.writeheader()
            for record in submissions:
                writer.writerow({
                    "experiment_id": record.get("experimentId", ""),
                    "participant_code": record.get("participantCode", ""),
                    "assignment_group": record.get("assignmentGroup", ""),
                    "started_at": record.get("startedAt", ""),
                    "completed_at": record.get("completedAt", ""),
                    "total_duration_ms": record.get("totalDurationMs", ""),
                    "stage_count": len(record.get("stages") or []),
                })
        with answers_path.open("w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=[
                "experiment_id", "participant_code", "assignment_group", "stage_index",
                "condition", "material_id", "question_id", "question_text", "answer",
                "primary_source", "left_evidence", "right_evidence", "duration_ms",
            ])
            writer.writeheader()
            for record in submissions:
                for stage in record.get("stages") or []:
                    for answer in stage.get("answers") or []:
                        writer.writerow({
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
        return {"summaryCsv": str(summary_path), "answersCsv": str(answers_path)}
