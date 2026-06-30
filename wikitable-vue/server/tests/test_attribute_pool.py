import pytest
import sys
import time
from types import SimpleNamespace

from services.attribute_pool import build_attribute_pool
from services.config import LLMConfig
from services.llm_client import LLMClient
from services.llm_client import MAX_PROMPT_PARAGRAPHS, MAX_SENTENCES_PER_PARAGRAPH
from services.llm_client import extract_json
from services.llm_client import _prompt_paragraphs


class FakeLLM:
    def extract_text_attributes(self, side, paragraphs):
        return [
            {
                "key": "export composition",
                "valueText": "electronics at 40%",
                "paragraphId": f"{side}-p-1",
                "sentenceIds": [f"{side}-s-1-2"],
                "confidence": 0.91,
            }
        ]


def test_build_attribute_pool_includes_infobox_and_main_text():
    article = {
        "infobox": [
            {
                "id": "left-info-1",
                "key": "GDP growth",
                "valueText": "2.3% (2024)",
                "source": "infobox",
                "side": "left",
                "section": "Statistics",
            }
        ],
        "paragraphs": [
            {
                "id": "left-p-1",
                "text": "Example A had GDP growth of 2.3% in 2024. Its exports were led by electronics at 40%.",
                "sentences": [
                    {
                        "id": "left-s-1-1",
                        "text": "Example A had GDP growth of 2.3% in 2024.",
                    },
                    {
                        "id": "left-s-1-2",
                        "text": "Its exports were led by electronics at 40%.",
                    },
                ],
            }
        ],
    }

    pool = build_attribute_pool(article, "left", FakeLLM())

    assert {item["source"] for item in pool} == {"infobox", "main_text"}
    assert pool[0]["sourceIds"] == ["left-info-1"]
    text_attr = next(item for item in pool if item["source"] == "main_text")
    assert text_attr["sourceIds"] == ["left-s-1-2"]
    assert text_attr["paragraphId"] == "left-p-1"


def test_build_attribute_pool_drops_text_attribute_with_invalid_source_id():
    article = {
        "infobox": [],
        "paragraphs": [
            {
                "id": "left-p-1",
                "text": "A sentence.",
                "sentences": [{"id": "left-s-1-1", "text": "A sentence."}],
            }
        ],
    }

    class BadLLM:
        def extract_text_attributes(self, side, paragraphs):
            return [
                {
                    "key": "bad",
                    "valueText": "bad",
                    "paragraphId": "left-p-99",
                    "sentenceIds": ["left-s-99-1"],
                }
            ]

    pool = build_attribute_pool(article, "left", BadLLM())

    assert pool == []


def test_build_attribute_pool_cleans_reference_and_edit_noise_from_values():
    article = {
        "infobox": [
            {
                "id": "left-info-1",
                "key": "GDP [1] edit",
                "valueText": "US$ 1.2 trillion [23] (2024 est.) edit",
            }
        ],
        "paragraphs": [
            {
                "id": "left-p-1",
                "text": "Exports were high.",
                "sentences": [{"id": "left-s-1-1", "text": "Exports were high."}],
            }
        ],
    }

    class NoisyLLM:
        def extract_text_attributes(self, side, paragraphs):
            return [
                {
                    "key": "Exports [2]",
                    "valueText": "US$ 700 billion [3] edit",
                    "paragraphId": "left-p-1",
                    "sentenceIds": ["left-s-1-1"],
                }
            ]

    pool = build_attribute_pool(article, "left", NoisyLLM())

    assert pool[0]["key"] == "GDP"
    assert pool[0]["valueText"] == "US$ 1.2 trillion (2024 est.)"
    assert pool[1]["key"] == "Exports"
    assert pool[1]["valueText"] == "US$ 700 billion"


def test_build_attribute_pool_returns_infobox_when_llm_unavailable_or_raises():
    article = {
        "infobox": [
            {
                "id": "right-info-1",
                "key": "Population",
                "valueText": "1 million",
                "source": "infobox",
                "side": "right",
                "section": None,
            }
        ],
        "paragraphs": [
            {
                "id": "right-p-1",
                "text": "A sentence.",
                "sentences": [{"id": "right-s-1-1", "text": "A sentence."}],
            }
        ],
    }

    class FailingLLM:
        def extract_text_attributes(self, side, paragraphs):
            raise RuntimeError("LLM is down")

    assert build_attribute_pool(article, "right", None) == [
        {
            "id": "right-attr-infobox-1",
            "side": "right",
            "key": "Population",
            "valueText": "1 million",
            "source": "infobox",
            "sourceIds": ["right-info-1"],
            "section": None,
        }
    ]
    assert build_attribute_pool(article, "right", FailingLLM()) == [
        {
            "id": "right-attr-infobox-1",
            "side": "right",
            "key": "Population",
            "valueText": "1 million",
            "source": "infobox",
            "sourceIds": ["right-info-1"],
            "section": None,
        }
    ]


def test_build_attribute_pool_drops_malformed_infobox_rows():
    article = {
        "infobox": [
            {"id": "left-info-1", "key": "GDP growth", "valueText": "2.3%"},
            {"key": "Missing source", "valueText": "bad"},
            {"id": "left-info-2", "key": "", "valueText": "bad"},
            {"id": "left-info-3", "key": "Blank value", "valueText": " "},
            "not a row",
        ],
        "paragraphs": [],
    }

    assert build_attribute_pool(article, "left", None) == [
        {
            "id": "left-attr-infobox-1",
            "side": "left",
            "key": "GDP growth",
            "valueText": "2.3%",
            "source": "infobox",
            "sourceIds": ["left-info-1"],
            "section": None,
        }
    ]


def test_build_attribute_pool_rejects_blank_text_key_or_value_and_missing_sentences():
    article = {
        "infobox": [],
        "paragraphs": [
            {
                "id": "left-p-1",
                "text": "A sentence.",
                "sentences": [{"id": "left-s-1-1", "text": "A sentence."}],
            }
        ],
    }

    class NoisyLLM:
        def extract_text_attributes(self, side, paragraphs):
            return [
                {
                    "key": "",
                    "valueText": "has value",
                    "paragraphId": "left-p-1",
                    "sentenceIds": ["left-s-1-1"],
                },
                {
                    "key": "has key",
                    "valueText": " ",
                    "paragraphId": "left-p-1",
                    "sentenceIds": ["left-s-1-1"],
                },
                {
                    "key": "missing sentences",
                    "valueText": "bad",
                    "paragraphId": "left-p-1",
                    "sentenceIds": [],
                },
            ]

    assert build_attribute_pool(article, "left", NoisyLLM()) == []


def test_build_attribute_pool_ignores_non_list_llm_output():
    article = {
        "infobox": [],
        "paragraphs": [
            {
                "id": "left-p-1",
                "text": "A sentence.",
                "sentences": [{"id": "left-s-1-1", "text": "A sentence."}],
            }
        ],
    }

    class MalformedLLM:
        def extract_text_attributes(self, side, paragraphs):
            return None

    assert build_attribute_pool(article, "left", MalformedLLM()) == []


def test_build_attribute_pool_times_out_slow_text_attribute_extraction():
    article = {
        "infobox": [
            {
                "id": "left-info-1",
                "key": "GDP growth",
                "valueText": "2.3%",
            }
        ],
        "paragraphs": [
            {
                "id": "left-p-1",
                "text": "A sentence.",
                "sentences": [{"id": "left-s-1-1", "text": "A sentence."}],
            }
        ],
    }

    class SlowLLM:
        config = SimpleNamespace(timeout_seconds=0.01)

        def extract_text_attributes(self, side, paragraphs):
            time.sleep(0.2)
            return [
                {
                    "key": "late attribute",
                    "valueText": "late value",
                    "paragraphId": "left-p-1",
                    "sentenceIds": ["left-s-1-1"],
                }
            ]

    started = time.monotonic()
    pool = build_attribute_pool(article, "left", SlowLLM())

    assert time.monotonic() - started < 0.15
    assert [item["key"] for item in pool] == ["GDP growth"]


def test_prompt_paragraphs_prioritizes_numeric_text_and_limits_payload():
    paragraphs = [
        {
            "id": "p-plain",
            "text": "This overview has no figures.",
            "sentences": [{"id": "s-plain", "text": "This overview has no figures."}],
        },
        *[
            {
                "id": f"p-{index}",
                "text": f"GDP growth was {index}% and exports were ${index} billion. " * 60,
                "sentences": [
                    {"id": f"s-{index}-{sentence}", "text": "Exports were worth $1 billion. " * 30}
                    for sentence in range(5)
                ],
            }
            for index in range(10)
        ],
    ]

    prompt_paragraphs = _prompt_paragraphs(paragraphs)

    assert len(prompt_paragraphs) == MAX_PROMPT_PARAGRAPHS
    assert prompt_paragraphs[0]["id"] == "p-0"
    assert "p-plain" not in [paragraph["id"] for paragraph in prompt_paragraphs]
    assert all(len(paragraph["sentences"]) == MAX_SENTENCES_PER_PARAGRAPH for paragraph in prompt_paragraphs)
    assert all(len(paragraph["text"]) <= 700 for paragraph in prompt_paragraphs)


def test_llm_client_disabled_config_does_not_instantiate_openai():
    client = LLMClient(
        LLMConfig(
            model="gpt-test",
            base_url="https://example.test/v1",
            api_key=None,
        )
    )

    assert client.client is None
    with pytest.raises(RuntimeError, match="disabled"):
        client.chat_json([])


def test_llm_client_configures_openai_timeout(monkeypatch):
    captured = {}

    class FakeOpenAI:
        def __init__(self, **kwargs):
            captured.update(kwargs)
            self.chat = SimpleNamespace(
                completions=SimpleNamespace(
                    create=lambda **_kwargs: SimpleNamespace(
                        choices=[
                            SimpleNamespace(
                                message=SimpleNamespace(content='{"ok": true}')
                            )
                        ]
                    )
                )
            )

    monkeypatch.setitem(sys.modules, "openai", SimpleNamespace(OpenAI=FakeOpenAI))

    client = LLMClient(
        LLMConfig(
            model="gpt-test",
            base_url="https://example.test/v1",
            api_key="test-key",
            timeout_seconds=6.5,
        )
    )

    assert client.chat_json([]) == {"ok": True}
    assert captured["timeout"] == 6.5
    assert captured["max_retries"] == 0


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ('```json\n[{"key": "GDP"}]\n```', [{"key": "GDP"}]),
        (
            'The answer is {"key": "GDP", "valueText": "2.3%"}',
            {"key": "GDP", "valueText": "2.3%"},
        ),
    ],
)
def test_extract_json_strips_markdown_fences_and_finds_json(text, expected):
    assert extract_json(text) == expected
