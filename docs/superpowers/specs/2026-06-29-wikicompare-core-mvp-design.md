# WikiCompare Core MVP Design

## Goal

Build a paper-faithful core MVP for WikiCompare that compares two English Wikipedia articles from user-provided URLs. The system should support side-by-side reading, semantic outline matching, dual-source comparable attribute extraction from both infoboxes and main text, ranked visual comparison, LLM-powered attribute explanations, and citation-driven source highlighting. Causal-chain generation and causal-chain diagrams are explicitly out of scope.

## Scope

In scope:

- Accept two `en.wikipedia.org` article URLs in the UI.
- Load and render both articles in the existing three-column layout.
- Extract structured source anchors from article HTML: headings, infobox rows, paragraphs, and sentences.
- Build attribute pools from both infoboxes and main text.
- Align semantically equivalent attributes across the two articles.
- Classify aligned attributes into the paper's data types.
- Choose chart types with deterministic rules based on the paper's Table 1.
- Normalize values into renderable JSON for side-by-side, expanded, and merged charts.
- Rank attributes using a trend-first difference score.
- Let users request concise LLM explanations for individual attributes.
- Let users ask general comparison questions.
- Return citations with source IDs for every LLM answer and support citation hover/click highlighting in the original articles.
- Move LLM configuration out of source code and into environment variables.

Out of scope:

- Causal-chain generation.
- Causal-chain diagrams.
- Automatic why-question suggestions.
- Multi-language Wikipedia support.
- Multi-entity comparison beyond two articles.
- Full replication of the paper's user study or evaluation tooling.

## Architecture

The MVP uses a backend-first architecture. The server owns the Wikipedia loading, extraction, alignment, normalization, ranking, and LLM orchestration pipeline. The Vue frontend renders a structured comparison session and handles interaction events such as scrolling, hover highlighting, chart expansion, merged chart display, and citation navigation.

This is intentionally different from the current repository, where much of the parsing, filtering, hardcoded field matching, and country-specific data handling lives in Vue components. The backend-first approach makes the paper pipeline easier to test and prevents hardcoded demo-specific results from leaking into the UI.

## LLM Configuration

The OpenAI-compatible client should be configured through environment variables:

- `OPENAI_MODEL`, defaulting to `gpt-5.5` for this project.
- `OPENAI_BASE_URL`, defaulting to `https://newapi.lxhei.xyz/v1`.
- `OPENAI_API_KEY`, required for LLM-powered alignment and answers.

No API key or bearer token should be committed to source code, README files, or frontend bundles. Existing hardcoded keys should be removed during implementation.

## Primary API

### `POST /api/compare-session`

Input:

```json
{
  "leftUrl": "https://en.wikipedia.org/wiki/Economy_of_South_Korea",
  "rightUrl": "https://en.wikipedia.org/wiki/Economy_of_Japan"
}
```

Output:

```json
{
  "sessionId": "session-id",
  "articles": {
    "left": {
      "title": "Article title",
      "url": "https://en.wikipedia.org/wiki/Article_title",
      "revision": null,
      "html": "<article>...</article>",
      "outline": [],
      "infobox": [],
      "paragraphs": []
    },
    "right": {
      "title": "Article title",
      "url": "https://en.wikipedia.org/wiki/Article_title",
      "revision": null,
      "html": "<article>...</article>",
      "outline": [],
      "infobox": [],
      "paragraphs": []
    }
  },
  "outlineMatches": [],
  "attributePools": {
    "left": [],
    "right": []
  },
  "alignedAttributes": [],
  "rankedRows": [],
  "warnings": []
}
```

### `POST /api/analyze-attribute`

Input:

```json
{
  "sessionId": "session-id",
  "attributeId": "attr-gdp-growth"
}
```

Output:

```json
{
  "summary": "Concise comparison text.",
  "citations": [
    {
      "id": "cite-1",
      "label": "Infobox: GDP growth",
      "side": "both",
      "sourceIds": ["left-info-8", "right-info-9"]
    }
  ]
}
```

### `POST /api/ask`

Input:

```json
{
  "sessionId": "session-id",
  "question": "Which article shows stronger recent growth?"
}
```

Output:

```json
{
  "answer": "Answer text grounded in the comparison session.",
  "citations": [
    {
      "id": "cite-1",
      "label": "Text: paragraph 12",
      "side": "left",
      "sourceIds": ["left-s-12-3"]
    }
  ]
}
```

All citation `sourceIds` must refer to IDs present in the current session source map. Invalid citations should be dropped server-side before returning a response.

## Data Model

### Article Sources

Every traceable part of an article receives a stable source ID:

- Heading: `left-heading-5`
- Infobox row: `left-info-8`
- Paragraph: `left-p-12`
- Sentence: `left-s-12-3`

The rendered HTML should include these IDs as DOM attributes so the frontend can scroll and highlight by source ID:

```html
<tr data-source-id="left-info-8">...</tr>
<span data-source-id="left-s-12-3">...</span>
```

### Infobox Attribute

```json
{
  "id": "left-info-8",
  "key": "GDP growth",
  "valueText": "1.5% (2023)",
  "section": "Statistics",
  "source": "infobox",
  "side": "left"
}
```

### Main Text Attribute

```json
{
  "id": "left-text-attr-23",
  "key": "share of global semiconductor production",
  "valueText": "South Korea accounts for ...",
  "source": "main_text",
  "side": "left",
  "paragraphId": "left-p-41",
  "sentenceIds": ["left-s-41-2"]
}
```

### Aligned Attribute

```json
{
  "id": "attr-gdp-growth",
  "label": "GDP growth",
  "leftKey": "GDP growth",
  "rightKey": "GDP growth",
  "leftSourceIds": ["left-info-8"],
  "rightSourceIds": ["right-info-9"],
  "sourceKind": "both",
  "dataType": "Trend",
  "chartType": "line",
  "score": 0.84,
  "visualization": {}
}
```

## Pipeline

### Article Loading

The server parses each English Wikipedia URL, extracts the article title and optional revision, fetches the REST HTML, sanitizes unsupported elements, and produces:

- Renderable article HTML.
- Outline tree from headings.
- Infobox rows.
- Paragraphs and sentence spans.
- Source map from source ID to article side, DOM selector, raw text, and source type.

Non-English Wikipedia URLs should return a clear validation error.

### Task 0: Dual-Source Attribute Pool Construction

Attribute pools must be built from both infoboxes and main text. Main text extraction is a first-class feature, not a fallback or small supplement to infobox extraction.

The server constructs two pools per article:

- `Infobox Attribute Pool`: rule-based extraction of key-value rows from infobox-like tables.
- `Main Text Attribute Pool`: LLM-assisted extraction of comparable attributes from article sentences and paragraphs.

Main text extraction should identify:

- Numeric factual claims.
- Time trends.
- Proportions and compositions.
- Rankings and ordinal facts.
- Categorical differences.
- Geographic facts.
- Descriptive facts that can be represented as key-value attributes.

Every main-text attribute must include paragraph and sentence source IDs. LLM outputs without valid source IDs should be rejected. The MVP may cap the number of main-text attributes per article, but the cap should be based on confidence and traceability rather than whether an attribute overlaps the infobox.

### S1: Comparative Attribute Detection

The server sends both complete attribute pools to the LLM and asks for semantic alignment between attributes. The LLM can match exact keys or semantically equivalent keys across infobox and main text sources. Unmatched attributes are excluded from the ranked comparison table.

The server validates that all returned attribute IDs exist. Invalid matches are discarded.

### S2: Data Type Judgment

The server classifies aligned attribute values into:

- `Numerical`
- `Proportional`
- `Trend`
- `Categorical`
- `Ordinal`
- `Geographical`
- `Text`

LLM classification is allowed, but deterministic rules should handle obvious percentages, numbers, coordinates, rankings, years, and lists.

### S3: Visual Type Judgment

Visual type selection is deterministic and based on the paper's Table 1:

- Numerical: bar for three or fewer values, scatter for more than three.
- Proportional: pie for four or fewer categories, stacked chart for more than four.
- Trend: bar for two or fewer values, line chart for more than two.
- Categorical: text for two or fewer categories, stacked chart for more than two.
- Ordinal: text.
- Geographical: text.
- Text: text.

### S4: Data Format Mapping and Normalization

The server normalizes values into a chart-ready JSON format. Rules should handle:

- Percentages.
- Currency symbols and units.
- Magnitude words such as million, billion, and trillion.
- Year-value pairs.
- Lists of categories and values.
- Plain text.

LLM conversion may be used for complex values, but the server must validate JSON shape and numeric fields before returning data to the frontend.

### Ranking

The server computes difference scores with a trend-first strategy:

- Numerical difference weight: `0.3`
- Trend difference weight: `0.5`
- Text difference weight: `0.2`

MVP scoring may use simplified versions of the paper formulas, but it must preserve the trend-first ranking behavior and be deterministic for the same normalized inputs.

## Frontend Design

The frontend keeps the three-column layout:

- Left article pane.
- Central analytical workspace.
- Right article pane.

The left and right panes receive article HTML, outline data, and source maps from the backend. They no longer hardcode article titles or revisions. The central workspace renders:

- Chat and explanation history.
- Ranked comparison table.
- Attribute-level charts.
- Full chart expansion.
- Merged chart view.

`CompareTable.vue` should consume backend `rankedRows` rather than a fixed `COMPARABLE_FIELDS` list. Rows should display:

- Left chart or text visualization.
- Attribute label.
- Data type.
- Source label: `Infobox`, `Text`, or `Both`.
- Compare action.
- Merge action when chart data supports it.
- Right chart or text visualization.

The existing causal-chain component should be removed from the active UI path.

## Traceable Answers and Highlighting

LLM responses from `/api/analyze-attribute` and `/api/ask` must include structured citations. The frontend renders citation chips below the answer. Interactions:

- Hover citation: temporarily highlight all referenced source IDs.
- Click citation: scroll the relevant article pane to the first referenced source ID and keep the highlight visible for a short period.
- Citations with `side: "both"` highlight both article panes.

This traceability applies to both infobox rows and main-text sentences. A response that only displays citation text without source highlighting does not satisfy the MVP.

## Error Handling

- Invalid URL: return an explanatory validation error.
- Non-English Wikipedia URL: return an explanatory validation error.
- Wikipedia fetch failure: return a retryable error.
- Missing LLM API key: return rule-based session data where possible and warnings for LLM-dependent features.
- LLM JSON parse failure: retry once with a repair prompt, then degrade gracefully with warnings.
- Invalid source IDs in LLM output: drop invalid citations or matches.
- Overlarge article text: cap extraction windows and return a warning.
- Session cache miss: tell the frontend to regenerate the comparison session.

## Testing Strategy

Backend tests should cover:

- URL parsing and validation.
- Wikipedia HTML fixtures for outline extraction.
- Infobox row extraction.
- Paragraph and sentence source ID generation.
- Dual-source attribute pool construction.
- Main-text attributes retaining valid paragraph and sentence source IDs.
- S1 alignment output validation.
- S2 data type classification.
- S3 deterministic chart selection.
- S4 value normalization for percentages, currencies, year series, lists, rankings, and text.
- Trend-first ranking.
- API contract shape for `/api/compare-session`.
- Citation validation for `/api/analyze-attribute` and `/api/ask`.

Frontend verification should cover:

- Loading two English Wikipedia URLs.
- Rendering both article panes.
- Rendering matched outlines.
- Rendering ranked rows from backend data.
- Clicking Compare and receiving a cited answer.
- Hovering and clicking citations to highlight original infobox rows or text sentences.
- Opening full and merged chart views.

## Migration Notes

Known current issues to address during implementation:

- `Div1.vue` and `Div3.vue` hardcode article titles and revision IDs.
- `ArticleOutline.vue` hardcodes matched outline pairs.
- `CompareTable.vue` hardcodes comparable fields and contains country-specific data branches.
- `server.py` hardcodes API keys and stores comparison state in a global variable.
- Root `README.md` and server copy files contain key-like secrets and should be cleaned.
- Duplicate `copy` components should be removed or ignored after the new flow is stable.

## Acceptance Criteria

The MVP is complete when:

- A user can input two English Wikipedia URLs and load a comparison session.
- The central table includes aligned attributes from both infobox and main text sources.
- Attribute rows are ranked and visualized without country-specific hardcoding.
- Clicking an attribute Compare action produces an LLM explanation with structured citations.
- Clicking or hovering citations highlights corresponding original infobox rows or text sentences.
- Outline matching and synchronized navigation work without hardcoded heading pairs.
- Causal-chain UI and automatic why suggestions are absent.
- LLM provider configuration is read from environment variables and no secrets remain in tracked source files.
