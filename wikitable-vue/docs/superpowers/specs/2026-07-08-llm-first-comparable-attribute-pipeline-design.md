# LLM-First Comparable Attribute Pipeline Design

## Goal

Build a comparison pipeline where both infobox and main-text content are interpreted by large language models through separate, source-appropriate workflows, then merged into one scored candidate pool for the three-column table.

The system should emphasize chartable comparable attributes, but it should also keep high-quality non-chartable text attributes when they add real comparison value.

## Current Problem

The current pipeline has improved main-text extraction by sending full cleaned body text to the model and by validating model-provided structured values. However, the architecture still has three important issues:

- Infobox content is mostly handled as structured rows rather than as an LLM-aligned comparison source.
- Source type can influence ordering too strongly; final ordering should follow the product scoring model, not a hard-coded source hierarchy.
- Main-text LLM extraction still needs a more deliberate discovery and cleaning process so it finds comparable dimensions before pairing and visualizing them.

## Design Principles

- Infobox and main text are different evidence types and need different prompts.
- All extracted attributes must become the same internal candidate shape before ranking.
- LLMs discover and clean comparable attributes; deterministic code validates evidence and renders charts.
- Scores, not source buckets, decide final rank.
- Chartable attributes are especially valuable, but unsupported or mismatched chart data must be rejected or downgraded.
- Duplicate dimensions from multiple sources should be merged or linked as related evidence instead of producing redundant rows.

## Source-Specific Extraction

### Infobox LLM Flow

Input:

- Left and right infobox rows with `key`, `valueText`, `structuredValues`, and `sourceId`.
- Article titles and light article context.

Prompt purpose:

- Align semantically equivalent infobox fields, such as `Revenue` and `Total revenue`.
- Split useful multi-value fields, such as demographics, age groups, industries, or market composition.
- Clean values into chartable structured data where possible.
- Mark `dataRole`, `dataType`, confidence, and comparison rationale.
- Preserve source IDs for each supporting infobox row.

The infobox prompt should be explicit that infobox is structured key-value evidence. The model should not invent attributes outside the provided rows.

### Main-Text LLM Flow

Input:

- Full cleaned main-text body for both articles.
- Paragraph IDs and sentence IDs.
- Heading context where available.
- Candidate hints from rule extraction, used only as hints.

Main-text extraction should be split into two conceptual stages:

1. Discovery
   - Identify comparison-worthy attributes independently from each article body.
   - Prefer chartable measurements from ordinary prose.
   - Also capture important text attributes such as policy, applications, technology mix, or business model.
   - Do not use a fixed template.

2. Pairing and cleaning
   - Pair left and right discovered attributes by semantic equivalence.
   - Clean labels and `valueText`.
   - Output structured `values` for charts.
   - Provide evidence sentence IDs and confidence.

The implementation can do these as one API call initially if needed, but the prompt and response schema should reflect both stages. A later implementation can split them into two calls without changing downstream candidate handling.

### Body Table Flow

Body tables can continue through deterministic extraction because yearly series tables are already structured. The table pipeline should still produce the same candidate shape as LLM outputs.

Later, model-assisted table header alignment can be added for ambiguous table columns, but it is not required for the first implementation of this design.

## Unified Candidate Shape

All sources should normalize into a common candidate structure:

```json
{
  "label": "Operating margin",
  "sourceKind": "infobox | main_text | body_table",
  "leftSourceIds": ["left-s-1-1"],
  "rightSourceIds": ["right-s-1-1"],
  "leftValueText": "operating margin in 2024",
  "rightValueText": "operating margin in 2024",
  "dataRole": "proportion",
  "dataType": "Proportional",
  "chartType": "pie",
  "values": {
    "left": [{"value": 18.4, "year": 2024, "rawText": "18.4%", "confidence": 0.96}],
    "right": [{"value": 4.1, "year": 2024, "rawText": "4.1%", "confidence": 0.96}]
  },
  "modelConfidence": 0.93,
  "evidenceQuality": 0.0,
  "comparabilityScore": 0.0,
  "visualizationScore": 0.0,
  "finalScore": 0.0
}
```

The exact wire shape can follow existing row fields, but internally the ranking step should receive equivalent information from every source.

## Validation

Validation applies to infobox, main text, and body table candidates.

Required checks:

- Every source ID exists in `sourceMap`.
- Evidence source type matches the candidate source type.
- `rawText` appears in the original cited evidence.
- Structured numeric `value` matches the number in `rawText`, including scaled forms such as `7.4 million` to `7400000`.
- Structured `year` appears in the original cited evidence, not just model-generated `valueText`.
- Left and right data roles are compatible.
- Units and years are compatible enough for the selected chart type.
- Standalone dates, founding dates, release dates, and temporal metadata are filtered or heavily penalized unless the user explicitly asks for timeline comparison.
- Text attributes without chartable values may pass only if they have high semantic comparison value.

## Scoring And Sorting

Final row order must be determined by score, not by hard-coded source priority.

Recommended score components:

```text
finalScore =
  comparabilityScore
+ visualizationScore
+ evidenceQuality
+ modelConfidence
+ userIntentBoost
+ sourceReliabilityBonus
- noisePenalty
- duplicatePenalty
```

Component meanings:

- `comparabilityScore`: whether left and right values truly measure the same dimension.
- `visualizationScore`: whether the row can produce a meaningful chart.
- `evidenceQuality`: source IDs are direct, values are traceable, and values are not inferred too loosely.
- `modelConfidence`: model-provided confidence after validation.
- `userIntentBoost`: boosts chartable prose-derived attributes because the current workflow goal emphasizes this ability.
- `sourceReliabilityBonus`: infobox and well-structured tables can earn reliability points, but this does not override the final score.
- `noisePenalty`: dates, metadata, weak generic rows, and low-value text are penalized.
- `duplicatePenalty`: repeated dimensions are merged or penalized.

This means a strong infobox chart can rank above a weak main-text chart, and a strong prose-derived chart can rank above an infobox row.

## Duplicate Handling

When the same dimension appears in multiple sources:

- Keep the candidate with the highest final score as the primary row.
- Attach other source IDs as related evidence where possible.
- Prefer direct chart evidence over vague text.
- Prefer validated structured values over inferred values.
- Do not show duplicate rows with the same label unless they represent genuinely different sub-dimensions.

## Click And Evidence Behavior

Rows should retain all supporting source IDs.

Click behavior should use evidence priority within the selected row:

- If the row's primary evidence is infobox, jump to infobox.
- If the row's primary evidence is main text, jump to the cited sentence.
- If duplicate evidence exists, expose related evidence without changing the primary jump target unexpectedly.

This avoids using source priority for ranking while still making click behavior predictable.

## Testing Strategy

Add tests in this order:

1. Infobox LLM extraction
   - Model aligns `Revenue` and `Total revenue`.
   - Model splits a multi-value infobox field into chartable values.
   - Unsupported or hallucinated infobox values are rejected.

2. Main-text discovery and pairing
   - Model discovers a chartable prose metric not present in candidate hints.
   - Model separates multiple metrics from one paragraph.
   - Model returns a valuable text attribute that ranks below chartable rows.

3. Unified scoring
   - A strong infobox chart can outrank a weak main-text text row.
   - A strong main-text prose chart can outrank a weaker infobox row.
   - Final order follows `finalScore`.

4. Duplicate merging
   - Same dimension from infobox and main text produces one row with related evidence.

5. Regression
   - Dates and founding years do not become chart rows.
   - Current Solar body-table trend rows still render.
   - Current paragraph structured-value tests still pass.

## Implementation Boundaries

Initial implementation should focus on backend extraction, validation, and ranking. UI changes should be limited to displaying any new fields that already fit the current row model.

Do not add non-Wikipedia support in this phase.

Do not remove deterministic fallback extraction. If LLM extraction is unavailable or invalid, the system should still return useful rule-based comparisons.

## Open Decisions

- Exact weight values for `finalScore` need to be chosen during implementation and verified against existing material presets.
- Whether main-text discovery and pairing are one model call or two can be decided pragmatically; the schema should keep the distinction clear.
- Whether infobox LLM extraction replaces or augments current infobox row alignment should be validated with tests. The recommended first version is augmentation with deterministic fallback.
