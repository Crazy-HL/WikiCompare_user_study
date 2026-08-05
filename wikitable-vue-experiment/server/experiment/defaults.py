Q6_TEXT = """在阅读两篇文章并回答前五个比较问题的过程中，你还产生了哪些额外的发现和问题？

请把每一条分开记录。

【额外发现】
- 发现内容：写成具体的两篇文章比较陈述；
- 主要来源：M 大模型/系统回答、A 文章原文或 T 三栏表格；
- 左侧证据位置：
- 右侧证据位置：

【额外问题】
- 问题内容：写成具体的双文档比较问题；
- 主要触发来源：M、A或T；
- 当前材料能否回答：能、部分能或不能；
- 如果能，写出当前答案和证据；
- 如果不能，写出还缺少什么信息。

不要重复Q1-Q5。没有额外发现或问题时填写“无”。"""

DEFAULT_MATERIALS = [
    {
        "id": "M1",
        "label": "M1：Economy of South Korea vs Economy of Japan",
        "leftTitle": "Economy of South Korea",
        "rightTitle": "Economy of Japan",
        "leftPresetId": "economy-korea-japan",
        "rightPresetId": "economy-korea-japan",
        "leftUrl": "https://en.wikipedia.org/w/index.php?title=Economy_of_South_Korea&oldid=1273871505",
        "rightUrl": "https://en.wikipedia.org/w/index.php?title=Economy_of_Japan&oldid=1297943898",
    },
    {
        "id": "M2",
        "label": "M2：India 2026 vs Indonesia 2026",
        "leftTitle": "India 2026",
        "rightTitle": "Indonesia 2026",
        "leftPresetId": "openfactbook-india-indonesia",
        "rightPresetId": "openfactbook-india-indonesia",
        "leftUrl": "https://openfactbook.org/countries/india/",
        "rightUrl": "https://openfactbook.org/countries/indonesia/",
    },
]

QUESTION_PROMPT_VERSION = "wikicompare-experiment-prompt-3-2026-08-05"
