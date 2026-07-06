import pytest
import sys
import time
from types import SimpleNamespace

from services.attribute_pool import build_attribute_pool, _text_attribute_timeout
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


def test_build_attribute_pool_merges_duplicate_text_attribute_as_related_evidence():
    article = {
        "infobox": [
            {
                "id": "left-info-1",
                "key": "GDP growth",
                "valueText": "2.3% (2024)",
            }
        ],
        "paragraphs": [
            {
                "id": "left-p-1",
                "text": "GDP growth was 2.3% in 2024.",
                "sentences": [
                    {"id": "left-s-1-1", "text": "GDP growth was 2.3% in 2024."},
                ],
            }
        ],
    }

    class DuplicateLLM:
        def extract_text_attributes(self, side, paragraphs):
            return [
                {
                    "key": "GDP growth",
                    "valueText": "2.3% in 2024",
                    "paragraphId": "left-p-1",
                    "sentenceIds": ["left-s-1-1"],
                }
            ]

    pool = build_attribute_pool(article, "left", DuplicateLLM())

    assert len(pool) == 1
    assert pool[0]["sourceIds"] == ["left-info-1"]
    assert pool[0]["relatedSourceIds"] == ["left-s-1-1"]


def test_build_attribute_pool_links_infobox_to_matching_text_without_llm():
    article = {
        "infobox": [
            {
                "id": "left-info-1",
                "key": "GDP growth",
                "valueText": "2.3% (2024)",
            }
        ],
        "paragraphs": [
            {
                "id": "left-p-1",
                "text": "GDP growth was 2.3% in 2024. Exports expanded later.",
                "sentences": [
                    {"id": "left-s-1-1", "text": "GDP growth was 2.3% in 2024."},
                    {"id": "left-s-1-2", "text": "Exports expanded later."},
                ],
            }
        ],
    }

    pool = build_attribute_pool(article, "left", None)

    assert len(pool) == 1
    assert pool[0]["sourceIds"] == ["left-info-1"]
    assert pool[0]["relatedSourceIds"] == ["left-s-1-1"]


def test_build_attribute_pool_links_infobox_to_acronym_text_evidence():
    article = {
        "infobox": [
            {
                "id": "left-info-1",
                "key": "Human Development Index",
                "valueText": "0.929 very high (2023) (19th)",
            }
        ],
        "paragraphs": [
            {
                "id": "left-p-1",
                "text": "The country recorded an HDI of 0.929 in 2023, ranking 19th globally.",
                "sentences": [
                    {
                        "id": "left-s-1-1",
                        "text": "The country recorded an HDI of 0.929 in 2023, ranking 19th globally.",
                    },
                ],
            }
        ],
    }

    pool = build_attribute_pool(article, "left", None)

    assert pool[0]["relatedSourceIds"] == ["left-s-1-1"]


def test_build_attribute_pool_preserves_structured_values_from_infobox_and_text():
    article = {
        "infobox": [
            {
                "id": "left-info-1",
                "key": "Main industries",
                "valueText": "Electronics Telecommunications Shipbuilding",
                "structuredValues": [
                    {"label": "Electronics", "value": "Electronics", "kind": "list_item"},
                    {"label": "Telecommunications", "value": "Telecommunications", "kind": "list_item"},
                ],
            }
        ],
        "paragraphs": [
            {
                "id": "left-p-1",
                "text": "The main industries are electronics and shipbuilding.",
                "sentences": [{"id": "left-s-1-1", "text": "The main industries are electronics and shipbuilding."}],
            }
        ],
    }

    class StructuredLLM:
        def extract_text_attributes(self, side, paragraphs):
            return [
                {
                    "key": "Main industries",
                    "valueText": "electronics; shipbuilding",
                    "paragraphId": "left-p-1",
                    "sentenceIds": ["left-s-1-1"],
                    "structuredValues": [
                        {"label": "electronics", "value": "electronics", "kind": "list_item"},
                        {"label": "shipbuilding", "value": "shipbuilding", "kind": "list_item"},
                    ],
                }
            ]

    pool = build_attribute_pool(article, "left", StructuredLLM())

    assert pool[0]["structuredValues"] == [
        {"label": "Electronics", "value": "Electronics", "kind": "list_item"},
        {"label": "Telecommunications", "value": "Telecommunications", "kind": "list_item"},
    ]
    assert pool[1]["structuredValues"] == [
        {"label": "electronics", "value": "electronics", "kind": "list_item"},
        {"label": "shipbuilding", "value": "shipbuilding", "kind": "list_item"},
    ]


def test_llm_client_refines_extracted_values_from_items_response():
    client = LLMClient(LLMConfig(model="test", base_url="http://example.test", api_key=None))

    def fake_chat_json(messages):
        assert "ruleValues" in messages[-1]["content"]
        assert "lowest 10%" in messages[-1]["content"]
        return {
            "items": [
                {
                    "value": 2.7,
                    "label": "lowest 10%",
                    "year": 2016,
                    "rawText": "lowest 10%: 2.7%",
                    "confidence": 0.9,
                }
            ]
        }

    client.chat_json = fake_chat_json

    assert client.refine_extracted_values(
        key="Income share",
        value_text="lowest 10%: 2.7%",
        rule_values=[{"value": 10.0}, {"value": 2.7}],
        data_type="Proportional",
    ) == [
        {
            "value": 2.7,
            "label": "lowest 10%",
            "year": 2016,
            "rawText": "lowest 10%: 2.7%",
            "confidence": 0.9,
        }
    ]


def test_llm_client_extracts_paired_text_attributes_with_data_first_prompt():
    client = LLMClient(LLMConfig(model="test", base_url="http://example.test", api_key=None))
    captured = {}
    pair = {
        "dimensionLabel": "Historical emergence",
        "comparisonQuestion": "When did it emerge?",
        "left": {"valueText": "founded in 1956", "sentenceIds": ["left-s-1-1"]},
        "right": {"valueText": "emerged in the 1950s", "sentenceIds": ["right-s-1-1"]},
        "dataPriority": True,
        "dataRole": "emergence_time",
        "confidence": 0.9,
    }

    def fake_chat_json(messages):
        captured["messages"] = messages
        return {"pairs": [pair]}

    client.chat_json = fake_chat_json

    result = client.extract_text_attribute_pairs(
        left_candidates=[{"claimText": "AI was founded in 1956.", "sentenceIds": ["left-s-1-1"]}],
        right_candidates=[{"claimText": "ML emerged in the 1950s.", "sentenceIds": ["right-s-1-1"]}],
        infobox_context={"left": [], "right": []},
    )

    assert result == {"pairs": [pair]}
    assert [message["role"] for message in captured["messages"]] == ["system", "user"]
    system_prompt = captured["messages"][0]["content"]
    prompt = captured["messages"][-1]["content"]
    assert "Return JSON only" in system_prompt
    assert "Return this JSON shape only" in prompt
    assert "Do not classify the article pair before extraction" in prompt
    assert "Do not fill or follow a fixed template" in prompt
    assert "Discover comparison dimensions from the evidence" in prompt
    assert "Prioritize data-bearing evidence" in prompt
    assert "Do not mark standalone years, dates, founding years, or emergence years as dataPriority" in prompt
    assert "Use dataPriority only for comparable measurements" in prompt
    assert "same semantic role" in prompt
    assert "Return only dimensions that have evidence on both sides" in prompt
    assert "Use only provided sentence IDs" in prompt
    assert "Do not invent values" in prompt
    assert "Keep valueText short and directly supported" in prompt
    assert "leftCandidates" in prompt
    assert "rightCandidates" in prompt
    assert "infoboxContext" in prompt


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


def test_build_attribute_pool_adds_rule_text_attributes_without_llm_for_concept_articles():
    article = {
        "infobox": [],
        "paragraphs": [
            {
                "id": "left-p-1",
                "text": (
                    "Artificial intelligence is intelligence exhibited by machines. "
                    "The field was founded as an academic discipline in 1956."
                ),
                "sentences": [
                    {"id": "left-s-1-1", "text": "Artificial intelligence is intelligence exhibited by machines."},
                    {"id": "left-s-1-2", "text": "The field was founded as an academic discipline in 1956."},
                ],
            },
            {
                "id": "left-p-2",
                "text": "Applications include search engines, recommendation systems, and robotics.",
                "sentences": [
                    {
                        "id": "left-s-2-1",
                        "text": "Applications include search engines, recommendation systems, and robotics.",
                    },
                ],
            },
        ],
    }

    pool = build_attribute_pool(article, "left", None)

    assert [(item["key"], item["sourceIds"]) for item in pool] == [
        ("Overview", ["left-s-1-1"]),
        ("History", ["left-s-1-2"]),
        ("Applications", ["left-s-2-1"]),
    ]


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


def test_text_attribute_timeout_caps_slow_provider_for_initial_compare():
    class SlowProviderLLM:
        config = SimpleNamespace(timeout_seconds=20)

    assert _text_attribute_timeout(SlowProviderLLM()) == 8.0


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
