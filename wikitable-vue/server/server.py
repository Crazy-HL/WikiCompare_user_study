import time
from concurrent.futures import ThreadPoolExecutor
from threading import Lock
import tornado.ioloop
import tornado.web
import json
import uuid
from openai import OpenAI
from services.analysis import (
    fallback_answer,
    fallback_attribute_summary,
    llm_answer,
    llm_attribute_summary,
    row_context,
)
from services.article_loader import fetch_article_html, parse_article_html
from services.attribute_pool import build_attribute_pool
from services.config import get_llm_config
from services.llm_client import LLMClient
from services.models import CompareSession
from services.outline_matcher import build_outline_matches
from services.pipeline import align_attribute_pools, normalize_attribute_pair, rank_rows
from services.session_store import SessionStore
from services.text_attribute_pairs import build_paired_text_attributes, build_text_evidence_candidates
from services.wiki_url import WikiUrlError, parse_english_wikipedia_url
from tool.obtainHtml import obtain_html
from tool.chart_formats import (
    get_bar_chart_format,
    get_pie_chart_format,
    get_line_chart_format,
    get_horizontal_bar_chart_format,
    get_histogram_format,
    get_stacked_bar_chart_format,
    get_scatter_plot_format,
    get_radar_chart_format,
    get_table_format
)
from tool.json_extractor import extract_json
import re

# 系统消息，用于为模型提供指导
system_messages = [
    {"role": "system", "content": "你是辅助阅读对比的专家，可以对比两篇文章。同时你还可以判断文章中的内容是否可以进行可视化，并擅长将相关的可视化数据识别提取出来。"},
]

# 用于记录对比结果
comparison_result = ""  # 对比后的文章内容
SESSION_STORE = SessionStore()
BLOCKING_EXECUTOR = ThreadPoolExecutor(max_workers=4)
ARTICLE_HTML_CACHE: dict[str, str] = {}
ARTICLE_HTML_CACHE_LOCK = Lock()
COMPARE_CACHE_VERSION = "compare-session-v1"

def make_messages(input: str, n: int = 20) -> list:
    """
    构造消息列表，用于每次请求的消息传递。保留最新的 n 条消息，并确保系统消息始终在列表中。
    """
    # 先将用户的最新问题添加到历史记录
    messages = [{
        "role": "user",
        "content": input,  
    }]
    
    # 构建新的消息列表
    new_messages = []
    new_messages.extend(system_messages)  # 添加系统消息
    
    # 保证不超过 n 条历史记录
    if len(messages) > n:
        messages = messages[-n:]
    
    new_messages.extend(messages)  # 添加历史消息
    return new_messages

def chat(input: str) -> str:
    """
    进行对话，并返回模型的回答，支持多轮对话。
    """
    config = get_llm_config()
    if not config.enabled:
        return json.dumps({
            "error": "OpenAI API 未配置",
            "message": "请设置 OPENAI_API_KEY、OPENAI_MODEL 和 OPENAI_BASE_URL 后重试"
        }, ensure_ascii=False)

    client = OpenAI(
        api_key=config.api_key,
        base_url=config.base_url,
        timeout=config.timeout_seconds,
        max_retries=0,
    )
    retry_attempts = 3
    for attempt in range(retry_attempts):
        try:
            completion = client.chat.completions.create(
                model=config.model,
                messages=make_messages(input),
                temperature=0.3,
            )

            # 获取模型的回答并返回
            assistant_message = completion.choices[0].message
            return assistant_message.content
        except Exception as e:
            if "rate_limit_reached_error" in str(e):
                #print(f"Rate limit reached, retrying in 30 seconds... (Attempt {attempt+1}/{retry_attempts})")
                time.sleep(30)  # 等待 30 秒后重试
            else:
                #print(f"Error occurred: {str(e)}")
                break
    return json.dumps({
        "error": "OpenAI API 调用失败",
        "message": "请检查 API 配置或稍后重试"
    })


class ApiHandler(tornado.web.RequestHandler):
    def set_default_headers(self):
        self.set_header("Access-Control-Allow-Origin", "*")
        self.set_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.set_header("Access-Control-Allow-Headers", "Content-Type")
        self.set_header("Content-Type", "application/json; charset=UTF-8")

    def options(self):
        self.set_status(204)
        self.finish()

    def read_json(self):
        try:
            data = json.loads(self.request.body or b"{}")
        except (json.JSONDecodeError, UnicodeDecodeError):
            self.write_error_json(400, "Invalid JSON body")
            return None
        if not isinstance(data, dict):
            self.write_error_json(400, "JSON body must be an object")
            return None
        return data

    def write_error_json(self, status_code: int, message: str):
        self.set_status(status_code)
        self.write(json.dumps({"error": message}, ensure_ascii=False))


class CompareSessionHandler(ApiHandler):
    async def post(self):
        data = self.read_json()
        if data is None:
            return

        left_url = str(data.get("leftUrl") or "").strip()
        right_url = str(data.get("rightUrl") or "").strip()
        if not left_url:
            self.write_error_json(400, "leftUrl is required")
            return
        if not right_url:
            self.write_error_json(400, "rightUrl is required")
            return

        try:
            left_wiki = parse_english_wikipedia_url(left_url)
            right_wiki = parse_english_wikipedia_url(right_url)
        except WikiUrlError as error:
            self.write_error_json(400, str(error))
            return

        force_refresh = data.get("forceRefresh") is True
        pair_key = _pair_cache_key(left_wiki, right_wiki)
        if not force_refresh:
            cached_session = SESSION_STORE.get_by_pair_key(pair_key)
            if cached_session is not None:
                payload = cached_session.to_dict()
                payload["fromCache"] = True
                self.write(json.dumps(payload, ensure_ascii=False))
                return

        status_code, payload = await tornado.ioloop.IOLoop.current().run_in_executor(
            BLOCKING_EXECUTOR,
            _create_compare_session_payload,
            left_wiki,
            right_wiki,
            force_refresh,
            pair_key,
        )
        if status_code != 200:
            self.write_error_json(status_code, payload["error"])
            return
        self.write(json.dumps(payload, ensure_ascii=False))


def _create_compare_session_payload(left_wiki, right_wiki, force_refresh=False, pair_key=None) -> tuple[int, dict]:
    warnings = []
    config = get_llm_config()
    llm_client = LLMClient(config) if config.enabled else None
    if not config.enabled:
        warnings.append("OPENAI_API_KEY is not configured; text attribute extraction is disabled")

    try:
        left_article = parse_article_html(
            _fetch_article_html_cached(left_wiki, force_refresh),
            side="left",
            title=left_wiki.title,
            url=left_wiki.display_url,
            revision=left_wiki.revision,
        )
        right_article = parse_article_html(
            _fetch_article_html_cached(right_wiki, force_refresh),
            side="right",
            title=right_wiki.title,
            url=right_wiki.display_url,
            revision=right_wiki.revision,
        )
    except Exception as error:
        return 502, {"error": f"Failed to load Wikipedia articles: {error}"}

    left_pool, right_pool = _build_attribute_pools(left_article, right_article, llm_client)
    paired_left_attrs, paired_right_attrs, paired_alignments = _build_paired_text_alignments(
        left_article,
        right_article,
        left_pool,
        right_pool,
        llm_client,
    )
    left_pool = left_pool + paired_left_attrs
    right_pool = right_pool + paired_right_attrs
    outline_matches = build_outline_matches(
        left_article.get("outline", []),
        right_article.get("outline", []),
    )
    aligned_attributes = paired_alignments + _without_duplicate_alignments(
        align_attribute_pools(left_pool, right_pool),
        paired_alignments,
    )
    rows = [
        _normalize_session_alignment(alignment)
        for alignment in aligned_attributes
    ]
    ranked_rows = rank_rows(rows)

    source_map = {}
    left_article = dict(left_article)
    right_article = dict(right_article)
    source_map.update(left_article.pop("sourceMap", {}) or {})
    source_map.update(right_article.pop("sourceMap", {}) or {})

    session = CompareSession(
        session_id=str(uuid.uuid4()),
        articles={"left": left_article, "right": right_article},
        outline_matches=outline_matches,
        attribute_pools={"left": left_pool, "right": right_pool},
        aligned_attributes=[
            {
                "leftId": alignment["left"]["id"],
                "rightId": alignment["right"]["id"],
                "label": alignment["label"],
            }
            for alignment in aligned_attributes
        ],
        ranked_rows=ranked_rows,
        source_map=source_map,
        warnings=warnings,
    )
    SESSION_STORE.save(session, pair_key=pair_key)
    payload = session.to_dict()
    payload["fromCache"] = False
    return 200, payload


def _fetch_article_html_cached(wiki, force_refresh=False) -> str:
    cache_key = _article_cache_key(wiki)
    if not force_refresh:
        with ARTICLE_HTML_CACHE_LOCK:
            cached_html = ARTICLE_HTML_CACHE.get(cache_key)
        if cached_html is not None:
            return cached_html

    html = fetch_article_html(wiki.title, wiki.revision)
    with ARTICLE_HTML_CACHE_LOCK:
        ARTICLE_HTML_CACHE[cache_key] = html
    return html


def _article_cache_key(wiki) -> str:
    return f"{wiki.normalized_url}|revision={wiki.revision or ''}"


def _pair_cache_key(left_wiki, right_wiki) -> str:
    return "|".join(
        [
            COMPARE_CACHE_VERSION,
            _article_cache_key(left_wiki),
            _article_cache_key(right_wiki),
        ]
    )


def _build_attribute_pools(left_article, right_article, llm_client):
    with ThreadPoolExecutor(max_workers=2) as executor:
        left_future = executor.submit(build_attribute_pool, left_article, "left", llm_client)
        right_future = executor.submit(build_attribute_pool, right_article, "right", llm_client)
        return left_future.result(), right_future.result()


def _build_paired_text_alignments(left_article, right_article, left_pool, right_pool, llm_client):
    if llm_client is None or not hasattr(llm_client, "extract_text_attribute_pairs"):
        return [], [], []

    left_candidates = build_text_evidence_candidates(left_article, "left")
    right_candidates = build_text_evidence_candidates(right_article, "right")
    if not left_candidates or not right_candidates:
        return [], [], []

    infobox_context = {
        "left": _pool_context(left_pool),
        "right": _pool_context(right_pool),
    }
    try:
        pair_response = llm_client.extract_text_attribute_pairs(
            left_candidates,
            right_candidates,
            infobox_context,
        )
    except Exception:
        return [], [], []

    return build_paired_text_attributes(
        left_article,
        right_article,
        pair_response,
        left_pool,
        right_pool,
    )


def _pool_context(pool):
    context = []
    for item in pool:
        if not isinstance(item, dict):
            continue
        context.append(
            {
                "key": item.get("key"),
                "valueText": item.get("valueText"),
                "source": item.get("source"),
            }
        )
        if len(context) >= 24:
            break
    return context


def _without_duplicate_alignments(alignments, paired_alignments):
    paired_pairs = {
        (alignment.get("left", {}).get("id"), alignment.get("right", {}).get("id"))
        for alignment in paired_alignments
        if isinstance(alignment, dict)
    }
    return [
        alignment
        for alignment in alignments
        if (alignment.get("left", {}).get("id"), alignment.get("right", {}).get("id")) not in paired_pairs
    ]


def _normalize_session_alignment(alignment):
    row = normalize_attribute_pair(
        alignment["left"],
        alignment["right"],
        alignment["label"],
    )
    if alignment["left"].get("source") == "main_text" and alignment["right"].get("source") == "main_text":
        row["sourceKind"] = "main_text"
    return row


def _align_exact_lowercase_keys(
    left_pool: list[dict],
    right_pool: list[dict],
) -> list[dict]:
    right_by_key = {
        _alignment_key(attribute.get("key")): attribute
        for attribute in right_pool
        if _alignment_key(attribute.get("key"))
    }
    alignments = []
    for left_attribute in left_pool:
        key = _alignment_key(left_attribute.get("key"))
        if not key or key not in right_by_key:
            continue
        alignments.append(
            {
                "left": left_attribute,
                "right": right_by_key[key],
                "label": left_attribute.get("key") or right_by_key[key].get("key") or key,
            }
        )
    return alignments


def _alignment_key(value) -> str:
    return str(value or "").strip().lower()


class AnalyzeAttributeHandler(ApiHandler):
    def post(self):
        data = self.read_json()
        if data is None:
            return

        session_id = str(data.get("sessionId") or "").strip()
        attribute_id = str(data.get("attributeId") or "").strip()
        if not session_id:
            self.write_error_json(400, "sessionId is required")
            return
        if not attribute_id:
            self.write_error_json(400, "attributeId is required")
            return

        session = SESSION_STORE.get(session_id)
        if session is None:
            self.write_error_json(404, "Session not found")
            return

        row = row_context(session, attribute_id)
        if row is None:
            self.write_error_json(404, "Attribute not found")
            return

        result = None
        config = get_llm_config()
        if config.enabled:
            try:
                result = llm_attribute_summary(LLMClient(config), row, session.source_map, session.articles)
            except Exception as error:
                print(f"LLM attribute analysis failed, using fallback: {error}")
        if result is None:
            result = fallback_attribute_summary(row, session.source_map, session.articles)
        self.write(json.dumps(result, ensure_ascii=False))


class AskHandlerV2(ApiHandler):
    def post(self):
        data = self.read_json()
        if data is None:
            return

        session_id = str(data.get("sessionId") or "").strip()
        question = str(data.get("question") or "").strip()
        if not session_id:
            self.write_error_json(400, "sessionId is required")
            return
        if not question:
            self.write_error_json(400, "question is required")
            return

        session = SESSION_STORE.get(session_id)
        if session is None:
            self.write_error_json(404, "Session not found")
            return

        result = None
        config = get_llm_config()
        if config.enabled:
            try:
                result = llm_answer(LLMClient(config), session, question)
            except Exception as error:
                print(f"LLM question answering failed, using fallback: {error}")
        if result is None:
            result = fallback_answer(session, question)
        self.write(json.dumps(result, ensure_ascii=False))

class GPTCompareHandler(tornado.web.RequestHandler):
    def set_default_headers(self):
        self.set_header("Access-Control-Allow-Origin", "*")
        self.set_header("Access-Control-Allow-Methods", "POST, OPTIONS")
        self.set_header("Access-Control-Allow-Headers", "Content-Type")

    def options(self):
        self.set_status(204)
        self.finish()

    def post(self):
        try:
            data = json.loads(self.request.body)
            text1 = data.get("text1")
            text2 = data.get("text2")
            #print("Comparing text 1 and text 2")

            # 对比文章的逻辑
            global comparison_result
            comparison_result = chat(f"请对比以下两篇文章的内容：\n文章1:\n{text1}\n文章2:\n{text2}")
            #print(f"对比结果：{comparison_result}")
            self.write(json.dumps({"result": comparison_result}))
        except Exception as e:
            self.write(json.dumps({
                "error": str(e),
                "message": "对比文章时出错"
            }))

# 新增 AnalyzeChartHandler 和 GPTAskChartHandler
class AnalyzeChartHandler(tornado.web.RequestHandler):
    def set_default_headers(self):
        self.set_header("Access-Control-Allow-Origin", "*")
        self.set_header("Access-Control-Allow-Methods", "POST, OPTIONS")
        self.set_header("Access-Control-Allow-Headers", "Content-Type")

    def options(self):
        self.set_status(204)
        self.finish()

    def post(self):
        try:
            data = json.loads(self.request.body)
            chart_data = data.get("chartData")
            chart_type = data.get("chartType")

            #print("接收到的图表数据:", chart_data)  # 调试日志
            #print("接收到的图表类型:", chart_type)  # 调试日志

            # 调用大模型分析图表
            analysis_result = chat(f"""
            请分析以下图表数据：
            - 图表类型：{chart_type}
            - 图表数据：{json.dumps(chart_data, ensure_ascii=False)}
            请总结图表的关键数据点和你的分析结论。对于关键数据点的分析，只需要指出是哪个点且关键的理由即可，回复尽可能简洁明了。
            对于分析结论，同样需要尽可能简洁明了。最后输出内容，要求美观。不需要给出总结性话语。
            """)

            #print("大模型分析结果:", analysis_result)  # 调试日志

            # 返回分析结果
            self.write(json.dumps({
                "analysis": analysis_result  # 确保返回的字段是 analysis
            }))
        except Exception as e:
            #print("图表分析失败:", str(e))  # 调试日志
            self.write(json.dumps({
                "error": str(e),
                "message": "图表分析失败"
            }))

class GPTAskChartHandler(tornado.web.RequestHandler):
    def set_default_headers(self):
        self.set_header("Access-Control-Allow-Origin", "*")
        self.set_header("Access-Control-Allow-Methods", "POST, OPTIONS")
        self.set_header("Access-Control-Allow-Headers", "Content-Type")

    def options(self):
        self.set_status(204)
        self.finish()

    def post(self):
        try:
            data = json.loads(self.request.body)
            question = data.get("question")
            chart_data = data.get("chartData")
            chart_type = data.get("chartType")

            # 使用图表数据和用户问题进行对话
            answer = chat(f"""
            以下是图表数据：
            - 图表类型：{chart_type}
            - 图表数据：{json.dumps(chart_data, ensure_ascii=False)}
            用户提问：{question}
            """)

            self.write(json.dumps({"answer": answer}))
        except Exception as e:
            self.write(json.dumps({
                "error": str(e),
                "message": "提问时出错"
            }))

class GPTAskHandler(tornado.web.RequestHandler):
    def set_default_headers(self):
        self.set_header("Access-Control-Allow-Origin", "*")
        self.set_header("Access-Control-Allow-Methods", "POST, OPTIONS")
        self.set_header("Access-Control-Allow-Headers", "Content-Type")

    def options(self):
        self.set_status(204)
        self.finish()

    def post(self):
        try:
            data = json.loads(self.request.body)
            question = data.get("question")
            global comparison_result  # 获取对比结果
            #print(f"用户问题: {question}, 上下文: {comparison_result}")
            
            # 使用对比结果和用户问题进行对话
            conversation_input = f"以下是文章对比结果：\n{comparison_result}\n用户提问：\n{question}"
            answer = chat(conversation_input)  # 获取 GPT 的回答
            self.write(json.dumps({"answer": answer}))
        except Exception as e:
            self.write(json.dumps({
                "error": str(e),
                "message": "提问时出错"
            }))


class MergedJsonsHandler(tornado.web.RequestHandler):
    def set_default_headers(self):
        self.set_header("Access-Control-Allow-Origin", "*")
        self.set_header("Access-Control-Allow-Methods", "POST, OPTIONS")
        self.set_header("Access-Control-Allow-Headers", "Content-Type")

    def options(self):
        self.set_status(204)
        self.finish()

    def post(self):
        try:
            data = json.loads(self.request.body)
            text1 = data.get("text1")
            text2 = data.get("text2")
            # yes_no = chat(f"""
            #                      帮我分别判断{text1}和{text2}的内容是否适合将数据提取出来进行可视化，如果有一个不适合则返回“no”，否则返回“yes”。
            #                      **预期输出**: 您的响应应该是列表["yes","no"]中的单个单词，不带任何额外的解释或理由。""")
            
            # if yes_no == 'no':
            #     # 直接返回结果，不执行后续代码
            #     self.write(json.dumps({
            #         "data_classification": "",
            #         "json_data": "",
            #         "yes_no":"no"
            #     }))
            #     return
            suitable_charts = ["Line Chart","Scatter Chart","Bar Chart","Stacked Bar Chart"]
            chart_classification = chat(f"""
            从以下列表中{suitable_charts}选择一个最适合{text1}可视化的图表类型，同时也适合{text2}可视化的图表类型。
            预期输出: 你的响应应该是以下列表中的一个单词{suitable_charts}，不需要额外的解释或理由。
            """)
            chart_classification = chart_classification.strip()
            #print("chart_classification：", chart_classification)

            # 根据不同的图表类型，选择对应的 JSON 格式
            if chart_classification == "Bar Chart":
                json_format = get_bar_chart_format()
            elif chart_classification == "Pie Chart":
                json_format = get_pie_chart_format()
            elif chart_classification == "Line Chart":
                json_format = get_line_chart_format()
            elif chart_classification == "Horizontal Bar Chart":
                json_format = get_horizontal_bar_chart_format()
            elif chart_classification == "Histogram":
                json_format = get_histogram_format()
            elif chart_classification == "Stacked Bar Chart":
                json_format = get_stacked_bar_chart_format()
            elif chart_classification == "Scatter Chart":
                json_format = get_scatter_plot_format()
            elif chart_classification == "Radar Chart":
                json_format = get_radar_chart_format()
            else:
                json_format = []

            # 提取数据并转换成标准 JSON 格式
            json1_data = chat(f"""
            将{text1}可视化为{chart_classification}所需的数据提取出来，提取的数据一定要完整且合理，如果是表格数据，则应该将全部数据都提取出来，不要删减。如果数据值为0，请不要省略。按照下面举例的 JSON 格式输出（内容需要自行分析，要符合提取的数据内容）：{json_format}
            预期输出: 你的响应应该是一个由花括号包裹的 JSON 格式的数据，该数据要符合规范
            （例如：1、不要添加\减少括号或逗号等；
            2、属性值要正确等；3、不要添加任何额外的解释或理由），
            同时花括号外也不带任何额外的解释或理由，同时数据中的非数值应该被替换为0（例如null、undefind等）。
            """)
            json2_data = chat(f"""
            将{text2}可视化为{chart_classification}所需的数据提取出来，提取的数据一定要完整且合理，如果是表格数据，则应该将全部数据都提取出来，不要删减。如果数据值为0，请不要省略。按照下面举例的 JSON 格式输出（内容需要自行分析，要符合提取的数据内容）：{json_format}
            预期输出: 你的响应应该是一个由花括号包裹的 JSON 格式的数据，该数据要符合规范
            （例如：1、不要添加\减少括号或逗号等；
            2、属性值要正确等；3、不要添加任何额外的解释或理由），
            同时花括号外也不带任何额外的解释或理由，同时数据中的非数值应该被替换为0（例如null、undefind等）。
            """)
            # 调用函数提取 JSON 数据
            json1_data = extract_json(json1_data)
            json2_data = extract_json(json2_data)
            #合并json数据
            json_data = chat(f"""
            帮我将{json1_data}和{json2_data}两个JSON数据合并，要求合并数据必须包含了这两个JSON数据的所有数据，并且合并后的JSON格式与这两个JSON数据相同。
            预期输出: 你的响应应该是一个由花括号包裹的 JSON 格式的数据，该数据要符合规范
            （例如：1、不要添加\减少括号或逗号等；
            2、属性值要正确等；3、不要添加任何额外的解释或理由），
            同时花括号外也不带任何额外的解释或理由，同时数据中的非数值应该被替换为0（例如null、undefind等）。""")
            # 调用函数提取 JSON 数据
            json_data = extract_json(json_data)
            #print("json1:",json1_data)
            #print("json2:",json2_data)
            #print("json:",json_data)
            # 返回结果
            self.write(json.dumps({
                "chart_classification": chart_classification,
                "json_data": json_data,
                "div1_json": json1_data,
                "div3_json": json2_data,
                "yes_no":"yes"
            }))
        except Exception as e:
            # 捕获所有异常并返回 JSON 格式的错误信息
            self.write(json.dumps({
                "error": str(e),
                "message": "处理文章内容时出错"
            }))

class ProcessTextHandler(tornado.web.RequestHandler):
    def set_default_headers(self):
        self.set_header("Access-Control-Allow-Origin", "*")
        self.set_header("Access-Control-Allow-Methods", "POST, OPTIONS")
        self.set_header("Access-Control-Allow-Headers", "Content-Type")

    def options(self):
        self.set_status(204)
        self.finish()

    def post(self):
        try:
            data = json.loads(self.request.body)
            text = data.get("text")

            # 判断文本类型
            data_type = chat(f"""
                            将以下内容'{text}'按照以下三个类别进行分类，同时判断逻辑为先判断该内容中是否有数据可以进行可视化，如果有则不考虑下方的非可视化数据（Non-Visual Data）这一类别，否则则最后考虑这一类别：
                            1、段落数据（Paragraph Data）：指在文本段落中散布的、可以用图表形式表现的数据信息，如统计数字、比例、趋势描述等。这些数据通常以自然语言的形式出现，但包含具体的数值或可量化的信息。
                            **示例**：统计数字（如“47分”）、比例（如“吸引了6,300名观众，几乎占格伦斯福尔斯14,354人口的一半”）、趋势描述（如“连续第二年晋级NCAA锦标赛第二轮”）。
                            2、表格数据（Tabular Data）：指以表格形式呈现的数据，通常包括行和列，用于系统地展示数值型或分类数据，便于分析和比较。表格数据可以直接用于生成图表。
                            **示例**：数据表（如球员的得分、篮板、助攻等统计）、时间序列数据（如不同日期的比赛得分）。
                            3、非可视化数据（Non-Visual Data）：指不适合或无法通过图表形式展示的数据，例如文本描述、理论概念、个人意见或主观评价等。这类数据通常需要通过文字或叙述来传达其意义。
                            **示例**：文本描述（如“弗雷戴特成为了‘流行文化传奇’”）、理论概念（如“Jimmermania”）、个人意见或主观评价（如“总统奥巴马评价他：‘难以置信。他是全国最好的得分手。很有天赋。’”）。
                            **预期输出**: 您的响应应该是列表["Paragraph","Tabular","Non-Visual"]中的单个单词，不带任何额外的解释或理由。""")
            data_type = data_type.strip()
            #print("data_type:", data_type)

            if data_type == 'Non-Visual':
                # 直接返回结果，不执行后续代码
                self.write(json.dumps({
                    "data_type": data_type,
                    "data_classification": "",
                    "json_data": ""
                }))
                return

            # 数据分类
            data_classification = chat(f"""
            根据以下数据类别对{text}进行分类：
            - 数值(Value): 表示可以量化的数值数据，如金额、数量、温度等。
            - 比例(Proportional): 表示各部分在整体中的占比，如百分比、比率等。
            - 分类(Categorical): 不涉及数值，只是对不同类别的区分。
            - 分布(Distribution): 展示数据在各个范围内的分布情况，如频率分布、数据集中趋势等。
            - 对比(Comparison): 用于对比不同组之间的差异。
            - 关系(Relational): 用于展示不同变量之间的相互关系或相关性。
            - 趋势(Trend): 表示数据随时间的变化趋势，如销售额随时间的变化。
            预期输出: 你的响应应该是以下列表中的一个单词 ["Value", "Proportional", "Categorical", "Distribution", "Comparison", "Relational", "Trend"]，不需要额外的解释或理由。""")
            data_classification = data_classification.strip()
            #print("data_classification:", data_classification)

            # 根据分类判断合适的可视化类型
            if data_classification == "Value":
                suitable_charts = ["Line Chart"]
            elif data_classification == "Proportional":
                suitable_charts = ["Line Chart","Scatter Chart"]
            elif data_classification == "Categorical":
                suitable_charts = ["Bar Chart"]
            elif data_classification == "Distribution":
                suitable_charts = ["Histogram"]
            elif data_classification == "Comparison":
                suitable_charts = ["Bar Chart", "Stacked Bar Chart", "Line Chart"]
            elif data_classification == "Relational":
                suitable_charts = ["Scatter Chart"]
            elif data_classification == "Trend":
                suitable_charts = ["Line Chart"]
            else:
                suitable_charts = []

            # 判断适合的图表类型
            chart_classification = chat(f"""
            从以下列表中{suitable_charts}选择一个最适合{text}可视化的图表类型。
            预期输出: 你的响应应该是以下列表中的一个单词{suitable_charts}，不需要额外的解释或理由。
            """)
            chart_classification = chart_classification.strip()
            #print("chart_classification：", chart_classification)

            # 根据不同的图表类型，选择对应的 JSON 格式
            if chart_classification == "Bar Chart":
                json_format = get_bar_chart_format()
            elif chart_classification == "Pie Chart":
                json_format = get_pie_chart_format()
            elif chart_classification == "Line Chart":
                json_format = get_line_chart_format()
            elif chart_classification == "Horizontal Bar Chart":
                json_format = get_horizontal_bar_chart_format()
            elif chart_classification == "Histogram":
                json_format = get_histogram_format()
            elif chart_classification == "Stacked Bar Chart":
                json_format = get_stacked_bar_chart_format()
            elif chart_classification == "Scatter Chart":
                json_format = get_scatter_plot_format()
                #print("format:",json_format)
            elif chart_classification == "Radar Chart":
                json_format = get_radar_chart_format()
            else:
                json_format = []

            # 提取数据并转换成标准 JSON 格式
            json_data = chat(f"""
            将{text}可视化为{chart_classification}所需的数据提取出来，尽可能提取的数据完整，按照下面举例的 JSON 格式输出（内容需要自行分析，要符合提取的数据内容）：{json_format}
            预期输出: 你的响应应该是一个由花括号包裹的 JSON 格式的数据，该数据要符合规范
            （例如：1、不要添加\减少括号或逗号等；
            2、属性值要正确等；3、不要添加任何额外的解释或理由），
            同时花括号外也不带任何额外的解释或理由，同时数据中的非数值应该被替换为0（例如null、undefind等）。
            """)
            #print('classification:',chart_classification)
            #print("format:",json_format)
            #print("###:",json_data)
            # 调用函数提取 JSON 数据
            json_data = extract_json(json_data)
            #print("json_data:",json_data)

            # 返回结果
            self.write(json.dumps({
                "data_type": data_type,
                "chart_classification": chart_classification,
                "json_data": json_data
            }))
        except Exception as e:
            # 捕获所有异常并返回 JSON 格式的错误信息
            self.write(json.dumps({
                "error": str(e),
                "message": "处理文章内容时出错"
            }))

class MainHandler(tornado.web.RequestHandler):
    def set_default_headers(self):
        self.set_header("Access-Control-Allow-Origin", "*")
        self.set_header("Access-Control-Allow-Headers", "Content-Type")

    def get(self):
        self.write("Welcome to the Tornado Server!")

class HtmlHandler(tornado.web.RequestHandler):
    def set_default_headers(self):
        self.set_header("Access-Control-Allow-Origin", "*")
        self.set_header("Access-Control-Allow-Headers", "Content-Type")

    def get(self):
        url = self.get_argument('url')
        html = obtain_html(url)  # 获取 HTML 内容
        if(type(html) == str):
            self.write(html)
        self.write('error')

class OutlineMatchHandler(tornado.web.RequestHandler):
    def set_default_headers(self):
        self.set_header("Access-Control-Allow-Origin", "*")
        self.set_header("Access-Control-Allow-Methods", "POST, OPTIONS")
        self.set_header("Access-Control-Allow-Headers", "Content-Type")

    def options(self):
        self.set_status(204)
        self.finish()

    def post(self):
        try:
            data = json.loads(self.request.body)
            outline1 = data.get("outline1")
            outline2 = data.get("outline2")

            # 调用大模型进行文本匹配
            match_result = chat(f"""
            输入参数{outline1} 和 {outline2}:
                这两个参数都是数组，包含每个大纲的章节信息。
                每个章节信息应该是一个对象，其中包含至少两个字段：
                id：章节的唯一标识符。
                text：章节标题的文本内容。
            示例输入：
            const outline1 = [
                {{id: "heading-0", text: "Introduction to AI" }},
                {{id: "heading-1", text: "Machine Learning Basics" }}];
            
            const outline2 = [
                {{id: "heading-0", text: "AI Introduction" }},
                {{id: "heading-1", text: "Basics of Machine Learning"}}];

            如果 outline1 和 outline2 中的两个章节标题被认为是相似的，那么这两个章节的 ID 将会被匹配在一起。
            预期输出: 你的响应应该是一个由花括号包裹的 JSON 格式的数据，，不需要额外的解释或理由。
            示例输出：
            {{
                {{leftId: "heading-0", rightId: "heading-0"}},
                {{leftId: "heading-1", rightId: "heading-1"}}
            }}
            """)

            # 解析大模型返回的匹配结果 (假设返回的是数组)
            try:
                # 如果大模型返回的是数组，直接使用
                match_result = match_result
            except Exception as e:
                match_result = []

            #print("match_result:",match_result)
            # 返回匹配结果
            self.write(json.dumps({
                "match_result": match_result  # 返回直接返回匹配的结果数组
            }))
        except Exception as e:
            self.write(json.dumps({
                "error": str(e),
                "message": "文本匹配时出错"
            }))



class AskInfoboxHandler(tornado.web.RequestHandler):
    def set_default_headers(self):
        self.set_header("Access-Control-Allow-Origin", "*")
        self.set_header("Access-Control-Allow-Methods", "POST, OPTIONS")
        self.set_header("Access-Control-Allow-Headers", "Content-Type")

    def options(self):
        self.set_status(204)
        self.finish()

    def post(self):
        try:
            data = json.loads(self.request.body)
            question = data.get("question")
            left_infobox = data.get("leftInfobox", {})
            right_infobox = data.get("rightInfobox", {})

            if not question:
                raise ValueError("问题不能为空")

            # 处理普通问题
            prompt = f"""
            用户问题: {question}
            
            回答要求:
            1、自行判断是否需要用到infobox数据，如果用到infobox数据，要严格基于以下提供的信息框数据回答
            2. 如果数据不足或无法回答，请明确说明
            3. 除了解释名词外，不要参考任何其他知识或信息
            4. 使用简洁明了的语言
            
            左侧infobox数据:
            {json.dumps(left_infobox, indent=2, ensure_ascii=False)}
            
            右侧infobox数据:
            {json.dumps(right_infobox, indent=2, ensure_ascii=False)}
            """
            
            analysis_result = chat(prompt)
            self.write(json.dumps({"answer": analysis_result}))
            
        except Exception as e:
            self.write(json.dumps({"error": str(e)}))
def make_app():
    return tornado.web.Application([
        (r"/", MainHandler),
        (r"/api/compare-session", CompareSessionHandler),
        (r"/api/analyze-attribute", AnalyzeAttributeHandler),
        (r"/api/ask", AskHandlerV2),
        (r"/html", HtmlHandler),
        (r"/gpt_compare", GPTCompareHandler),
        (r"/gpt_ask", GPTAskHandler),
        (r"/process_text", ProcessTextHandler),
        (r"/merged_json", MergedJsonsHandler),
        (r"/analyze_chart", AnalyzeChartHandler),
        (r"/gpt_ask_chart", GPTAskChartHandler),
        (r"/outline_match", OutlineMatchHandler),
    ], debug=True)

if __name__ == "__main__":
    app = make_app()
    app.listen(8888)  # 监听8888端口
    print("Server is running on http://localhost:8888")
    tornado.ioloop.IOLoop.current().start()
