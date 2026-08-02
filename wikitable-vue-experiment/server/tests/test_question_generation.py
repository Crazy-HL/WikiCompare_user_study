import json

from experiment.question_generation import build_question_prompt, normalize_generated_questions


def test_build_question_prompt_includes_material_and_required_question_types():
    prompt = build_question_prompt(
        {"id": "M1", "leftTitle": "Left", "rightTitle": "Right"},
        {"title": "Left", "paragraphs": [{"id": "L-P001", "text": "Left text."}]},
        {"title": "Right", "paragraphs": [{"id": "R-P001", "text": "Right text."}]},
    )
    assert "只根据下面两篇冻结文章" in prompt
    assert "Q1【单维事实比较】" in prompt
    assert "Q5【综合结论证据验证】" in prompt
    assert "Left text." in prompt
    assert "Right text." in prompt


def test_normalize_generated_questions_accepts_json_string_and_sets_version():
    raw = json.dumps({
        "material_id": "M1",
        "questions": [
            {"question_id": f"Q{index}", "question_text": f"Question {index}", "gold_atoms": []}
            for index in range(1, 6)
        ],
    })
    normalized = normalize_generated_questions(raw, "M1", 3)
    assert normalized["material_id"] == "M1"
    assert normalized["version"] == 3
    assert normalized["frozen"] is False
    assert [item["question_id"] for item in normalized["questions"]] == ["Q1", "Q2", "Q3", "Q4", "Q5"]


def test_normalize_generated_questions_rejects_incomplete_question_set():
    try:
        normalize_generated_questions({"questions": [{"question_id": "Q1"}]}, "M1", 1)
    except ValueError as error:
        assert "Q1-Q5" in str(error)
    else:
        raise AssertionError("Expected ValueError")


def test_normalize_generated_questions_rejects_non_list_questions():
    try:
        normalize_generated_questions({"questions": "abc"}, "M1", 1)
    except ValueError as error:
        assert "questions must be a list" in str(error)
    else:
        raise AssertionError("Expected ValueError")


def test_normalize_generated_questions_rejects_non_object_question_items():
    try:
        normalize_generated_questions({"questions": [None]}, "M1", 1)
    except ValueError as error:
        assert "question item" in str(error)
    else:
        raise AssertionError("Expected ValueError")
