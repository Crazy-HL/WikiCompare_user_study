import csv
import json
from pathlib import Path

from experiment.storage import ExperimentStorage


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
    payload = {
        "material_id": "M1",
        "version": 1,
        "frozen": False,
        "questions": [{"question_id": "Q1", "question_text": "Compare one fact."}],
    }

    saved = storage.save_questions("M1", payload)
    assert saved["material_id"] == "M1"
    assert saved["questions"][0]["question_id"] == "Q1"

    frozen = storage.freeze_questions("M1", True)
    assert frozen["frozen"] is True
    assert storage.load_questions("M1")["frozen"] is True


def test_save_submission_assigns_id_and_exports_csv(tmp_path):
    storage = ExperimentStorage(tmp_path)
    storage.ensure_defaults()
    saved = storage.save_submission({
        "participantCode": "P01",
        "assignmentGroup": "S1",
        "startedAt": "2026-07-31T00:00:00Z",
        "completedAt": "2026-07-31T00:20:00Z",
        "totalDurationMs": 1200000,
        "stages": [
            {
                "stageIndex": 1,
                "condition": "wikicompare",
                "materialId": "M1",
                "stageDurationMs": 600000,
                "answers": [
                    {
                        "questionId": "Q1",
                        "questionText": "Question text",
                        "answer": "Answer text",
                        "primarySource": "T",
                        "leftEvidence": "L-P001",
                        "rightEvidence": "R-P001",
                        "durationMs": 30000,
                    }
                ],
            }
        ],
    })

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
