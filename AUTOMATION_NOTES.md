# Skill Draft Generator

当前项目提供一个半自动卡片生成脚本，用来从 GitHub URL 生成 Skill 卡片数据。

## 基本流程

```text
GitHub URL
  ->
抓取仓库基础信息
  ->
读取 README / SKILL.md / 可选结构化文件
  ->
提炼一句话简介
  ->
自动推断平台、类别、适用人群、难度和标签
  ->
写入 data.js
```

## 生成并查看结果

```bash
python scripts/generate_skill_draft.py https://github.com/<owner>/<repo> --stdout
```

这个命令会：

- 生成 `drafts/<owner>__<repo>.json`
- 在终端打印生成结果

## 直接新增到 data.js

```bash
python scripts/generate_skill_draft.py https://github.com/<owner>/<repo> --append-data
```

这个命令会：

- 生成 `drafts/*.json`
- 写入 `data.js`
- 如果 `github_url` 已存在，则跳过，不覆盖原卡片
- 如果 `github_url` 不存在，则追加新卡片

写入后维护者仍然可以手动修改 `data.js`。

## 强制更新已有卡片

```bash
python scripts/generate_skill_draft.py https://github.com/<owner>/<repo> --update-data
```

这个命令会：

- 如果 `github_url` 已存在，则更新原卡片
- 如果 `github_url` 不存在，则追加新卡片

只有明确想覆盖手动修改内容时，才使用 `--update-data`。

## 当前已支持

- GitHub 仓库 URL 输入
- 仓库 metadata 抓取
- `README.md` / `SKILL.md` 读取
- 简单读取 `skill.yaml` / `project.yaml` / `skill.json` / `project.json`
- 自动提取 `tags`
- 自动推断 `platforms`
- 自动推断 `audience`
- 自动推断 `category`
- 自动推断 `level`
- 简介统一收敛为一句话说明作用
- 自动尝试提取 `logo_url`，优先读取 README 图片和常见图标路径
- `--append-data` 默认保护已有卡片，不覆盖手动修改
- `--update-data` 才会按 `github_url` 更新已有卡片

## 当前说明

- `description` 只保留一句话
- 不再单独生成 `use_case`
- 自动分类和难度判断基于关键词规则，生成后仍建议人工检查
- 双语 `zh / en` 字段还未实现

## Logo 字段

卡片支持可选字段：

```json
"logo_url": "https://raw.githubusercontent.com/owner/repo/HEAD/path/to/logo.png"
```

页面会优先显示 `logo_url`。如果没有这个字段，会显示项目名称首字母作为占位。

自动生成草稿时会尝试从以下位置提取 logo：

- README 里的第一张图片
- `src-tauri/icons/icon.png`
- `src-tauri/icons/128x128.png`
- `public/logo.png`
- `assets/logo.png`
- `logo.png`
- `icon.png`

## 自动发现候选 Skill

如果不想手动提供单个 GitHub URL，可以先运行候选发现脚本：

```bash
python scripts/discover_skills.py --stdout
```

如果只想扫描某个作者或组织的仓库，而不是全 GitHub 搜索，可以使用：

```bash
python scripts/discover_skills.py --owner zuoliangyu --stdout
```

这个脚本会：

- 使用一组 GitHub 搜索关键词寻找候选仓库
- 或者在 `--owner` 模式下只扫描指定作者/组织的公开仓库
- 读取仓库 metadata、topics、README 和 SKILL.md
- 根据是否存在 `SKILL.md`、是否包含 Agent / Skill 相关关键词、是否有相关目录进行打分
- 根据 README 和仓库 metadata 做安全风险初筛，输出 `risk_level` 和 `risk_reasons`
- 输出到 `candidates/skills_candidates.json`

它不会修改 `data.js`。候选确认后，再用 `generate_skill_draft.py` 加入正式数据。

候选里的 `risk_level` 只是提醒你人工复核，不代表仓库一定安全或一定恶意。

候选文件还会标记当前状态：

- `published` / `已上卡片`：已经存在于 `data.js`
- `candidate` / `候选，待确认`：可以人工确认是否上卡片
- `blocked_high_risk` / `高风险，需人工复核`：风险较高，不建议直接上卡片

## 从候选生成草稿

当 `candidates/skills_candidates.json` 已经生成后，可以批量把候选转成草稿：

```bash
python scripts/generate_drafts_from_candidates.py --stdout
```

默认只处理 `confidence=high` 且 `risk_level!=high` 的候选，并把草稿写到 `drafts/*.json`。

它默认会跳过已经上卡片的 `published` 候选，避免重复生成或重复写入。

如果你确认要顺手写入 `data.js`，再加：

```bash
python scripts/generate_drafts_from_candidates.py --append-data
```

这一步仍然保留你手动确认的控制权，不会绕过你直接上架。

如果想做更严格的候选判断，可以加上：

```bash
python scripts/discover_skills.py --check-paths --stdout
```

这会额外检查仓库里是否存在 `.codex`、`.claude`、`skills`、`agents` 等目录，判断会更准，但速度更慢，也更容易遇到 GitHub 限流。

推荐流程：

```text
discover_skills.py
  ->
candidates/skills_candidates.json
  ->
人工确认候选
  ->
generate_skill_draft.py --append-data
```

## 从 anbeime/skill 技能商店导入

`anbeime/skill` 是一个聚合型技能仓库，不应该把仓库本身做成一张卡片，而应该先把它收集的 Skill 当成候选池评分。

当前流程：

```bash
python scripts/import_anbeime_skills.py
```

这个命令会读取 `candidates/anbeime_skills.json`，生成：

- `candidates/anbeime_scored_skills.json`：完整评分结果，包含 `score`、`status`、`risk_level` 和判断原因。
- 不修改 `data.js`。

确认后再执行：

```bash
python scripts/import_anbeime_skills.py --append-data --limit 100
```

写入规则：

- 只追加 `status=selected` 的条目。
- 已存在的 `github_url` 自动跳过，避免重复卡片。
- 有明显风险词或无法稳定生成中文简介的条目先保留为候选，不直接上线。
- 正式卡片仍写入 `data.js`，维护者可以继续手动修改。

## 从 awesome skill 合集仓库导入

多个 awesome 仓库本质上是 Skill 候选池，不能把合集仓库本身直接做成卡片。当前使用独立脚本解析 README 和目录结构：

```bash
python scripts/import_skill_collections.py
```

这个命令会读取 `candidates/collections/*README.md` 和 `*contents.json`，输出：

- `candidates/collections/scored_collection_skills.json`：完整评分结果。
- 不修改 `data.js`。

确认后再执行：

```bash
python scripts/import_skill_collections.py --append-data --limit 60
```

写入规则：

- 只追加 `status=selected` 的条目。
- `score > 7`、`risk_level=low` 且不是合集首页 / 泛目录的条目会被标记为 `selected`。
- 通过 canonical GitHub URL 去重，已存在的卡片自动跳过。
- 合集首页、泛目录、高风险词条只保留为候选，不直接上线。
- 正式卡片仍写入 `data.js`，维护者可以继续手动修正文案、分类和标签。
