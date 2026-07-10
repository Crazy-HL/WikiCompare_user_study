# Real Web Material Display Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Polish real public-web material display and make Microsoft FY25/FY24 headers distinguishable.

**Architecture:** Preserve the existing compare-session data flow. Add optional client-provided display titles to the compare request, persist page source kind from URL parsing into parsed articles, and branch article content styling by source kind.

**Tech Stack:** Vue 3 single-file components, CommonJS client test scripts, Tornado/Python server tests with pytest, BeautifulSoup article parsing.

## Global Constraints

- Keep the material list to exactly two built-in pairs.
- Do not reintroduce synthetic `demo://` materials.
- Do not change the extraction/ranking algorithm in this UI pass.
- Use TDD: failing tests first, then minimal implementation.

---

### Task 1: Preserve Preset Titles in Session Requests

**Files:**
- Modify: `client/src/components/UrlCompareForm.vue`
- Modify: `client/src/js/sessionStore.js`
- Test: `client/tests/urlCompareFormPolish.test.cjs`
- Test: `client/tests/sessionHistory.test.cjs`

**Steps:**
- [ ] Add failing client tests that selecting Microsoft material sends `leftTitle: "Microsoft FY25 Q4 earnings"` and `rightTitle: "Microsoft FY24 Q4 earnings"`.
- [ ] Add optional title parameters to `store.loadSession`.
- [ ] Pass preset titles from `selectMaterial`.
- [ ] Verify client tests pass.

### Task 2: Apply Display Titles and Source Kind on Server

**Files:**
- Modify: `server/server.py`
- Modify: `server/services/article_loader.py`
- Test: `server/tests/test_compare_api.py`
- Test: `server/tests/test_article_loader.py`

**Steps:**
- [ ] Add failing server tests for public URL `sourceKind: "web"` and title overrides.
- [ ] Carry `source_kind` from parsed URL into `parse_article_html`.
- [ ] Accept optional `leftTitle/rightTitle` in compare-session POST payload.
- [ ] Verify targeted pytest tests pass.

### Task 3: Web Source Reading Style

**Files:**
- Modify: `client/src/components/compoents_base/ParentComponent.vue`
- Modify: `client/src/components/compoents_base/WikipediaContent.vue`
- Modify: `client/src/components/compoents_base/CompareTable.vue`
- Test: `client/tests/sourceCopy.test.cjs`

**Steps:**
- [ ] Add failing text tests for `source-web` class and responsive title/header CSS hooks.
- [ ] Pass `article.sourceKind` into `WikipediaContent`.
- [ ] Add web-specific content CSS and responsive table header/title CSS.
- [ ] Verify all client tests pass.

### Task 4: Final Verification

**Files:**
- No new files.

**Steps:**
- [ ] Run all client `.cjs` tests.
- [ ] Run `PYTHONPATH=server python3 -m pytest server/tests -q`.
- [ ] Run a real Microsoft compare-session diagnostic and confirm headers/source metadata and main-text chart rows.
