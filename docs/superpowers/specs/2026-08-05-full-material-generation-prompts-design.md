# Full Material Generation Prompts Design

## Goal
Question/answer generation and ChatGPT static three-column table generation must use the complete article body plus the complete article infobox for both materials, and admin prompt records must show that full input structure.

## Requirements
- Do not silently truncate article content for experiment generation prompts.
- Include infobox and body as separate, explicit sections for the left and right articles.
- Treat infobox and body as equally valid evidence in prompt instructions.
- Use the same complete-material input policy for question/hidden-answer generation and ChatGPT static table generation.
- If a future material exceeds model context, fail loudly for the administrator instead of generating from hidden truncated content.
- Keep participant endpoints redacted: prompts and hidden answers remain admin-only.

## Design
Create one shared article prompt renderer in `server/experiment/question_generation.py` that outputs title, full infobox fields, and full body paragraphs with source ids. Use it from both question and static-table prompt builders. Remove the compact prompt path from static-table generation. Strengthen system/user prompts so they explicitly say complete infobox and complete body are the only evidence base, and no truncation is allowed.
