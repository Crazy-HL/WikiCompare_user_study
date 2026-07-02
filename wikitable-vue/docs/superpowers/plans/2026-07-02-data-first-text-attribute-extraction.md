# Data-First Text Attribute Extraction Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a data-first, pair-first, template-free main-text extraction pipeline that finds comparison-ready body-text attributes before the three-column table is rendered.

**Architecture:** Add a focused backend service for text comparison evidence, keeping sentence candidate generation, LLM pair extraction, validation, and attribute conversion separate from the existing normalization logic. The server will still build infobox pools first, then add paired text rows and direct alignments before falling back to existing key/semantic alignment.

**Tech Stack:** Python 3.9, Tornado backend, existing `LLMClient`, pytest, Vue client consuming existing compare-session payloads.

---

## File Structure

- Create `server/services/text_attribute_pairs.py`
  - Owns sentence metadata, data candidate detection, fallback claim candidates, pair validation, duplicate filtering, and conversion into left/right attributes plus alignments.
- Modify `server/services/llm_client.py`
  - Adds `extract_text_attribute_pairs(left_candidates, right_candidates, infobox_context)` with a pair-level prompt.
- Modify `server/server.py`
  - Calls the pair-level text extraction after infobox pool creation and before general alignment.
  - Combines direct paired-text alignments with existing `align_attribute_pools`.
- Modify `server/services/pipeline.py`
  - Adjusts ranking so paired text rows with comparable data can rank before generic text fallback rows.
- Modify `server/tests/test_text_attribute_pairs.py`
  - Unit tests for candidate detection, validation, duplicate behavior, and attribute conversion.
- Modify `server/tests/test_llm_client.py` or `server/tests/test_attribute_pool.py`
  - Tests prompt contract and JSON validation for the pair-level method.
- Modify `server/tests/test_compare_api.py`
  - API-level regression tests for concept pairs, data-first ordering, and invalid model output.

## Task 1: Add Data Candidate Detection

**Files:**
- Create: `server/services/text_attribute_pairs.py`
- Test: `server/tests/test_text_attribute_pairs.py`

- [ ] **Step 1: Write the failing tests**

Add this file:

```python
from services.text_attribute_pairs import build_text_evidence_candidates


def test_build_text_evidence_candidates_marks_data_roles():
    article = {
        "paragraphs": [
            {
                "id": "left-p-1",
                "section": "History",
                "sentences": [
                    {
                        "id": "left-s-1-1",
                        "text": "The field was founded as an academic discipline in 1956.",
                    },
                    {
                        "id": "left-s-1-2",
                        "text": "Applications include search engines and robotics.",
                    },
                ],
            }
        ]
    }

    candidates = build_text_evidence_candidates(article, "left")

    assert candidates[0]["side"] == "left"
    assert candidates[0]["sentenceIds"] == ["left-s-1-1"]
    assert candidates[0]["kind"] == "data"
    assert candidates[0]["dataItems"][0]["role"] == "emergence_time"
    assert candidates[0]["dataItems"][0]["value"] == 1956
    assert candidates[1]["kind"] == "claim"
    assert candidates[1]["semanticCue"] == "applications"


def test_build_text_evidence_candidates_ignores_noise_years():
    article = {
        "paragraphs": [
            {
                "id": "left-p-1",
                "sentences": [
                    {"id": "left-s-1-1", "text": "Smith published a paper in 2019."},
                    {"id": "left-s-1-2", "text": "The model reached 95% accuracy."},
                ],
            }
        ]
    }

    candidates = build_text_evidence_candidates(article, "left")

    assert [candidate["sentenceIds"] for candidate in candidates] == [["left-s-1-2"]]
    assert candidates[0]["dataItems"][0]["role"] == "proportion"
```

- [ ] **Step 2: Run tests to verify they fail**

Run:

```bash
python3 -m pytest server/tests/test_text_attribute_pairs.py -q
```

Expected: FAIL with `ModuleNotFoundError: No module named 'services.text_attribute_pairs'`.

- [ ] **Step 3: Implement minimal candidate generation**

Create `server/services/text_attribute_pairs.py`:

```python
from __future__ import annotations

import re
from typing import Any


NUMBER_RE = re.compile(r"([-+]?\d+(?:\.\d+)?)\s*(%|percent|million|billion|trillion)?", re.I)
MONEY_RE = re.compile(r"[$€£¥₩]\s*[-+]?\d+(?:\.\d+)?", re.I)
ORDINAL_RE = re.compile(r"\b\d+(?:st|nd|rd|th)\b", re.I)
DATA_CONTEXT_RE = re.compile(
    r"\b(founded|introduced|launched|released|created|developed|grew|emerged|"
    r"accuracy|rate|share|percent|rank|score|revenue|population|users|models|cases|"
    r"growth|decline|increase|decrease|duration)\b",
    re.I,
)
CLAIM_CUE_RE = re.compile(
    r"\b(is|are|refers to|used|uses|include|includes|applications|methods|"
    r"techniques|consists|types|risks|limitations|impact|effects)\b",
    re.I,
)
PUBLICATION_NOISE_RE = re.compile(r"\b(published|paper|study|article|journal|conference)\b", re.I)


def build_text_evidence_candidates(article: dict[str, Any], side: str, limit: int = 24) -> list[dict[str, Any]]:
    candidates: list[dict[str, Any]] = []
    for paragraph in article.get("paragraphs", []) or []:
        if not isinstance(paragraph, dict):
            continue
        for sentence in paragraph.get("sentences", []) or []:
            candidate = _sentence_candidate(sentence, paragraph, side)
            if candidate is not None:
                candidates.append(candidate)
            if len(candidates) >= limit:
                return candidates
    return candidates


def _sentence_candidate(sentence: Any, paragraph: dict[str, Any], side: str) -> dict[str, Any] | None:
    if not isinstance(sentence, dict):
        return None
    sentence_id = sentence.get("id")
    text = _clean_text(sentence.get("text"))
    if not isinstance(sentence_id, str) or not sentence_id or not text:
        return None
    data_items = _data_items(text)
    if data_items:
        return {
            "side": side,
            "kind": "data",
            "claimText": text,
            "sentenceIds": [sentence_id],
            "paragraphId": paragraph.get("id"),
            "section": paragraph.get("section"),
            "semanticCue": _semantic_cue(text),
            "dataItems": data_items,
        }
    if CLAIM_CUE_RE.search(text):
        return {
            "side": side,
            "kind": "claim",
            "claimText": text,
            "sentenceIds": [sentence_id],
            "paragraphId": paragraph.get("id"),
            "section": paragraph.get("section"),
            "semanticCue": _semantic_cue(text),
            "dataItems": [],
        }
    return None


def _data_items(text: str) -> list[dict[str, Any]]:
    if not DATA_CONTEXT_RE.search(text) and not MONEY_RE.search(text) and not ORDINAL_RE.search(text):
        return []
    if PUBLICATION_NOISE_RE.search(text) and not re.search(r"%|accuracy|score|rank", text, re.I):
        return []
    items: list[dict[str, Any]] = []
    for match in NUMBER_RE.finditer(text):
        raw = match.group(1)
        unit = (match.group(2) or "").lower()
        try:
            value = float(raw)
        except ValueError:
            continue
        role = _data_role(text, unit)
        if role == "context_year" and PUBLICATION_NOISE_RE.search(text):
            continue
        item: dict[str, Any] = {"value": int(value) if value.is_integer() else value, "role": role}
        if unit:
            item["unit"] = unit
        items.append(item)
    return items


def _data_role(text: str, unit: str) -> str:
    lower = text.lower()
    if unit in {"%", "percent"} or "accuracy" in lower or "share" in lower or "rate" in lower:
        return "proportion"
    if re.search(r"\b(founded|introduced|launched|released|created|developed|grew|emerged)\b", lower):
        return "emergence_time"
    if "rank" in lower or ORDINAL_RE.search(text):
        return "ranking"
    if MONEY_RE.search(text) or unit in {"million", "billion", "trillion"}:
        return "scale"
    return "quantity"


def _semantic_cue(text: str) -> str:
    lower = text.lower()
    for label, pattern in [
        ("applications", r"\b(application|applications|used|uses|include|includes)\b"),
        ("methods", r"\b(method|methods|technique|techniques|algorithm|model)\b"),
        ("limitations", r"\b(risk|risks|limitation|limitations|criticism)\b"),
        ("definition", r"\b(is|are|refers to)\b"),
        ("history", r"\b(founded|introduced|launched|developed|grew|emerged)\b"),
    ]:
        if re.search(pattern, lower):
            return label
    return ""


def _clean_text(value: Any) -> str:
    return " ".join(str(value or "").split())
```

- [ ] **Step 4: Run tests to verify they pass**

Run:

```bash
python3 -m pytest server/tests/test_text_attribute_pairs.py -q
```

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add server/services/text_attribute_pairs.py server/tests/test_text_attribute_pairs.py
git commit -m "feat: detect text evidence candidates"
```

## Task 2: Add Pair Validation And Attribute Conversion

**Files:**
- Modify: `server/services/text_attribute_pairs.py`
- Modify: `server/tests/test_text_attribute_pairs.py`

- [ ] **Step 1: Write the failing tests**

Append:

```python
from services.text_attribute_pairs import build_paired_text_attributes


def test_build_paired_text_attributes_rejects_invalid_sentence_ids():
    left_article = {
        "paragraphs": [
            {
                "id": "left-p-1",
                "sentences": [{"id": "left-s-1-1", "text": "AI was founded in 1956."}],
            }
        ]
    }
    right_article = {
        "paragraphs": [
            {
                "id": "right-p-1",
                "sentences": [{"id": "right-s-1-1", "text": "ML emerged in the 1950s."}],
            }
        ]
    }
    pair_response = {
        "pairs": [
            {
                "dimensionLabel": "Historical emergence",
                "comparisonQuestion": "When did it emerge?",
                "left": {"valueText": "founded in 1956", "sentenceIds": ["left-s-missing"]},
                "right": {"valueText": "emerged in the 1950s", "sentenceIds": ["right-s-1-1"]},
                "dataPriority": True,
                "dataRole": "emergence_time",
                "confidence": 0.9,
            }
        ]
    }

    left_attrs, right_attrs, alignments = build_paired_text_attributes(
        left_article,
        right_article,
        pair_response,
        [],
        [],
    )

    assert left_attrs == []
    assert right_attrs == []
    assert alignments == []


def test_build_paired_text_attributes_creates_aligned_attributes():
    left_article = {
        "paragraphs": [
            {
                "id": "left-p-1",
                "sentences": [{"id": "left-s-1-1", "text": "AI was founded in 1956."}],
            }
        ]
    }
    right_article = {
        "paragraphs": [
            {
                "id": "right-p-1",
                "sentences": [{"id": "right-s-1-1", "text": "ML emerged in the 1950s."}],
            }
        ]
    }
    pair_response = {
        "pairs": [
            {
                "dimensionLabel": "Historical emergence",
                "comparisonQuestion": "When did it emerge?",
                "left": {"valueText": "founded in 1956", "sentenceIds": ["left-s-1-1"]},
                "right": {"valueText": "emerged in the 1950s", "sentenceIds": ["right-s-1-1"]},
                "dataPriority": True,
                "dataRole": "emergence_time",
                "confidence": 0.9,
            }
        ]
    }

    left_attrs, right_attrs, alignments = build_paired_text_attributes(
        left_article,
        right_article,
        pair_response,
        [],
        [],
    )

    assert left_attrs[0]["key"] == "Historical emergence"
    assert left_attrs[0]["source"] == "main_text"
    assert left_attrs[0]["sourceIds"] == ["left-s-1-1"]
    assert left_attrs[0]["dataPriority"] is True
    assert right_attrs[0]["sourceIds"] == ["right-s-1-1"]
    assert alignments == [
        {
            "left": left_attrs[0],
            "right": right_attrs[0],
            "label": "Historical emergence",
        }
    ]
```

- [ ] **Step 2: Run tests to verify they fail**

Run:

```bash
python3 -m pytest server/tests/test_text_attribute_pairs.py -q
```

Expected: FAIL with `ImportError` or missing `build_paired_text_attributes`.

- [ ] **Step 3: Implement validation and conversion**

Add to `server/services/text_attribute_pairs.py`:

```python
MIN_PAIR_CONFIDENCE = 0.55


def build_paired_text_attributes(
    left_article: dict[str, Any],
    right_article: dict[str, Any],
    pair_response: Any,
    left_infobox_pool: list[dict[str, Any]],
    right_infobox_pool: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    pairs = pair_response.get("pairs") if isinstance(pair_response, dict) else pair_response
    if not isinstance(pairs, list):
        return [], [], []
    left_sources = _source_lookup(left_article)
    right_sources = _source_lookup(right_article)
    left_attrs: list[dict[str, Any]] = []
    right_attrs: list[dict[str, Any]] = []
    alignments: list[dict[str, Any]] = []
    seen_labels: set[str] = set()
    for raw_pair in pairs:
        clean_pair = _validated_pair(raw_pair, left_sources, right_sources)
        if clean_pair is None:
            continue
        label_key = clean_pair["dimensionLabel"].lower()
        if label_key in seen_labels:
            continue
        if _duplicates_infobox(clean_pair, left_infobox_pool, right_infobox_pool):
            continue
        seen_labels.add(label_key)
        index = len(left_attrs) + 1
        left_attr = _attribute_from_pair_side(clean_pair, "left", index, left_sources)
        right_attr = _attribute_from_pair_side(clean_pair, "right", index, right_sources)
        left_attrs.append(left_attr)
        right_attrs.append(right_attr)
        alignments.append({"left": left_attr, "right": right_attr, "label": clean_pair["dimensionLabel"]})
    return left_attrs, right_attrs, alignments


def _validated_pair(
    raw_pair: Any,
    left_sources: dict[str, dict[str, Any]],
    right_sources: dict[str, dict[str, Any]],
) -> dict[str, Any] | None:
    if not isinstance(raw_pair, dict):
        return None
    label = _clean_text(raw_pair.get("dimensionLabel"))
    question = _clean_text(raw_pair.get("comparisonQuestion"))
    confidence = _confidence(raw_pair.get("confidence"))
    if not label or confidence < MIN_PAIR_CONFIDENCE:
        return None
    left = _validated_pair_side(raw_pair.get("left"), left_sources)
    right = _validated_pair_side(raw_pair.get("right"), right_sources)
    if left is None or right is None:
        return None
    data_priority = bool(raw_pair.get("dataPriority"))
    data_role = _clean_text(raw_pair.get("dataRole"))
    if data_priority and not data_role:
        return None
    return {
        "dimensionLabel": label,
        "comparisonQuestion": question,
        "left": left,
        "right": right,
        "dataPriority": data_priority,
        "dataRole": data_role,
        "confidence": confidence,
    }


def _validated_pair_side(raw_side: Any, sources: dict[str, dict[str, Any]]) -> dict[str, Any] | None:
    if not isinstance(raw_side, dict):
        return None
    value_text = _clean_text(raw_side.get("valueText"))
    sentence_ids = raw_side.get("sentenceIds")
    if not value_text or not isinstance(sentence_ids, list) or not sentence_ids:
        return None
    clean_ids = []
    for sentence_id in sentence_ids:
        if not isinstance(sentence_id, str) or sentence_id not in sources:
            return None
        clean_ids.append(sentence_id)
    return {"valueText": value_text, "sentenceIds": clean_ids}


def _attribute_from_pair_side(
    pair: dict[str, Any],
    side: str,
    index: int,
    sources: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    side_pair = pair[side]
    first_source = sources[side_pair["sentenceIds"][0]]
    attribute = {
        "id": f"{side}-attr-paired-text-{index}",
        "side": side,
        "key": pair["dimensionLabel"],
        "valueText": side_pair["valueText"],
        "source": "main_text",
        "sourceIds": side_pair["sentenceIds"],
        "paragraphId": first_source.get("paragraphId"),
        "confidence": pair["confidence"],
        "dataPriority": pair["dataPriority"],
        "comparisonQuestion": pair["comparisonQuestion"],
    }
    if pair["dataRole"]:
        attribute["dataRole"] = pair["dataRole"]
    return attribute


def _source_lookup(article: dict[str, Any]) -> dict[str, dict[str, Any]]:
    lookup: dict[str, dict[str, Any]] = {}
    for paragraph in article.get("paragraphs", []) or []:
        if not isinstance(paragraph, dict):
            continue
        paragraph_id = paragraph.get("id")
        for sentence in paragraph.get("sentences", []) or []:
            if not isinstance(sentence, dict):
                continue
            sentence_id = sentence.get("id")
            if isinstance(sentence_id, str) and sentence_id:
                lookup[sentence_id] = {"paragraphId": paragraph_id, "text": sentence.get("text")}
    return lookup


def _confidence(value: Any) -> float:
    try:
        parsed = float(value)
    except (TypeError, ValueError):
        return 0.0
    return max(0.0, min(parsed, 1.0))


def _duplicates_infobox(
    pair: dict[str, Any],
    left_infobox_pool: list[dict[str, Any]],
    right_infobox_pool: list[dict[str, Any]],
) -> bool:
    label = pair["dimensionLabel"].lower()
    left_keys = {_clean_text(item.get("key")).lower() for item in left_infobox_pool}
    right_keys = {_clean_text(item.get("key")).lower() for item in right_infobox_pool}
    return label in left_keys and label in right_keys
```

- [ ] **Step 4: Run tests to verify they pass**

Run:

```bash
python3 -m pytest server/tests/test_text_attribute_pairs.py -q
```

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add server/services/text_attribute_pairs.py server/tests/test_text_attribute_pairs.py
git commit -m "feat: validate paired text attributes"
```

## Task 3: Add Pair-Level LLM Method

**Files:**
- Modify: `server/services/llm_client.py`
- Modify: `server/tests/test_attribute_pool.py`

- [ ] **Step 1: Write the failing test**

Append to `server/tests/test_attribute_pool.py`:

```python
def test_llm_client_extracts_paired_text_attributes_with_data_first_prompt():
    client = LLMClient(LLMConfig(model="test", base_url="http://example.test", api_key=None))

    captured = {}

    def fake_chat_json(messages):
        captured["messages"] = messages
        return {
            "pairs": [
                {
                    "dimensionLabel": "Historical emergence",
                    "comparisonQuestion": "When did it emerge?",
                    "left": {"valueText": "founded in 1956", "sentenceIds": ["left-s-1-1"]},
                    "right": {"valueText": "emerged in the 1950s", "sentenceIds": ["right-s-1-1"]},
                    "dataPriority": True,
                    "dataRole": "emergence_time",
                    "confidence": 0.9,
                }
            ]
        }

    client.chat_json = fake_chat_json

    result = client.extract_text_attribute_pairs(
        left_candidates=[{"claimText": "AI was founded in 1956.", "sentenceIds": ["left-s-1-1"]}],
        right_candidates=[{"claimText": "ML emerged in the 1950s.", "sentenceIds": ["right-s-1-1"]}],
        infobox_context={"left": [], "right": []},
    )

    prompt = captured["messages"][-1]["content"]
    assert result["pairs"][0]["dimensionLabel"] == "Historical emergence"
    assert "Do not classify the article pair" in prompt
    assert "Prioritize data-bearing evidence" in prompt
    assert "same semantic role" in prompt
```

- [ ] **Step 2: Run test to verify it fails**

Run:

```bash
python3 -m pytest server/tests/test_attribute_pool.py::test_llm_client_extracts_paired_text_attributes_with_data_first_prompt -q
```

Expected: FAIL with missing `extract_text_attribute_pairs`.

- [ ] **Step 3: Implement the LLM method**

Add to `LLMClient` in `server/services/llm_client.py`:

```python
    def extract_text_attribute_pairs(
        self,
        *,
        left_candidates: list[dict[str, Any]],
        right_candidates: list[dict[str, Any]],
        infobox_context: dict[str, Any],
    ) -> dict[str, Any]:
        result = self.chat_json(
            [
                {
                    "role": "system",
                    "content": (
                        "Extract paired comparison dimensions from two article bodies. "
                        "Use only provided candidate evidence and sentence IDs. Return JSON only."
                    ),
                },
                {
                    "role": "user",
                    "content": (
                        "Find comparison-ready text attributes for the two articles.\n\n"
                        "Rules:\n"
                        "1. Do not classify the article pair before extraction.\n"
                        "2. Do not fill a fixed template.\n"
                        "3. Discover comparison dimensions from the evidence.\n"
                        "4. Prioritize data-bearing evidence, but only pair data when both sides have the same semantic role.\n"
                        "5. Return only dimensions that have evidence on both sides.\n"
                        "6. Use only provided sentence IDs.\n"
                        "7. Do not invent values.\n"
                        "8. Keep valueText short and directly supported by the cited sentence.\n\n"
                        "Return this JSON shape only:\n"
                        '{"pairs":[{"dimensionLabel":string,"comparisonQuestion":string,'
                        '"left":{"valueText":string,"sentenceIds":[string]},'
                        '"right":{"valueText":string,"sentenceIds":[string]},'
                        '"dataPriority":boolean,"dataRole":string|null,"confidence":number}]}\n\n'
                        f"infoboxContext: {json.dumps(infobox_context, ensure_ascii=False)}\n"
                        f"leftCandidates: {json.dumps(left_candidates, ensure_ascii=False)}\n"
                        f"rightCandidates: {json.dumps(right_candidates, ensure_ascii=False)}"
                    ),
                },
            ]
        )
        if not isinstance(result, dict) or not isinstance(result.get("pairs"), list):
            raise ValueError("Expected paired text attribute response to contain a pairs list")
        return result
```

- [ ] **Step 4: Run test to verify it passes**

Run:

```bash
python3 -m pytest server/tests/test_attribute_pool.py::test_llm_client_extracts_paired_text_attributes_with_data_first_prompt -q
```

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add server/services/llm_client.py server/tests/test_attribute_pool.py
git commit -m "feat: add pair-level text extraction prompt"
```

## Task 4: Integrate Paired Text Rows Into Compare Session

**Files:**
- Modify: `server/server.py`
- Modify: `server/tests/test_compare_api.py`

- [ ] **Step 1: Write the failing API test**

Append to `CompareApiTest`:

```python
    def test_compare_session_uses_paired_text_attributes_from_llm(self):
        left_html = """
        <html><body><main>
          <p>Artificial intelligence was founded as an academic discipline in 1956.</p>
          <p>Applications include search engines and robotics.</p>
        </main></body></html>
        """
        right_html = """
        <html><body><main>
          <p>Machine learning grew from pattern recognition in the 1950s.</p>
          <p>Uses include computer vision and speech recognition.</p>
        </main></body></html>
        """

        class PairLLMClient:
            def __init__(self, _config):
                pass

            def extract_text_attributes(self, _side, _paragraphs):
                return []

            def extract_text_attribute_pairs(self, **_kwargs):
                return {
                    "pairs": [
                        {
                            "dimensionLabel": "Historical emergence",
                            "comparisonQuestion": "When did it emerge?",
                            "left": {"valueText": "founded as an academic discipline in 1956", "sentenceIds": ["left-s-1-1"]},
                            "right": {"valueText": "grew from pattern recognition in the 1950s", "sentenceIds": ["right-s-1-1"]},
                            "dataPriority": True,
                            "dataRole": "emergence_time",
                            "confidence": 0.9,
                        },
                        {
                            "dimensionLabel": "Applications",
                            "comparisonQuestion": "What is it used for?",
                            "left": {"valueText": "search engines and robotics", "sentenceIds": ["left-s-2-1"]},
                            "right": {"valueText": "computer vision and speech recognition", "sentenceIds": ["right-s-2-1"]},
                            "dataPriority": False,
                            "dataRole": None,
                            "confidence": 0.84,
                        },
                    ]
                }

            def refine_extracted_values(self, **_kwargs):
                return []

        server.SESSION_STORE.clear()
        server.ARTICLE_HTML_CACHE.clear()
        with patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"}, clear=False), patch.object(
            server,
            "LLMClient",
            PairLLMClient,
        ), patch.object(
            server,
            "fetch_article_html",
            side_effect=[left_html, right_html],
        ):
            response = self.fetch(
                "/api/compare-session",
                method="POST",
                body=json.dumps(
                    {
                        "leftUrl": "https://en.wikipedia.org/wiki/Artificial_intelligence",
                        "rightUrl": "https://en.wikipedia.org/wiki/Machine_learning",
                    }
                ),
                headers={"Content-Type": "application/json"},
            )

        payload = json.loads(response.body)
        labels = [row["label"] for row in payload["rankedRows"]]
        historical = next(row for row in payload["rankedRows"] if row["label"] == "Historical emergence")
        assert response.code == 200
        assert labels.index("Historical emergence") < labels.index("Applications")
        assert historical["leftSourceIds"] == ["left-s-1-1"]
        assert historical["rightSourceIds"] == ["right-s-1-1"]
        assert historical["sourceKind"] == "main_text"
```

- [ ] **Step 2: Run test to verify it fails**

Run:

```bash
python3 -m pytest server/tests/test_compare_api.py::CompareApiTest::test_compare_session_uses_paired_text_attributes_from_llm -q
```

Expected: FAIL because paired text extraction is not called.

- [ ] **Step 3: Add server integration**

Modify imports in `server/server.py`:

```python
from services.text_attribute_pairs import (
    build_paired_text_attributes,
    build_text_evidence_candidates,
)
```

Add helper near `_build_attribute_pools`:

```python
def _build_paired_text_alignments(left_article, right_article, left_pool, right_pool, llm_client):
    if llm_client is None or not hasattr(llm_client, "extract_text_attribute_pairs"):
        return [], [], []
    left_candidates = build_text_evidence_candidates(left_article, "left")
    right_candidates = build_text_evidence_candidates(right_article, "right")
    if not left_candidates or not right_candidates:
        return [], [], []
    infobox_context = {
        "left": _pool_context(left_pool),
        "right": _pool_context(right_pool),
    }
    try:
        pair_response = llm_client.extract_text_attribute_pairs(
            left_candidates=left_candidates,
            right_candidates=right_candidates,
            infobox_context=infobox_context,
        )
    except Exception:
        return [], [], []
    return build_paired_text_attributes(
        left_article,
        right_article,
        pair_response,
        left_pool,
        right_pool,
    )


def _pool_context(pool):
    return [
        {"key": item.get("key"), "valueText": item.get("valueText"), "source": item.get("source")}
        for item in pool
        if isinstance(item, dict)
    ][:24]
```

Modify `_create_compare_session_payload` after `_build_attribute_pools`:

```python
    paired_left_attrs, paired_right_attrs, paired_alignments = _build_paired_text_alignments(
        left_article,
        right_article,
        left_pool,
        right_pool,
        llm_client,
    )
    left_pool = left_pool + paired_left_attrs
    right_pool = right_pool + paired_right_attrs
```

Modify alignment creation:

```python
    aligned_attributes = paired_alignments + _without_duplicate_alignments(
        align_attribute_pools(left_pool, right_pool),
        paired_alignments,
    )
```

Add:

```python
def _without_duplicate_alignments(alignments, existing_alignments):
    existing_pairs = {
        (item["left"].get("id"), item["right"].get("id"))
        for item in existing_alignments
        if isinstance(item, dict)
    }
    return [
        item
        for item in alignments
        if (item["left"].get("id"), item["right"].get("id")) not in existing_pairs
    ]
```

- [ ] **Step 4: Run test to verify it passes**

Run:

```bash
python3 -m pytest server/tests/test_compare_api.py::CompareApiTest::test_compare_session_uses_paired_text_attributes_from_llm -q
```

Expected: PASS.

- [ ] **Step 5: Run existing compare API tests**

Run:

```bash
python3 -m pytest server/tests/test_compare_api.py -q
```

Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add server/server.py server/tests/test_compare_api.py
git commit -m "feat: add paired text rows to compare sessions"
```

## Task 5: Add Deterministic Fallback Pairing For Obvious Data

**Files:**
- Modify: `server/services/text_attribute_pairs.py`
- Modify: `server/tests/test_text_attribute_pairs.py`

- [ ] **Step 1: Write the failing tests**

Append:

```python
from services.text_attribute_pairs import build_rule_paired_text_attributes


def test_build_rule_paired_text_attributes_pairs_compatible_data_roles():
    left_article = {
        "paragraphs": [
            {
                "id": "left-p-1",
                "sentences": [{"id": "left-s-1-1", "text": "The field was founded in 1956."}],
            }
        ]
    }
    right_article = {
        "paragraphs": [
            {
                "id": "right-p-1",
                "sentences": [{"id": "right-s-1-1", "text": "The method emerged in the 1950s."}],
            }
        ]
    }

    left_attrs, right_attrs, alignments = build_rule_paired_text_attributes(left_article, right_article, [], [])

    assert alignments[0]["label"] == "Historical emergence"
    assert left_attrs[0]["dataRole"] == "emergence_time"
    assert right_attrs[0]["dataRole"] == "emergence_time"


def test_build_rule_paired_text_attributes_does_not_pair_different_data_roles():
    left_article = {
        "paragraphs": [
            {
                "id": "left-p-1",
                "sentences": [{"id": "left-s-1-1", "text": "The model reached 95% accuracy."}],
            }
        ]
    }
    right_article = {
        "paragraphs": [
            {
                "id": "right-p-1",
                "sentences": [{"id": "right-s-1-1", "text": "The field was founded in 1956."}],
            }
        ]
    }

    left_attrs, right_attrs, alignments = build_rule_paired_text_attributes(left_article, right_article, [], [])

    assert left_attrs == []
    assert right_attrs == []
    assert alignments == []
```

- [ ] **Step 2: Run tests to verify they fail**

Run:

```bash
python3 -m pytest server/tests/test_text_attribute_pairs.py::test_build_rule_paired_text_attributes_pairs_compatible_data_roles server/tests/test_text_attribute_pairs.py::test_build_rule_paired_text_attributes_does_not_pair_different_data_roles -q
```

Expected: FAIL with missing function.

- [ ] **Step 3: Implement fallback pairing**

Add:

```python
ROLE_LABELS = {
    "emergence_time": "Historical emergence",
    "proportion": "Proportion / rate",
    "ranking": "Ranking",
    "scale": "Scale",
    "quantity": "Quantity",
}


def build_rule_paired_text_attributes(
    left_article: dict[str, Any],
    right_article: dict[str, Any],
    left_infobox_pool: list[dict[str, Any]],
    right_infobox_pool: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    left_candidates = [item for item in build_text_evidence_candidates(left_article, "left") if item["kind"] == "data"]
    right_candidates = [item for item in build_text_evidence_candidates(right_article, "right") if item["kind"] == "data"]
    pairs = []
    used_right: set[int] = set()
    for left_candidate in left_candidates:
        left_role = _primary_role(left_candidate)
        if not left_role:
            continue
        for right_index, right_candidate in enumerate(right_candidates):
            if right_index in used_right or _primary_role(right_candidate) != left_role:
                continue
            used_right.add(right_index)
            label = ROLE_LABELS.get(left_role, left_role.replace("_", " ").title())
            pairs.append(
                {
                    "dimensionLabel": label,
                    "comparisonQuestion": _question_for_role(left_role),
                    "left": {
                        "valueText": left_candidate["claimText"],
                        "sentenceIds": left_candidate["sentenceIds"],
                    },
                    "right": {
                        "valueText": right_candidate["claimText"],
                        "sentenceIds": right_candidate["sentenceIds"],
                    },
                    "dataPriority": True,
                    "dataRole": left_role,
                    "confidence": 0.62,
                }
            )
            break
    return build_paired_text_attributes(left_article, right_article, {"pairs": pairs}, left_infobox_pool, right_infobox_pool)


def _primary_role(candidate: dict[str, Any]) -> str:
    data_items = candidate.get("dataItems") or []
    if not data_items or not isinstance(data_items[0], dict):
        return ""
    return _clean_text(data_items[0].get("role"))


def _question_for_role(role: str) -> str:
    return {
        "emergence_time": "When did it emerge or become established?",
        "proportion": "What proportion, rate, or percentage is reported?",
        "ranking": "What rank or index score is reported?",
        "scale": "What scale or monetary value is reported?",
        "quantity": "What quantity is reported?",
    }.get(role, "What comparable data is reported?")
```

- [ ] **Step 4: Run tests to verify they pass**

Run:

```bash
python3 -m pytest server/tests/test_text_attribute_pairs.py -q
```

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add server/services/text_attribute_pairs.py server/tests/test_text_attribute_pairs.py
git commit -m "feat: add rule fallback for paired text data"
```

## Task 6: Use Fallback When LLM Is Unavailable Or Empty

**Files:**
- Modify: `server/server.py`
- Modify: `server/tests/test_compare_api.py`

- [ ] **Step 1: Write the failing API test**

Append:

```python
    def test_compare_session_uses_rule_paired_data_when_llm_disabled(self):
        left_html = "<html><body><main><p>The field was founded in 1956.</p></main></body></html>"
        right_html = "<html><body><main><p>The method emerged in the 1950s.</p></main></body></html>"

        server.SESSION_STORE.clear()
        server.ARTICLE_HTML_CACHE.clear()
        with patch.dict(os.environ, {"OPENAI_API_KEY": ""}, clear=False), patch.object(
            server,
            "fetch_article_html",
            side_effect=[left_html, right_html],
        ):
            response = self.fetch(
                "/api/compare-session",
                method="POST",
                body=json.dumps(
                    {
                        "leftUrl": "https://en.wikipedia.org/wiki/Artificial_intelligence",
                        "rightUrl": "https://en.wikipedia.org/wiki/Machine_learning",
                    }
                ),
                headers={"Content-Type": "application/json"},
            )

        payload = json.loads(response.body)
        labels = [row["label"] for row in payload["rankedRows"]]
        assert response.code == 200
        assert "Historical emergence" in labels
```

- [ ] **Step 2: Run test to verify it fails**

Run:

```bash
python3 -m pytest server/tests/test_compare_api.py::CompareApiTest::test_compare_session_uses_rule_paired_data_when_llm_disabled -q
```

Expected: FAIL because disabled LLM currently only gets generic fallback dimensions.

- [ ] **Step 3: Integrate fallback**

Modify import:

```python
from services.text_attribute_pairs import (
    build_paired_text_attributes,
    build_rule_paired_text_attributes,
    build_text_evidence_candidates,
)
```

Modify `_build_paired_text_alignments`:

```python
def _build_paired_text_alignments(left_article, right_article, left_pool, right_pool, llm_client):
    if llm_client is not None and hasattr(llm_client, "extract_text_attribute_pairs"):
        left_candidates = build_text_evidence_candidates(left_article, "left")
        right_candidates = build_text_evidence_candidates(right_article, "right")
        if left_candidates and right_candidates:
            infobox_context = {"left": _pool_context(left_pool), "right": _pool_context(right_pool)}
            try:
                pair_response = llm_client.extract_text_attribute_pairs(
                    left_candidates=left_candidates,
                    right_candidates=right_candidates,
                    infobox_context=infobox_context,
                )
                result = build_paired_text_attributes(
                    left_article,
                    right_article,
                    pair_response,
                    left_pool,
                    right_pool,
                )
                if result[2]:
                    return result
            except Exception:
                pass
    return build_rule_paired_text_attributes(left_article, right_article, left_pool, right_pool)
```

- [ ] **Step 4: Run test to verify it passes**

Run:

```bash
python3 -m pytest server/tests/test_compare_api.py::CompareApiTest::test_compare_session_uses_rule_paired_data_when_llm_disabled -q
```

Expected: PASS.

- [ ] **Step 5: Run compare API tests**

Run:

```bash
python3 -m pytest server/tests/test_compare_api.py -q
```

Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add server/server.py server/tests/test_compare_api.py
git commit -m "feat: fallback to rule paired text data"
```

## Task 7: Rank Data-First Paired Text Rows Above Generic Text Rows

**Files:**
- Modify: `server/services/pipeline.py`
- Modify: `server/tests/test_pipeline.py`

- [ ] **Step 1: Write the failing test**

Append to `server/tests/test_pipeline.py`:

```python
def test_rank_rows_prioritizes_paired_data_text_over_generic_text():
    rows = [
        {
            "id": "overview",
            "label": "Overview",
            "dataType": "Text",
            "chartType": "text",
            "score": 0.8,
            "sourceKind": "main_text",
            "comparisonQuality": "text",
            "visualization": {"left": {"rawText": "A is a concept."}, "right": {"rawText": "B is a concept."}},
        },
        {
            "id": "history",
            "label": "Historical emergence",
            "dataType": "Numerical",
            "chartType": "bar",
            "score": 0.4,
            "sourceKind": "main_text",
            "comparisonQuality": "paired_text_data",
            "dataPriority": True,
            "visualization": {"left": {"values": [{"value": 1956}]}, "right": {"values": [{"value": 1950}]}},
        },
    ]

    ranked = rank_rows(rows)

    assert [row["label"] for row in ranked] == ["Historical emergence", "Overview"]
```

- [ ] **Step 2: Run test to verify it fails**

Run:

```bash
python3 -m pytest server/tests/test_pipeline.py::test_rank_rows_prioritizes_paired_data_text_over_generic_text -q
```

Expected: FAIL because current ordering does not inspect `dataPriority`.

- [ ] **Step 3: Preserve `dataPriority` in normalized rows**

Modify `normalize_attribute_pair` row creation in `server/services/pipeline.py`:

```python
        "dataPriority": bool(left_attr.get("dataPriority") or right_attr.get("dataPriority")),
        "dataRole": left_attr.get("dataRole") or right_attr.get("dataRole"),
        "comparisonQuestion": left_attr.get("comparisonQuestion") or right_attr.get("comparisonQuestion"),
```

Place these near `comparisonQuality`.

Then modify `_visual_rank_bucket` or the rank key helper:

```python
def _visual_rank_bucket(row: dict[str, Any]) -> int:
    if row.get("dataPriority") and row.get("sourceKind") == "main_text":
        return 0
    ...
```

Keep the rest of the existing bucket behavior after this special case.

- [ ] **Step 4: Run test to verify it passes**

Run:

```bash
python3 -m pytest server/tests/test_pipeline.py::test_rank_rows_prioritizes_paired_data_text_over_generic_text -q
```

Expected: PASS.

- [ ] **Step 5: Run pipeline tests**

Run:

```bash
python3 -m pytest server/tests/test_pipeline.py -q
```

Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add server/services/pipeline.py server/tests/test_pipeline.py
git commit -m "feat: rank paired text data first"
```

## Task 8: Full Verification And Manual API Check

**Files:**
- No new files.

- [ ] **Step 1: Run backend test suite**

Run:

```bash
python3 -m pytest server/tests -q
```

Expected: all tests pass.

- [ ] **Step 2: Run client tests**

Run:

```bash
for f in client/tests/*.test.cjs; do node "$f" || exit 1; done
```

Expected: all client tests pass.

- [ ] **Step 3: Build frontend**

Run:

```bash
cd client && npm run build
```

Expected: build succeeds. Existing bundle-size warnings are acceptable.

- [ ] **Step 4: Restart backend**

Run:

```bash
lsof -tiTCP:8888 -sTCP:LISTEN | xargs -r kill
cd server && python3 server.py
```

Expected: backend prints `Server is running on http://localhost:8888`.

- [ ] **Step 5: Manually verify AI vs machine learning output**

Run:

```bash
python3 - <<'PY'
import json, urllib.request
payload = json.dumps({
    "leftUrl": "https://en.wikipedia.org/w/index.php?title=Artificial_intelligence&oldid=1361732815",
    "rightUrl": "https://en.wikipedia.org/w/index.php?title=Machine_learning&oldid=1360517605",
    "forceRefresh": True,
}).encode()
req = urllib.request.Request(
    "http://127.0.0.1:8888/api/compare-session",
    data=payload,
    headers={"Content-Type": "application/json"},
    method="POST",
)
with urllib.request.urlopen(req, timeout=90) as resp:
    data = json.loads(resp.read())
rows = data.get("rankedRows") or []
print("rows", len(rows))
for row in rows[:8]:
    print(row.get("label"), row.get("dataPriority"), row.get("sourceKind"), row.get("leftSourceIds"), row.get("rightSourceIds"))
PY
```

Expected:

- `rows` is greater than zero.
- At least one text-derived row has `sourceKind == "main_text"`.
- Data-bearing rows, when present and comparable, appear before generic text rows.
- Rows have source IDs for both sides.

- [ ] **Step 6: Final commit if verification changes were needed**

If any verification fixes were needed:

```bash
git add server client
git commit -m "fix: stabilize data-first text extraction"
```
