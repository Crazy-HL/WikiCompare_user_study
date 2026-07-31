import json

from .defaults import QUESTION_PROMPT_VERSION
from .storage import utc_now_iso


def article_text(article):
    lines = []
    for paragraph in article.get("paragraphs") or []:
        source_id = paragraph.get("id", "")
        text = paragraph.get("text", "")
        if text:
            lines.append(f"[{source_id}] {text}" if source_id else text)
    for field in article.get("infobox") or []:
        source_id = field.get("id", "")
        label = field.get("label", "")
        value = field.get("value", "")
        if label or value:
            lines.append(f"[{source_id}] {label}: {value}" if source_id else f"{label}: {value}")
    return "\n".join(lines)


def build_question_prompt(material, left_article, right_article):
    left_title = material.get("leftTitle") or left_article.get("title") or "左文"
    right_title = material.get("rightTitle") or right_article.get("title") or "右文"
    return f"""你是双文档比较阅读实验的问题设计器。

你的任务是：只根据下面两篇冻结文章，生成5个能够帮助读者理解两篇文章关系的问题，并同时生成研究人员使用的隐藏标准答案。

问题不能为了适配三栏表而生成。三栏表只是参与者寻找答案时可能使用的一种工具。

================ 输入材料 ================

【左侧文章】
标题：{left_title}
内容：
{article_text(left_article)}

【右侧文章】
标题：{right_title}
内容：
{article_text(right_article)}

============================================

## 第一步：建立内部比较内容图谱

不要向参与者展示本步骤内容。先分别识别：
1. 两篇文章各自的主题和主要讨论对象；
2. 两篇文章共同讨论的核心主题；
3. 两篇文章中具有真实比较意义的事实、类别、组成、趋势或文本描述；
4. 两篇文章在重要主题上的关键差异和共同点；
5. 文章明确说明的背景、过程、原因或结果关系；
6. 可以由两篇文章共同验证的具体结论；
7. 不应作为问题依据的边缘事实、孤立字段和无法确定的信息。

## 第二步：为每种类型生成候选问题

### Q1【单维事实比较】
只比较一个与文章核心主题有关的属性、事实或类别，必须需要同时查看左右文章。

### Q2【结构、组成或变化模式比较】
比较同一主题下的多个值、多个类别、多个时间点、组成关系、排名结构或发展阶段。

### Q3【跨属性综合比较】
必须结合至少两个内容上相关的重要属性，答案必须是有限、确定的判断。

### Q4【明确背景、过程或原因理解】
必须使用文章正文明确表达的背景、过程、原因、结果、政策、事件或发展关系。

### Q5【综合结论证据验证】
提供一个与两篇文章核心内容相关的具体综合结论，参与者只能回答“支持”“不支持”或“材料不足”。

## 输出格式

只输出合法 JSON，不输出 Markdown 说明。结构如下：
{{
  "material_id": "{material.get('id', '')}",
  "questions": [
    {{
      "question_id": "Q1",
      "question_type": "单维事实比较",
      "question_text": "给参与者显示的自然语言题目",
      "answer_format": "结构化填写或固定选项",
      "understanding_target": "该题帮助读者理解的文章核心内容",
      "gold_atoms": [
        {{
          "atom_id": "Q1-A1",
          "requirement": "必须回答的事实或关系",
          "canonical_answer": "唯一标准答案",
          "accepted_variants": ["允许的等价表达"],
          "source_ids": ["L-P001", "R-P001"],
          "required_unit": "无或具体单位",
          "required_time_scope": "无或具体年份/时期"
        }}
      ],
      "answer_options": [],
      "unique_answer": true,
      "uses_both_articles": true,
      "primary_evidence_distinct_from_previous": true
    }}
  ]
}}

输出前逐题检查：题干前提真实、同时涉及两篇文章、存在唯一答案、每个评分原子有来源编号、Q1至Q5不重复、Q5清楚区分“不支持”和“材料不足”。"""


def parse_raw_json(raw):
    if isinstance(raw, str):
        cleaned = raw.strip()
        if cleaned.startswith("```"):
            cleaned = cleaned.strip("`")
            cleaned = cleaned.replace("json\n", "", 1).replace("JSON\n", "", 1)
        return json.loads(cleaned)
    return dict(raw)


def normalize_generated_questions(raw, material_id, version):
    parsed = parse_raw_json(raw)
    questions = parsed.get("questions") or []
    ids = [item.get("question_id") for item in questions]
    if ids != ["Q1", "Q2", "Q3", "Q4", "Q5"]:
        raise ValueError("Generated questions must contain Q1-Q5 in order")
    return {
        "material_id": material_id,
        "version": int(version),
        "frozen": False,
        "generated_at": utc_now_iso(),
        "prompt_version": QUESTION_PROMPT_VERSION,
        "questions": questions,
    }
