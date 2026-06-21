# SkillScope 项目构建总结

> 这份文档用于复盘 SkillScope 从 0 到当前版本的构建过程：我们如何定义目标、拆解需求、实现功能、处理问题、部署上线，以及整个过程中采用的方法。

## 1. 项目起点

最初的想法是做一个“网上 Skills 的汇总网页”。

核心要求很明确：

- 介绍 Skills 的作用，但不教用户安装和使用
- 让用户快速理解每个 Skill 是干什么的
- 用户根据自己的需求选择合适的 Skill
- 每个 Skill 做成卡片样式
- 卡片能点击跳转到对应 GitHub 地址
- 访问者只能浏览，不能自己新增或修改
- 维护者可以手动更新卡片数据

因此项目一开始就被定位为一个“发现与选择层”，不是教程站、社区站、后台系统或 Skill 商店。

## 2. 规划方式

项目采用了 Trellis 流程来持续沉淀需求和规则。

主要规划文件包括：

- `.trellis/tasks/06-16-skills-directory-framework/prd.md`
- `.trellis/spec/guides/skills-directory-product-guide.md`
- `.trellis/spec/guides/skills-directory-security-guide.md`
- `.trellis/spec/frontend/quality-guidelines.md`

规划过程中没有一开始直接写复杂系统，而是先用 ASCII 图和 PRD 固定项目边界：

```text
+-----------------------------+
| 页面介绍 / Hero             |
+-----------------------------+
| 搜索与筛选                  |
+-----------------------------+
| Skills 卡片网格             |
+-----------------------------+
| 点击跳转 GitHub             |
+-----------------------------+
```

后来页面布局经过讨论，从顶部筛选逐步调整为左侧栏结构，右侧展示卡片，用来更高效利用宽屏空间。

## 3. 产品边界

项目最终确认只做四件事：

- 展示 Skills
- 搜索和筛选 Skills
- 帮用户比较卡片信息
- 跳转 GitHub 查看原项目

明确不做：

- 安装教程
- 详细使用教程
- 用户账号
- 访客投稿
- 后台 CMS
- 自动无审核上架
- 复杂推荐算法

这个边界很重要。它避免项目过早变成一个难维护的后台系统。

## 4. 技术路线

项目采用纯静态网站实现：

```text
index.html   页面结构
style.css    页面样式
main.js      渲染、筛选、语言切换
data.js      Skills 数据
assets/      Logo 等静态资源
scripts/     数据生成与导入脚本
```

选择静态网站的原因：

- 部署简单
- 不需要数据库
- 不需要后端服务
- 维护者可以直接改数据文件
- 访问者只读，权限模型简单
- 适合当前阶段快速上线

## 5. 卡片数据模型演进

最早的卡片字段包括：

```text
name
description
use_case
audience
level
platforms
tags
category
github_url
```

随着讨论推进，字段不断收敛。

最终保留：

```text
name
description
audience
source
category
tags
github_url
logo_url
```

关键变化：

- 删除 `use_case`，避免和简介重复
- 删除 `level`，因为难度判断标准不稳定
- 删除 `platforms`，因为平台兼容容易误导且维护成本高
- 用 `source` 替代难度，用来标注作者、组织和仓库路径
- `name` 只保留 Skill 名，不重复显示作者和组织
- `description` 只保留一句话，直接说明作用

## 6. 筛选模型演进

最初讨论过三层筛选：

```text
平台 -> 类别 -> 适用人群
```

后来删除平台维度，最终变成：

```text
搜索框
  ->
类别
  ->
适用人群
  ->
高频来源标签
```

原因：

- 平台字段维护成本高
- 很多 Skill 可能跨 Claude、Codex、Cursor、Gemini 等 Agent 使用
- 强行分类平台容易误导用户
- 类别和适用人群更稳定

后来又加入“高频来源标签”：

- 当同一作者或组织超过 15 个 Skills 时自动显示
- 固定展示 `anthropics` 和 `zuoliangyu`
- 用户可快速筛选某个重要来源

## 7. 页面设计过程

页面设计经历了几次关键调整：

1. 最初是简洁卡片网格
2. 后来讨论顶部筛选和左侧筛选哪种更合适
3. 确认使用左侧栏，右侧显示卡片
4. 背景改成类似 Apple 风格的柔和渐变
5. 卡片做玻璃感和圆角
6. 卡片从全局等高改为“按行等高”
7. 通过缩小内部间距减少卡片留白
8. 保持整体干净、简洁、可快速扫描

关于卡片高度，我们讨论过“内容少的卡片单独排一列，内容多的排一列”的方案。最后没有采用，因为它会让页面变成瀑布流，影响横向比较。最终选择了更稳定的方案：

```text
同一行卡片等高，不同卡片行可有不同高度
```

这样既减少留白，又保持整齐。

## 8. 数据来源和自动化

一开始数据由维护者手动填写。

后来增加了半自动流程：

```text
GitHub URL
  ->
抓取 README / SKILL.md / description / topics
  ->
生成卡片草稿
  ->
写入 data.js
  ->
维护者人工检查和修改
```

相关脚本包括：

- `scripts/generate_skill_draft.py`
- `scripts/discover_skills.py`
- `scripts/generate_drafts_from_candidates.py`
- `scripts/import_anbeime_skills.py`
- `scripts/import_skill_collections.py`
- `scripts/fill_english_fields.py`

后来又支持从 Skill 合集仓库中解析候选，例如：

- `anbeime/skill`
- `awesome-agent-skills`
- `google/skills`
- `github/awesome-copilot`
- `anthropics/skills`
- `NVIDIA/skills`

为了避免把普通 AI 项目误判成 Skill，加入了评分和风险判断。

## 9. 候选评分和安全判断

自动发现不能直接上架。我们设计了候选流程：

```text
发现候选
  ->
规则打分
  ->
风险判断
  ->
输出 candidates
  ->
维护者确认
  ->
写入 data.js
```

判断 Skill 的核心标准是：

```text
它是否为 Agent / AI 工作流提供可复用能力？
```

强信号：

- 存在 `SKILL.md`
- topic 包含 `skill`、`claude-code`、`codex`、`ai-agent`
- README 明确提到 Agent Skill
- 仓库存在 `.codex`、`.claude`、`skills`、`agents` 等目录

风险信号：

- README 诱导执行不明脚本
- 要求输入密钥、token 或敏感凭据
- 仓库信息过少
- 功能描述和代码结构不一致
- 存在可疑下载链接

最终规则是：候选可以自动生成，但正式上线必须由维护者确认。

## 10. 双语功能

双语不是一步到位，而是分阶段实现。

第一阶段：界面双语。

- 增加 `中文 / English` 按钮
- 页面固定文案可切换
- 筛选字段、按钮、空状态、反馈区可切换
- 类别和适用人群显示可切换

第二阶段：卡片数据兼容双语字段。

前端同时支持：

```js
name: "report"
description: "用于..."
```

和：

```js
name: { zh: "report", en: "report" }
description: { zh: "用于...", en: "Used for..." }
```

第三阶段：迁移现有数据。

489 张卡片都迁移为：

```js
name: { zh: "...", en: "..." }
description: { zh: "...", en: "..." }
```

英文初稿由 `scripts/fill_english_fields.py` 生成。它是可用占位，不是人工精翻。重要卡片后续可以人工修正。

## 11. 遇到的问题和解决方式

### 11.1 README 抓取信息不准确

早期从 GitHub description 抓取时，很多仓库简介会变成：

```text
Contribute to owner/repo development by creating an account on GitHub.
```

这类信息没有价值。

解决方式：

- 优先读取 README / SKILL.md
- 再读取 description / topics
- 简介统一收敛为一句话作用说明
- 生成后允许维护者手动修改

### 11.2 卡片简介和适用场景重复

原来同时有 `description` 和 `use_case`，容易重复。

解决方式：

- 删除 `use_case`
- `description` 只保留一句话，说明 Skill 做什么

### 11.3 难度字段标准不清

讨论过 `level`，但很难客观判断 Skill 难度。

解决方式：

- 删除 `level`
- 改用 `source`
- 让用户通过来源、类别、简介判断是否值得点击

### 11.4 平台分类不稳定

最初考虑按 Claude、Codex、Cursor、Gemini 分类。

问题是很多 Skill 不是严格绑定某个平台，平台判断容易过时。

解决方式：

- 删除平台筛选
- 删除卡片“支持平台”
- 删除数据里的 `platforms`
- 改为类别、适用人群和来源筛选

### 11.5 卡片留白过多

卡片早期使用全局统一高度，内容少的卡片底部空白很大。

解决方式：

- 改为按行统一高度
- 调整卡片内部间距
- 保持横向比较体验

### 11.6 GitHub Pages 与自有服务器混用

早期页面在 GitHub Pages 可访问，后来改成自有服务器：

```text
https://www.lean.wang/
```

问题是服务器目录不是 `/www/...`，而是 1Panel 的实际目录：

```text
/opt/1panel/www/sites/www.lean.wang/index
```

解决方式：

- 通过 1Panel 文件管理确认真实目录
- 将原手动上传目录备份
- 在网站目录中 `git clone` 仓库
- 后续用 `git pull` 更新服务器

### 11.7 Git 安全目录报错

服务器执行 `git pull` 时出现：

```text
fatal: detected dubious ownership
```

原因是目录所有权和当前执行用户不一致。

解决方式：

```bash
git config --global --add safe.directory /opt/1panel/www/sites/www.lean.wang/index
```

### 11.8 浏览器缓存导致页面显示 0 个 Skills

有一次服务器文件已更新，但浏览器仍加载旧 `main.js`，导致报错：

```text
Cannot read properties of null
```

解决方式：

- 给静态资源加版本号
- 每次重要前端或数据更新递增版本

示例：

```html
<script src="./data.js?v=20260620-8"></script>
<script src="./main.js?v=20260620-8"></script>
```

### 11.9 XSS 和安全问题

代码审查后发现动态数据插入页面时需要防止 XSS。

解决方式：

- 增加 `escapeHtml()`
- 对动态 HTML 内容做转义
- `logo_url` 只允许 `https://`
- 外链加 `rel="noreferrer"`
- 增加前端质量规范

### 11.10 resize 性能问题

原来卡片高度同步可能造成 layout thrashing。

解决方式：

- DOM 写入和读取分阶段
- resize 事件用 `requestAnimationFrame` 控制
- 按行计算高度，减少不必要重排

## 12. 使用的方法

整个项目不是一次性设计完成，而是迭代出来的。

主要方法包括：

- 先明确产品边界，再写代码
- 用 Trellis 记录 PRD、规则和开发过程
- 每次关键讨论都沉淀到 `.trellis/spec`
- 先做最小可用版本，再逐步增强
- 数据和页面分离
- 自动生成和人工确认结合
- 用 Git 提交保存每个阶段
- 通过截图和实际页面反馈调整 UI
- 用脚本减少重复维护成本
- 用代码审查补安全、性能和可访问性问题

可以概括为：

```text
讨论需求
  ->
写入 Trellis
  ->
实现最小版本
  ->
用户查看反馈
  ->
修正设计和数据
  ->
脚本化重复流程
  ->
提交 Git
  ->
部署服务器
```

## 13. 当前成果

当前项目已经具备：

- 静态站点页面
- 左侧介绍和筛选栏
- 右侧卡片网格
- 搜索、类别、适用人群筛选
- 高频来源标签
- GitHub 跳转
- Logo 展示
- 中英文界面切换
- 双语卡片字段结构
- 489 张 Skills 卡片数据
- 半自动 GitHub URL 卡片生成
- 候选发现和评分
- 风险标记
- awesome 合集导入
- anbeime/skill 导入
- 英文初稿补全脚本
- 服务器部署到 `https://www.lean.wang/`
- GitHub 仓库作为代码源和服务器更新源

## 14. 当前部署方式

本地开发完成后：

```bash
git add .
git commit -m "更新说明"
git push
```

服务器更新：

```bash
cd /opt/1panel/www/sites/www.lean.wang/index
git pull
```

正式访问地址：

```text
https://www.lean.wang/
```

GitHub 仓库主要用于：

- 代码存储
- 版本管理
- 服务器拉取更新
- 对外查看源码

正式网站不再依赖 GitHub Pages。

## 15. 后续建议

优先级较高：

- 人工校正重点卡片的英文简介
- 持续清理不准确的自动生成简介
- 为新增卡片建立人工审核清单
- 定期检查 GitHub 链接是否失效

中期可以考虑：

- 将 `data.js` 拆成 JSON 数据文件
- 增加构建脚本自动更新资源版本号
- 增加简单测试脚本检查数据结构
- 增加更多高质量来源

暂时不建议做：

- 后台 CMS
- 用户登录
- 访客自由投稿
- 无审核自动抓取全 GitHub
- 复杂推荐算法

原因是当前项目的价值来自“干净、可信、可筛选”，不是功能复杂。

## 16. 总结

SkillScope 的构建过程不是简单做一个网页，而是从产品定位、信息架构、数据结构、自动化维护、安全审查、部署方式逐步搭建出来的。

项目最终形成了一个清晰的工作模式：

```text
维护者控制数据质量
脚本降低录入成本
页面只负责展示和筛选
Git 管理版本
服务器承载正式访问
Trellis 沉淀规则和经验
```

这套方式让项目既能快速上线，也能继续长期维护。
