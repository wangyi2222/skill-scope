<p align="center">
  <img src="./assets/logo.svg" alt="SkillScope" width="96" height="96">
</p>

<h1 align="center">SkillScope</h1>

<p align="center">
  AI Skills 发现与筛选目录 &nbsp;|&nbsp; Discover and Filter AI Skills
</p>

<p align="center">
  <a href="https://www.lean.wang/"><strong>🌐 www.lean.wang</strong></a>
  &nbsp;·&nbsp;
  <a href="https://github.com/wangyi2222/skill-scope/discussions">💬 反馈 / Feedback</a>
  &nbsp;·&nbsp;
  <a href="./LICENSE">📄 MIT</a>
</p>

---

## 这是什么？

SkillScope 是一个**轻量静态目录网站**，用卡片形式整理来自 GitHub 的 AI Skills（面向 Claude Code、Codex、Gemini CLI 等 Agent 平台的能力扩展），帮助你快速了解它们的能力、适用场景、分类和来源，并一键跳转到原项目。

- **只做展示和筛选**，不做安装教程或完整使用文档
- **面向普通访问者只读**，卡片数据由维护者更新
- **零后端依赖**，纯 HTML / CSS / JS 静态部署

## 主要功能

- 🃏 **卡片化展示**：名称、简介、类别、适用人群、标签、来源、GitHub 链接一目了然
- 🔍 **多维度筛选**：按关键词搜索 + 按类别、适用人群过滤
- 🏷️ **高频来源标签**：同一作者/组织收录超过 15 个 Skill 时自动显示快捷入口
- 🌐 **中英双语界面**：一键切换，卡片内容同步翻译
- 🛠️ **半自动数据维护**：Python 脚本从 GitHub URL 生成卡片草稿，支持批量导入
- 🛡️ **安全防护**：XSS 防御、CSP 策略、URL 协议白名单校验

## 技术栈

| 层 | 技术 |
|---|------|
| 页面 | HTML5 + CSS3（Grid / Custom Properties） |
| 逻辑 | Vanilla JavaScript（零框架、零依赖） |
| 数据 | 静态 JS 文件，驱动式卡片渲染 |
| 工具链 | Python 3 脚本（GitHub API + 静态分析） |
| 部署 | 任意静态服务器，当前 Nginx |

## 项目结构

```
.
├── index.html              # 页面入口
├── style.css               # 样式表
├── main.js                 # 渲染、筛选、i18n
├── data.js                 # Skill 数据集（维护者编辑）
├── assets/
│   └── logo.svg            # 站点 Logo
├── scripts/                # 数据维护工具
│   ├── common.py           # 共享模块（数据 I/O、常量、URL 工具）
│   ├── generate_skill_draft.py      # 从 GitHub URL 生成卡片草稿
│   ├── discover_skills.py           # 自动发现候选 Skill
│   ├── import_anbeime_skills.py     # 从 anbeime/skill 导入
│   ├── import_skill_collections.py  # 从 awesome-* 合集导入
│   ├── fill_english_fields.py       # 补全英文字段
│   ├── clean_skill_descriptions.py  # 清理描述文案
│   └── generate_drafts_from_candidates.py  # 批量生成草稿
├── candidates/             # 候选数据池（评分、风险标记）
├── drafts/                 # 卡片草稿
└── .trellis/               # 项目规范与开发记录
```

## 数据维护流程

```
发现候选              评分过滤             生成草稿              人工审核           写入 data.js
─────────────────┼──────────────────┼──────────────────┼─────────────────┼──────────────────
discover_skills   →  import_*_skills  →  generate_draft   →  维护者确认      →  --append-data
                  →  scored_*.json    →  drafts/*.json     →  修正文案/标签
```

### 快速上手

```bash
# 从单个 GitHub 仓库生成卡片草稿（--stdout 预览，--append-data 写入）
python scripts/generate_skill_draft.py https://github.com/owner/repo --stdout
python scripts/generate_skill_draft.py https://github.com/owner/repo --append-data

# 发现某个作者的全部候选 Skill
python scripts/discover_skills.py --owner zuoliangyu --stdout

# 从 anbeime/skill 导入（评分后写入）
python scripts/import_anbeime_skills.py --append-data --limit 50

# 从 awesome-* 合集导入
python scripts/import_skill_collections.py --append-data --limit 60
```

> **注意**：自动生成的草稿建议人工检查名称、简介、类别、适用人群和标签后再上线。

## 本地预览

```bash
# 直接打开 index.html，或用任意静态服务器
python -m http.server 8000
# → http://localhost:8000
```

## 部署

网站目录使用 Git 仓库部署：

```bash
# 服务器端
cd /opt/1panel/www/sites/www.lean.wang/index
git pull

# 本地提交
git add . && git commit -m "更新说明" && git push
```

> 如果页面更新后浏览器仍显示旧内容，使用 `Ctrl + F5` 强制刷新。

## 安全

- 前端对所有动态数据字段做 HTML 实体转义
- Logo URL 仅允许 `https://` 协议
- 页面启用 Content-Security-Policy
- 外部链接均带 `rel="noreferrer"`
- 候选数据含 `risk_level` 评分，高风险条目需人工复核后才上线
- 详情见 [`.trellis/spec/guides/skills-directory-security-guide.md`](.trellis/spec/guides/skills-directory-security-guide.md)

## 参与贡献

- 🐛 **反馈问题**：[GitHub Discussions](https://github.com/wangyi2222/skill-scope/discussions)
- ➕ **推荐新 Skill**：在 Discussions 留下项目链接和简要说明
- 🔧 **代码贡献**：请先阅读 [`.trellis/workflow.md`](.trellis/workflow.md) 了解开发流程

## License

[MIT](./LICENSE) © 2026 wangyi2222
