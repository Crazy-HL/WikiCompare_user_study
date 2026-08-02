import csv
from pathlib import Path

import pytest

from experiment.assignment import assignment_for_code
from experiment.storage import ExperimentStorage


def complete_questions_payload(material_id="M1"):
    return {
        "material_id": material_id,
        "version": 1,
        "frozen": False,
        "questions": [
            {"question_id": f"Q{index}", "question_text": f"Compare fact {index}."}
            for index in range(1, 6)
        ],
    }


def complete_submission_payload(participant_code="P01"):
    assignment = assignment_for_code(participant_code)
    payload = {
        "participantCode": assignment["participantCode"],
        "assignmentGroup": assignment["group"],
        "startedAt": "2026-07-31T00:00:00Z",
        "completedAt": "2026-07-31T00:20:00Z",
        "startedAtMs": 1000,
        "completedAtMs": 1201000,
        "totalDurationMs": 1200000,
        "stages": [],
    }
    for stage_offset, stage in enumerate(assignment["stages"]):
        payload["stages"].append({
            **stage,
            "questionVersion": 1,
            "stageStartedAtMs": 1000 + stage_offset * 600000,
            "stageSubmittedAtMs": 601000 + stage_offset * 600000,
            "stageDurationMs": 600000,
            "answers": [
                {
                    "questionId": f"Q{index}",
                    "questionText": f"Question {index}",
                    "answer": "Answer text",
                    "primarySource": "T",
                    "leftEvidence": "L-P001",
                    "rightEvidence": "R-P001",
                    "answerStartedAtMs": 2000 + index,
                    "submittedAtMs": 3000 + index,
                    "durationMs": 1000,
                }
                for index in range(1, 7)
            ],
        })
    return payload


def test_storage_creates_default_config_and_question_files(tmp_path):
    storage = ExperimentStorage(tmp_path)
    storage.ensure_defaults()

    config = storage.get_config()
    assert [item["id"] for item in config["materials"]] == ["M1", "M2"]
    assert "在阅读两篇文章" in config["q6Text"]
    assert (tmp_path / "config" / "questions" / "M1.json").exists()
    assert (tmp_path / "config" / "questions" / "M2.json").exists()


def test_question_save_and_freeze_round_trip(tmp_path):
    storage = ExperimentStorage(tmp_path)
    storage.ensure_defaults()
    payload = complete_questions_payload("M1")

    saved = storage.save_questions("M1", payload)
    assert saved["material_id"] == "M1"
    assert saved["questions"][0]["question_id"] == "Q1"

    frozen = storage.freeze_questions("M1", True)
    assert frozen["frozen"] is True
    assert storage.load_participant_questions("M1")["frozen"] is True

    with pytest.raises(ValueError, match="frozen"):
        storage.save_questions("M1", complete_questions_payload("M1"))


def test_static_table_save_and_freeze_round_trip(tmp_path):
    storage = ExperimentStorage(tmp_path)
    storage.ensure_defaults()
    rows = [{"id": "r1", "label": "GDP", "left": {"value": "1"}, "right": {"value": "2"}}]

    saved = storage.save_static_table("M1", rows)
    assert saved["version"] == 1
    assert saved["rows"] == rows

    frozen = storage.freeze_static_table("M1", True)
    assert frozen["frozen"] is True
    assert storage.load_participant_static_table("M1") == {"material_id": "M1", "version": 1, "rows": rows}

    with pytest.raises(ValueError, match="frozen"):
        storage.save_static_table("M1", rows)


def test_save_submission_assigns_id_and_exports_csv(tmp_path):
    storage = ExperimentStorage(tmp_path)
    storage.ensure_defaults()
    saved = storage.save_submission(complete_submission_payload("P01"))

    assert saved["experimentId"].startswith("exp-")
    submissions = storage.list_submissions()
    assert len(submissions) == 1
    assert submissions[0]["participantCode"] == "P01"

    exports = storage.write_exports()
    summary_path = Path(exports["summaryCsv"])
    answers_path = Path(exports["answersCsv"])
    assert summary_path.exists()
    assert answers_path.exists()

    with answers_path.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    assert rows[0]["participant_code"] == "P01"
    assert rows[0]["question_id"] == "Q1"
    assert rows[0]["primary_source"] == "T"
    assert rows[-1]["stage_index"] == "2"
    assert rows[-1]["question_id"] == "Q6"
