# Comparison Table, Charts, and Text Evidence Design

## Goal

Improve WikiCompare so the three-column table, URL controls, merged charts, enlarged charts, main-text attributes, and hover highlighting feel coherent, simple, and comparison-first.

The central interaction remains unchanged: left article, middle comparison table, right article, plus chart modals and LLM panel.

## Current Problems

1. The table uses multiple display styles at once: compact chart rows, text cards, structured chips, and raw chart previews. This makes left and right cells visually inconsistent.
2. Some rows show labels on one side but not the other, which weakens direct comparison.
3. Text length changes card height and vertical centering, making rows look uneven.
4. The URL area looks like a developer toolbar in both collapsed and expanded states.
5. Merged charts sometimes change chart semantics. For example, a line-vs-line row should merge into a line chart, not a bar chart.
6. Merged and enlarged chart modals show too many repeated details. They should emphasize axes, legend, values, and direct comparison.
7. Main-text attributes are present in the pipeline but still too limited and easy to miss because exact key alignment favors infobox rows.
8. Hovering table attributes highlights the attribute source, but not enough related explanatory sentences from article body text.

## Design Principles

1. Keep the table lightweight.
   Table cells should be for scanning, not full analysis.

2. Use one visual grammar.
   Multi-value rows display as simple `label: value` lines everywhere in the table.

3. Preserve comparison semantics.
   Merged charts should keep the same chart family as the source row when possible.

4. Put explanation in the right layer.
   Raw source text and full chart detail belong in tooltips, modals, or highlighted source text, not dense table cells.

5. Evidence must travel with the row.
   Every aligned attribute row should carry both primary source IDs and related sentence IDs.

## Three-Column Table Design

### Display Format

All multi-value table cells use a simple inline list:

```text
nominal: $1.87 trillion
PPP: $3.36 trillion
```

No two-line card hierarchy is used. A label and value stay on the same line unless the line is too long, in which case it wraps naturally.

Single-value rows do not add a fake label. They display only the value:

```text
$542.4 billion
```

### Label Alignment

For each row, build a shared display plan before rendering either side:

1. Collect left labels and right labels.
2. Normalize labels by lowercase, whitespace, and punctuation.
3. Shared labels appear first.
4. Shared labels use the same order on both sides.
5. Shared labels use the same color token on both sides.
6. Left-only labels appear after shared labels on the left.
7. Right-only labels appear after shared labels on the right.
8. Unlabeled multi-value items only use `1:`, `2:`, etc. when both sides are unlabeled multi-value lists.

Example for `FDI stock`:

Left:

```text
Inward: $230.6 billion
Abroad: $344.7 billion
```

Right:

```text
Inward: $25 billion
Outward: $147 billion
```

`Inward` shares the same color on both sides. `Abroad` and `Outward` use muted unmatched colors.

### Visual Style

Cells use a flat list rather than nested cards:

- left accent: quiet blue
- right accent: quiet green
- shared label color: same hue on both sides
- unmatched labels: low-saturation neutral
- consistent row padding
- top-aligned content inside value cells
- no strong center alignment for variable-length text

This avoids the current uneven centered look.

## URL Control Design

### Collapsed State

The collapsed URL bar becomes a compact session strip:

```text
WikiCompare   Economy of South Korea  ↔  Economy of Japan        Change
```

It should feel like a paper-system control surface:

- 40-44px height
- subtle bottom border
- title and compared article names aligned on one baseline
- only one clear action: `Change`
- no heavy shadows
- no visual competition with article/table content

### Expanded State

The expanded URL panel becomes a quiet form panel:

- two URL fields in one row on desktop
- labels are small but readable
- actions are grouped on the right: `Compare`, `Regenerate`, `Collapse`
- recent comparisons appear as compact chips
- panel uses a restrained background and border
- no tall empty space
- on smaller widths, fields stack cleanly

The expanded panel should not feel like a landing page or marketing block.

## Merged Chart Design

Merged chart type follows the source row chart type:

| Source row visualization | Merged visualization |
| --- | --- |
| `line-chart` | two-series line chart |
| `bar-chart` | grouped bar chart |
| `stacked-chart` | grouped proportional/stacked comparison |
| `pie-chart` | grouped bar chart when comparing two articles, because two pies are harder to compare directly |
| `text-only` | aligned text comparison list |

For line rows, the merged chart must remain a line chart when both sides have year-like x values.

For multi-label numerical rows such as GDP or FDI, the merged chart uses labels as x-axis categories:

```text
Inward    Abroad    Outward
```

If one side lacks a category, show a gap rather than inventing a value.

### Merged Chart Visual Style

Merged chart modals should be clean:

- chart title
- legend
- x/y axes
- tooltip
- direct value labels only when they do not clutter
- no large summary cards above the chart
- no raw source cards below by default
- no source detail disclosure in this iteration

The chart area should carry the comparison, not the surrounding chrome.

## Enlarged Single Chart Design

Clicking a table-side chart opens a simplified chart modal.

The modal should show:

- title
- chart
- axes and legend when applicable
- concise tooltip
- optional small source line, not a large raw-values block

For multi-value rows, x-axis labels should be comparison dimensions such as `Inward`, `Abroad`, `nominal`, `PPP`, not only years. Year can appear in tooltip or subtitle.

For text-only rows, the modal uses the same aligned `label: value` list style as the table, with more room.

## Main-Text Attribute Extraction Design

The pipeline should continue to use infobox extraction, but main text must become a first-class source.

### Extraction

Use LLM main-text extraction with stricter instructions:

1. Extract comparison-ready attributes from article body paragraphs, not just infobox-like fields.
2. Prefer facts with values, dates, quantities, named categories, rankings, sectors, causes, or outcomes.
3. Return paragraph and sentence IDs for every extracted attribute.
4. Include a normalized key and a display key.
5. Include structured values when the sentence contains multiple comparable dimensions.
6. Avoid duplicates with existing infobox attributes.

### Deduplication

Deduplicate at two levels:

1. Within one article:
   - same normalized key
   - highly similar value text
   - overlapping source sentence IDs

2. Across infobox and text:
   - if text repeats an infobox value, merge its sentence IDs into the infobox row as related evidence
   - if text adds different context or a new dimension, keep it as a separate text-derived attribute

### Alignment

Alignment should not rely only on exact lowercase keys.

Use this order:

1. exact normalized key
2. alias/synonym match
3. label overlap for structured values
4. LLM alignment for text-derived attributes when available
5. conservative fallback: do not align

This makes non-Wikipedia and body-text comparisons more reusable.

## Hover Highlight Design

Each ranked row should expose:

```json
{
  "leftSourceIds": ["left-info-4"],
  "rightSourceIds": ["right-info-4"],
  "leftRelatedSourceIds": ["left-s-2-1", "left-s-3-2"],
  "rightRelatedSourceIds": ["right-s-2-1"]
}
```

Hover behavior:

1. Hover left value cell highlights left primary source and related text evidence.
2. Hover right value cell highlights right primary source and related text evidence.
3. Hover middle attribute cell highlights both sides and reveals the first primary source.
4. This iteration keeps hover behavior only, plus the existing citation pin behavior where it already exists.

Highlight style:

- primary source: stronger warm highlight
- related sentence/paragraph: softer highlight
- reveal scroll only when triggered from middle-cell hover/click, not every side hover

## Testing Plan

### Unit Tests

Add or update tests for:

1. table display plan:
   - shared labels sorted consistently
   - shared labels share color token
   - unmatched labels are kept after shared labels
   - single-value rows do not receive fake labels

2. merged chart mode:
   - line source remains line merged chart
   - bar source remains grouped bar
   - pie source converts to grouped bar only for comparison
   - stacked source remains proportional comparison

3. text extraction:
   - text attributes are included when LLM returns valid sentence IDs
   - duplicate text attributes merge related source IDs into existing infobox row
   - invalid sentence IDs are rejected

4. highlight IDs:
   - ranked rows include related source IDs
   - highlight functions receive primary plus related IDs

### Browser Verification

Use browser checks for:

1. URL collapsed state
2. URL expanded state
3. three-column table after loading Korea vs Japan
4. merged chart for FDI/GDP
5. merged chart for a line/trend row
6. enlarged chart for FDI/GDP
7. hover highlight on infobox and related body text

The iteration is complete only when screenshots show consistent formatting and the DOM audit confirms no mixed display styles for comparable rows.
