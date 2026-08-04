import json

from services.config import get_llm_config
from services.llm_client import LLMClient

from .question_generation import (
    COMPACT_ARTICLE_PROMPT_CHARS,
    MAX_ARTICLE_PROMPT_CHARS,
    article_text,
    load_material_articles,
)

STATIC_TABLE_GENERATION_SYSTEM_PROMPT = "You generate static three-column comparison tables for a reading experiment. Return JSON only."


def build_static_table_prompt(material, left_article, right_article, max_article_chars=MAX_ARTICLE_PROMPT_CHARS):
    left_title = material.get("leftTitle") or left_article.get("title") or "左文"
    right_title = material.get("rightTitle") or right_article.get("title") or "右文"
    return f"""你是一个实验条件中的 ChatGPT 表格生成器。

你的任务：只根据下面两篇冻结材料，生成一个给参与者阅读时使用的静态三栏比较表。

这个表格代表 ChatGPT 条件下系统根据材料真实输出给参与者看的比较表。请避免主观推断，只使用材料中明确给出的信息。

================ 输入材料 ================

【左侧文章】
标题：{left_title}
内容：
{article_text(left_article, max_article_chars)}

【右侧文章】
标题：{right_title}
内容：
{article_text(right_article, max_article_chars)}

============================================

输出要求：
1. 生成 8-14 行，覆盖两篇材料中最有比较意义的核心维度。
2. 表格必须是三栏：左侧、比较项、右侧。
3. 每行的比较项 label 应具体、清楚，不要使用“其他”等笼统标签。
4. 左右两侧必须分别对应输入的左侧文章和右侧文章。
5. 如果某一侧材料没有明确给出该信息，写“材料未明确说明”。
6. 不要编造材料中没有的信息。
7. 只输出合法 JSON，不输出 Markdown 说明。

JSON 结构：
{{
  "rows": [
    {{
      "id": "R1",
      "label": "比较项名称",
      "left": {{ "value": "左侧文章中的对应信息" }},
      "right": {{ "value": "右侧文章中的对应信息" }}
    }}
  ]
}}
"""


def normalize_static_table(raw):
    if isinstance(raw, str):
        parsed = json.loads(raw)
    else:
        parsed = raw
    rows = parsed.get("rows") if isinstance(parsed, dict) else parsed
    if not isinstance(rows, list) or not rows:
        raise ValueError("Static table generation must return a non-empty rows list")
    normalized_rows = []
    for index, row in enumerate(rows, start=1):
        if not isinstance(row, dict):
            raise ValueError(f"Static table row {index} must be an object")
        normalized_rows.append(_normalize_static_row(row, index))
    return {"rows": normalized_rows}


def generate_static_table_from_material(material, llm_client=None):
    config = get_llm_config()
    client = llm_client or (LLMClient(config) if config.enabled else None)
    if client is None:
        raise RuntimeError("OPENAI_API_KEY is required to auto-generate ChatGPT static table")
    left_article, right_article = load_material_articles(material)
    prompt = build_static_table_prompt(
        material,
        left_article,
        right_article,
        max_article_chars=COMPACT_ARTICLE_PROMPT_CHARS,
    )
    raw_table = client.chat_json([
        {"role": "system", "content": STATIC_TABLE_GENERATION_SYSTEM_PROMPT},
        {"role": "user", "content": prompt},
    ])
    return normalize_static_table(raw_table)


def _normalize_static_row(row, index):
    return {
        **row,
        "id": str(row.get("id") or f"R{index}"),
        "label": str(row.get("label") or f"比较项 {index}"),
        "left": _normalize_side(row.get("left") or row.get("leftValue") or row.get("left_value")),
        "right": _normalize_side(row.get("right") or row.get("rightValue") or row.get("right_value")),
    }


def _normalize_side(value):
    if isinstance(value, dict):
        if not any(key in value for key in ("value", "text", "raw", "values", "display", "rawText")):
            return {"value": json.dumps(value, ensure_ascii=False)}
        return value
    if value is None or value == "":
        return {"value": "材料未明确说明"}
    return {"value": str(value)}
