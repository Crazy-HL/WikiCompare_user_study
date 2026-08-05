# Full Material Generation Prompts Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make all experiment generation prompts include complete infobox and complete body content for both materials.

**Architecture:** Reuse `question_generation.py` as the shared material prompt renderer and import it from `static_table_generation.py`. Existing admin prompt persistence remains unchanged; it will store the improved prompts automatically after regeneration.

**Tech Stack:** Python server modules, pytest API/unit tests, Vue client unchanged except prior localized errors remain.

## Global Constraints
- No silent truncation of experiment prompt material.
- Infobox and body must be visibly separate sections.
- Static table generation must not use compact article snippets.
- Participant API must not expose generation prompts.

---

### Task 1: Full Material Prompt Renderer

**Files:**
- Modify: `wikitable-vue-experiment/server/experiment/question_generation.py`
- Test: `wikitable-vue-experiment/server/tests/test_question_generation.py`

**Interfaces:**
- Produces: `article_text(article, max_chars=None)` returns complete material text unless a caller explicitly passes a positive limit.
- Produces: `build_question_prompt(material, left_article, right_article, max_article_chars=None)` uses full materials by default.

- [ ] Write tests proving full infobox/body content appears and no truncation notice appears by default.
- [ ] Run targeted pytest and confirm failure under old limits.
- [ ] Change prompt renderer to explicit `【Infobox】` and `【正文】` sections and default no truncation.
- [ ] Run targeted pytest and confirm pass.

### Task 2: Full Static Table Prompt Input

**Files:**
- Modify: `wikitable-vue-experiment/server/experiment/static_table_generation.py`
- Test: `wikitable-vue-experiment/server/tests/test_question_generation.py`

**Interfaces:**
- Consumes: `article_text(article, max_chars=None)` from Task 1.
- Produces: `build_static_table_prompt(..., max_article_chars=None)` and `generate_static_table_from_material()` with full material input.

- [ ] Write tests proving static-table prompt includes late body text and full infobox by default.
- [ ] Run targeted pytest and confirm failure under compact limits.
- [ ] Remove compact character limit use from static table generation.
- [ ] Update static table instructions to say full infobox plus full body are used.
- [ ] Run targeted pytest and confirm pass.

### Task 3: Verify and Publish

**Files:**
- Commit changed server tests/code and docs.

- [ ] Run `python3 -m pytest tests -q` in server.
- [ ] Run `npm run build` in client because deployed bundle should still compile.
- [ ] Run `git diff --check`.
- [ ] Commit and push to `user-study HEAD:main`.
