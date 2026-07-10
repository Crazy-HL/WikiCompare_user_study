# Three-Column Extraction Validation Fix Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Prevent the three-column comparison table from showing semantically mismatched repeated infobox rows or weak main-text attribute pairs.

**Architecture:** Keep the existing extraction and rendering pipeline, but strengthen validation at two boundaries: infobox alignment and paired main-text conversion. Exact-key alignment must handle repeated labels by matching compatible values instead of letting later right-side rows overwrite earlier ones. Paired text attributes with measurement-like data roles must prove left and right evidence share the same measurement cue before they enter ranked rows.

**Tech Stack:** Python 3.9, pytest, existing Tornado backend services.

## Global Constraints

- Do not revert existing uncommitted work.
- Follow TDD: each production change needs a failing test first.
- Keep fixes scoped to backend extraction/alignment; frontend display code is not the root cause for the confirmed bad rows.
- Prefer deterministic validation over new LLM prompts for correctness.

---

### Task 1: Align Repeated Infobox Keys By Compatible Values

**Files:**
- Modify: `server/tests/test_pipeline.py`
- Modify: `server/services/pipeline.py`

**Interfaces:**
- Consumes: `align_attribute_pools(left_pool: list[dict], right_pool: list[dict]) -> list[dict]`
- Produces: repeated exact-key alignments that choose compatible right attributes and avoid reusing one right row.

- [ ] **Step 1: Write the failing test**

Add a test where `15-64 years` appears twice on both sides: once as age structure percentage and once as sex ratio. The first left percentage row must align to the first right percentage row, not the later sex-ratio row.

- [ ] **Step 2: Run the test and verify it fails**

Run: `python3 -m pytest server/tests/test_pipeline.py::test_align_attribute_pools_matches_repeated_keys_by_value_shape -q`

Expected before fix: the row aligns to the wrong sex-ratio value.

- [ ] **Step 3: Implement minimal alignment fix**

Change `align_attribute_pools()` so `right_by_key` stores a list per normalized key. For each left attribute, choose the first unused right attribute with a compatible value shape. Compatibility rules:

- proportional text with `%` prefers proportional text with `%`
- sex-ratio text containing `male(s)/female` or `male to female` prefers the same shape
- otherwise fall back to the first unused right attribute for that key

- [ ] **Step 4: Run the focused test**

Run: `python3 -m pytest server/tests/test_pipeline.py::test_align_attribute_pools_matches_repeated_keys_by_value_shape -q`

Expected: PASS.

### Task 2: Reject Incompatible Measurement Text Pairs

**Files:**
- Modify: `server/tests/test_text_attribute_pairs.py`
- Modify: `server/services/text_attribute_pairs.py`

**Interfaces:**
- Consumes: `build_paired_text_attributes(left_article, right_article, pair_response, left_infobox_pool, right_infobox_pool)`
- Produces: no attributes/alignments for measurement-like pairs whose left/right cues conflict or are missing.

- [ ] **Step 1: Write the failing tests**

Add tests for:

- `Cases`: left text has confirmed cases, right text only says cases are confirmed in provinces; reject.
- `Population`: left text reports deaths per million population, right text reports seroprevalence people infected; reject.
- `Growth`: left text reports 2010 recovery growth, right text reports annualized fourth-quarter growth; reject unless cue/time shape is compatible.

- [ ] **Step 2: Run tests and verify they fail**

Run: `python3 -m pytest server/tests/test_text_attribute_pairs.py -q`

Expected before fix: at least the new incompatible-pair test accepts a bad pair.

- [ ] **Step 3: Implement minimal validation fix**

In `_validated_pair()`, after pair sides validate and data role is normalized, reject visual data roles when `_measurement_cue(left.valueText)` and `_measurement_cue(right.valueText)` are absent or differ. For the broad `growth` cue, require matching year sets or both sides lacking explicit years.

- [ ] **Step 4: Run focused tests**

Run: `python3 -m pytest server/tests/test_text_attribute_pairs.py -q`

Expected: PASS.

### Task 3: Verify API-Level Material Regressions

**Files:**
- Modify: `server/tests/test_compare_api.py`

**Interfaces:**
- Consumes: API session creation behavior tested through `CompareApiTest`.
- Produces: regression coverage for ranked rows that previously reached the three-column table.

- [ ] **Step 1: Add API regression tests**

Cover:

- repeated `15-64 years` and `65 and over` demographic rows align percentage-to-percentage
- LLM-produced incompatible `Cases` pair falls back to valid infobox rows instead of entering ranked main-text rows

- [ ] **Step 2: Run API focused tests**

Run: `python3 -m pytest server/tests/test_compare_api.py -q`

Expected: PASS after Tasks 1 and 2.

### Task 4: Final Verification

**Files:**
- No production file changes.

**Interfaces:**
- Consumes: all previous tasks.
- Produces: verified backend/client baseline.

- [ ] **Step 1: Run backend tests**

Run: `python3 -m pytest server/tests -q`

Expected: all tests pass.

- [ ] **Step 2: Run client tests**

Run: `for f in client/tests/*.cjs; do node "$f" || exit 1; done`

Expected: all tests pass.
