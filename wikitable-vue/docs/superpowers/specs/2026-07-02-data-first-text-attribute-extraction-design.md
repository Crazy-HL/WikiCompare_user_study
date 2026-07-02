# Data-First Text Attribute Extraction Design

## Goal

Upgrade WikiCompare's main-text attribute extraction so it can find reusable, comparison-ready attributes from article body text, even when articles have weak or missing infoboxes.

The key change is conceptual: the system should not ask "what attributes exist in each article?" and then hope the keys match. It should ask "what evidence in both articles can answer the same comparison question?"

## Current Problem

The current pipeline has three limitations:

1. It extracts text attributes independently per article, then aligns them after the fact.
2. Its rule fallback only covers a small set of broad labels such as `Overview`, `History`, `Applications`, and `Methods`.
3. It does not treat numerical evidence as a first-class signal, so data-rich comparisons can be missed or ranked behind generic text rows.

This creates two bad outcomes:

- Conceptual article pairs can produce sparse or generic rows.
- Data-bearing text facts can be ignored unless they happen to resemble infobox keys.

## Design Principles

1. Do not classify the article pair before extraction.
   Pre-classifying a pair as concept, entity, event, or economy can bias extraction toward a fixed template and cause important article-specific attributes to be missed.

2. Do not use fixed templates as the source of truth.
   Dimensions such as definition, applications, and limitations are useful fallback language, but the system should discover comparison dimensions from the article evidence itself.

3. Prioritize data-bearing evidence.
   Numbers, percentages, dates, rankings, monetary amounts, counts, durations, and proportions should be inspected first because they often produce stronger comparisons and visualizations.

4. Pair before finalizing attributes.
   A text-derived row should enter the three-column table only after the system has evidence that left and right sides answer the same comparison question.

5. Evidence must remain traceable.
   Every extracted item must carry source sentence IDs so hovering or pinning the table row can highlight the exact supporting text.

## Definition Of A Comparable Attribute

A comparable attribute is not simply a fact from one article. It is a paired comparison dimension with evidence from both articles.

It should satisfy these conditions:

1. The left and right evidence answer the same implicit question.
2. The evidence is specific enough to be useful in the table.
3. The row label names the comparison dimension, not merely one side's wording.
4. The value text can be traced to source sentences.
5. If the value contains data, the data has the same semantic role on both sides.

Examples:

```text
Question: What is it used for?
Left evidence: Applications include search engines, recommendation systems, and robotics.
Right evidence: Uses include computer vision, speech recognition, and language processing.
Dimension label: Applications / Uses
```

```text
Question: When did it emerge?
Left evidence: The field was founded as an academic discipline in 1956.
Right evidence: Machine learning grew from pattern recognition in the 1950s.
Dimension label: Historical emergence
```

## What Should Not Become A Row

The pipeline should reject:

1. One-sided facts with no comparable counterpart.
2. Facts whose only relation is that both contain a number.
3. Years that are merely citations, publication dates, or context noise.
4. Isolated names of people, organizations, or places unless both sides use them for the same dimension.
5. Broad summaries with no specific source evidence.
6. Text that duplicates an infobox row without adding evidence or a new subdimension.
7. Rows where one side is a data value and the other side is unrelated prose.

## Proposed Pipeline

### Stage 1: Sentence Preparation

Use parsed article paragraphs and sentences from the existing article loader.

For each sentence, compute lightweight metadata:

- `sentenceId`
- `paragraphId`
- section title when available
- normalized text
- detected numbers, years, percentages, money, ranks, and units
- cue words around detected data
- named terms or noun phrases when cheaply available

This stage is deterministic and does not call the model.

### Stage 2: Data Candidate Detection

Scan both articles for data-bearing sentences.

Data-bearing evidence includes:

- percentages and proportions
- monetary values
- counts and quantities
- rankings and ordinal values
- index scores
- years and periods when they describe origin, launch, discovery, development, or events
- growth, decline, increase, decrease, frequency, and duration

The system should not immediately turn every detected value into a row. It should create candidates for later pairing.

Each data candidate should include:

```json
{
  "side": "left",
  "claimText": "The field was founded as an academic discipline in 1956.",
  "sentenceIds": ["left-s-1-2"],
  "dataItems": [{"value": 1956, "role": "emergence_time"}],
  "semanticCue": "founded as an academic discipline",
  "section": "History"
}
```

### Stage 3: Non-Data Claim Detection

After data candidates, extract concise non-data claims that may still form useful comparisons.

These include:

- definitions
- purposes
- mechanisms
- applications
- components or subtypes
- effects
- limitations
- controversies
- examples

These labels are not templates. They are only weak descriptors for the candidate claim. The final comparison dimension should be generated from paired evidence.

### Stage 4: Cross-Document Pairing

Use a pair-level model call that sees candidates from both articles.

The model should receive:

- left data candidates
- right data candidates
- left non-data candidates
- right non-data candidates
- existing infobox attributes as context to avoid duplicates

The model should return paired comparison dimensions, not independent attributes.

Expected output shape:

```json
{
  "pairs": [
    {
      "dimensionLabel": "Historical emergence",
      "comparisonQuestion": "When did it emerge or become established?",
      "left": {
        "valueText": "founded as an academic discipline in 1956",
        "sentenceIds": ["left-s-1-2"]
      },
      "right": {
        "valueText": "grew from pattern recognition in the 1950s",
        "sentenceIds": ["right-s-1-2"]
      },
      "dataPriority": true,
      "dataRole": "emergence_time",
      "confidence": 0.86
    }
  ]
}
```

### Stage 5: Validation And Filtering

Validate every model-produced pair before adding it to the attribute pools.

Rules:

1. All referenced sentence IDs must exist.
2. Both sides must have non-empty value text.
3. Both sides must answer the same comparison question.
4. If `dataPriority` is true, both sides must contain compatible data roles.
5. The pair must not duplicate an existing infobox row unless it adds related text evidence.
6. The pair confidence must meet a minimum threshold.
7. Similar rows should be merged or the lower-confidence row dropped.

This keeps the LLM creative at the pairing step while keeping final table rows deterministic and auditable.

### Stage 6: Attribute Pool Integration

Represent paired text dimensions as normal attributes so the existing normalization and rendering pipeline can continue to work.

Generated attributes should use stable fields:

```json
{
  "id": "left-attr-paired-text-1",
  "side": "left",
  "key": "Historical emergence",
  "valueText": "founded as an academic discipline in 1956",
  "source": "main_text",
  "sourceIds": ["left-s-1-2"],
  "paragraphId": "left-p-1",
  "confidence": 0.86,
  "dataPriority": true,
  "comparisonQuestion": "When did it emerge or become established?"
}
```

The server can then create alignments directly from pair output instead of relying only on key matching.

### Stage 7: Ranking

Rows extracted from text should rank by comparison value, not simply by source order.

Suggested ranking priority:

1. Paired data attributes with compatible data roles.
2. Paired attributes with structured values or clear category lists.
3. Paired concise text attributes with strong evidence on both sides.
4. Generic fallback dimensions such as overview/history/applications.

Infobox rows should still be included and can rank highly when they have strong numeric or structured values.

## LLM Prompt Requirements

The pair-level prompt should explicitly say:

1. Do not classify the article pair before extraction.
2. Do not fill a fixed template.
3. Discover comparison dimensions from the evidence.
4. Prioritize data-bearing evidence, but only pair data when both sides have the same semantic role.
5. Return only dimensions that have evidence on both sides.
6. Use only provided sentence IDs.
7. Do not invent values.
8. Keep `valueText` short and directly supported by the cited sentence.
9. Return JSON only.

## Fallback Behavior

If the LLM is unavailable:

1. Keep infobox extraction.
2. Run deterministic data candidate pairing for obvious cases:
   - same normalized cue phrase
   - same section title and compatible numeric role
   - same important noun phrase near a number
3. Use broad rule fallback only when no infobox or paired data rows are available.

This keeps the system usable without an API key, but makes the LLM path the preferred route for reusable text comparison.

## Testing Strategy

Tests should cover:

1. Concept articles without infoboxes produce paired dimensions from body text.
2. Data-bearing text facts are preferred over generic overview rows.
3. Numeric facts are not paired when their semantic roles differ.
4. Model output with invalid sentence IDs is rejected.
5. Infobox duplicates are merged as related evidence instead of duplicated rows.
6. Non-Wikipedia-style paragraph input still produces pairs when sentence IDs are present.
7. Rows preserve source IDs so article text highlighting works.

## Success Criteria

The feature is successful when:

1. The AI vs machine learning material pair produces meaningful text-derived rows beyond a generic empty-state fix.
2. Data-bearing body-text facts appear before generic text rows when they are comparable.
3. Switching to non-economy or non-infobox-heavy article pairs still yields useful rows.
4. The table does not fill with one-sided or loosely related facts.
5. Hovering or pinning a text-derived row highlights the exact supporting sentence in both articles.
