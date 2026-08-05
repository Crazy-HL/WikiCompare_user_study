import json
import re
from pathlib import Path
from types import SimpleNamespace
from urllib.parse import urlparse

import requests

from services.article_loader import fetch_article_html, parse_article_html
from services.config import get_llm_config
from services.llm_client import LLMClient
from services.wiki_url import WikiUrlError, parse_english_wikipedia_url

from .defaults import QUESTION_PROMPT_VERSION
from .storage import utc_now_iso


MAX_ARTICLE_PROMPT_CHARS = None
COMPACT_ARTICLE_PROMPT_CHARS = 1800
QUESTION_GENERATION_SYSTEM_PROMPT = "You generate bilingual dual-document comparison-reading experiment questions from complete article infoboxes and complete article bodies. Follow the provided study-design prompt exactly, use only supplied source IDs, and return valid JSON only."
QUESTION_VALIDATION_SYSTEM_PROMPT = "You are an independent reviewer for dual-document comparison-reading experiment questions. Use only the supplied materials, questions, and gold answers; return valid JSON only."
ANSWER_PROMPT_NOTE = "当前系统按照《WikiCompare实验设计.docx》的提示词 2，在同一次模型请求中共同生成参与者 Q1-Q5 和管理员隐藏标准答案；没有单独的第二次答案生成 prompt。"
MATERIAL_SNAPSHOT_DIR = Path(__file__).resolve().parent / "material_snapshots"


def article_text(article, max_chars=MAX_ARTICLE_PROMPT_CHARS):
    sections = []

    infobox_lines = []
    for field in article.get("infobox") or []:
        source_id = field.get("id", "")
        label = field.get("label") or field.get("key") or ""
        value = field.get("value") or field.get("valueText") or ""
        if label or value:
            infobox_lines.append(f"[{source_id}] {label}: {value}" if source_id else f"{label}: {value}")
    sections.append("【Infobox】")
    sections.extend(infobox_lines or ["（无 infobox 或未提取到 infobox 字段）"])

    body_lines = []
    for paragraph in article.get("paragraphs") or []:
        source_id = paragraph.get("id", "")
        text = paragraph.get("text", "")
        if text:
            body_lines.append(f"[{source_id}] {text}" if source_id else text)
    sections.append("")
    sections.append("【正文】")
    sections.extend(body_lines or ["（未提取到正文段落）"])

    return _cap_article_lines(sections, max_chars)


def _cap_article_lines(lines, max_chars):
    if not max_chars or max_chars <= 0:
        return "\n".join(lines)

    kept = []
    used = 0
    truncated = False
    notice = "[系统提示] 内容已截断：请只根据已显示的带来源编号片段生成题目。"
    notice_budget = len(notice) + 1

    for line in lines:
        separator = 1 if kept else 0
        projected = used + separator + len(line)
        if projected + notice_budget <= max_chars:
            kept.append(line)
            used = projected
            continue

        remaining = max_chars - used - separator - notice_budget
        if remaining > 120:
            kept.append(line[:remaining].rstrip() + "…")
        truncated = True
        break

    if truncated or len(kept) < len(lines):
        kept.append(notice)
    return "\n".join(kept)


def build_question_prompt(material, left_article, right_article, max_article_chars=MAX_ARTICLE_PROMPT_CHARS):
    left_title = material.get("leftTitle") or left_article.get("title") or "左文"
    right_title = material.get("rightTitle") or right_article.get("title") or "右文"
    material_id = material.get("id", "")
    return f"""提示词 2：生成五个双文档比较问题

你是双文档比较阅读实验的问题设计器。

本 prompt 以《WikiCompare实验设计.docx》为唯一实验设计依据。你的任务是：只根据下面两篇冻结文章的完整 infobox 和完整正文，生成5个能够帮助读者理解两篇文章关系的问题，并同时生成研究人员使用的隐藏标准答案。

问题不能为了适配三栏表而生成。三栏表只是参与者寻找答案时可能使用的一种工具。生成题目时不得输入、引用或假设 WikiCompare 表格、ChatGPT 静态三栏表、可视化状态、系统高亮或界面位置。

输入材料中的 infobox 和正文具有同等证据地位。题目、标准答案和来源编号都必须基于下方完整输入材料，不允许使用网页搜索、外部工具、连接器、模型记忆、常识补全或其他会话内容。材料没有提供或无法确定时，必须写“材料不足”，不得把推测写成文章事实。

================ 输入材料 ================

【左侧文章】
标题：{left_title}
完整材料（完整 infobox + 完整正文）：
{article_text(left_article, max_article_chars)}

【右侧文章】
标题：{right_title}
完整材料（完整 infobox + 完整正文）：
{article_text(right_article, max_article_chars)}

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

问题应优先覆盖文章标题、导言、主要章节、infobox 核心内容和正文反复讨论的主题。不得仅因为某个数字容易提取就选择该数字。

## 第二步：实验设计文档中的 Q1-Q5 固定题型

请严格按以下五类题生成。Q1-Q5 的顺序、题型和主要理解目标不可改变。每种类型先在内部生成至少2个候选问题，然后按第三步标准选择最终题；候选问题不要输出。

### Q1【单维事实比较】
定义：Q1 是要求参与者比较两篇文章中同一个明确属性、事实、类别或数值的题目。它考察参与者能否在两篇文章中定位同一维度的信息，并形成一个简单、确定的比较判断。
必须满足：
- 只围绕一个比较维度；
- 左右两篇文章都必须涉及该维度；
- 答案必须包含左侧事实、右侧事实以及两者之间的明确比较关系；
- 答案必须唯一，并能由材料中的真实来源编号直接支持。
禁止生成：
- 只问一篇文章的信息；
- 同时比较多个不相关属性；
- 问“哪个更重要”“哪个更好”；
- 需要外部知识才能判断；
- 只因为某个数字容易提取就生成题目。
合格题目特征：在同一属性上，左文和右文分别是什么，二者有什么明确差异。

### Q2【结构、组成或变化模式比较】
定义：Q2 是要求参与者比较两篇文章中某一主题内部的结构、组成、类别、阶段、排名、分布或变化模式的题目。它不是比较一个单独事实，而是比较一个由多个元素组成的模式。
必须满足：
- 至少比较同一主题下的多个值、多个类别、多个时间点、组成关系、排名结构或发展阶段之一；
- 答案必须描述左右两侧各自的结构或模式，并指出二者差异；
- 如果材料没有时间序列，不得强行生成趋势题，应改用组成、类别结构、排名或阶段模式；
- 标准答案必须避免“大致”“总体感觉”“可能”等模糊表达。
禁止生成：
- 只比较一个静态值；
- 没有时间序列却强行问“趋势”；
- 把多个无关事实拼成所谓“结构比较”；
- 问无法穷尽的开放列表题。
合格题目特征：两篇文章在某个主题的内部构成、阶段、类别或变化模式上分别是什么，结构上有什么不同。

### Q3【跨属性综合比较】
定义：Q3 是要求参与者结合两篇文章中的至少两个相关属性或事实条件，判断一个具体对象、关系或结论是否成立的题目。它考察参与者能否把多个相关信息点整合起来，而不是只提取单个事实。
必须满足：
- 至少涉及两个内容上相关的属性或事实条件；
- 这些属性或条件之间必须与文章主题有实际关系；
- 必须同时使用两篇文章信息；
- 答案必须是有限、明确、可评分的；
- 标准答案中的 gold_atoms 要分别对应每个必要事实点。
禁止生成：
- 不得只是把两个独立事实题简单拼接；
- 不得问开放式总结、主观判断或文章外推理；
- 不得生成多个合理答案都成立的问题。
合格题目特征：结合多个相关属性后，左右两篇文章中的对象是否满足某个明确条件，或某个具体关系是否成立。

### Q4【明确背景、过程或原因理解】
定义：Q4 是要求参与者理解两篇文章正文中明确表达的背景、过程、原因、结果、政策、事件、发展阶段或现象关系的题目。它考察的不是事实定位，而是对正文中明确关系的理解。
必须满足：
- 主要证据应来自正文，不能只来自 infobox；
- 必须是文章明确说明的关系；
- 可以比较两篇文章如何描述同类背景、过程或原因；
- 如果没有明确因果关系，可以使用明确的时间顺序、发展阶段、事件过程、背景与现象关系、政策与结果关系；
- 每个必要因素都必须有真实来源编号。
禁止生成：
- 禁止开放式问“为什么”但材料没有明确原因；
- 禁止要求参与者自行推测、评价原因重要性或补充文章外解释；
- 禁止把模型常识解释当作文章结论；
- 如果答案有多个无法穷尽的合理版本，必须放弃该候选问题。
合格题目特征：两篇文章分别如何明确描述某个现象的背景、过程、原因或结果关系。

### Q5【综合结论证据验证】
定义：Q5 是给参与者一个具体的双文档综合结论，让参与者根据两篇文章判断这个结论是否被材料支持。Q5 考察证据验证能力，而不是自由回答能力。
参与者只能在以下三种答案中选择：支持、不支持、材料不足。
必须满足：
- 题干必须给出一个具体、可验证、与两篇文章核心内容相关的综合结论；
- 判断该结论至少需要两条证据，且证据应来自两篇文章；
- 标准答案必须明确说明为什么是“支持”“不支持”或“材料不足”；
- “支持”表示材料中有足够证据证明该综合结论成立；
- “不支持”表示材料中存在相反证据，或者结论中的必要条件被材料明确否定；
- “材料不足”表示材料没有提供足够信息判断该结论是否成立。材料不足不是“不支持”。
禁止生成：
- 结论过大、过泛或依赖外部知识；
- 结论只是重复 Q1、Q2 或 Q3；
- 参与者需要主观评价；
- “不支持”和“材料不足”无法区分；
- 只用一篇文章就能判断。
合格题目特征：根据两篇文章中的证据，下面这个综合结论是支持、不支持，还是材料不足。

## 第三步：选择最终五题

从候选问题中各选择1题，顺序固定为 Q1 至 Q5。最终五题必须满足：
1. 全部涉及两篇文章；
2. 五题的主要理解目标不同；
3. 五题共同覆盖两篇文章的核心内容；
4. 不只是围绕三栏表中的字段提问；
5. 不重复考察相同事实；
6. Q1 至 Q5 的理解层次逐步提高；
7. 每题答案都能由冻结文章唯一确定；
8. 每个评分原子都有真实来源编号；
9. 不需要外部知识、常识或主观意见；
10. 问题文本不出现“三栏表”“表格行”“单元格”“可视化”“高亮”等界面词；
11. 不使用“哪个更好”“哪个更重要”“你认为”“为什么会”“总体上有什么特点”等无法客观评分的问法；
12. 如果任意一题不满足要求，重新选择候选题，不要降低标准。

## 输出格式

只输出合法 JSON，不输出 Markdown 说明。结构如下：
{{
  "material_id": "{material_id}",
  "questions": [
    {{
      "question_id": "Q1",
      "question_type": "单维事实比较",
      "question_text": "给参与者显示的自然语言题目",
      "answer_format": "结构化填写或固定选项；Q5 必须为固定选项",
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
    }},
    {{
      "question_id": "Q5",
      "question_type": "综合结论证据验证",
      "question_text": "根据两篇文章，判断以下综合结论是支持、不支持还是材料不足：……",
      "answer_format": "固定选项",
      "understanding_target": "该题帮助读者验证一个双文档综合结论",
      "gold_atoms": [],
      "answer_options": ["支持", "不支持", "材料不足"],
      "unique_answer": true,
      "uses_both_articles": true,
      "primary_evidence_distinct_from_previous": true
    }}
  ]
}}

输出前逐题静默检查：
- 题干前提是否真实；
- 是否同时涉及两篇文章；
- 是否真的有助于理解文章；
- 是否存在唯一答案；
- 每个评分原子是否有来源编号；
- 是否保留必要的年份、单位和口径；
- 是否与其他题重复；
- 是否把推测写成文章事实；
- Q4 是否有明确正文依据；
- Q5 是否清楚区分“不支持”和“材料不足”。"""


def build_question_validation_prompt(material, questions):
    material_id = material.get("id", "") if isinstance(material, dict) else ""
    question_json = json.dumps({"material_id": material_id, "questions": questions}, ensure_ascii=False, indent=2)
    return f"""提示词 3：验证问题是否合理

你是双文档比较阅读实验的独立题目审查员。

请逐题检查以下 Q1-Q5，不要自行补充文章外知识。你的任务是判断题目能否进入正式实验，而不是评价题目写得是否漂亮。

================ 待审查题目与隐藏标准答案 ================
{question_json}
==========================================================

每道题检查以下项目：
1. 题目是否同时涉及两篇文章；
2. 题目是否与两篇文章的核心内容直接相关；
3. 参与者回答后是否能更好理解文章内容；
4. 题目是否具有唯一确定答案；
5. 隐藏标准答案是否被左右文章明确支持；
6. 每个评分原子是否有真实、足够具体的来源编号；
7. 是否遗漏年份、单位、范围或统计口径；
8. 是否依赖外部知识、常识或研究人员推测；
9. Q1至Q5的理解操作是否真正不同；
10. 是否与其他题重复考察同一事实；
11. Q4是否有明确正文关系，而不是开放式原因推测；
12. Q5是否能区分支持、不支持和材料不足。

特别按五类题目定义复核：
- Q1 必须是单个明确维度的事实比较；
- Q2 必须是结构、组成、类别、阶段、排名、分布或变化模式比较，不能只是单个静态值；
- Q3 必须整合至少两个相关属性或事实条件，不能只是两个独立事实拼接；
- Q4 的主要证据应来自正文明确关系，不能要求开放式推测原因；
- Q5 必须只能回答“支持”“不支持”“材料不足”，并能清楚区分“不支持”和“材料不足”。

输出合法 JSON：
{{
  "overall": "PASS 或 REJECT",
  "question_reviews": [
    {{
      "question_id": "Q1",
      "status": "PASS 或 REJECT",
      "answer_is_unique": true,
      "uses_both_articles": true,
      "content_relevant": true,
      "source_ids_valid": true,
      "matches_question_type_definition": true,
      "duplicate_with": [],
      "problems": [],
      "required_action": "无或重新生成"
    }}
  ]
}}

任何一道题存在两个合理答案、证据不足、内容不相关、依赖外部知识、与其他题重复，或不符合对应题型定义时，overall 必须为 REJECT。REJECT 后不要把该题直接带入正式实验。"""


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
    questions = parsed.get("questions", [])
    if not isinstance(questions, list):
        raise ValueError("Generated questions must be a list")
    for index, item in enumerate(questions, start=1):
        if not isinstance(item, dict):
            raise ValueError(f"Generated question item {index} must be an object")
    ids = [item.get("question_id") for item in questions]
    if ids != ["Q1", "Q2", "Q3", "Q4", "Q5"]:
        raise ValueError("Generated questions must contain Q1-Q5 in order")
    normalized = {
        "material_id": material_id,
        "version": int(version),
        "frozen": False,
        "generated_at": utc_now_iso(),
        "prompt_version": QUESTION_PROMPT_VERSION,
        "questions": questions,
    }
    if isinstance(parsed.get("generation_prompts"), dict):
        normalized["generation_prompts"] = parsed["generation_prompts"]
    return normalized



def _generic_page_title(parsed):
    path_parts = [part for part in parsed.path.split("/") if part]
    if path_parts:
        return path_parts[-1].replace("-", " ").replace("_", " ").strip() or parsed.netloc
    return parsed.netloc


def parse_material_source(url):
    try:
        parsed_wiki = parse_english_wikipedia_url(url)
        return SimpleNamespace(
            title=parsed_wiki.title,
            display_url=parsed_wiki.display_url,
            revision=parsed_wiki.revision,
            source_kind="wikipedia",
        )
    except WikiUrlError:
        parsed = urlparse(str(url or ""))
        if parsed.scheme not in {"http", "https"} or not parsed.netloc:
            raise ValueError("Material source URL must be an English Wikipedia or public http(s) URL")
        normalized_url = parsed.geturl()
        return SimpleNamespace(
            title=_generic_page_title(parsed),
            display_url=normalized_url,
            revision=None,
            source_kind="web",
        )


def fetch_material_html(source):
    if source.source_kind == "wikipedia":
        return fetch_article_html(source.title, source.revision)
    try:
        response = requests.get(source.display_url, headers={"User-Agent": "WikiCompare/0.1"}, timeout=20)
        response.raise_for_status()
        return response.text
    except requests.exceptions.RequestException:
        snapshot_html = _load_material_snapshot_html(source.display_url)
        if snapshot_html is not None:
            return snapshot_html
        raise


def _load_material_snapshot_html(url):
    snapshot_path = _material_snapshot_path(url)
    if snapshot_path is None or not snapshot_path.exists():
        return None
    return snapshot_path.read_text(encoding="utf-8")


def _material_snapshot_path(url):
    parsed = urlparse(str(url or ""))
    host = parsed.netloc.lower()
    if host.startswith("www."):
        host = host[4:]
    parts = [part for part in parsed.path.split("/") if part]
    if host != "openfactbook.org" or len(parts) < 2 or parts[0] != "countries":
        return None
    country_slug = re.sub(r"[^a-z0-9-]+", "-", parts[1].lower()).strip("-")
    if not country_slug:
        return None
    return MATERIAL_SNAPSHOT_DIR / f"openfactbook-countries-{country_slug}.html"


def load_material_articles(material):
    articles = []
    for side in ("left", "right"):
        source_url = material.get(f"{side}Url")
        if not source_url:
            raise ValueError(f"Material {material.get('id', '')} is missing {side}Url for question generation")
        source = parse_material_source(source_url)
        title = material.get(f"{side}Title") or source.title
        html = fetch_material_html(source)
        articles.append(parse_article_html(
            html,
            side=side,
            title=title,
            url=source.display_url,
            revision=source.revision,
            source_kind=source.source_kind,
        ))
    return articles[0], articles[1]


def generate_questions_from_material(material, version, llm_client=None):
    config = get_llm_config()
    client = llm_client or (LLMClient(config) if config.enabled else None)
    if client is None:
        raise RuntimeError("OPENAI_API_KEY is required to auto-generate experiment questions")
    left_article, right_article = load_material_articles(material)
    prompt = build_question_prompt(
        material,
        left_article,
        right_article,
        max_article_chars=MAX_ARTICLE_PROMPT_CHARS,
    )
    try:
        raw_questions = _chat_question_generation(client, prompt)
    except Exception as error:
        if not _is_transient_llm_generation_error(error):
            raise
        raw_questions = _build_local_draft_questions(material, left_article, right_article)
    normalized = normalize_generated_questions(raw_questions, material.get("id", ""), version)
    normalized.setdefault("generation_prompts", _generation_prompt_metadata(prompt, normalized, material))
    return normalized


def _chat_question_generation(client, prompt):
    return client.chat_json([
        {
            "role": "system",
            "content": QUESTION_GENERATION_SYSTEM_PROMPT,
        },
        {
            "role": "user",
            "content": prompt,
        },
    ])



def _generation_prompt_metadata(user_prompt, normalized_questions=None, material=None):
    prompt_pair = {
        "system": QUESTION_GENERATION_SYSTEM_PROMPT,
        "user": user_prompt,
    }
    questions = []
    if isinstance(normalized_questions, dict):
        questions = normalized_questions.get("questions") or []
    return {
        "question_prompt": dict(prompt_pair),
        "answer_prompt": {
            **prompt_pair,
            "note": ANSWER_PROMPT_NOTE,
        },
        "validation_prompt": {
            "system": QUESTION_VALIDATION_SYSTEM_PROMPT,
            "user": build_question_validation_prompt(material or {}, questions),
            "title": "提示词 3：验证问题是否合理",
        },
    }


def _is_transient_llm_generation_error(error):
    message = str(error).lower()
    return any(
        token in message
        for token in (
            "504",
            "gateway",
            "timed out",
            "timeout",
            "request timed out",
            "temporarily unavailable",
        )
    )



def _uses_openfactbook_material(material):
    return any(
        _material_snapshot_path(material.get(f"{side}Url")) is not None
        for side in ("left", "right")
    )



def _build_local_draft_questions(material, left_article, right_article):
    left_title = material.get("leftTitle") or left_article.get("title") or "左侧材料"
    right_title = material.get("rightTitle") or right_article.get("title") or "右侧材料"
    left_evidence = _article_evidence_items(left_article)
    right_evidence = _article_evidence_items(right_article)

    first_pair = _pick_evidence_pair(left_evidence, right_evidence, ("area", "population", "gdp"), 0)
    structure_pair = _pick_evidence_pair(left_evidence, right_evidence, ("age structure", "ethnic", "language", "religion", "sector"), 1)
    economy_pair = _pick_evidence_pair(left_evidence, right_evidence, ("gdp", "growth", "inflation", "labor", "export", "import"), 2)
    background_pair = _pick_evidence_pair(left_evidence, right_evidence, ("background", "independence", "government"), 3)
    conclusion_pair = _pick_evidence_pair(left_evidence, right_evidence, ("population", "area", "gdp"), 4)

    return {
        "material_id": material.get("id", ""),
        "questions": [
            _local_question(
                "Q1",
                "单维事实比较",
                f"根据材料，{left_title} 和 {right_title} 在“{first_pair['key']}”这一项上分别是什么？",
                "分别填写两侧材料中的对应事实",
                first_pair,
            ),
            _local_question(
                "Q2",
                "结构、组成或变化模式比较",
                f"比较 {left_title} 和 {right_title} 关于“{structure_pair['key']}”的描述，它们呈现出哪些组成或结构差异？",
                "用简短文字分别概括两侧结构，并指出主要差异",
                structure_pair,
            ),
            _local_question(
                "Q3",
                "跨属性综合比较",
                f"结合“{economy_pair['key']}”以及前面事实，判断两篇材料展示的国家/经济特征有什么重要差别？",
                "写出综合判断，并分别引用两侧证据",
                economy_pair,
            ),
            _local_question(
                "Q4",
                "明确背景、过程或原因理解",
                f"两篇材料在背景或发展过程上分别给出了什么关键信息？请围绕“{background_pair['key']}”比较。",
                "分别概括两侧背景/过程信息",
                background_pair,
            ),
            _local_question(
                "Q5",
                "综合结论证据验证",
                f"结论验证：两篇材料都能支持对“{conclusion_pair['key']}”进行直接比较。这个结论是“支持”“不支持”还是“材料不足”？",
                "只能回答：支持 / 不支持 / 材料不足，并说明证据",
                conclusion_pair,
                canonical_prefix="支持；两侧材料都提供了对应信息。",
            ),
        ],
    }


def _article_evidence_items(article):
    records = []
    for field in article.get("infobox") or []:
        source_id = field.get("id") or ""
        label = " ".join(str(field.get("label") or field.get("key") or "").split())
        value = " ".join(str(field.get("value") or field.get("valueText") or "").split())
        text = f"{label}: {value}" if label or value else ""
        if not text:
            continue
        records.append({"source_id": source_id, "key": label or "Infobox", "value": value or text, "text": text})
    for paragraph in article.get("paragraphs") or []:
        source_id = paragraph.get("id") or ""
        text = " ".join(str(paragraph.get("text") or "").split())
        if not text:
            continue
        key, value = _split_evidence_text(text)
        records.append({"source_id": source_id, "key": key, "value": value, "text": text})
    if not records:
        records.append({"source_id": "", "key": "核心内容", "value": "材料中未提取到可用段落。", "text": "材料中未提取到可用段落。"})
    return records


def _split_evidence_text(text):
    if ":" not in text:
        return _short_text(text, 60), _short_text(text, 320)
    key, value = text.split(":", 1)
    return _short_text(key.strip(), 90) or "核心内容", _short_text(value.strip(), 420)


def _pick_evidence_pair(left_evidence, right_evidence, keywords, fallback_index):
    right_by_key = {item["key"].lower(): item for item in right_evidence}
    for left_item in left_evidence:
        left_key = left_item["key"].lower()
        right_item = right_by_key.get(left_key)
        if right_item is None:
            continue
        if not keywords or any(keyword in left_key for keyword in keywords):
            return {"key": left_item["key"], "left": left_item, "right": right_item}

    left_item = left_evidence[fallback_index % len(left_evidence)]
    right_item = right_evidence[fallback_index % len(right_evidence)]
    key = left_item["key"] if left_item["key"].lower() == right_item["key"].lower() else f"{left_item['key']} / {right_item['key']}"
    return {"key": key, "left": left_item, "right": right_item}


def _local_question(question_id, question_type, question_text, answer_format, pair, canonical_prefix=None):
    left = pair["left"]
    right = pair["right"]
    canonical_answer = f"左侧：{left['value']}；右侧：{right['value']}"
    if canonical_prefix:
        canonical_answer = f"{canonical_prefix} {canonical_answer}"
    return {
        "question_id": question_id,
        "question_type": question_type,
        "question_text": question_text,
        "answer_format": answer_format,
        "understanding_target": "本地备用生成：请管理员在冻结前检查题目质量和标准答案。",
        "gold_atoms": [
            {
                "atom_id": f"{question_id}-A1",
                "requirement": "回答必须同时包含两侧材料的对应信息，并与来源片段一致。",
                "canonical_answer": canonical_answer,
                "accepted_variants": [],
                "source_ids": [source_id for source_id in (left.get("source_id"), right.get("source_id")) if source_id],
                "required_unit": "按材料原文",
                "required_time_scope": "按材料原文",
            }
        ],
        "evidence_distinct_from_previous": True,
    }


def _short_text(value, max_chars):
    value = " ".join(str(value or "").split())
    if len(value) <= max_chars:
        return value
    return value[: max_chars - 1].rstrip() + "…"
