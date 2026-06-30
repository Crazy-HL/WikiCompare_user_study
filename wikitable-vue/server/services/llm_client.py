from __future__ import annotations

import json
import re
from typing import Any

from services.config import LLMConfig


MAX_PROMPT_PARAGRAPHS = 6
MAX_SENTENCES_PER_PARAGRAPH = 3
MAX_PARAGRAPH_TEXT_CHARS = 700
MAX_SENTENCE_TEXT_CHARS = 260


def extract_json(text: str) -> Any:
    cleaned = _strip_markdown_fence(text.strip())
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        pass

    decoder = json.JSONDecoder()
    for index, char in enumerate(cleaned):
        if char not in "[{":
            continue
        try:
            value, _ = decoder.raw_decode(cleaned[index:])
            return value
        except json.JSONDecodeError:
            continue
    raise ValueError("No JSON object or array found in LLM response")


class LLMClient:
    def __init__(self, config: LLMConfig):
        self.config = config
        self.client = None
        if config.enabled:
            from openai import OpenAI

            self.client = OpenAI(
                api_key=config.api_key,
                base_url=config.base_url,
                timeout=config.timeout_seconds,
                max_retries=0,
            )

    def chat_json(self, messages: list[dict[str, str]]) -> Any:
        if self.client is None:
            raise RuntimeError("LLM client is disabled")

        response = self.client.chat.completions.create(
            model=self.config.model,
            messages=messages,
            temperature=0.2,
        )
        content = response.choices[0].message.content
        return extract_json(content or "")

    def extract_text_attributes(self, side: str, paragraphs: list[dict[str, Any]]) -> list[dict[str, Any]]:
        prompt_paragraphs = _prompt_paragraphs(paragraphs)

        result = self.chat_json(
            [
                {
                    "role": "system",
                    "content": (
                        "Extract comparison-ready attributes from Wikipedia article main text. "
                        "Use only the provided paragraph and sentence IDs. Return JSON only."
                    ),
                },
                {
                    "role": "user",
                    "content": (
                        "For the article side below, extract up to 8 factual attributes from the "
                        "main text. Prefer values with numbers, percentages, money, dates, sectors, "
                        "trade, labor, debt, growth, inflation, and population. Do not limit "
                        "extraction to infobox-like concepts. Return a JSON array where each item "
                        "has key, valueText, paragraphId, sentenceIds, and confidence.\n\n"
                        f"side: {side}\n"
                        f"paragraphs: {json.dumps(prompt_paragraphs, ensure_ascii=False)}"
                    ),
                },
            ]
        )
        if not isinstance(result, list):
            raise ValueError("Expected LLM text attribute response to be a JSON list")
        return result


def _prompt_paragraphs(paragraphs: list[dict[str, Any]]) -> list[dict[str, Any]]:
    candidates = sorted(
        [
            (paragraph, _paragraph_score(paragraph), index)
            for index, paragraph in enumerate(paragraphs)
            if isinstance(paragraph, dict)
        ],
        key=lambda item: (-item[1], item[2]),
    )
    selected = [item[0] for item in candidates[:MAX_PROMPT_PARAGRAPHS]]
    return [
        {
            "id": paragraph.get("id"),
            "text": _truncate_text(paragraph.get("text"), MAX_PARAGRAPH_TEXT_CHARS),
            "sentences": [
                {
                    "id": sentence.get("id"),
                    "text": _truncate_text(sentence.get("text"), MAX_SENTENCE_TEXT_CHARS),
                }
                for sentence in paragraph.get("sentences", [])[:MAX_SENTENCES_PER_PARAGRAPH]
            ],
        }
        for paragraph in selected
    ]


def _paragraph_score(paragraph: dict[str, Any]) -> int:
    text = str(paragraph.get("text") or "")
    score = 0
    if re.search(r"\d", text):
        score += 4
    if re.search(r"%|GDP|growth|inflation|debt|trade|export|import|labor|unemployment|population|sector", text, re.I):
        score += 3
    if re.search(r"\$|€|¥|₩|billion|million|trillion", text, re.I):
        score += 2
    return score


def _truncate_text(value: Any, limit: int) -> str:
    text = " ".join(str(value or "").split())
    if len(text) <= limit:
        return text
    return text[: limit - 1].rstrip() + "…"


def _strip_markdown_fence(text: str) -> str:
    if not text.startswith("```"):
        return text

    lines = text.splitlines()
    if not lines:
        return text
    if not lines[0].startswith("```"):
        return text
    if len(lines) > 1 and lines[-1].strip() == "```":
        return "\n".join(lines[1:-1]).strip()
    return "\n".join(lines[1:]).strip()
