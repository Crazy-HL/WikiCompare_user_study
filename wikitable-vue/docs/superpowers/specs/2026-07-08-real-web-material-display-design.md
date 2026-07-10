# Real Web Material Display Design

## Goal

Make the non-Wikipedia Microsoft earnings material look polished in the existing three-column workspace and make the table headers distinguish FY25 Q4 from FY24 Q4.

## Requirements

- Keep exactly two built-in material pairs: South Korea vs Japan, and Microsoft FY25 Q4 vs FY24 Q4.
- Use the preset material titles in the compare session when a user selects a preset, so the table header shows year/fiscal-year differences.
- Preserve the existing Wikipedia-like visual density, but use a cleaner reading style for generic public web pages.
- Adapt article titles and source content to narrow and medium workspace widths without overflowing the three-column layout.
- Do not change the attribute extraction algorithm in this pass.

## Design

The client will send optional display titles with compare-session requests. The server will accept those titles, use them as article titles after parsing each source page, and include a `sourceKind` field on each parsed article (`wikipedia` or `web`). The compare table and article panes will continue reading titles from `session.articles`.

The article pane will pass `sourceKind` into `WikipediaContent`. The component will keep the existing base styling for Wikipedia pages and add a `source-web` variant for official/public web pages: constrained readable media, tighter headings, hidden navigation/footer chrome where available, and responsive padding/table/image behavior.

## Testing

- Unit-test material preset titles and compare-session request payloads.
- Unit-test server title override and `sourceKind` metadata for public web URLs.
- Unit-test frontend copy/style hooks so generic web pages receive a source-specific class and responsive title/header CSS remains present.
