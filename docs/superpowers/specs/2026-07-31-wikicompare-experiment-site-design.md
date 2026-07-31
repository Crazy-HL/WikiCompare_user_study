# WikiCompare 实验专用网站设计

**日期：** 2026-07-31  
**项目根目录：** `/Users/hl/Documents/wikiCompare`  
**原系统目录：** `/Users/hl/Documents/wikiCompare/wikitable-vue`  
**实验版目录：** `/Users/hl/Documents/wikiCompare/wikitable-vue-experiment`  
**参考材料：** `/Users/hl/Desktop/文件/WikiCompare实验设计.docx`

## 1. 目标

在不破坏原有 WikiCompare 系统的前提下，复制出一个独立实验版网站，用于正式或小规模线上双文档比较阅读实验。实验版网站需要支持：

1. 参与者按编号进入受控实验流程；
2. 系统自动分配两个实验阶段的系统条件和材料；
3. 参与者端只显示阅读、问答和答题所需内容，不显示计时器、后台指标或题目管理功能；
4. 管理员后台可生成、重生成、保存和冻结 Q1-Q5；
5. 管理员后台可查看答题情况、答案来源、每题用时、阶段用时和导出数据；
6. 后端使用本地 JSON/CSV 文件保存数据，不引入数据库。

## 2. 非目标

第一版不实现以下内容：

1. 复杂账号系统或多角色权限数据库；
2. 数据库保存；
3. 自动评分；
4. 复杂统计图表；
5. 大规模并发优化；
6. 让参与者自由选择实验系统或条件顺序。

## 3. 文件夹策略

原系统保留在：

```text
/Users/hl/Documents/wikiCompare/wikitable-vue
```

创建实验版副本：

```text
/Users/hl/Documents/wikiCompare/wikitable-vue-experiment
```

后续所有实验网站改动只发生在实验版目录。原目录作为可回退的原始 WikiCompare 版本保留。

## 4. 参与者端流程

### 4.1 入口

参与者进入实验网站后只需要选择实验编号，例如：

```text
P01, P02, ..., P12
```

参与者不输入自由文本编号，也不选择 WikiCompare 或 ChatGPT。系统根据编号自动决定条件顺序和材料分配。

### 4.2 分配规则

| 编号 | 分组 | 第一阶段 | 第二阶段 |
|---|---|---|---|
| P01 / P05 / P09 | S1 | WikiCompare + M1 | ChatGPT + M2 |
| P02 / P06 / P10 | S2 | ChatGPT + M2 | WikiCompare + M1 |
| P03 / P07 / P11 | S3 | ChatGPT + M1 | WikiCompare + M2 |
| P04 / P08 / P12 | S4 | WikiCompare + M2 | ChatGPT + M1 |

超过 P12 的编号可继续按编号序号对 4 取模循环分配。

### 4.3 阶段流程

每个参与者完成两个阶段：

1. 选择实验编号；
2. 系统创建隐藏实验 ID；
3. 进入第一阶段；
4. 加载对应材料和系统条件；
5. 显示统一说明、文章/表格/问答界面、Q1-Q5 答题区和 Q6 答题区；
6. 参与者完成第一阶段并提交；
7. 显示休息提示；
8. 进入第二阶段；
9. 加载另一套材料和另一系统条件；
10. 参与者完成第二阶段并提交；
11. 显示完成页。

### 4.4 参与者端隐藏内容

参与者端不得显示：

1. 计时器；
2. 每题用时或总用时；
3. 管理员后台指标；
4. 题目生成、重生成、保存或冻结按钮；
5. 条件选择按钮；
6. 数据导出按钮。

时间数据由前端静默记录并提交到后端。

## 5. 两个实验条件

### 5.1 WikiCompare 条件

WikiCompare 条件复用现有系统能力：

1. 左右文章展示；
2. 中央动态三栏比较表；
3. LLM 问答；
4. 来源跳转和高亮；
5. 表格属性 Compare 分析。

参与者可以在阅读和使用系统过程中填写 Q1-Q6 答案。

### 5.2 ChatGPT 条件

ChatGPT 条件在实验网站内实现为受控基线界面，不跳转到外部 ChatGPT。

该界面显示：

1. 同组材料的左右文章；
2. 冻结后的 ChatGPT 静态三栏表；
3. 简化的自然语言问答区域；
4. Q1-Q6 答题区。

此设计可以统一记录数据，并避免参与者使用外部搜索、插件、连接器或未受控会话能力。

## 6. 题目生成与冻结

题目管理仅管理员可见。

### 6.1 Q1-Q5

管理员后台支持：

1. 选择材料 M1 或 M2；
2. 点击自动生成 Q1-Q5；
3. 后端基于实验文档中的“提示词 2”调用 LLM 生成题目和隐藏标准答案；
4. 管理员查看题目、答案格式、理解目标、gold atoms 和来源编号；
5. 如果不合适，点击重新生成；
6. 如果合适，保存并冻结为该材料的固定题目；
7. 冻结后参与者端使用固定题目；
8. 管理员后续可以解冻或重新生成。

同一材料在两个条件中使用完全相同的 Q1-Q5。

### 6.2 Q6

Q6 固定为：

```text
在阅读两篇文章并回答前五个比较问题的过程中，你还产生了哪些额外的发现和问题？

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

不要重复Q1-Q5。没有额外发现或问题时填写“无”。
```

## 7. 管理员后台

后台入口建议为：

```text
/admin
```

第一版采用简单密码保护，密码从环境变量读取：

```bash
EXPERIMENT_ADMIN_PASSWORD=your-password
```

### 7.1 材料与题目管理

管理员后台需要支持：

1. 查看材料 M1、M2；
2. 查看每组材料的左右文章标题和来源；
3. 生成 Q1-Q5；
4. 重生成 Q1-Q5；
5. 保存并冻结题目；
6. 解冻题目；
7. 查看隐藏标准答案和评分原子；
8. 查看 ChatGPT 静态三栏表。

### 7.2 结果查看

管理员后台需要支持查看：

1. 参与者编号；
2. 系统隐藏实验 ID；
3. 分组 S1-S4；
4. 两个阶段的系统条件和材料；
5. 每道题答案；
6. 每道题主要来源 M/A/T；
7. 证据位置；
8. 每题用时；
9. 每阶段总用时；
10. Q6 额外发现和问题。

### 7.3 导出

后台支持导出：

1. 完整 JSON；
2. 参与者汇总 CSV；
3. 每题明细 CSV。

## 8. 后端本地文件结构

实验版后端新增数据目录：

```text
wikitable-vue-experiment/server/experiment_data/
  config/
    materials.json
    assignment.json
    questions/
      M1.json
      M2.json
    static_tables/
      M1.json
      M2.json
  submissions/
    exp-YYYYMMDD-random.json
  exports/
    submissions_summary.csv
    answers_detail.csv
```

### 8.1 questions 文件

每个材料一个题目文件，包含：

1. material_id；
2. frozen 状态；
3. version；
4. generated_at；
5. prompt_version；
6. questions；
7. hidden gold answers；
8. source ids。

### 8.2 submissions 文件

每次完整实验提交保存一份 JSON，包含：

1. experiment_id；
2. participant_code；
3. assignment_group；
4. created_at；
5. completed_at；
6. stages；
7. browser metadata；
8. answer records。

## 9. 需要记录的数据字段

### 9.1 实验级字段

1. experiment_id：系统隐藏 ID；
2. participant_code：参与者选择的编号；
3. assignment_group：S1-S4；
4. started_at；
5. completed_at；
6. total_duration_ms。

### 9.2 阶段级字段

1. stage_index；
2. condition：wikicompare 或 chatgpt；
3. material_id：M1 或 M2；
4. question_version；
5. stage_started_at；
6. stage_submitted_at；
7. stage_duration_ms。

### 9.3 题目级字段

1. question_id：Q1-Q6；
2. question_text；
3. answer；
4. primary_source：M/A/T；
5. left_evidence；
6. right_evidence；
7. answer_started_at；
8. answer_updated_at；
9. submitted_at；
10. duration_ms。

## 10. 前端结构建议

在实验版前端新增：

```text
src/experiment/
  assignment.js
  experimentApi.js
  experimentStore.js
  timing.js
  q6.js

src/components/experiment/
  ParticipantEntry.vue
  ExperimentShell.vue
  StageHeader.vue
  AnswerPanel.vue
  BreakScreen.vue
  CompleteScreen.vue
  ChatGptCondition.vue
  AdminLogin.vue
  AdminDashboard.vue
  AdminQuestions.vue
  AdminSubmissions.vue
```

现有 WikiCompare 三栏布局保留，并通过 `ExperimentShell` 嵌入。

## 11. 后端 API 建议

新增接口：

```text
GET  /api/experiment/config
POST /api/experiment/start
GET  /api/experiment/questions?materialId=M1
POST /api/experiment/stage-submit
POST /api/experiment/complete

POST /api/admin/login
GET  /api/admin/materials
POST /api/admin/questions/generate
POST /api/admin/questions/freeze
POST /api/admin/questions/unfreeze
GET  /api/admin/submissions
GET  /api/admin/export/submissions.csv
GET  /api/admin/export/answers.csv
```

后端继续使用 Tornado，与现有 server.py 集成。

## 12. 初始实现顺序

1. 复制 `wikitable-vue` 为 `wikitable-vue-experiment`；
2. 添加实验配置和数据目录；
3. 实现编号到 S1-S4 的分配逻辑；
4. 实现参与者入口和两阶段流程；
5. 实现答题面板和静默计时；
6. 实现后端 JSON 保存；
7. 实现 CSV 导出；
8. 实现管理员后台登录；
9. 实现管理员题目生成、重生成和冻结；
10. 实现管理员结果查看；
11. 运行前后端测试和构建验证。

## 13. 成功标准

第一版完成后应满足：

1. 原始 `/Users/hl/Documents/wikiCompare/wikitable-vue` 未被改动；
2. 实验版 `/Users/hl/Documents/wikiCompare/wikitable-vue-experiment` 可以独立运行；
3. 参与者只能通过编号进入自动分配流程；
4. 每位参与者完成两个条件，且顺序按 S1-S4 分配；
5. Q1-Q5 可由管理员生成、重生成、冻结；
6. 参与者端不显示计时或后台信息；
7. 后端能保存完整 JSON；
8. 后台能导出 CSV；
9. 前端构建通过；
10. 后端测试通过或新增实验 API 测试通过。
