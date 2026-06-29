from __future__ import annotations

import json
from typing import Any

from services.config import LLMConfig


MAX_PROMPT_PARAGRAPHS = 12


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

            self.client = OpenAI(api_key=config.api_key, base_url=config.base_url)

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
        prompt_paragraphs = [
            {
                "id": paragraph.get("id"),
                "text": paragraph.get("text"),
                "sentences": [
                    {"id": sentence.get("id"), "text": sentence.get("text")}
                    for sentence in paragraph.get("sentences", [])
                ],
            }
            for paragraph in paragraphs[:MAX_PROMPT_PARAGRAPHS]
        ]

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
                        "For the article side below, extract factual attributes from the main text. "
                        "Do not limit extraction to infobox-like concepts. Return a JSON array where "
                        "each item has key, valueText, paragraphId, sentenceIds, and confidence.\n\n"
                        f"side: {side}\n"
                        f"paragraphs: {json.dumps(prompt_paragraphs, ensure_ascii=False)}"
                    ),
                },
            ]
        )
        if not isinstance(result, list):
            raise ValueError("Expected LLM text attribute response to be a JSON list")
        return result


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
