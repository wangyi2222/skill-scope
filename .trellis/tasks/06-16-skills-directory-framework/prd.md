# PRD：Skills 目录项目框架

## 1. 项目目标

创建一个用于展示网上 Skills 的静态网页。

这个页面的目标不是教学，不负责教用户安装或使用 Skill，而是帮助用户快速了解：

- Skill 是什么
- 每个 Skill 的核心作用是什么
- 它是否适合自己的当前需求
- 去哪里查看更多信息

页面最终承担的是“认知、筛选、跳转”三件事，不承担“编辑、发布、教学、账号系统”。

---

## 2. 产品定位

这是一个 Skills 展示目录，不是教程网站，不是社区网站，也不是后台管理系统。

### 2.1 范围内

- 用中文介绍 Skills 的作用
- 以卡片形式展示每个 Skill
- 支持搜索和筛选
- 点击卡片可跳转到对应 GitHub 页面
- 维护者手动更新数据
- 后续支持根据 GitHub URL 半自动生成卡片数据
- 支持中英文双语展示切换

### 2.2 范围外

- 不做安装教程
- 不做使用教程
- 不做评论、收藏、登录、投稿
- 不做访客编辑
- 当前阶段不做后端管理系统
- 当前阶段不做自动发布流程

---

## 3. 当前页面原则

当前页面样式和结构已经确定，后续以内容和数据流程为主，不再大改界面。

### 3.1 当前结构

```text
+--------------------------------------------------+
| Hero / 页面介绍                                  |
| - Skills 是什么                                  |
| - 这个页面帮助用户做什么                         |
+--------------------------------------------------+

+--------------------------------------------------+
| 搜索与筛选栏                                     |
| - 搜索框                                         |
| - 类别筛选                                       |
| - 适用人群筛选                                   |
| - 语言切换（中文 / English）                     |
+--------------------------------------------------+

+--------------------------------------------------+
| Skills 卡片网格                                  |
| - 卡片更紧凑                                     |
| - 信息不减少                                     |
| - 点击跳转 GitHub                                |
+--------------------------------------------------+
```

### 3.2 当前确认

- 不使用左侧筛选栏
- 筛选统一放在卡片上方
- 页面文案整体保持简洁
- 公开页面不给观众编辑入口
- 卡片尺寸可以更小，但字段信息不减少

---

## 4. 卡片信息模型

卡片只保留帮助用户做选择的信息，不写教程，不展开操作步骤。

### 4.1 卡片展示字段

- 名称
- 一句话简介
- 类别
- 适用人群
- 来源
- 标签
- GitHub 链接

### 4.2 数据字段

当前建议统一为：

```text
name
description
audience
source
category
tags
github_url
```

### 4.3 双语字段方案

为了避免抓取中文仓库时输出中文、抓取英文仓库时输出英文，后续数据模型调整为“双语字段 + 前端切换”。

推荐结构：

```js
{
  name: {
    zh: "会话查看器",
    en: "Session Viewer"
  },
  description: {
    zh: "用于查看和整理 Claude Code 与 Codex 会话记录的本地工具。",
    en: "A local tool for viewing and organizing Claude Code and Codex session records."
  },
  audience: "开发",
  source: "owner/repo",
  category: "工作流",
  tags: ["session", "viewer"],
  github_url: "https://github.com/owner/repo"
}
```

说明：

- `name` 和 `description` 支持 `zh` / `en`
- 其余结构化字段继续保持单值或数组
- 页面通过语言切换决定展示 `zh` 还是 `en`
- 维护者可以手动修改任一语言版本

### 4.4 文案要求

- 不再保留单独的 `use_case`
- 只保留一句 `description`
- `description` 必须直接说明“这个 Skill 是干什么的”
- 避免写成安装说明、使用说明或宣传口号

---

## 5. 分类与筛选模型

为了让用户更快锁定目标 Skill，当前按“搜索 + 两个辅助筛选维度”组织。

### 5.1 第一层：类别 / 用途

这是主要筛选维度，用来回答“这个 Skill 是做什么的”。

当前建议控制在 5 到 7 类，例如：

- 文档
- 开发
- 工作流
- 插件
- 图像
- 自动化
- 研究
- 嵌入式

### 5.2 第二层：适用人群

这是辅助判断层。

当前固定为：

- 开发
- 设计
- 工作流

### 5.4 筛选顺序

```text
搜索框
  ->
类别
  ->
适用人群
```

---

## 6. 数据维护方式

当前阶段仍然坚持“维护者可改，观众只读”。

```text
维护者编辑 data.js
      |
      v
页面读取数据并展示
      |
      v
观众搜索、筛选、点击跳转
```

规则如下：

- 只有维护者可以修改数据
- 观众只能浏览、筛选、跳转
- 当前不提供后台管理页面
- 当前不提供访客提交入口

---

## 7. GitHub URL 半自动卡片生成流程

后续数据更新流程采用“输入 GitHub URL -> 自动生成卡片 -> 写入 data.js -> 维护者可继续修改”的方式。

### 7.1 目标

维护者给出一个 GitHub 仓库地址，系统自动提取公开信息，生成卡片数据，并直接写入或更新 `data.js`。

自动生成只是降低维护者手动录入成本，不代表数据不可修改。写入后维护者仍然可以手动调整名称、简介、类别、适用人群、来源、标签和 GitHub 链接。

### 7.2 流程

```text
GitHub URL
   |
   v
抓取仓库公开信息
   |
   v
优先读取结构化或高质量文本
   |
   +-- SKILL.md
   +-- README.md
   +-- GitHub description
   +-- GitHub topics
   |
   v
提炼出统一卡片数据
   |
   v
直接写入或更新 data.js
   |
   v
页面读取并显示
   |
   v
维护者按需要继续手动修改
```

### 7.3 原则

- 页面本身不承担抓取逻辑
- 抓取脚本和展示页面分离
- 自动生成的目标是减少维护者手动录入成本
- 自动写入后，维护者仍保留最终修改权
- 对同一个 `github_url`，应更新原卡片，而不是重复追加
- 观众只能浏览、筛选和跳转，不能修改卡片数据

---

## 8. 双语策略

### 8.1 目标

无论原始仓库是中文还是英文，网站展示都统一输出为用户选择的语言。

### 8.2 推荐做法

- 自动抓取时先识别和提炼信息
- 生成 `zh` 和 `en` 两份名称与简介
- 页面增加语言切换
- 默认显示中文，保留英文切换

### 8.3 阶段策略

第一阶段：

- 自动抓取仓库信息
- 自动生成双语卡片数据
- 维护者确认后再入库

第二阶段：

- 如果后续接入更强的模型能力，再提升自动双语生成质量

---

## 9. GitHub 自动发现候选 Skill

后续可以从“维护者提供单个 URL”扩展为“系统自动发现候选仓库”。

这一步不应直接写入 `data.js`，而是先生成候选列表，由维护者确认后再进入正式卡片生成流程。

推荐流程：

```text
GitHub Search
   |
   v
按关键词和 topic 搜索候选仓库
   |
   v
抓取 README / SKILL.md / topics / 仓库描述
   |
   v
按规则打分
   |
   v
输出 candidates/skills_candidates.json
   |
   v
维护者确认
   |
   v
再用 generate_skill_draft.py 写入 data.js
```

候选判断信号：

- 强信号：存在 `SKILL.md`
- 强信号：topics 包含 `skill`、`claude-code`、`codex`、`ai-agent`
- 中信号：README 明确提到 Claude Code、Codex、Agent Skill
- 中信号：仓库存在 `.codex`、`.claude`、`skills`、`agents` 目录
- 弱信号：README 或描述出现 workflow、prompt、automation、assistant 等词

原则：

- 自动发现只生成候选，不直接上架
- 是否加入正式页面仍由维护者决定
- 不是所有 AI 项目都是 Skill
- 判断重点是：它是否为 Agent / AI 工作流提供可复用能力

---

## 10. 当前最小实现顺序

```text
1. 固定页面结构与中文文案
2. 固定卡片字段模型
3. 固定搜索、类别、适用人群筛选模型
4. 固定维护者手动更新流程
5. 完成 GitHub URL 卡片生成脚本
6. 调整为双语字段结构
7. 前端增加语言切换
8. 优化重复链接处理与人工校正流程
```

---

## 11. 成功标准

- 用户进入首页后，能快速理解 Skills 的用途
- 用户能通过搜索和筛选快速锁定相关 Skill
- 用户能通过卡片快速比较多个 Skill
- 用户能明确跳转到 GitHub 查看详情
- 维护者能通过 GitHub URL 更高效地产出卡片数据
- 页面最终可稳定支持中文和英文展示
---

## 12. Electronics Vertical Extension

### 12.1 Positioning

SkillScope remains a general AI skills discovery directory. The electronics direction should be implemented as a vertical inside the existing directory, not as a replacement for the whole site.

The vertical goal is to help users discover skills, agents, MCP tools, and workflow helpers that have direct value for electronic information work such as:

- embedded development
- FPGA and HDL workflows
- PCB and EDA work
- signal analysis
- test and measurement
- datasheet and technical document parsing
- laboratory automation

### 12.2 Why a Vertical Instead of a Separate Site

- It preserves the current broad collection strategy
- It creates a clear domain specialty without shrinking the rest of the product
- It lets the site grow by adding more verticals later if they prove valuable

### 12.3 Inclusion Boundary

The electronics vertical should use a practical, not overly strict, inclusion rule.

Include a repository when at least one of these is true:

- it is explicitly a skill, agent, MCP tool, or workflow package for electronics-related work
- its README, SKILL file, examples, or topics show clear use in embedded, hardware, FPGA, EDA, protocol, measurement, or datasheet workflows
- it is a general AI workflow helper whose primary documented value is in electronic information work

Exclude a repository when:

- it is only a generic writing or coding helper with no electronics evidence
- the electronics relevance is hypothetical rather than documented
- the repository is too vague to classify confidently

### 12.4 Proposed Data Extensions

Add the following fields to support the vertical:

```text
domain
subdomain
type
workflow_stage
stack_keywords
```

Recommended values:

- `domain`: `general`, `electronic-information`
- `type`: `skill`, `agent`, `mcp`, `workflow-tool`
- `workflow_stage`: `learn`, `design`, `develop`, `debug`, `test`, `document`

Recommended `subdomain` values:

- `embedded`
- `fpga-hdl`
- `pcb-eda`
- `signal-processing`
- `test-measurement`
- `datasheet-doc`
- `lab-automation`
- `communication`
- `hardware-debug`

`stack_keywords` remains a flexible array for terms such as `stm32`, `esp32`, `uart`, `spi`, `verilog`, or `kicad`.

### 12.5 UI Rollout Strategy

Phase 1:

- keep the current site structure
- add a domain filter
- expose electronics as a vertical entry or quick filter
- show a second-level subdomain filter only when the electronics vertical is active

Phase 2:

- add a dedicated electronics landing page if the dataset becomes large enough
- keep the same underlying card model and filtering logic

Phase 3:

- optionally add curated views such as student-friendly, lab-friendly, or hardware-debug-focused collections

### 12.6 Content Curation Workflow

The vertical should start with a candidate-review workflow before changing `data.js` aggressively.

Recommended order:

1. collect candidate repositories
2. classify them by `type` and `subdomain`
3. record inclusion evidence
4. confirm a first sample batch
5. then extend `data.js` and UI filters

### 12.7 Success Criteria for the Vertical

- The main directory still works as a broad AI skills discovery product
- Electronics users can quickly narrow results to relevant workflows
- The vertical classification uses domain-native language instead of generic labels only
- Maintainers can explain clearly why a repository belongs in the electronics vertical


### 12.8 Resource Scope Decision

Decision: the electronics vertical should use an AI workflow resource scope, not a strict-only Skill scope.

Include `skill`, `agent`, `mcp`, and `workflow-tool` resources when they clearly support electronic information workflows.

Reason: the supply of strict packaged Skills in electronics is still limited, while adjacent Agent/MCP/workflow resources can deliver the same discovery value for embedded, FPGA, EDA, datasheet, test, and lab automation users.

Consequence: each non-strict-Skill entry must show explicit electronics workflow evidence and must not broaden into generic AI tools without domain relevance.

Decision: reposition the public product as electronics-first, with general AI workflow resources retained as supporting inventory.

### 12.9 Homepage Positioning Decision

Decision: the homepage should default to the electronics-first view and provide a clear `All resources` / general directory escape hatch.

Recommended first version:

- hero copy emphasizes electronic information AI workflows
- default filter state highlights `electronic-information`
- general resources remain searchable and accessible
- empty or low-count electronics states should explain that the vertical is curated and growing
- no separate electronics landing page until the electronics inventory is large enough to justify it

Reason: this makes the vertical positioning clear while avoiding an empty early product. General resources provide useful adjacent value and prevent the site from feeling sparse, but they should not dominate the first impression.

Consequence: every resource needs a `domain` classification so the product can switch between electronics-first and all-resource views without reworking the dataset later.

### 12.10 Candidate Pool Strategy

Decision: the next phase should prioritize electronics content curation over additional UI expansion.

Recommended sequence:

1. build an electronics candidate pool before writing many new cards into `data.js`
2. classify each candidate with `type`, `subdomain`, `workflow_stage`, and `stack_keywords`
3. require `inclusion_evidence` so maintainers can explain why the resource belongs in the vertical
4. keep `risk_level` and `risk_reasons` for security review before publishing
5. promote only a small confirmed batch into `data.js` first, then iterate

Candidate pool target for the first pass: 20 to 50 candidates.

Published seed target: 10 to 20 high-confidence resources.

Priority order:

1. embedded development and hardware debug
2. datasheet and technical document workflows
3. PCB / EDA and circuit simulation
4. FPGA / HDL workflows
5. test, measurement, and lab automation

Reason: the website now has the minimum electronics-first UI and data fields. The main remaining product risk is not interaction design, but whether the vertical has enough trustworthy, clearly classified resources.