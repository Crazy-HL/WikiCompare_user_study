import json
from types import SimpleNamespace

import requests

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


def test_build_question_prompt_caps_long_article_contexts_to_avoid_provider_gateway_timeout():
    long_left = [
        {"id": f"L-P{index:03d}", "text": "Left comparison evidence " + ("x" * 500)}
        for index in range(1, 90)
    ]
    long_right = [
        {"id": f"R-P{index:03d}", "text": "Right comparison evidence " + ("y" * 500)}
        for index in range(1, 90)
    ]
    prompt = build_question_prompt(
        {"id": "M1", "leftTitle": "Left", "rightTitle": "Right"},
        {"title": "Left", "paragraphs": long_left},
        {"title": "Right", "paragraphs": long_right},
    )

    assert len(prompt) <= 15000
    assert "L-P001" in prompt
    assert "R-P001" in prompt
    assert "内容已截断" in prompt


def test_fetch_material_html_falls_back_to_openfactbook_snapshot_on_ssl_error(tmp_path, monkeypatch):
    import experiment.question_generation as question_generation

    snapshot_dir = tmp_path / "material_snapshots"
    snapshot_dir.mkdir()
    (snapshot_dir / "openfactbook-countries-india.html").write_text(
        "<main><h1>India 2026</h1><div class='group/field'><h3>GDP</h3><p>snapshot GDP text</p></div></main>",
        encoding="utf-8",
    )

    def raise_ssl_error(*args, **kwargs):
        raise requests.exceptions.SSLError("SSL EOF")

    monkeypatch.setattr(question_generation, "MATERIAL_SNAPSHOT_DIR", snapshot_dir, raising=False)
    monkeypatch.setattr(question_generation.requests, "get", raise_ssl_error)

    html = question_generation.fetch_material_html(SimpleNamespace(
        source_kind="web",
        display_url="https://openfactbook.org/countries/india/",
    ))

    assert "snapshot GDP text" in html


def test_generate_questions_retries_with_compact_prompt_after_gateway_timeout(monkeypatch):
    import experiment.question_generation as question_generation

    long_paragraphs = [
        {"id": f"left-p-{index}", "text": "left evidence " + ("x" * 400)}
        for index in range(20)
    ]
    right_paragraphs = [
        {"id": f"right-p-{index}", "text": "right evidence " + ("y" * 400)}
        for index in range(20)
    ]
    monkeypatch.setattr(
        question_generation,
        "load_material_articles",
        lambda material: (
            {"title": "Left", "paragraphs": long_paragraphs},
            {"title": "Right", "paragraphs": right_paragraphs},
        ),
    )

    class GatewayThenSuccessClient:
        def __init__(self):
            self.prompts = []

        def chat_json(self, messages):
            prompt = messages[-1]["content"]
            self.prompts.append(prompt)
            if len(self.prompts) == 1:
                raise RuntimeError("504 Gateway Time-out")
            return {
                "questions": [
                    {"question_id": f"Q{index}", "question_text": f"Question {index}", "gold_atoms": []}
                    for index in range(1, 6)
                ]
            }

    client = GatewayThenSuccessClient()
    result = question_generation.generate_questions_from_material(
        {"id": "M2", "leftTitle": "Left", "rightTitle": "Right"},
        7,
        llm_client=client,
    )

    assert result["material_id"] == "M2"
    assert len(client.prompts) == 2
    assert len(client.prompts[1]) < len(client.prompts[0])
    assert "内容已截断" in client.prompts[1]


def test_generate_questions_falls_back_to_local_draft_after_repeated_gateway_timeouts(monkeypatch):
    import experiment.question_generation as question_generation

    monkeypatch.setattr(
        question_generation,
        "load_material_articles",
        lambda material: (
            {
                "title": "India 2026",
                "paragraphs": [
                    {"id": "left-p-1", "text": "Introduction - Background: India became independent in 1947."},
                    {"id": "left-p-2", "text": "Geography - Area - total: 3,287,263 sq km."},
                    {"id": "left-p-3", "text": "People and Society - Population: 1,409,128,296."},
                    {"id": "left-p-4", "text": "Economy - Real GDP growth rate: 6.5%."},
                ],
            },
            {
                "title": "Indonesia 2026",
                "paragraphs": [
                    {"id": "right-p-1", "text": "Introduction - Background: Indonesia declared independence in 1945."},
                    {"id": "right-p-2", "text": "Geography - Area - total: 1,904,569 sq km."},
                    {"id": "right-p-3", "text": "People and Society - Population: 283,487,931."},
                    {"id": "right-p-4", "text": "Economy - Real GDP growth rate: 5%."},
                ],
            },
        ),
    )

    class AlwaysGatewayClient:
        def __init__(self):
            self.calls = 0

        def chat_json(self, messages):
            self.calls += 1
            raise RuntimeError("504 Gateway Time-out")

    client = AlwaysGatewayClient()
    result = question_generation.generate_questions_from_material(
        {"id": "M2", "leftTitle": "India 2026", "rightTitle": "Indonesia 2026"},
        8,
        llm_client=client,
    )

    assert client.calls == 2
    assert result["material_id"] == "M2"
    assert result["version"] == 8
    assert [item["question_id"] for item in result["questions"]] == ["Q1", "Q2", "Q3", "Q4", "Q5"]
    assert all(item["gold_atoms"] for item in result["questions"])
    assert "本地备用生成" in result["questions"][0]["understanding_target"]


def test_openfactbook_generation_uses_compact_prompt_and_local_draft_after_one_gateway_timeout(monkeypatch):
    import experiment.question_generation as question_generation

    paragraphs = [{"id": "left-p-1", "text": "Geography - Area - total: 3,287,263 sq km."}]
    right_paragraphs = [{"id": "right-p-1", "text": "Geography - Area - total: 1,904,569 sq km."}]
    monkeypatch.setattr(
        question_generation,
        "load_material_articles",
        lambda material: (
            {"title": "India 2026", "paragraphs": paragraphs},
            {"title": "Indonesia 2026", "paragraphs": right_paragraphs},
        ),
    )

    class AlwaysGatewayClient:
        def __init__(self):
            self.prompts = []

        def chat_json(self, messages):
            self.prompts.append(messages[-1]["content"])
            raise RuntimeError("504 Gateway Time-out")

    client = AlwaysGatewayClient()
    result = question_generation.generate_questions_from_material(
        {
            "id": "M2",
            "leftTitle": "India 2026",
            "rightTitle": "Indonesia 2026",
            "leftUrl": "https://openfactbook.org/countries/india/",
            "rightUrl": "https://openfactbook.org/countries/indonesia/",
        },
        9,
        llm_client=client,
    )

    assert len(client.prompts) == 1
    assert len(client.prompts[0]) < 7000
    assert result["questions"][0]["understanding_target"].startswith("本地备用生成")


def test_generate_questions_records_question_and_answer_prompt_metadata(monkeypatch):
    import experiment.question_generation as question_generation

    monkeypatch.setattr(
        question_generation,
        "load_material_articles",
        lambda material: (
            {"title": "Left", "paragraphs": [{"id": "left-p-1", "text": "Left fact."}]},
            {"title": "Right", "paragraphs": [{"id": "right-p-1", "text": "Right fact."}]},
        ),
    )

    class PromptCapturingClient:
        def chat_json(self, messages):
            return {
                "questions": [
                    {"question_id": f"Q{index}", "question_text": f"Question {index}", "gold_atoms": []}
                    for index in range(1, 6)
                ]
            }

    result = question_generation.generate_questions_from_material(
        {"id": "M1", "leftTitle": "Left", "rightTitle": "Right"},
        10,
        llm_client=PromptCapturingClient(),
    )

    prompts = result["generation_prompts"]
    assert prompts["question_prompt"]["system"] == "You generate bilingual comparison-reading experiment questions. Return JSON only."
    assert "Left fact." in prompts["question_prompt"]["user"]
    assert prompts["answer_prompt"]["system"] == prompts["question_prompt"]["system"]
    assert prompts["answer_prompt"]["user"] == prompts["question_prompt"]["user"]
    assert "同一次模型请求" in prompts["answer_prompt"]["note"]
