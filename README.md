# SkillScope

SkillScope 是一个 AI Skills 发现与筛选目录，用卡片形式整理来自 GitHub 的 Skills，帮助用户快速了解它们的作用、适用人群、类别和来源，并跳转到原项目继续查看。

访问地址：

```text
https://www.lean.wang/
```

## 项目定位

这个项目只做 Skills 的展示、筛选和跳转，不做安装教程，也不做完整使用文档。页面面向普通访问者只读，卡片数据由维护者更新。

## 主要功能

- 卡片化展示 Skills 的名称、简介、类别、适用人群、来源、标签和 GitHub 链接
- 支持按关键词、类别、适用人群筛选
- 当同一作者或组织收录超过 15 个 Skills 时，显示高频来源标签
- 支持从 GitHub URL 半自动生成卡片草稿并写入 `data.js`
- 静态网站部署，不依赖后端服务

## 数据维护

正式展示的数据集中在：

```text
data.js
```

维护者可以手动编辑 `data.js`，也可以使用脚本从 GitHub 仓库生成卡片：

```bash
python scripts/generate_skill_draft.py https://github.com/owner/repo --append-data
```

生成后仍建议人工检查名称、简介、类别、适用人群、来源和标签。

## 本地预览

这个项目是静态页面，可以直接打开 `index.html`，也可以用任意静态服务器预览。

```bash
python -m http.server 8000
```

然后访问：

```text
http://localhost:8000
```

## 部署更新

服务器网站目录使用 Git 仓库部署：

```bash
cd /opt/1panel/www/sites/www.lean.wang/index
git pull
```

本地修改后先提交并推送：

```bash
git add .
git commit -m "更新说明"
git push
```

如果页面更新后浏览器仍显示旧内容，使用 `Ctrl + F5` 强制刷新。
