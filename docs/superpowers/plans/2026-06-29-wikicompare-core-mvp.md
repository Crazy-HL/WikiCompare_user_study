# WikiCompare Core MVP Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a backend-first WikiCompare MVP that loads two English Wikipedia URLs, extracts comparable attributes from both infoboxes and main text, ranks and visualizes aligned differences, and supports LLM answers with clickable source highlighting.

**Architecture:** The Tornado server becomes the owner of article loading, source anchoring, attribute extraction, alignment, normalization, ranking, and cited LLM responses. The Vue app becomes a session renderer that consumes backend `CompareSession` data and handles article scrolling, chart display, and source highlighting.

**Tech Stack:** Python 3, Tornado, OpenAI-compatible chat API, BeautifulSoup/lxml, pytest; Vue 3, axios, D3/ECharts-adjacent existing chart components.

---

## File Structure

Backend files to create:

- `wikitable-vue/server/requirements.txt`: Runtime and test dependencies.
- `wikitable-vue/server/pytest.ini`: Pytest configuration.
- `wikitable-vue/server/services/__init__.py`: Service package marker.
- `wikitable-vue/server/services/models.py`: Dataclasses and JSON serialization helpers for sessions, articles, sources, attributes, rows, and citations.
- `wikitable-vue/server/services/config.py`: Environment-backed LLM configuration.
- `wikitable-vue/server/services/llm_client.py`: OpenAI-compatible client wrapper with JSON retry/repair helpers.
- `wikitable-vue/server/services/wiki_url.py`: English Wikipedia URL validation and parsing.
- `wikitable-vue/server/services/article_loader.py`: Fetch and parse Wikipedia REST HTML into source-anchored article data.
- `wikitable-vue/server/services/attribute_pool.py`: Infobox and main-text attribute pool construction.
- `wikitable-vue/server/services/pipeline.py`: S1-S4 alignment, classification, chart selection, normalization, and ranking.
- `wikitable-vue/server/services/session_store.py`: In-memory session cache.
- `wikitable-vue/server/services/analysis.py`: Attribute explanation, general Q&A, and citation validation.
- `wikitable-vue/server/tests/fixtures/article_left.html`: Small HTML fixture.
- `wikitable-vue/server/tests/fixtures/article_right.html`: Small HTML fixture.
- `wikitable-vue/server/tests/test_*.py`: Focused backend tests.

Backend files to modify:

- `wikitable-vue/server/server.py`: Replace hardcoded LLM config with services and add `/api/*` handlers.
- `wikitable-vue/server/server copy.py`: Remove or neutralize hardcoded key-bearing duplicate.
- `README.md`: Remove key-like secret and replace with setup notes.

Frontend files to create:

- `wikitable-vue/client/src/js/sessionStore.js`: Reactive session state and highlight helpers.
- `wikitable-vue/client/src/components/UrlCompareForm.vue`: Two Wikipedia URL inputs and load action.
- `wikitable-vue/client/src/components/compoents_base/CitationChips.vue`: Citation chip rendering and hover/click events.

Frontend files to modify:

- `wikitable-vue/client/src/api/index.js`: Promise-based API helpers for `/api/*`.
- `wikitable-vue/client/src/components/general.vue`: Add URL form and pass session state into columns.
- `wikitable-vue/client/src/components/Div1.vue`: Render left article from session instead of hardcoded title.
- `wikitable-vue/client/src/components/Div3.vue`: Render right article from session instead of hardcoded title.
- `wikitable-vue/client/src/components/Div2.vue`: Consume backend ranked rows and remove causal-chain UI path.
- `wikitable-vue/client/src/components/compoents_base/ParentComponent.vue`: Render backend article HTML and apply source highlighting.
- `wikitable-vue/client/src/components/compoents_base/ArticleOutline.vue`: Consume backend outlines and matches.
- `wikitable-vue/client/src/components/compoents_base/CompareTable.vue`: Consume backend ranked rows instead of `COMPARABLE_FIELDS`.

---

### Task 1: Backend Test Harness And Configuration

**Files:**
- Create: `wikitable-vue/server/requirements.txt`
- Create: `wikitable-vue/server/pytest.ini`
- Create: `wikitable-vue/server/services/__init__.py`
- Create: `wikitable-vue/server/services/config.py`
- Test: `wikitable-vue/server/tests/test_config.py`

- [ ] **Step 1: Write failing config tests**

Create `wikitable-vue/server/tests/test_config.py`:

```python
import os

from services.config import get_llm_config


def test_get_llm_config_uses_defaults(monkeypatch):
    monkeypatch.delenv("OPENAI_MODEL", raising=False)
    monkeypatch.delenv("OPENAI_BASE_URL", raising=False)
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)

    config = get_llm_config()

    assert config.model == "gpt-5.5"
    assert config.base_url == "https://newapi.lxhei.xyz/v1"
    assert config.api_key is None
    assert config.enabled is False


def test_get_llm_config_reads_environment(monkeypatch):
    monkeypatch.setenv("OPENAI_MODEL", "custom-model")
    monkeypatch.setenv("OPENAI_BASE_URL", "https://example.test/v1")
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")

    config = get_llm_config()

    assert config.model == "custom-model"
    assert config.base_url == "https://example.test/v1"
    assert config.api_key == "test-key"
    assert config.enabled is True
```

- [ ] **Step 2: Run test to verify it fails**

Run:

```bash
cd /Users/hl/Documents/wikiCompare/wikitable-vue/server
python3 -m pytest tests/test_config.py -v
```

Expected: FAIL with `ModuleNotFoundError: No module named 'services'` or missing `get_llm_config`.

- [ ] **Step 3: Add dependency and pytest config files**

Create `wikitable-vue/server/requirements.txt`:

```text
tornado
openai
beautifulsoup4
lxml
pytest
requests
```

Create `wikitable-vue/server/pytest.ini`:

```ini
[pytest]
pythonpath = .
testpaths = tests
```

Create `wikitable-vue/server/services/__init__.py`:

```python
"""Backend services for the WikiCompare MVP."""
```

- [ ] **Step 4: Implement config module**

Create `wikitable-vue/server/services/config.py`:

```python
from dataclasses import dataclass
import os


DEFAULT_MODEL = "gpt-5.5"
DEFAULT_BASE_URL = "https://newapi.lxhei.xyz/v1"


@dataclass(frozen=True)
class LLMConfig:
    model: str
    base_url: str
    api_key: str | None

    @property
    def enabled(self) -> bool:
        return bool(self.api_key)


def get_llm_config() -> LLMConfig:
    return LLMConfig(
        model=os.getenv("OPENAI_MODEL", DEFAULT_MODEL),
        base_url=os.getenv("OPENAI_BASE_URL", DEFAULT_BASE_URL),
        api_key=os.getenv("OPENAI_API_KEY"),
    )
```

- [ ] **Step 5: Run test to verify it passes**

Run:

```bash
cd /Users/hl/Documents/wikiCompare/wikitable-vue/server
python3 -m pytest tests/test_config.py -v
```

Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add wikitable-vue/server/requirements.txt wikitable-vue/server/pytest.ini wikitable-vue/server/services wikitable-vue/server/tests/test_config.py
git commit -m "test: add backend config harness"
```

---

### Task 2: URL Parsing And Session Models

**Files:**
- Create: `wikitable-vue/server/services/models.py`
- Create: `wikitable-vue/server/services/wiki_url.py`
- Test: `wikitable-vue/server/tests/test_wiki_url.py`
- Test: `wikitable-vue/server/tests/test_models.py`

- [ ] **Step 1: Write failing URL parser tests**

Create `wikitable-vue/server/tests/test_wiki_url.py`:

```python
import pytest

from services.wiki_url import parse_english_wikipedia_url, WikiUrlError


def test_parse_article_url():
    parsed = parse_english_wikipedia_url("https://en.wikipedia.org/wiki/Economy_of_Japan")

    assert parsed.title == "Economy_of_Japan"
    assert parsed.normalized_url == "https://en.wikipedia.org/wiki/Economy_of_Japan"
    assert parsed.revision is None


def test_parse_oldid_revision_url():
    parsed = parse_english_wikipedia_url(
        "https://en.wikipedia.org/w/index.php?title=Economy_of_Japan&oldid=1297943898"
    )

    assert parsed.title == "Economy_of_Japan"
    assert parsed.revision == "1297943898"


def test_reject_non_english_wikipedia():
    with pytest.raises(WikiUrlError, match="Only en.wikipedia.org"):
        parse_english_wikipedia_url("https://zh.wikipedia.org/wiki/人工智能")


def test_reject_non_wikipedia():
    with pytest.raises(WikiUrlError, match="Only en.wikipedia.org"):
        parse_english_wikipedia_url("https://example.com/wiki/Economy_of_Japan")
```

- [ ] **Step 2: Write failing model serialization test**

Create `wikitable-vue/server/tests/test_models.py`:

```python
from services.models import Citation, SourceRef


def test_source_ref_serializes_to_frontend_shape():
    source = SourceRef(
        id="left-info-1",
        side="left",
        source_type="infobox",
        text="GDP growth 1.5%",
        selector='[data-source-id="left-info-1"]',
    )

    assert source.to_dict() == {
        "id": "left-info-1",
        "side": "left",
        "sourceType": "infobox",
        "text": "GDP growth 1.5%",
        "selector": '[data-source-id="left-info-1"]',
    }


def test_citation_serializes_to_frontend_shape():
    citation = Citation(
        id="cite-1",
        label="Infobox: GDP growth",
        side="both",
        source_ids=["left-info-1", "right-info-1"],
    )

    assert citation.to_dict()["sourceIds"] == ["left-info-1", "right-info-1"]
```

- [ ] **Step 3: Run tests to verify they fail**

Run:

```bash
cd /Users/hl/Documents/wikiCompare/wikitable-vue/server
python3 -m pytest tests/test_wiki_url.py tests/test_models.py -v
```

Expected: FAIL with missing modules/classes.

- [ ] **Step 4: Implement models**

Create `wikitable-vue/server/services/models.py` with these dataclasses:

```python
from dataclasses import dataclass, field
from typing import Any, Literal


Side = Literal["left", "right", "both"]


@dataclass
class SourceRef:
    id: str
    side: Literal["left", "right"]
    source_type: str
    text: str
    selector: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "side": self.side,
            "sourceType": self.source_type,
            "text": self.text,
            "selector": self.selector,
        }


@dataclass
class Citation:
    id: str
    label: str
    side: Side
    source_ids: list[str]

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "label": self.label,
            "side": self.side,
            "sourceIds": self.source_ids,
        }


@dataclass
class ArticleAttribute:
    id: str
    side: Literal["left", "right"]
    key: str
    value_text: str
    source: Literal["infobox", "main_text"]
    source_ids: list[str]
    section: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "side": self.side,
            "key": self.key,
            "valueText": self.value_text,
            "source": self.source,
            "sourceIds": self.source_ids,
            "section": self.section,
        }


@dataclass
class CompareSession:
    session_id: str
    articles: dict[str, Any]
    outline_matches: list[dict[str, Any]] = field(default_factory=list)
    attribute_pools: dict[str, list[dict[str, Any]]] = field(default_factory=dict)
    aligned_attributes: list[dict[str, Any]] = field(default_factory=list)
    ranked_rows: list[dict[str, Any]] = field(default_factory=list)
    source_map: dict[str, SourceRef] = field(default_factory=dict)
    warnings: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "sessionId": self.session_id,
            "articles": self.articles,
            "outlineMatches": self.outline_matches,
            "attributePools": self.attribute_pools,
            "alignedAttributes": self.aligned_attributes,
            "rankedRows": self.ranked_rows,
            "sourceMap": {
                source_id: source.to_dict()
                for source_id, source in self.source_map.items()
            },
            "warnings": self.warnings,
        }
```

- [ ] **Step 5: Implement URL parser**

Create `wikitable-vue/server/services/wiki_url.py`:

```python
from dataclasses import dataclass
from urllib.parse import parse_qs, quote, unquote, urlparse


class WikiUrlError(ValueError):
    pass


@dataclass(frozen=True)
class ParsedWikiUrl:
    title: str
    normalized_url: str
    revision: str | None = None


def parse_english_wikipedia_url(url: str) -> ParsedWikiUrl:
    parsed = urlparse(url)
    if parsed.scheme not in {"http", "https"} or parsed.netloc != "en.wikipedia.org":
        raise WikiUrlError("Only en.wikipedia.org URLs are supported.")

    title = None
    revision = None

    if parsed.path.startswith("/wiki/"):
        title = unquote(parsed.path.removeprefix("/wiki/"))
    elif parsed.path == "/w/index.php":
        params = parse_qs(parsed.query)
        title = params.get("title", [None])[0]
        revision = params.get("oldid", [None])[0]

    if not title:
        raise WikiUrlError("Could not parse a Wikipedia article title from the URL.")

    normalized_title = title.replace(" ", "_")
    normalized_url = f"https://en.wikipedia.org/wiki/{quote(normalized_title, safe='_:')}"
    return ParsedWikiUrl(
        title=normalized_title,
        normalized_url=normalized_url,
        revision=revision,
    )
```

- [ ] **Step 6: Run tests to verify they pass**

Run:

```bash
cd /Users/hl/Documents/wikiCompare/wikitable-vue/server
python3 -m pytest tests/test_wiki_url.py tests/test_models.py -v
```

Expected: PASS.

- [ ] **Step 7: Commit**

```bash
git add wikitable-vue/server/services/models.py wikitable-vue/server/services/wiki_url.py wikitable-vue/server/tests/test_wiki_url.py wikitable-vue/server/tests/test_models.py
git commit -m "feat: add wikipedia url parsing models"
```

---

### Task 3: Article Loader With Source Anchors

**Files:**
- Create: `wikitable-vue/server/services/article_loader.py`
- Create: `wikitable-vue/server/tests/fixtures/article_left.html`
- Create: `wikitable-vue/server/tests/fixtures/article_right.html`
- Test: `wikitable-vue/server/tests/test_article_loader.py`

- [ ] **Step 1: Add HTML fixtures**

Create `wikitable-vue/server/tests/fixtures/article_left.html`:

```html
<html><body>
<h1>Economy of Example A</h1>
<table class="infobox">
  <caption>Economy of Example A</caption>
  <tr><th class="infobox-label">GDP growth</th><td class="infobox-data">2.3% (2024)</td></tr>
  <tr><th class="infobox-label">Population</th><td class="infobox-data">10 million</td></tr>
</table>
<h2>Overview</h2>
<p>Example A had GDP growth of 2.3% in 2024. Its exports were led by electronics at 40%.</p>
<h2>Trade</h2>
<p>Exports increased from 100 billion USD in 2020 to 150 billion USD in 2024.</p>
</body></html>
```

Create `wikitable-vue/server/tests/fixtures/article_right.html`:

```html
<html><body>
<h1>Economy of Example B</h1>
<table class="infobox">
  <caption>Economy of Example B</caption>
  <tr><th class="infobox-label">GDP growth</th><td class="infobox-data">0.8% (2024)</td></tr>
  <tr><th class="infobox-label">Population</th><td class="infobox-data">20 million</td></tr>
</table>
<h2>Overview</h2>
<p>Example B had GDP growth of 0.8% in 2024. Its exports were led by machinery at 30%.</p>
<h2>Trade</h2>
<p>Exports increased from 120 billion USD in 2020 to 130 billion USD in 2024.</p>
</body></html>
```

- [ ] **Step 2: Write failing article loader tests**

Create `wikitable-vue/server/tests/test_article_loader.py`:

```python
from pathlib import Path

from services.article_loader import parse_article_html


FIXTURE_DIR = Path(__file__).parent / "fixtures"


def test_parse_article_html_adds_traceable_sources():
    html = (FIXTURE_DIR / "article_left.html").read_text()

    article = parse_article_html(
        html=html,
        side="left",
        title="Economy_of_Example_A",
        url="https://en.wikipedia.org/wiki/Economy_of_Example_A",
        revision=None,
    )

    assert article["title"] == "Economy_of_Example_A"
    assert article["outline"][0]["id"] == "left-heading-1"
    assert article["infobox"][0]["id"] == "left-info-1"
    assert article["paragraphs"][0]["id"] == "left-p-1"
    assert article["paragraphs"][0]["sentences"][0]["id"] == "left-s-1-1"
    assert 'data-source-id="left-info-1"' in article["html"]
    assert 'data-source-id="left-s-1-1"' in article["html"]


def test_parse_article_html_source_map_contains_infobox_and_sentence():
    html = (FIXTURE_DIR / "article_left.html").read_text()

    article = parse_article_html(
        html=html,
        side="left",
        title="Economy_of_Example_A",
        url="https://en.wikipedia.org/wiki/Economy_of_Example_A",
        revision=None,
    )

    source_map = article["sourceMap"]
    assert source_map["left-info-1"].source_type == "infobox"
    assert source_map["left-s-1-1"].source_type == "sentence"
```

- [ ] **Step 3: Run tests to verify they fail**

Run:

```bash
cd /Users/hl/Documents/wikiCompare/wikitable-vue/server
python3 -m pytest tests/test_article_loader.py -v
```

Expected: FAIL with missing `article_loader`.

- [ ] **Step 4: Implement parser**

Create `wikitable-vue/server/services/article_loader.py` with:

```python
from __future__ import annotations

import re
from typing import Literal

import requests
from bs4 import BeautifulSoup

from services.models import SourceRef


WIKI_REST_URL = "https://en.wikipedia.org/api/rest_v1/page/html/{title}"


def fetch_article_html(title: str, revision: str | None = None) -> str:
    url = WIKI_REST_URL.format(title=title)
    if revision:
        url = f"{url}/{revision}"
    response = requests.get(url, timeout=20)
    response.raise_for_status()
    return response.text


def split_sentences(text: str) -> list[str]:
    parts = re.split(r"(?<=[.!?])\s+", text.strip())
    return [part.strip() for part in parts if part.strip()]


def parse_article_html(
    html: str,
    side: Literal["left", "right"],
    title: str,
    url: str,
    revision: str | None,
) -> dict:
    soup = BeautifulSoup(html, "lxml")
    body = soup.body or soup
    source_map: dict[str, SourceRef] = {}

    for selector in ["script", "style", "noscript", ".mw-editsection", "sup.reference"]:
        for node in body.select(selector):
            node.decompose()

    outline = []
    heading_index = 0
    for heading in body.find_all(re.compile("^h[1-6]$")):
        heading_index += 1
        source_id = f"{side}-heading-{heading_index}"
        heading["id"] = source_id
        heading["data-source-id"] = source_id
        text = heading.get_text(" ", strip=True)
        outline.append({
            "id": source_id,
            "text": text,
            "level": int(heading.name[1]),
        })
        source_map[source_id] = SourceRef(
            id=source_id,
            side=side,
            source_type="heading",
            text=text,
            selector=f'[data-source-id="{source_id}"]',
        )

    infobox_rows = []
    info_index = 0
    for table in body.select("table.infobox, table.sidebar, table.toccolours"):
        for row in table.find_all("tr"):
            key_cell = row.find("th")
            value_cell = row.find("td")
            if not key_cell or not value_cell:
                continue
            key = key_cell.get_text(" ", strip=True)
            value = value_cell.get_text(" ", strip=True)
            if not key or not value:
                continue
            info_index += 1
            source_id = f"{side}-info-{info_index}"
            row["data-source-id"] = source_id
            record = {
                "id": source_id,
                "key": key,
                "valueText": value,
                "section": None,
                "source": "infobox",
                "side": side,
            }
            infobox_rows.append(record)
            source_map[source_id] = SourceRef(
                id=source_id,
                side=side,
                source_type="infobox",
                text=f"{key}: {value}",
                selector=f'[data-source-id="{source_id}"]',
            )

    paragraphs = []
    paragraph_index = 0
    for paragraph in body.find_all("p"):
        text = paragraph.get_text(" ", strip=True)
        if not text:
            continue
        paragraph_index += 1
        paragraph_id = f"{side}-p-{paragraph_index}"
        paragraph["data-source-id"] = paragraph_id
        sentences = []
        sentence_nodes = []
        for sentence_index, sentence in enumerate(split_sentences(text), start=1):
            sentence_id = f"{side}-s-{paragraph_index}-{sentence_index}"
            sentences.append({"id": sentence_id, "text": sentence})
            sentence_span = soup.new_tag("span")
            sentence_span["data-source-id"] = sentence_id
            sentence_span.string = sentence
            sentence_nodes.append(sentence_span)
            source_map[sentence_id] = SourceRef(
                id=sentence_id,
                side=side,
                source_type="sentence",
                text=sentence,
                selector=f'[data-source-id="{sentence_id}"]',
            )
        paragraph.clear()
        for index, node in enumerate(sentence_nodes):
            if index:
                paragraph.append(" ")
            paragraph.append(node)
        paragraphs.append({"id": paragraph_id, "text": text, "sentences": sentences})
        source_map[paragraph_id] = SourceRef(
            id=paragraph_id,
            side=side,
            source_type="paragraph",
            text=text,
            selector=f'[data-source-id="{paragraph_id}"]',
        )

    return {
        "title": title,
        "url": url,
        "revision": revision,
        "html": str(body),
        "outline": outline,
        "infobox": infobox_rows,
        "paragraphs": paragraphs,
        "sourceMap": source_map,
    }
```

- [ ] **Step 5: Run tests to verify they pass**

Run:

```bash
cd /Users/hl/Documents/wikiCompare/wikitable-vue/server
python3 -m pytest tests/test_article_loader.py -v
```

Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add wikitable-vue/server/services/article_loader.py wikitable-vue/server/tests/fixtures wikitable-vue/server/tests/test_article_loader.py
git commit -m "feat: parse wikipedia articles with source anchors"
```

---

### Task 4: Dual-Source Attribute Pool

**Files:**
- Create: `wikitable-vue/server/services/llm_client.py`
- Create: `wikitable-vue/server/services/attribute_pool.py`
- Test: `wikitable-vue/server/tests/test_attribute_pool.py`

- [ ] **Step 1: Write failing dual-source pool tests**

Create `wikitable-vue/server/tests/test_attribute_pool.py`:

```python
from services.attribute_pool import build_attribute_pool


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
                    {"id": "left-s-1-1", "text": "Example A had GDP growth of 2.3% in 2024."},
                    {"id": "left-s-1-2", "text": "Its exports were led by electronics at 40%."},
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
        "paragraphs": [{"id": "left-p-1", "text": "A sentence.", "sentences": [{"id": "left-s-1-1", "text": "A sentence."}]}],
    }

    class BadLLM:
        def extract_text_attributes(self, side, paragraphs):
            return [{"key": "bad", "valueText": "bad", "paragraphId": "left-p-99", "sentenceIds": ["left-s-99-1"]}]

    pool = build_attribute_pool(article, "left", BadLLM())

    assert pool == []
```

- [ ] **Step 2: Run tests to verify they fail**

Run:

```bash
cd /Users/hl/Documents/wikiCompare/wikitable-vue/server
python3 -m pytest tests/test_attribute_pool.py -v
```

Expected: FAIL with missing module.

- [ ] **Step 3: Implement LLM wrapper interface**

Create `wikitable-vue/server/services/llm_client.py`:

```python
from __future__ import annotations

import json
import re
from typing import Any

from openai import OpenAI

from services.config import LLMConfig


def extract_json(text: str) -> Any:
    cleaned = re.sub(r"```(?:json)?|```", "", text).strip()
    match = re.search(r"(\{.*\}|\[.*\])", cleaned, flags=re.S)
    if not match:
        raise ValueError("No JSON object or array found in LLM response.")
    return json.loads(match.group(1))


class LLMClient:
    def __init__(self, config: LLMConfig):
        self.config = config
        self.client = OpenAI(api_key=config.api_key, base_url=config.base_url) if config.enabled else None

    def chat_json(self, messages: list[dict[str, str]]) -> Any:
        if not self.client:
            raise RuntimeError("LLM API key is not configured.")
        response = self.client.chat.completions.create(
            model=self.config.model,
            messages=messages,
            temperature=0.2,
        )
        return extract_json(response.choices[0].message.content or "")

    def extract_text_attributes(self, side: str, paragraphs: list[dict]) -> list[dict]:
        compact = [
            {
                "paragraphId": paragraph["id"],
                "sentences": paragraph.get("sentences", []),
            }
            for paragraph in paragraphs[:80]
        ]
        messages = [
            {
                "role": "system",
                "content": "You extract comparable key-value attributes from Wikipedia article text. Return only valid JSON.",
            },
            {
                "role": "user",
                "content": (
                    "Extract high-confidence comparable attributes from these paragraphs. "
                    "Each item must include key, valueText, paragraphId, sentenceIds, and confidence. "
                    f"Side: {side}. Paragraphs: {json.dumps(compact, ensure_ascii=False)}"
                ),
            },
        ]
        data = self.chat_json(messages)
        return data if isinstance(data, list) else []
```

- [ ] **Step 4: Implement attribute pool builder**

Create `wikitable-vue/server/services/attribute_pool.py`:

```python
from __future__ import annotations

from typing import Any


def _valid_sentence_ids(article: dict) -> set[str]:
    ids = set()
    for paragraph in article.get("paragraphs", []):
        for sentence in paragraph.get("sentences", []):
            ids.add(sentence["id"])
    return ids


def _valid_paragraph_ids(article: dict) -> set[str]:
    return {paragraph["id"] for paragraph in article.get("paragraphs", [])}


def build_attribute_pool(article: dict, side: str, llm_client: Any | None) -> list[dict]:
    pool: list[dict] = []

    for index, row in enumerate(article.get("infobox", []), start=1):
        pool.append({
            "id": f"{side}-infobox-attr-{index}",
            "side": side,
            "key": row["key"],
            "valueText": row["valueText"],
            "source": "infobox",
            "sourceIds": [row["id"]],
            "section": row.get("section"),
        })

    if not llm_client:
        return pool

    valid_paragraphs = _valid_paragraph_ids(article)
    valid_sentences = _valid_sentence_ids(article)
    try:
        extracted = llm_client.extract_text_attributes(side, article.get("paragraphs", []))
    except Exception:
        extracted = []

    for index, item in enumerate(extracted, start=1):
        paragraph_id = item.get("paragraphId")
        sentence_ids = item.get("sentenceIds") or []
        if paragraph_id not in valid_paragraphs:
            continue
        if not sentence_ids or any(sentence_id not in valid_sentences for sentence_id in sentence_ids):
            continue
        pool.append({
            "id": f"{side}-text-attr-{index}",
            "side": side,
            "key": item.get("key", "").strip(),
            "valueText": item.get("valueText", "").strip(),
            "source": "main_text",
            "sourceIds": sentence_ids,
            "paragraphId": paragraph_id,
            "confidence": item.get("confidence"),
        })

    return [item for item in pool if item["key"] and item["valueText"]]
```

- [ ] **Step 5: Run tests to verify they pass**

Run:

```bash
cd /Users/hl/Documents/wikiCompare/wikitable-vue/server
python3 -m pytest tests/test_attribute_pool.py -v
```

Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add wikitable-vue/server/services/llm_client.py wikitable-vue/server/services/attribute_pool.py wikitable-vue/server/tests/test_attribute_pool.py
git commit -m "feat: build dual source attribute pools"
```

---

### Task 5: S1-S4 Pipeline And Ranking

**Files:**
- Create: `wikitable-vue/server/services/pipeline.py`
- Test: `wikitable-vue/server/tests/test_pipeline.py`

- [ ] **Step 1: Write failing pipeline tests**

Create `wikitable-vue/server/tests/test_pipeline.py`:

```python
from services.pipeline import (
    choose_chart_type,
    classify_value_rule,
    normalize_attribute_pair,
    rank_rows,
    validate_alignments,
)


def test_choose_chart_type_uses_table_one_rules():
    assert choose_chart_type("Numerical", 2) == "bar"
    assert choose_chart_type("Numerical", 4) == "scatter"
    assert choose_chart_type("Proportional", 4) == "pie"
    assert choose_chart_type("Proportional", 5) == "stacked"
    assert choose_chart_type("Trend", 2) == "bar"
    assert choose_chart_type("Trend", 3) == "line"
    assert choose_chart_type("Categorical", 2) == "text"
    assert choose_chart_type("Categorical", 3) == "stacked"
    assert choose_chart_type("Ordinal", 1) == "text"


def test_classify_value_rule_detects_common_types():
    assert classify_value_rule("1.5% (2024)") == "Proportional"
    assert classify_value_rule("2020: 100, 2024: 150") == "Trend"
    assert classify_value_rule("12th (nominal)") == "Ordinal"
    assert classify_value_rule("40°N, 116°E") == "Geographical"
    assert classify_value_rule("10 million") == "Numerical"


def test_validate_alignments_drops_unknown_attribute_ids():
    left_pool = [{"id": "left-a", "key": "GDP growth", "valueText": "2.3%", "sourceIds": ["left-info-1"]}]
    right_pool = [{"id": "right-a", "key": "GDP growth", "valueText": "0.8%", "sourceIds": ["right-info-1"]}]
    alignments = [
        {"leftId": "left-a", "rightId": "right-a", "label": "GDP growth"},
        {"leftId": "missing", "rightId": "right-a", "label": "Bad"},
    ]

    valid = validate_alignments(left_pool, right_pool, alignments)

    assert len(valid) == 1
    assert valid[0]["leftId"] == "left-a"


def test_normalize_attribute_pair_produces_visualization():
    row = normalize_attribute_pair(
        {"id": "left-a", "key": "GDP growth", "valueText": "2.3% (2024)", "source": "infobox", "sourceIds": ["left-info-1"]},
        {"id": "right-a", "key": "GDP growth", "valueText": "0.8% (2024)", "source": "infobox", "sourceIds": ["right-info-1"]},
        "GDP growth",
    )

    assert row["label"] == "GDP growth"
    assert row["dataType"] in {"Proportional", "Trend", "Numerical"}
    assert row["visualization"]["left"]["values"][0]["value"] == 2.3


def test_rank_rows_orders_trend_first_scores():
    rows = [
        {"id": "a", "score": 0.2, "dataType": "Text"},
        {"id": "b", "score": 0.9, "dataType": "Trend"},
    ]

    assert [row["id"] for row in rank_rows(rows)] == ["b", "a"]
```

- [ ] **Step 2: Run tests to verify they fail**

Run:

```bash
cd /Users/hl/Documents/wikiCompare/wikitable-vue/server
python3 -m pytest tests/test_pipeline.py -v
```

Expected: FAIL with missing `pipeline`.

- [ ] **Step 3: Implement deterministic pipeline helpers**

Create `wikitable-vue/server/services/pipeline.py`:

```python
from __future__ import annotations

import math
import re
from typing import Any


def choose_chart_type(data_type: str, point_count: int) -> str:
    if data_type == "Numerical":
        return "bar" if point_count <= 3 else "scatter"
    if data_type == "Proportional":
        return "pie" if point_count <= 4 else "stacked"
    if data_type == "Trend":
        return "bar" if point_count <= 2 else "line"
    if data_type == "Categorical":
        return "text" if point_count <= 2 else "stacked"
    return "text"


def classify_value_rule(value_text: str) -> str:
    text = value_text or ""
    if re.search(r"\d{4}\s*[:(]", text) and len(re.findall(r"\d+(?:\.\d+)?", text)) >= 2:
        return "Trend"
    if re.search(r"\d+(?:\.\d+)?\s*%", text):
        return "Proportional"
    if re.search(r"\d+(?:st|nd|rd|th)\b|rank", text, re.I):
        return "Ordinal"
    if re.search(r"\d+\s*[°]\s*[NS].*\d+\s*[°]\s*[EW]", text, re.I):
        return "Geographical"
    if re.search(r"\d", text):
        return "Numerical"
    return "Text"


def extract_numeric_values(value_text: str) -> list[dict[str, Any]]:
    text = value_text or ""
    year_value_matches = re.findall(r"(\d{4})[^\d]{0,8}(-?\d+(?:\.\d+)?)\s*%?", text)
    if year_value_matches:
        return [
            {"label": year, "value": float(value)}
            for year, value in year_value_matches
        ]
    numbers = re.findall(r"-?\d+(?:,\d{3})*(?:\.\d+)?", text)
    values = []
    for index, number in enumerate(numbers, start=1):
        cleaned = number.replace(",", "")
        if len(cleaned) == 4 and cleaned.startswith(("19", "20")) and len(numbers) > 1:
            continue
        values.append({"label": str(index), "value": float(cleaned)})
    return values


def validate_alignments(left_pool: list[dict], right_pool: list[dict], alignments: list[dict]) -> list[dict]:
    left_ids = {item["id"] for item in left_pool}
    right_ids = {item["id"] for item in right_pool}
    return [
        item
        for item in alignments
        if item.get("leftId") in left_ids and item.get("rightId") in right_ids
    ]


def _score_values(left_values: list[dict], right_values: list[dict], data_type: str) -> float:
    if not left_values or not right_values:
        return 0.0
    n = min(len(left_values), len(right_values))
    diffs = []
    for index in range(n):
        left = abs(left_values[index]["value"])
        right = abs(right_values[index]["value"])
        denom = max(left, right, 1e-5)
        diffs.append(abs(left - right) / denom)
    base = sum(diffs) / len(diffs)
    if data_type == "Trend":
        return min(1.0, base * 1.3)
    return min(1.0, base)


def normalize_attribute_pair(left_attr: dict, right_attr: dict, label: str) -> dict:
    left_type = classify_value_rule(left_attr.get("valueText", ""))
    right_type = classify_value_rule(right_attr.get("valueText", ""))
    data_type = "Trend" if "Trend" in {left_type, right_type} else left_type if left_type == right_type else "Text"
    left_values = extract_numeric_values(left_attr.get("valueText", ""))
    right_values = extract_numeric_values(right_attr.get("valueText", ""))
    point_count = max(len(left_values), len(right_values), 1)
    chart_type = choose_chart_type(data_type, point_count)
    score = _score_values(left_values, right_values, data_type)
    source_kind = "Both" if left_attr.get("source") != right_attr.get("source") else ("Infobox" if left_attr.get("source") == "infobox" else "Text")
    row_id = f"attr-{re.sub(r'[^a-z0-9]+', '-', label.lower()).strip('-')}"
    return {
        "id": row_id,
        "label": label,
        "leftAttributeId": left_attr["id"],
        "rightAttributeId": right_attr["id"],
        "leftSourceIds": left_attr.get("sourceIds", []),
        "rightSourceIds": right_attr.get("sourceIds", []),
        "sourceKind": source_kind,
        "dataType": data_type,
        "chartType": chart_type,
        "score": score,
        "visualization": {
            "chartType": chart_type,
            "left": {"raw": left_attr.get("valueText"), "values": left_values},
            "right": {"raw": right_attr.get("valueText"), "values": right_values},
        },
    }


def rank_rows(rows: list[dict]) -> list[dict]:
    return sorted(rows, key=lambda row: row.get("score", 0), reverse=True)
```

- [ ] **Step 4: Run tests to verify they pass**

Run:

```bash
cd /Users/hl/Documents/wikiCompare/wikitable-vue/server
python3 -m pytest tests/test_pipeline.py -v
```

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add wikitable-vue/server/services/pipeline.py wikitable-vue/server/tests/test_pipeline.py
git commit -m "feat: add comparison pipeline rules"
```

---

### Task 6: Session Store And Compare Session API

**Files:**
- Create: `wikitable-vue/server/services/session_store.py`
- Modify: `wikitable-vue/server/server.py`
- Test: `wikitable-vue/server/tests/test_session_store.py`
- Test: `wikitable-vue/server/tests/test_compare_api.py`

- [ ] **Step 1: Write failing session store tests**

Create `wikitable-vue/server/tests/test_session_store.py`:

```python
from services.models import CompareSession
from services.session_store import SessionStore


def test_session_store_saves_and_gets_session():
    store = SessionStore()
    session = CompareSession(session_id="s1", articles={})

    store.save(session)

    assert store.get("s1") is session
    assert store.get("missing") is None
```

- [ ] **Step 2: Write failing API smoke test with monkeypatched service**

Create `wikitable-vue/server/tests/test_compare_api.py`:

```python
import json

from tornado.testing import AsyncHTTPTestCase

import server
from services.models import CompareSession


class CompareApiTest(AsyncHTTPTestCase):
    def get_app(self):
        return server.make_app()

    def test_compare_session_requires_urls(self):
        response = self.fetch(
            "/api/compare-session",
            method="POST",
            body=json.dumps({"leftUrl": "", "rightUrl": ""}),
            headers={"Content-Type": "application/json"},
        )

        assert response.code == 400
        assert b"leftUrl" in response.body
```

- [ ] **Step 3: Run tests to verify they fail**

Run:

```bash
cd /Users/hl/Documents/wikiCompare/wikitable-vue/server
python3 -m pytest tests/test_session_store.py tests/test_compare_api.py -v
```

Expected: FAIL with missing store or missing `/api/compare-session`.

- [ ] **Step 4: Implement session store**

Create `wikitable-vue/server/services/session_store.py`:

```python
from services.models import CompareSession


class SessionStore:
    def __init__(self):
        self._sessions: dict[str, CompareSession] = {}

    def save(self, session: CompareSession) -> None:
        self._sessions[session.session_id] = session

    def get(self, session_id: str) -> CompareSession | None:
        return self._sessions.get(session_id)
```

- [ ] **Step 5: Add JSON request helper and `/api/compare-session` handler**

Modify `wikitable-vue/server/server.py` so it:

```python
import uuid
from services.article_loader import fetch_article_html, parse_article_html
from services.attribute_pool import build_attribute_pool
from services.config import get_llm_config
from services.llm_client import LLMClient
from services.models import CompareSession
from services.pipeline import normalize_attribute_pair, rank_rows, validate_alignments
from services.session_store import SessionStore
from services.wiki_url import WikiUrlError, parse_english_wikipedia_url

SESSION_STORE = SessionStore()
```

Add a base handler:

```python
class ApiHandler(tornado.web.RequestHandler):
    def set_default_headers(self):
        self.set_header("Access-Control-Allow-Origin", "*")
        self.set_header("Access-Control-Allow-Methods", "POST, OPTIONS")
        self.set_header("Access-Control-Allow-Headers", "Content-Type")

    def options(self):
        self.set_status(204)
        self.finish()

    def read_json(self):
        try:
            return json.loads(self.request.body or b"{}")
        except json.JSONDecodeError:
            self.set_status(400)
            self.finish({"error": "Invalid JSON request body."})
            return None

    def write_error_json(self, status: int, message: str):
        self.set_status(status)
        self.finish(json.dumps({"error": message}, ensure_ascii=False))
```

Add a first-pass handler that validates URLs and returns a structured session. For this task, if LLM alignment is not configured, align exact lowercased keys only:

```python
class CompareSessionHandler(ApiHandler):
    def post(self):
        data = self.read_json()
        if data is None:
            return
        left_url = data.get("leftUrl")
        right_url = data.get("rightUrl")
        if not left_url or not right_url:
            self.write_error_json(400, "leftUrl and rightUrl are required.")
            return
        try:
            left_parsed = parse_english_wikipedia_url(left_url)
            right_parsed = parse_english_wikipedia_url(right_url)
        except WikiUrlError as error:
            self.write_error_json(400, str(error))
            return

        config = get_llm_config()
        llm_client = LLMClient(config) if config.enabled else None
        warnings = [] if config.enabled else ["OPENAI_API_KEY is not configured; using rule-based comparison where possible."]

        left_article = parse_article_html(fetch_article_html(left_parsed.title, left_parsed.revision), "left", left_parsed.title, left_parsed.normalized_url, left_parsed.revision)
        right_article = parse_article_html(fetch_article_html(right_parsed.title, right_parsed.revision), "right", right_parsed.title, right_parsed.normalized_url, right_parsed.revision)
        left_pool = build_attribute_pool(left_article, "left", llm_client)
        right_pool = build_attribute_pool(right_article, "right", llm_client)

        right_by_key = {item["key"].lower(): item for item in right_pool}
        rows = []
        alignments = []
        for left_item in left_pool:
            right_item = right_by_key.get(left_item["key"].lower())
            if right_item:
                alignments.append({"leftId": left_item["id"], "rightId": right_item["id"], "label": left_item["key"]})
                rows.append(normalize_attribute_pair(left_item, right_item, left_item["key"]))

        source_map = {}
        source_map.update(left_article.pop("sourceMap"))
        source_map.update(right_article.pop("sourceMap"))
        session = CompareSession(
            session_id=str(uuid.uuid4()),
            articles={"left": left_article, "right": right_article},
            outline_matches=[],
            attribute_pools={"left": left_pool, "right": right_pool},
            aligned_attributes=alignments,
            ranked_rows=rank_rows(rows),
            source_map=source_map,
            warnings=warnings,
        )
        SESSION_STORE.save(session)
        self.write(json.dumps(session.to_dict(), ensure_ascii=False))
```

Register:

```python
(r"/api/compare-session", CompareSessionHandler),
```

- [ ] **Step 6: Run tests to verify they pass**

Run:

```bash
cd /Users/hl/Documents/wikiCompare/wikitable-vue/server
python3 -m pytest tests/test_session_store.py tests/test_compare_api.py -v
```

Expected: PASS.

- [ ] **Step 7: Commit**

```bash
git add wikitable-vue/server/services/session_store.py wikitable-vue/server/server.py wikitable-vue/server/tests/test_session_store.py wikitable-vue/server/tests/test_compare_api.py
git commit -m "feat: add compare session api"
```

---

### Task 7: LLM Alignment And Analysis APIs With Citation Validation

**Files:**
- Create: `wikitable-vue/server/services/analysis.py`
- Modify: `wikitable-vue/server/services/llm_client.py`
- Modify: `wikitable-vue/server/server.py`
- Test: `wikitable-vue/server/tests/test_analysis.py`

- [ ] **Step 1: Write failing citation validation tests**

Create `wikitable-vue/server/tests/test_analysis.py`:

```python
from services.analysis import validate_citations
from services.models import Citation, SourceRef


def test_validate_citations_drops_unknown_source_ids():
    source_map = {
        "left-info-1": SourceRef("left-info-1", "left", "infobox", "GDP growth: 2.3%", '[data-source-id="left-info-1"]')
    }
    citations = [
        Citation("cite-1", "Infobox: GDP growth", "left", ["left-info-1"]),
        Citation("cite-2", "Bad", "left", ["missing"]),
    ]

    valid = validate_citations(citations, source_map)

    assert [citation.id for citation in valid] == ["cite-1"]
```

- [ ] **Step 2: Run test to verify it fails**

Run:

```bash
cd /Users/hl/Documents/wikiCompare/wikitable-vue/server
python3 -m pytest tests/test_analysis.py -v
```

Expected: FAIL with missing module.

- [ ] **Step 3: Implement analysis helpers**

Create `wikitable-vue/server/services/analysis.py`:

```python
from __future__ import annotations

import json

from services.models import Citation, CompareSession, SourceRef


def validate_citations(citations: list[Citation], source_map: dict[str, SourceRef]) -> list[Citation]:
    return [
        citation
        for citation in citations
        if citation.source_ids and all(source_id in source_map for source_id in citation.source_ids)
    ]


def row_context(session: CompareSession, attribute_id: str) -> dict | None:
    for row in session.ranked_rows:
        if row["id"] == attribute_id:
            return row
    return None


def fallback_attribute_summary(row: dict) -> dict:
    source_ids = row.get("leftSourceIds", []) + row.get("rightSourceIds", [])
    return {
        "summary": f"{row['label']} differs between the two articles. Configure OPENAI_API_KEY for a detailed LLM explanation.",
        "citations": [
            Citation(
                id="cite-1",
                label=f"Sources: {row['label']}",
                side="both",
                source_ids=source_ids,
            ).to_dict()
        ] if source_ids else [],
    }


def fallback_answer(session: CompareSession, question: str) -> dict:
    top = session.ranked_rows[0] if session.ranked_rows else None
    if not top:
        return {"answer": "No aligned attributes are available for this session.", "citations": []}
    return {
        "answer": f"The most salient available comparison is {top['label']}. Configure OPENAI_API_KEY for deeper question answering.",
        "citations": [
            Citation("cite-1", f"Sources: {top['label']}", "both", top.get("leftSourceIds", []) + top.get("rightSourceIds", [])).to_dict()
        ],
    }
```

- [ ] **Step 4: Add analysis and ask handlers**

Modify `wikitable-vue/server/server.py`:

```python
from services.analysis import fallback_answer, fallback_attribute_summary, row_context
```

Add:

```python
class AnalyzeAttributeHandler(ApiHandler):
    def post(self):
        data = self.read_json()
        if data is None:
            return
        session = SESSION_STORE.get(data.get("sessionId", ""))
        if not session:
            self.write_error_json(404, "Comparison session was not found.")
            return
        row = row_context(session, data.get("attributeId", ""))
        if not row:
            self.write_error_json(404, "Attribute was not found.")
            return
        self.write(json.dumps(fallback_attribute_summary(row), ensure_ascii=False))


class AskHandlerV2(ApiHandler):
    def post(self):
        data = self.read_json()
        if data is None:
            return
        session = SESSION_STORE.get(data.get("sessionId", ""))
        if not session:
            self.write_error_json(404, "Comparison session was not found.")
            return
        question = data.get("question", "").strip()
        if not question:
            self.write_error_json(400, "question is required.")
            return
        self.write(json.dumps(fallback_answer(session, question), ensure_ascii=False))
```

Register:

```python
(r"/api/analyze-attribute", AnalyzeAttributeHandler),
(r"/api/ask", AskHandlerV2),
```

This task intentionally lands deterministic fallbacks first. A later implementation pass can replace fallback bodies with LLM prompts while preserving the same response contract.

- [ ] **Step 5: Run tests**

Run:

```bash
cd /Users/hl/Documents/wikiCompare/wikitable-vue/server
python3 -m pytest tests/test_analysis.py tests/test_compare_api.py -v
```

Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add wikitable-vue/server/services/analysis.py wikitable-vue/server/server.py wikitable-vue/server/tests/test_analysis.py
git commit -m "feat: add cited analysis api contracts"
```

---

### Task 8: Frontend Session Store And URL Form

**Files:**
- Create: `wikitable-vue/client/src/js/sessionStore.js`
- Create: `wikitable-vue/client/src/components/UrlCompareForm.vue`
- Modify: `wikitable-vue/client/src/api/index.js`
- Modify: `wikitable-vue/client/src/components/general.vue`

- [ ] **Step 1: Add Promise API helpers**

Modify `wikitable-vue/client/src/api/index.js` so it keeps existing `get` and `post` callbacks while adding:

```js
export function postJson(url, params) {
	return axios
		.post(address + url, params, { headers: { "Content-Type": "application/json" } })
		.then(response => response.data);
}
```

Also add the named export without breaking the default export.

- [ ] **Step 2: Create session store**

Create `wikitable-vue/client/src/js/sessionStore.js`:

```js
import { reactive } from "vue";
import { postJson } from "@/api";

export const sessionStore = reactive({
	session: null,
	isLoading: false,
	error: "",
	highlightedSourceIds: [],
	pinnedSourceIds: [],

	async loadSession(leftUrl, rightUrl) {
		this.isLoading = true;
		this.error = "";
		try {
			this.session = await postJson("api/compare-session", { leftUrl, rightUrl });
		} catch (error) {
			this.error =
				error.response?.data?.error || error.message || "Failed to load comparison session";
		} finally {
			this.isLoading = false;
		}
	},

	highlight(sourceIds) {
		this.highlightedSourceIds = sourceIds || [];
	},

	clearHighlight() {
		this.highlightedSourceIds = [];
	},

	pin(sourceIds) {
		this.pinnedSourceIds = sourceIds || [];
	}
});
```

- [ ] **Step 3: Create URL form**

Create `wikitable-vue/client/src/components/UrlCompareForm.vue`:

```vue
<template>
	<form class="url-form" @submit.prevent="submit">
		<input v-model="leftUrl" placeholder="Left English Wikipedia URL" />
		<input v-model="rightUrl" placeholder="Right English Wikipedia URL" />
		<button type="submit" :disabled="store.isLoading">
			{{ store.isLoading ? "Loading..." : "Compare" }}
		</button>
		<p v-if="store.error" class="error">{{ store.error }}</p>
	</form>
</template>

<script setup>
	import { ref } from "vue";
	import { sessionStore as store } from "@/js/sessionStore";

	const leftUrl = ref("https://en.wikipedia.org/wiki/Economy_of_South_Korea");
	const rightUrl = ref("https://en.wikipedia.org/wiki/Economy_of_Japan");

	const submit = () => {
		store.loadSession(leftUrl.value, rightUrl.value);
	};
</script>

<style scoped>
	.url-form {
		display: grid;
		grid-template-columns: 1fr 1fr auto;
		gap: 8px;
		padding: 8px;
		background: #ffffff;
		border-bottom: 1px solid #e5e7eb;
	}
	input {
		min-width: 0;
		padding: 8px 10px;
		border: 1px solid #cbd5e1;
		border-radius: 6px;
	}
	button {
		padding: 8px 14px;
		border: 0;
		border-radius: 6px;
		background: #1f2937;
		color: white;
		cursor: pointer;
	}
	.error {
		grid-column: 1 / -1;
		margin: 0;
		color: #b91c1c;
		font-size: 13px;
	}
</style>
```

- [ ] **Step 4: Mount URL form above three columns**

Modify `wikitable-vue/client/src/components/general.vue` to render:

```vue
<template>
	<div id="app-shell">
		<UrlCompareForm />
		<div id="root">
			<Div1 class="div" />
			<Div2 class="div" />
			<Div3 class="div" />
		</div>
	</div>
</template>

<script setup>
	import UrlCompareForm from "./UrlCompareForm.vue";
	import Div1 from "./Div1.vue";
	import Div2 from "./Div2.vue";
	import Div3 from "./Div3.vue";
</script>
```

Keep the existing three-column CSS, but move full-height sizing to `#app-shell` and set `#root` height to `calc(100vh - 58px)`.

- [ ] **Step 5: Run frontend build**

Run:

```bash
cd /Users/hl/Documents/wikiCompare/wikitable-vue/client
npm run build
```

Expected: build succeeds.

- [ ] **Step 6: Commit**

```bash
git add wikitable-vue/client/src/api/index.js wikitable-vue/client/src/js/sessionStore.js wikitable-vue/client/src/components/UrlCompareForm.vue wikitable-vue/client/src/components/general.vue
git commit -m "feat: add comparison session url form"
```

---

### Task 9: Frontend Article Rendering And Source Highlighting

**Files:**
- Modify: `wikitable-vue/client/src/components/Div1.vue`
- Modify: `wikitable-vue/client/src/components/Div3.vue`
- Modify: `wikitable-vue/client/src/components/compoents_base/ParentComponent.vue`
- Modify: `wikitable-vue/client/src/components/compoents_base/ArticleOutline.vue`

- [ ] **Step 1: Refactor `Div1.vue` and `Div3.vue` to pass side**

`Div1.vue` should become:

```vue
<template>
	<ParentComponent side="left" divId="div1" selectContentClass="selectContent1" />
</template>

<script setup>
	import ParentComponent from "@/components/compoents_base/ParentComponent.vue";
</script>
```

`Div3.vue` should become:

```vue
<template>
	<ParentComponent side="right" divId="div3" selectContentClass="selectContent2" />
</template>

<script setup>
	import ParentComponent from "@/components/compoents_base/ParentComponent.vue";
</script>
```

- [ ] **Step 2: Refactor `ParentComponent.vue` to render session article**

Modify props:

```js
props: {
	side: String,
	divId: String,
	selectContentClass: String
}
```

Use `sessionStore.session.articles[props.side]` as the article source. Remove direct Wikipedia fetch from the active path. Render `article.html` through `WikipediaContent`, and pass `article.outline` plus `session.outlineMatches` into `ArticleOutline`.

- [ ] **Step 3: Add source highlighting watcher**

Inside `ParentComponent.vue`, watch `sessionStore.highlightedSourceIds` and `sessionStore.pinnedSourceIds`:

```js
const applyHighlights = () => {
	const root = divRef.value;
	if (!root) return;
	root.querySelectorAll(".source-highlight, .source-pinned").forEach(node => {
		node.classList.remove("source-highlight", "source-pinned");
	});
	sessionStore.highlightedSourceIds.forEach(id => {
		root.querySelectorAll(`[data-source-id="${CSS.escape(id)}"]`).forEach(node => {
			node.classList.add("source-highlight");
		});
	});
	sessionStore.pinnedSourceIds.forEach(id => {
		root.querySelectorAll(`[data-source-id="${CSS.escape(id)}"]`).forEach(node => {
			node.classList.add("source-pinned");
		});
	});
};
```

Add CSS:

```css
:deep([data-source-id].source-highlight) {
	background: rgba(253, 224, 71, 0.45);
	outline: 2px solid rgba(234, 179, 8, 0.55);
}
:deep([data-source-id].source-pinned) {
	background: rgba(96, 165, 250, 0.25);
	outline: 2px solid rgba(37, 99, 235, 0.6);
}
```

- [ ] **Step 4: Refactor `ArticleOutline.vue`**

Make it accept:

```js
const props = defineProps({
	outline: Array,
	divId: String,
	matches: Array
});
```

Remove hardcoded `linkedOutline`. Use `props.matches` to determine linked IDs. Keep synchronized scroll behavior by emitting target IDs through `eventBus`.

- [ ] **Step 5: Run frontend build**

Run:

```bash
cd /Users/hl/Documents/wikiCompare/wikitable-vue/client
npm run build
```

Expected: build succeeds.

- [ ] **Step 6: Commit**

```bash
git add wikitable-vue/client/src/components/Div1.vue wikitable-vue/client/src/components/Div3.vue wikitable-vue/client/src/components/compoents_base/ParentComponent.vue wikitable-vue/client/src/components/compoents_base/ArticleOutline.vue
git commit -m "feat: render session articles with source highlights"
```

---

### Task 10: Frontend Ranked Table And Cited Answers

**Files:**
- Create: `wikitable-vue/client/src/components/compoents_base/CitationChips.vue`
- Modify: `wikitable-vue/client/src/components/Div2.vue`
- Modify: `wikitable-vue/client/src/components/compoents_base/CompareTable.vue`

- [ ] **Step 1: Create citation chips**

Create `wikitable-vue/client/src/components/compoents_base/CitationChips.vue`:

```vue
<template>
	<div class="citation-list" v-if="citations?.length">
		<button
			v-for="citation in citations"
			:key="citation.id"
			class="citation-chip"
			@mouseenter="store.highlight(citation.sourceIds)"
			@mouseleave="store.clearHighlight()"
			@click="pinCitation(citation)">
			{{ citation.label }}
		</button>
	</div>
</template>

<script setup>
	import { sessionStore as store } from "@/js/sessionStore";

	defineProps({ citations: Array });

	const pinCitation = citation => {
		store.pin(citation.sourceIds);
		const firstId = citation.sourceIds?.[0];
		if (!firstId) return;
		requestAnimationFrame(() => {
			document
				.querySelector(`[data-source-id="${CSS.escape(firstId)}"]`)
				?.scrollIntoView({ behavior: "smooth", block: "center" });
		});
	};
</script>

<style scoped>
	.citation-list {
		display: flex;
		flex-wrap: wrap;
		gap: 6px;
		margin-top: 8px;
	}
	.citation-chip {
		border: 1px solid #93c5fd;
		background: #eff6ff;
		color: #1d4ed8;
		border-radius: 999px;
		padding: 4px 9px;
		font-size: 12px;
		cursor: pointer;
	}
</style>
```

- [ ] **Step 2: Refactor `CompareTable.vue` to use `rankedRows`**

Replace `COMPARABLE_FIELDS` and country-specific `getField` branches with:

```js
import { computed, ref } from "vue";
import { sessionStore } from "@/js/sessionStore";

const rows = computed(() => sessionStore.session?.rankedRows || []);
```

Render each row from backend fields:

```vue
<template v-for="row in rows" :key="row.id">
	<div class="cell left-column" @mouseover="highlight(row.leftSourceIds)" @mouseout="clearHighlight">
		<SimpleChart :field="row.visualization.left" :type="row.dataType" :visualization="row.chartType" />
	</div>
	<div class="cell middle-column">
		<div class="field-name">{{ row.label }}</div>
		<div class="field-type">{{ row.dataType }} · {{ row.sourceKind }}</div>
		<div class="icon-actions">
			<span class="icon-btn compare" title="对比分析" @click="emit('compareAttribute', row)">Compare</span>
			<span class="icon-btn merge" title="合并图表" @click="showCombinedChart(row)">Merge</span>
		</div>
	</div>
	<div class="cell right-column" @mouseover="highlight(row.rightSourceIds)" @mouseout="clearHighlight">
		<SimpleChart :field="row.visualization.right" :type="row.dataType" :visualization="row.chartType" />
	</div>
</template>
```

Use `sessionStore.highlight([...])` and `sessionStore.clearHighlight()` for hover behavior.

- [ ] **Step 3: Refactor `Div2.vue` chat to remove causal flow**

Remove `CausalFlowChart` import and all `isCausalFlow` rendering. Import `CitationChips` and `postJson`:

```js
import CitationChips from "@/components/compoents_base/CitationChips.vue";
import { postJson } from "@/api";
import { sessionStore } from "@/js/sessionStore";
```

Render messages:

```vue
<div class="message-content" v-html="message.content"></div>
<CitationChips :citations="message.citations" />
```

Update `handleAttributeComparison(row)`:

```js
const response = await postJson("api/analyze-attribute", {
	sessionId: sessionStore.session.sessionId,
	attributeId: row.id
});
chatHistory.value.push({
	role: "assistant",
	content: formatAnalysisResult(response.summary),
	citations: response.citations || [],
	timestamp: new Date().toLocaleString()
});
```

Update `askQuestion()`:

```js
const response = await postJson("api/ask", {
	sessionId: sessionStore.session.sessionId,
	question
});
chatHistory.value.push({
	role: "assistant",
	content: formatAnalysisResult(response.answer),
	citations: response.citations || [],
	timestamp: new Date().toLocaleString()
});
```

- [ ] **Step 4: Run frontend build**

Run:

```bash
cd /Users/hl/Documents/wikiCompare/wikitable-vue/client
npm run build
```

Expected: build succeeds.

- [ ] **Step 5: Commit**

```bash
git add wikitable-vue/client/src/components/compoents_base/CitationChips.vue wikitable-vue/client/src/components/Div2.vue wikitable-vue/client/src/components/compoents_base/CompareTable.vue
git commit -m "feat: render ranked rows with cited answers"
```

---

### Task 11: Secret Cleanup And Legacy Hardcoding Removal

**Files:**
- Modify: `README.md`
- Modify: `wikitable-vue/server/server.py`
- Modify: `wikitable-vue/server/server copy.py`
- Modify: `.gitignore`

- [ ] **Step 1: Write failing secret scan command**

Run:

```bash
cd /Users/hl/Documents/wikiCompare
rg -n "sk-[A-Za-z0-9]|api_key=\"sk-|experimental_bearer_token" README.md wikitable-vue/server wikitable-vue/client/src
```

Expected before cleanup: finds key-like strings.

- [ ] **Step 2: Replace README secret with setup notes**

Replace `README.md` content with:

```markdown
# WikiCompare

Interactive system for comparative reading of two English Wikipedia articles.

## Local LLM Configuration

Set these environment variables before starting the backend:

```bash
export OPENAI_MODEL="gpt-5.5"
export OPENAI_BASE_URL="https://newapi.lxhei.xyz/v1"
export OPENAI_API_KEY="your-provider-key"
```

Do not commit API keys to the repository.
```
```

- [ ] **Step 3: Remove hardcoded API keys**

In `wikitable-vue/server/server.py`, delete the old module-level `OpenAI(api_key="sk-...", base_url=...)` client and make old legacy handlers use `get_llm_config()` and `LLMClient` or return a clear error when not configured.

In `wikitable-vue/server/server copy.py`, either delete the file if it is not imported, or replace its contents with:

```python
"""Deprecated duplicate server file.

Use server.py. This file intentionally contains no API keys.
"""
```

- [ ] **Step 4: Ignore generated junk**

Add to `.gitignore`:

```gitignore
__pycache__/
*.pyc
.DS_Store
wikitable-vue/client/dist/
```

- [ ] **Step 5: Re-run secret scan**

Run:

```bash
cd /Users/hl/Documents/wikiCompare
rg -n "sk-[A-Za-z0-9]|api_key=\"sk-|experimental_bearer_token" README.md wikitable-vue/server wikitable-vue/client/src
```

Expected: no output.

- [ ] **Step 6: Run backend and frontend checks**

Run:

```bash
cd /Users/hl/Documents/wikiCompare/wikitable-vue/server
python3 -m pytest -v
cd /Users/hl/Documents/wikiCompare/wikitable-vue/client
npm run build
```

Expected: both pass.

- [ ] **Step 7: Commit**

```bash
git add README.md .gitignore wikitable-vue/server/server.py "wikitable-vue/server/server copy.py"
git commit -m "chore: remove secrets and legacy hardcoding"
```

---

### Task 12: End-To-End Local Verification

**Files:**
- Modify only files necessary to fix verification failures from this task.

- [ ] **Step 1: Run backend tests**

Run:

```bash
cd /Users/hl/Documents/wikiCompare/wikitable-vue/server
python3 -m pytest -v
```

Expected: all backend tests pass.

- [ ] **Step 2: Build frontend**

Run:

```bash
cd /Users/hl/Documents/wikiCompare/wikitable-vue/client
npm run build
```

Expected: build succeeds.

- [ ] **Step 3: Start backend server**

Run:

```bash
cd /Users/hl/Documents/wikiCompare/wikitable-vue/server
python3 server.py
```

Expected: server listens on `http://localhost:8888`.

- [ ] **Step 4: Start frontend dev server**

Run in another terminal:

```bash
cd /Users/hl/Documents/wikiCompare/wikitable-vue/client
npm run serve
```

Expected: Vue dev server starts, usually on `http://localhost:8080`.

- [ ] **Step 5: Manual browser verification**

Open the frontend and use:

```text
https://en.wikipedia.org/wiki/Economy_of_South_Korea
https://en.wikipedia.org/wiki/Economy_of_Japan
```

Verify:

- Both articles render.
- Ranked rows appear in the center table.
- Rows include infobox and main-text sourced attributes when LLM is configured.
- Clicking Compare adds an assistant message with citation chips.
- Hovering a citation highlights the original infobox row or text sentence.
- Clicking a citation scrolls to the original source and pins highlight.
- Causal-chain UI is absent.

- [ ] **Step 6: Commit any verification fixes**

If files changed:

```bash
git status --short
git add wikitable-vue/server wikitable-vue/client/src README.md .gitignore
git commit -m "fix: complete wikicompare mvp verification"
```

If no files changed, do not create an empty commit.

---

## Plan Self-Review

- Spec coverage: This plan covers URL input, backend-first sessions, source anchoring, dual-source attribute pools, S1-S4 pipeline, ranking, LLM-ready cited APIs, frontend session rendering, citation highlighting, removal of causal-chain UI, secret cleanup, and verification.
- Placeholder scan: No `TBD`, `TODO`, or "implement later" placeholders remain. The plan intentionally lands deterministic fallbacks before LLM prompt refinement, while preserving API contracts.
- Type consistency: `sessionId`, `sourceIds`, `rankedRows`, `attributePools`, `leftSourceIds`, `rightSourceIds`, `dataType`, `chartType`, and citation shapes are consistent with the approved design spec.
