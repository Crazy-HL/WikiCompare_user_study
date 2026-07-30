from __future__ import annotations

import json
import re
from typing import Any

from services.config import LLMConfig


MAX_PROMPT_PARAGRAPHS = 6
MAX_SENTENCES_PER_PARAGRAPH = 3
MAX_PARAGRAPH_TEXT_CHARS = 700
MAX_SENTENCE_TEXT_CHARS = 260
MAX_BODY_PROMPT_CHARS = 120_000
MAX_BODY_PARAGRAPH_TEXT_CHARS = 1_800
MAX_BODY_PARAGRAPH_SENTENCE_CHARS = 900


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
                        "Extract comparison-ready attributes from source page main text. "
                        "Use only the provided paragraph and sentence IDs. Return JSON only."
                    ),
                },
                {
                    "role": "user",
                    "content": (
                        "For the article side below, extract comparison-ready attributes from the "
                        "main text. Extract prose measurements, not just overview facts. Scan every "
                        "provided paragraph and sentence before choosing items. Prefer values with "
                        "numbers, percentages, money, sectors, trade, labor, debt, growth, "
                        "inflation, capacity, ranks, scores, and population. If one sentence "
                        "contains multiple measurable attributes, return separate items. Do not stop "
                        "after finding table-like or infobox-like attributes. Do not limit "
                        "extraction to infobox-like concepts. Do not overrepresent early paragraphs; "
                        "check whether later sections contain additional measurable attributes. "
                        "Preserve numbers, units, years, and "
                        "category labels in valueText so downstream comparison can visualize them. "
                        "Return up to 12 high-confidence items as a JSON array where each item has "
                        "key, valueText, paragraphId, sentenceIds, and confidence.\n\n"
                        f"side: {side}\n"
                        f"paragraphs: {json.dumps(prompt_paragraphs, ensure_ascii=False)}"
                    ),
                },
            ]
        )
        if not isinstance(result, list):
            raise ValueError("Expected LLM text attribute response to be a JSON list")
        return result

    def extract_text_attribute_pairs(
        self,
        *,
        left_body: dict[str, Any],
        right_body: dict[str, Any],
        infobox_context: dict[str, Any],
        left_candidates: list[dict[str, Any]] | None = None,
        right_candidates: list[dict[str, Any]] | None = None,
    ) -> dict[str, Any]:
        result = self.chat_json(
            [
                {
                    "role": "system",
                    "content": (
                        "Extract paired comparison dimensions from two full source page main text bodies. "
                        "Use only provided body text and sentence IDs. Return JSON only."
                    ),
                },
                {
                    "role": "user",
                    "content": (
                        "Find comparison-ready text attributes for the two articles.\n\n"
                        "Rules:\n"
                        "1. Do not classify the article pair before extraction.\n"
                        "2. Do not fill or follow a fixed template.\n"
                        "3. Discover comparison dimensions from the full body text, not only the candidate hints.\n"
                        "4. Scan every provided paragraph before choosing pairs; do not sample only the lead or obvious data blocks.\n"
                        "5. Do not overrepresent early paragraphs; cover early, middle, and late sections before finalizing pairs.\n"
                        "6. Prioritize chartable measurements found in ordinary prose paragraphs.\n"
                        "7. Extract measurements from prose sentences even when they are not formatted as tables or infobox rows.\n"
                        "8. Do not stop after finding table-like rows; continue looking for prose-only measurements.\n"
                        "9. If one sentence contains multiple comparable measurements, split them into separate dimensions / standard comparable rows.\n"
                        "10. Return every strongly supported comparable measurement pair you find, up to 12 pairs.\n"
                        "11. Do not mark standalone years, dates, founding years, or emergence years as dataPriority.\n"
                        "12. Use dataPriority only for comparable measurements such as money, counts, percentages, capacity, population, rank, or index scores.\n"
                        "13. The model is responsible for numeric extraction: For every chartable pair, populate both left.values and right.values with numeric values for visualization.\n"
                        "14. Do not rely on downstream code to parse numbers from valueText. If you cannot extract grounded numeric values for both sides, set dataPriority false or omit the pair.\n"
                        "15. Each values item must describe one measurement only: value is normalized as a number, label names the sub-metric when needed, unit names the measurement unit, valueKind is aggregate/component/rate/share/point, year is the measurement year when stated, and rawText is the exact numeric phrase from evidence.\n"
                        "16. When a sentence contains mixed units or dimensions, such as total subscriptions and subscriptions per 100 inhabitants, return separate dimensions or separate labeled values with matching labels on both sides; never merge incompatible units into one series.\n"
                        "17. Do not put an aggregate total and component categories in the same values array. For example, output Alcohol consumption per capita: total as one pair and Alcohol consumption per capita: beverage categories as a separate pair.\n"
                        "18. A component-category pair must contain only peer components such as beer, wine, spirits, and other alcohols; it must not include total, overall, or all.\n"
                        "19. Pair data only when both sides have the same semantic role.\n"
                        "20. Return only dimensions that have evidence on both sides.\n"
                        "21. Use only provided sentence IDs.\n"
                        "22. Do not invent values.\n"
                        "23. Keep valueText short and directly supported by the cited sentence.\n"
                        "24. Clean valueText for display, preserving numbers, units, years, and category labels.\n"
                        "25. Treat candidateHints as a coverage checklist with full-document span of likely measurable prose evidence.\n"
                        "26. For each candidateHint with a same-metric counterpart on the other side, return a pair; do not omit it merely because earlier pairs were already found.\n"
                        "27. Use candidateHints as hints, not a limit; search the full bodies for better comparable attributes too.\n\n"
                        "Return this JSON shape only:\n"
                        '{"pairs":[{"dimensionLabel":string,"comparisonQuestion":string,'
                        '"left":{"valueText":string,"sentenceIds":[string],'
                        '"values":[{"value":number,"label":string|null,"unit":string|null,"valueKind":"aggregate|component|rate|share|point"|null,"year":number|null,"rawText":string,"confidence":number}]},'
                        '"right":{"valueText":string,"sentenceIds":[string],'
                        '"values":[{"value":number,"label":string|null,"unit":string|null,"valueKind":"aggregate|component|rate|share|point"|null,"year":number|null,"rawText":string,"confidence":number}]},'
                        '"dataPriority":boolean,"dataRole":string|null,"confidence":number}]}\n\n'
                        f"infoboxContext: {json.dumps(infobox_context, ensure_ascii=False)}\n"
                        f"leftBody: {json.dumps(left_body, ensure_ascii=False)}\n"
                        f"rightBody: {json.dumps(right_body, ensure_ascii=False)}\n"
                        f"candidateHints: {json.dumps({'left': left_candidates or [], 'right': right_candidates or []}, ensure_ascii=False)}"
                    ),
                },
            ]
        )
        if not isinstance(result, dict) or not isinstance(result.get("pairs"), list):
            raise ValueError("Expected paired text attribute response to contain a pairs list")
        return result

    def review_text_attribute_pairs(
        self,
        *,
        left_body: dict[str, Any],
        right_body: dict[str, Any],
        pair_response: dict[str, Any],
        infobox_context: dict[str, Any],
    ) -> dict[str, Any]:
        result = self.chat_json(
            [
                {
                    "role": "system",
                    "content": (
                        "You are a strict comparison-data reviewer. Review model-extracted paired "
                        "attributes against the provided source text. Return JSON only."
                    ),
                },
                {
                    "role": "user",
                    "content": (
                        "Review the extracted comparison pairs below before they are visualized.\n\n"
                        "Your job is quality control, not adding loose comparisons.\n\n"
                        "Reject or fix any pair where:\n"
                        "1. The left and right values are not the same metric.\n"
                        "2. The units or denominators differ, such as total subscriptions vs subscriptions per 100 inhabitants.\n"
                        "3. A total, rate, share, rank, percentage, capacity, money amount, or count is compared with a different kind of measurement.\n"
                        "4. The label is broader than the actual measured sub-metric.\n"
                        "5. A values item is not directly supported by its cited sentence rawText.\n"
                        "6. One side contains multiple measurements and the selected value does not match the other side's selected value.\n"
                        "7. The pair would make a misleading chart.\n"
                        "8. It puts an aggregate total and component categories in one values array.\n\n"
                        "Rules for output:\n"
                        "1. Return only pairs that are logically comparable and chart-safe.\n"
                        "2. If a candidate contains mixed metrics, split it into standard comparable rows only when both sides contain matching evidence.\n"
                        "3. Split aggregate totals from component categories. For example, keep Alcohol consumption per capita: total separate from Alcohol consumption per capita: beverage categories, and never include total inside the beverage categories values.\n"
                        "4. Preserve only provided sentence IDs.\n"
                        "5. Keep dataPriority true only when both sides have validated numeric values.\n"
                        "6. Do not invent values or evidence.\n"
                        "7. Prefer fewer high-quality pairs over many weak pairs.\n\n"
                        "Return this JSON shape only:\n"
                        '{"pairs":[{"dimensionLabel":string,"comparisonQuestion":string,'
                        '"left":{"valueText":string,"sentenceIds":[string],'
                        '"values":[{"value":number,"label":string|null,"unit":string|null,"valueKind":"aggregate|component|rate|share|point"|null,"year":number|null,"rawText":string,"confidence":number}]},'
                        '"right":{"valueText":string,"sentenceIds":[string],'
                        '"values":[{"value":number,"label":string|null,"unit":string|null,"valueKind":"aggregate|component|rate|share|point"|null,"year":number|null,"rawText":string,"confidence":number}]},'
                        '"dataPriority":boolean,"dataRole":string|null,"confidence":number}]}\n\n'
                        f"infoboxContext: {json.dumps(infobox_context, ensure_ascii=False)}\n"
                        f"leftBody: {json.dumps(left_body, ensure_ascii=False)}\n"
                        f"rightBody: {json.dumps(right_body, ensure_ascii=False)}\n"
                        f"candidatePairs: {json.dumps(pair_response, ensure_ascii=False)}"
                    ),
                },
            ]
        )
        if not isinstance(result, dict) or not isinstance(result.get("pairs"), list):
            raise ValueError("Expected reviewed paired text attribute response to contain a pairs list")
        return result

    def refine_extracted_values(
        self,
        *,
        key: str,
        value_text: str,
        rule_values: list[dict[str, Any]],
        data_type: str,
    ) -> list[dict[str, Any]]:
        result = self.chat_json(
            [
                {
                    "role": "system",
                    "content": (
                        "You correct rule-extracted comparable values from source page attributes. "
                        "Use only the provided valueText and ruleValues. Return JSON only."
                    ),
                },
                {
                    "role": "user",
                    "content": (
                        "Review the rule extraction below and return corrected comparable values.\n\n"
                        "Goals:\n"
                        "1. Preserve or add labels that define comparable dimensions, such as nominal, PPP, "
                        "exports, imports, revenues, expenditures, male, female, agriculture, industry, "
                        "services, lowest 10%, highest 10%, countries, sectors, or categories.\n"
                        "2. Remove numbers that are part of labels or context rather than values, such as the "
                        "10% in 'lowest 10%'.\n"
                        "3. Keep the numeric value field on the same scale as ruleValues when correcting an "
                        "existing item. Do not convert units.\n"
                        "4. Do not invent values. If unsure, return ruleValues unchanged.\n"
                        "5. Keep original order.\n"
                        "6. rawText must be the exact source fragment supporting the item.\n\n"
                        "Return this JSON object shape only:\n"
                        '{"items":[{"value":number,"label":string|null,"year":number|null,'
                        '"rawText":string,"confidence":number}]}\n\n'
                        f"attributeKey: {key}\n"
                        f"dataType: {data_type}\n"
                        f"valueText: {value_text}\n"
                        f"ruleValues: {json.dumps(rule_values, ensure_ascii=False)}"
                    ),
                },
            ]
        )
        items = result.get("items") if isinstance(result, dict) else result
        if not isinstance(items, list):
            raise ValueError("Expected LLM value refinement response to contain an items list")
        return items


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


def prompt_article_body(article: dict[str, Any], side: str) -> dict[str, Any]:
    source_paragraphs = [
        paragraph
        for paragraph in article.get("paragraphs", []) or []
        if isinstance(paragraph, dict)
    ]
    paragraphs = []
    for paragraph in source_paragraphs:
        prompt_paragraph = _prompt_body_paragraph(paragraph, MAX_BODY_PROMPT_CHARS)
        if prompt_paragraph is not None:
            paragraphs.append(prompt_paragraph)
    limited_paragraphs = _limit_body_paragraphs_with_document_coverage(
        paragraphs,
        MAX_BODY_PROMPT_CHARS,
    )
    return {
        "side": side,
        "title": article.get("title"),
        "paragraphs": limited_paragraphs,
        "truncated": len(limited_paragraphs) < len(paragraphs),
    }


def _limit_body_paragraphs_with_document_coverage(
    paragraphs: list[dict[str, Any]],
    char_budget: int,
) -> list[dict[str, Any]]:
    if char_budget <= 0 or not paragraphs:
        return []
    if _prompt_body_total_size(paragraphs) <= char_budget:
        return paragraphs

    sizes = [max(1, _prompt_body_size(paragraph)) for paragraph in paragraphs]
    average_size = max(1, sum(sizes) // len(sizes))
    target_count = max(1, min(len(paragraphs), char_budget // average_size))
    while target_count > 0:
        indices = _coverage_indices(len(paragraphs), target_count)
        selected = [paragraphs[index] for index in indices]
        if _prompt_body_total_size(selected) <= char_budget:
            return selected
        target_count -= 1
    return []


def _coverage_indices(total_count: int, limit: int) -> list[int]:
    if total_count <= 0 or limit <= 0:
        return []
    if total_count <= limit:
        return list(range(total_count))
    if limit == 1:
        return [0]

    last_index = total_count - 1
    selected = {
        round(position * last_index / (limit - 1))
        for position in range(limit)
    }
    cursor = 0
    while len(selected) < limit and cursor <= last_index:
        selected.add(cursor)
        cursor += 1
    return sorted(selected)[:limit]


def _prompt_body_total_size(paragraphs: list[dict[str, Any]]) -> int:
    return sum(_prompt_body_size(paragraph) for paragraph in paragraphs)


def _prompt_body_paragraph(paragraph: dict[str, Any], char_budget: int) -> dict[str, Any] | None:
    paragraph_id = paragraph.get("id")
    text = _clean_prompt_text(paragraph.get("text"))
    if not text or char_budget <= 0:
        return None
    text = _truncate_text(text, min(len(text), char_budget, MAX_BODY_PARAGRAPH_TEXT_CHARS))
    sentence_budget = max(
        min(char_budget - len(text), MAX_BODY_PARAGRAPH_SENTENCE_CHARS),
        0,
    )
    sentences = []
    for sentence in paragraph.get("sentences", []) or []:
        if not isinstance(sentence, dict):
            continue
        sentence_id = sentence.get("id")
        sentence_text = _clean_prompt_text(sentence.get("text"))
        if not sentence_id or not sentence_text:
            continue
        if sentence_budget <= 0:
            break
        sentence_text = _truncate_text(sentence_text, min(len(sentence_text), sentence_budget))
        sentences.append({"id": sentence_id, "text": sentence_text})
        sentence_budget -= len(sentence_text)
    return {
        "id": paragraph_id,
        "text": text,
        "sentences": sentences,
    }


def _prompt_body_size(paragraph: dict[str, Any]) -> int:
    return len(str(paragraph.get("text") or "")) + sum(
        len(str(sentence.get("text") or ""))
        for sentence in paragraph.get("sentences", []) or []
        if isinstance(sentence, dict)
    )


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
    text = _clean_prompt_text(value)
    if len(text) <= limit:
        return text
    if limit <= 1:
        return text[:limit]
    return text[: limit - 1].rstrip() + "…"


def _clean_prompt_text(value: Any) -> str:
    return " ".join(str(value or "").split())


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
