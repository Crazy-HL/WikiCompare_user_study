import json
from types import SimpleNamespace

import requests

from experiment.question_generation import article_text, build_question_prompt, normalize_generated_questions
from experiment.static_table_generation import build_static_table_prompt


def test_build_question_prompt_includes_complete_infobox_and_body_sections():
    prompt = build_question_prompt(
        {"id": "M1", "leftTitle": "Left", "rightTitle": "Right"},
        {
            "title": "Left",
            "infobox": [{"id": "L-I001", "label": "GDP", "value": "Left GDP infobox value."}],
            "paragraphs": [{"id": "L-P001", "text": "Left body text."}],
        },
        {
            "title": "Right",
            "infobox": [{"id": "R-I001", "label": "GDP", "value": "Right GDP infobox value."}],
            "paragraphs": [{"id": "R-P001", "text": "Right body text."}],
        },
    )
    assert "完整 infobox" in prompt
    assert "完整正文" in prompt
    assert "【Infobox】" in prompt
    assert "【正文】" in prompt
    assert "[L-I001] GDP: Left GDP infobox value." in prompt
    assert "[R-I001] GDP: Right GDP infobox value." in prompt
    assert "[L-P001] Left body text." in prompt
    assert "[R-P001] Right body text." in prompt
    assert "Q1【单维事实比较】" in prompt
    assert "Q5【综合结论证据验证】" in prompt


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


def test_article_text_supports_parsed_infobox_key_and_value_text_fields():
    rendered = article_text({
        "infobox": [{"id": "left-info-1", "key": "GDP", "valueText": "1 trillion"}],
        "paragraphs": [{"id": "left-p-1", "text": "Body fact."}],
    })

    assert "[left-info-1] GDP: 1 trillion" in rendered
    assert "[left-p-1] Body fact." in rendered
    assert "未提取到 infobox" not in rendered


def test_article_text_keeps_full_infobox_and_body_by_default():
    article = {
        "infobox": [{"id": "L-I001", "label": "Long infobox", "value": "i" * 6000}],
        "paragraphs": [
            {"id": "L-P001", "text": "first paragraph"},
            {"id": "L-P089", "text": "late paragraph " + ("x" * 6000)},
        ],
    }

    rendered = article_text(article)

    assert "[L-I001] Long infobox: " + ("i" * 6000) in rendered
    assert "[L-P001] first paragraph" in rendered
    assert "[L-P089] late paragraph " + ("x" * 6000) in rendered
    assert "内容已截断" not in rendered


def test_build_question_prompt_keeps_late_article_content_without_truncation_by_default():
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
        {"title": "Left", "infobox": [{"id": "L-I001", "label": "Population", "value": "full left infobox"}], "paragraphs": long_left},
        {"title": "Right", "infobox": [{"id": "R-I001", "label": "Population", "value": "full right infobox"}], "paragraphs": long_right},
    )

    assert "[L-I001] Population: full left infobox" in prompt
    assert "[R-I001] Population: full right infobox" in prompt
    assert "L-P001" in prompt
    assert "R-P001" in prompt
    assert "L-P089" in prompt
    assert "R-P089" in prompt
    assert "内容已截断" not in prompt


def test_build_static_table_prompt_uses_complete_infobox_and_body_by_default():
    prompt = build_static_table_prompt(
        {"id": "M1", "leftTitle": "Left", "rightTitle": "Right"},
        {
            "title": "Left",
            "infobox": [{"id": "L-I001", "label": "Capital", "value": "Left capital"}],
            "paragraphs": [
                {"id": "L-P001", "text": "Left opening."},
                {"id": "L-P050", "text": "Left late body evidence."},
            ],
        },
        {
            "title": "Right",
            "infobox": [{"id": "R-I001", "label": "Capital", "value": "Right capital"}],
            "paragraphs": [
                {"id": "R-P001", "text": "Right opening."},
                {"id": "R-P050", "text": "Right late body evidence."},
            ],
        },
    )

    assert "完整 infobox" in prompt
    assert "完整正文" in prompt
    assert "[L-I001] Capital: Left capital" in prompt
    assert "[R-I001] Capital: Right capital" in prompt
    assert "[L-P050] Left late body evidence." in prompt
    assert "[R-P050] Right late body evidence." in prompt
    assert "内容已截断" not in prompt


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


def test_generate_questions_does_not_retry_with_compact_prompt_after_gateway_timeout(monkeypatch):
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
    assert len(client.prompts) == 1
    assert "left-p-19" in client.prompts[0]
    assert "right-p-19" in client.prompts[0]
    assert "内容已截断" not in client.prompts[0]
    assert "本地备用生成" in result["questions"][0]["understanding_target"]


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

    assert client.calls == 1
    assert result["material_id"] == "M2"
    assert result["version"] == 8
    assert [item["question_id"] for item in result["questions"]] == ["Q1", "Q2", "Q3", "Q4", "Q5"]
    assert all(item["gold_atoms"] for item in result["questions"])
    assert "本地备用生成" in result["questions"][0]["understanding_target"]


def test_openfactbook_generation_uses_full_prompt_and_local_draft_after_one_gateway_timeout(monkeypatch):
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
    assert "Geography - Area - total: 3,287,263 sq km." in client.prompts[0]
    assert "Geography - Area - total: 1,904,569 sq km." in client.prompts[0]
    assert "内容已截断" not in client.prompts[0]
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
    assert "complete article infoboxes" in prompts["question_prompt"]["system"]
    assert "完整 infobox" in prompts["question_prompt"]["user"]
    assert "完整正文" in prompts["question_prompt"]["user"]
    assert "Left fact." in prompts["question_prompt"]["user"]
    assert prompts["answer_prompt"]["system"] == prompts["question_prompt"]["system"]
    assert prompts["answer_prompt"]["user"] == prompts["question_prompt"]["user"]
    assert "同一次模型请求" in prompts["answer_prompt"]["note"]


def test_generate_static_table_from_material_sends_full_infobox_and_body_prompt(monkeypatch):
    import experiment.static_table_generation as static_table_generation

    monkeypatch.setattr(
        static_table_generation,
        "load_material_articles",
        lambda material: (
            {
                "title": "Left",
                "infobox": [{"id": "L-I001", "label": "Currency", "value": "Left currency"}],
                "paragraphs": [
                    {"id": "L-P001", "text": "Left opening."},
                    {"id": "L-P099", "text": "Left final paragraph evidence."},
                ],
            },
            {
                "title": "Right",
                "infobox": [{"id": "R-I001", "label": "Currency", "value": "Right currency"}],
                "paragraphs": [
                    {"id": "R-P001", "text": "Right opening."},
                    {"id": "R-P099", "text": "Right final paragraph evidence."},
                ],
            },
        ),
    )

    class CapturingClient:
        def __init__(self):
            self.prompt = ""

        def chat_json(self, messages):
            self.prompt = messages[-1]["content"]
            return {
                "rows": [
                    {
                        "id": "R1",
                        "label": "Currency",
                        "left": {"value": "Left currency"},
                        "right": {"value": "Right currency"},
                    }
                ]
            }

    client = CapturingClient()
    result = static_table_generation.generate_static_table_from_material(
        {"id": "M1", "leftTitle": "Left", "rightTitle": "Right"},
        llm_client=client,
    )

    assert result["rows"][0]["label"] == "Currency"
    assert "[L-I001] Currency: Left currency" in client.prompt
    assert "[R-I001] Currency: Right currency" in client.prompt
    assert "[L-P099] Left final paragraph evidence." in client.prompt
    assert "[R-P099] Right final paragraph evidence." in client.prompt
    assert "内容已截断" not in client.prompt
    assert "完整 infobox" in result["generation_prompts"]["static_table_prompt"]["user"]
