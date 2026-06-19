#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import pathlib
import re
from urllib.parse import urlparse


ROOT = pathlib.Path(__file__).resolve().parent.parent
DEFAULT_SOURCE = ROOT / "candidates" / "anbeime_skills.json"
DEFAULT_REPORT = ROOT / "candidates" / "anbeime_scored_skills.json"
DATA_FILE = ROOT / "data.js"

CATEGORY_MAP = {
    "Document Creation": "文档",
    "Creative and Design": "图像",
    "Development": "开发",
    "Development and Testing": "开发",
    "Security Skills by Trail of Bits Team": "开发",
    "Skills by Vercel Engineering Team": "开发",
    "Skills by Hugging Face Team": "研究",
    "Context Engineering": "工作流",
    "Skills by Cloudflare Team": "开发",
    "Skills by Sentry team for their dev team.": "开发",
    "n8n Automation": "自动化",
    "Skills by fal.ai Team": "图像",
    "Skills by Sanity Team": "工作流",
    "Marketing": "工作流",
    "Skills by Expo Team": "开发",
    "Skills by Better Auth Team": "开发",
    "Branding and Communication": "工作流",
    "Meta": "工作流",
    "Skills by Google Labs (Stitch)": "图像",
    "Skills by Stripe Team": "开发",
    "Skills by Supabase Team": "开发",
    "Skills by Tinybird Team": "开发",
    "Skills by Neon Team": "开发",
    "Skill by Cloudflare Engineer": "开发",
    "Skills by Remotion Team": "图像",
    "Productivity and Collaboration": "工作流",
    "Specialized Domains": "研究",
    "Other": "工作流",
}

AUDIENCE_BY_CATEGORY = {
    "文档": "工作流",
    "图像": "设计",
    "设计": "设计",
    "开发": "开发",
    "嵌入式": "开发",
    "自动化": "开发",
    "研究": "工作流",
    "工作流": "工作流",
}

EMBEDDED_KEYWORDS = [
    "embedded",
    "stm32",
    "gd32",
    "mspm0",
    "firmware",
    "probe",
    "openocd",
    "rtt",
    "ble",
    "spice",
    "multisim",
    "ngspice",
    "simulink",
    "嵌入式",
    "固件",
    "烧录",
    "电路",
    "仿真",
]

TRUSTED_OWNERS = {
    "anthropics",
    "vercel-labs",
    "cloudflare",
    "supabase",
    "google-labs-code",
    "huggingface",
    "stripe",
    "trailofbits",
    "expo",
    "getsentry",
    "better-auth",
    "tinybirdco",
    "neondatabase",
    "fal-ai-community",
    "sanity-io",
    "remotion-dev",
    "notiondevs",
    "czlonkowski",
    "obra",
}

HIGH_RISK_PATTERNS = [
    r"\btoken\b",
    r"\bsecret\b",
    r"\bpassword\b",
    r"\bcredential\b",
    r"\bapk\b",
    r"\bmedical\b",
    r"\bhealth\b",
]

DESC_TRANSLATIONS = {
    "Create, edit, and analyze Word documents": "用于创建、编辑和分析 Word 文档。",
    "Collaborative document editing and co-authoring": "用于协作文档编辑和共同写作。",
    "Create, edit, and analyze PowerPoint presentations": "用于创建、编辑和分析 PowerPoint 演示文稿。",
    "Create, edit, and analyze Excel spreadsheets": "用于创建、编辑和分析 Excel 表格。",
    "Extract text, create PDFs, and handle forms": "用于提取 PDF 文本、创建 PDF 并处理表单。",
    "Create generative art using p5.js with seeded randomness": "用于基于 p5.js 和随机种子创建生成式艺术。",
    "Design visual art in PNG and PDF formats": "用于设计并输出 PNG 和 PDF 格式的视觉作品。",
    "Frontend design and UI/UX development tools": "用于辅助前端界面设计和 UI/UX 开发。",
    "Create animated GIFs optimized for Slack size constraints": "用于创建适合 Slack 体积限制的动画 GIF。",
    "Style artifacts with professional themes or generate custom themes": "用于为作品应用专业主题或生成自定义主题。",
    "Build complex claude.ai HTML artifacts with React and Tailwind": "用于用 React 和 Tailwind 构建复杂的 Claude HTML 作品。",
    "Create MCP servers to integrate external APIs and services": "用于创建 MCP 服务，把外部 API 和服务接入 Agent 工作流。",
    "Test local web applications using Playwright": "用于通过 Playwright 测试本地 Web 应用。",
    "React best practices and patterns": "用于为 React 项目提供最佳实践和常用模式指导。",
    "Deploy projects to Vercel": "用于辅助把项目部署到 Vercel。",
    "Web design guidelines and standards": "用于提供网页设计规范和视觉标准指导。",
    "React component composition and reusable patterns": "用于指导 React 组件组合和可复用模式。",
    "Next.js best practices and recommended patterns": "用于为 Next.js 项目提供最佳实践和推荐模式。",
    "Caching strategies and cache-aware components in Next.js": "用于处理 Next.js 缓存策略和缓存感知组件设计。",
    "Upgrade Next.js projects to newer versions": "用于辅助 Next.js 项目升级到新版本。",
    "Build AI agents with state and WebSockets on Cloudflare": "用于在 Cloudflare 上构建带状态和 WebSocket 能力的 AI Agent。",
    "Build remote MCP servers with tools and OAuth": "用于在 Cloudflare 上构建带工具和 OAuth 的远程 MCP 服务。",
    "Cloudflare CLI commands reference": "用于查询和使用 Cloudflare CLI 命令。",
    "Audit Core Web Vitals and render-blocking resources": "用于审查 Core Web Vitals 和阻塞渲染资源。",
    "Deploy and manage Workers, KV, R2, D1, Vectorize, Queues, Workflows": "用于部署和管理 Cloudflare Workers、KV、R2、D1、Vectorize、Queues 和 Workflows。",
    "PostgreSQL best practices for Supabase": "用于为 Supabase PostgreSQL 项目提供最佳实践。",
    "Create and manage DESIGN.md files": "用于创建和维护 DESIGN.md 设计说明文件。",
    "Stitch to React components conversion": "用于把 Stitch 设计结果转换为 React 组件。",
    "HF Hub CLI for models, datasets, repos, and compute jobs": "用于操作 Hugging Face Hub 的模型、数据集、仓库和计算任务。",
    "Create and manage datasets with configs and SQL querying": "用于创建和管理 Hugging Face 数据集，并支持配置和 SQL 查询。",
    "Model evaluation with vLLM/lighteval and eval tables": "用于使用 vLLM、lighteval 和评测表进行模型评估。",
    "Run compute jobs and Python scripts on HF infrastructure": "用于在 Hugging Face 基础设施上运行计算任务和 Python 脚本。",
    "Train models with TRL: SFT, DPO, GRPO, GGUF conversion": "用于基于 TRL 进行 SFT、DPO、GRPO 训练和 GGUF 转换。",
    "Build reusable scripts for HF API operations": "用于构建可复用的 Hugging Face API 操作脚本。",
    "Best practices for building Stripe integrations": "用于为 Stripe 集成开发提供最佳实践。",
    "Upgrade Stripe SDK and API versions": "用于辅助升级 Stripe SDK 和 API 版本。",
    "Perform code reviews": "用于执行代码审查并发现实现风险。",
    "Find and identify bugs in code": "用于在代码中定位和识别缺陷。",
    "Best practices for Better Auth integration": "用于为 Better Auth 集成提供最佳实践。",
    "Better Auth CLI commands": "用于查询和使用 Better Auth CLI 命令。",
    "Create authentication setup with Better Auth": "用于基于 Better Auth 创建认证配置。",
    "Generate images and videos using fal.ai AI models": "用于通过 fal.ai 模型生成图片和视频。",
    "AI-powered image editing with style transfer and object removal": "用于进行 AI 图像编辑、风格迁移和对象移除。",
    "Generate workflow JSON files for chaining AI models": "用于生成串联 AI 模型的工作流 JSON。",
    "Best practices for Sanity Studio, GROQ queries, and content workflows": "用于为 Sanity Studio、GROQ 查询和内容工作流提供最佳实践。",
    "Guidelines for designing scalable content models in Sanity": "用于设计可扩展的 Sanity 内容模型。",
    "Programmatic video creation with React": "用于基于 React 进行程序化视频创作。",
    "AI-powered PPT generation with document analysis and styled images": "用于结合文档分析和风格化图片生成 PPT。",
    "Generate animation-rich HTML presentations with visual style previews": "用于生成带动画和视觉预览的 HTML 演示文稿。",
    "Manage Linear issues, projects, and teams": "用于管理 Linear 议题、项目和团队协作。",
    "Generate comprehensive project documentation": "用于生成较完整的项目文档。",
    "Browser automation with Playwright": "用于通过 Playwright 执行浏览器自动化。",
    "Opinionated, evolving constraints to guide agents when building interfaces": "用于为 Agent 构建界面提供有约束的 UI 指导。",
    "Vector-powered CLI for semantic file search with a Claude/Codex skill": "用于通过向量语义搜索辅助 Claude 或 Codex 查找文件。",
    "Write tests before implementing code": "用于指导先写测试再实现代码的开发流程。",
    "Transform git commits into release notes": "用于把 Git 提交记录转换成发布说明。",
    "Development using multiple sub-agents": "用于指导多子 Agent 协作开发流程。",
    "Methodical problem-solving in code": "用于按系统化方法定位和解决代码问题。",
    "Investigate and identify fundamental problems": "用于追踪问题根因并识别底层缺陷。",
    "Complete Git code branches": "用于辅助完成开发分支收尾工作。",
    "Manage multiple Git working trees": "用于管理多个 Git worktree 并行开发环境。",
    "Validate work before finalizing": "用于在完成前验证实现质量。",
    "Develop and document capabilities": "用于编写和维护 Skill 能力说明。",
    "Understand what context is, why it matters, and the anatomy of context in agent systems": "用于理解 Agent 系统中的上下文结构、作用和失效原因。",
    "Recognize patterns of context failure: lost-in-middle, poisoning, distraction, and clash": "用于识别上下文丢失、污染、分心和冲突等失效模式。",
    "Design and evaluate compression strategies for long-running sessions": "用于设计和评估长会话中的上下文压缩策略。",
    "Apply compaction, masking, and caching strategies": "用于应用上下文压缩、遮蔽和缓存策略。",
    "Master orchestrator, peer-to-peer, and hierarchical multi-agent architectures": "用于理解编排式、点对点和层级式多 Agent 架构。",
    "Design short-term, long-term, and graph-based memory architectures": "用于设计短期、长期和图结构记忆系统。",
    "Build tools that agents can use effectively, including architectural reduction patterns": "用于设计 Agent 可高效调用的工具和架构降维模式。",
    "Build evaluation frameworks for agent systems": "用于构建 Agent 系统评估框架。",
    "JavaScript in n8n Code nodes with data access patterns": "用于在 n8n Code 节点中编写 JavaScript 并处理数据访问。",
    "Python coding in n8n Code nodes with limitations": "用于在 n8n Code 节点中编写 Python 并理解限制。",
    "n8n expression syntax with {{}} and $json/$node variables": "用于理解 n8n 表达式语法和节点变量。",
    "MCP tools guide with tool selection and node formats": "用于指导 n8n MCP 工具选择和节点格式配置。",
    "Node configuration with dependency rules and AI connections": "用于配置 n8n 节点依赖规则和 AI 连接。",
    "Fix n8n validation errors with error catalog": "用于根据错误目录修复 n8n 工作流校验问题。",
    "Workflow patterns for webhook, HTTP, database, and AI tasks": "用于构建 webhook、HTTP、数据库和 AI 任务相关的 n8n 工作流模式。",
}


def load_data() -> list[dict]:
    raw = DATA_FILE.read_text(encoding="utf-8")
    match = re.search(r"window\.skillsData\s*=\s*(\[[\s\S]*\]);?\s*$", raw)
    if not match:
        raise RuntimeError("Unable to parse data.js")
    return json.loads(match.group(1))


def write_data(items: list[dict]) -> None:
    DATA_FILE.write_text("window.skillsData = " + json.dumps(items, ensure_ascii=False, indent=2) + ";\n", encoding="utf-8")


def owner_from_link(link: str) -> str:
    parts = [part for part in urlparse(link).path.strip("/").split("/") if part]
    return parts[0].lower() if parts else ""


def repo_from_link(link: str) -> str:
    parts = [part for part in urlparse(link).path.strip("/").split("/") if part]
    return parts[1].lower() if len(parts) > 1 else ""


def skill_slug(name: str, link: str) -> str:
    if "/" in name:
        return name.split("/")[-1]
    parts = [part for part in urlparse(link).path.strip("/").split("/") if part]
    return parts[-1] if parts else name


def normalize_name(name: str, link: str) -> str:
    owner = owner_from_link(link)
    slug = skill_slug(name, link)
    if owner == "anthropics":
        return slug
    return name


def translate_description(description: str, name: str) -> str:
    if description in DESC_TRANSLATIONS:
        return DESC_TRANSLATIONS[description]
    text = description.strip().rstrip(".")
    if not text:
        return f"用于辅助 {name} 相关的 Agent 工作流。"
    return f"用于{text}。"


def infer_platforms(link: str, name: str, description: str) -> list[str]:
    text = f"{link} {name} {description}".lower()
    platforms: list[str] = []
    if "anthropics" in text or "claude" in text:
        platforms.append("Claude")
    if "codex" in text:
        platforms.append("Codex")
    if "cursor" in text:
        platforms.append("Cursor")
    if not platforms:
        platforms.append("Claude")
    return platforms


def infer_level(category: str, description: str) -> str:
    text = f"{category} {description}".lower()
    if any(word in text for word in ("security", "mcp", "cloudflare", "infrastructure", "evaluation", "training", "postgres", "stripe", "auth", "n8n")):
        return "高级"
    if any(word in text for word in ("development", "testing", "context", "automation", "api", "react", "next")):
        return "进阶"
    return "基础"


def risk_level(item: dict) -> tuple[str, list[str]]:
    text = f"{item.get('name', '')} {item.get('description', '')} {item.get('category', '')}".lower()
    reasons = [pattern.strip(r"\b") for pattern in HIGH_RISK_PATTERNS if re.search(pattern, text)]
    if reasons:
        return "medium", reasons
    return "low", ["结构化来源明确，未发现明显高风险信号"]


def score_item(item: dict) -> dict:
    link = str(item.get("link") or "")
    name = str(item.get("name") or "")
    description = str(item.get("description") or "")
    category = str(item.get("category") or "")
    owner = owner_from_link(link)
    score = 0
    reasons: list[str] = []

    if link.startswith("https://github.com/"):
        score += 3
        reasons.append("GitHub 链接明确")
    if description and len(description) >= 18:
        score += 2
        reasons.append("简介可判断用途")
    if category in CATEGORY_MAP:
        score += 2
        reasons.append("类别可映射到站点筛选")
    if owner in TRUSTED_OWNERS:
        score += 2
        reasons.append("来源组织可信度较高")
    if "/tree/" in link:
        score += 1
        reasons.append("指向具体 Skill 目录")
    if any(word in description.lower() for word in ("best practices", "testing", "workflow", "create", "build", "manage", "analyze", "guide")):
        score += 1
        reasons.append("说明包含明确动作")

    risk, risk_reasons = risk_level(item)
    if risk != "low":
        score -= 2
        reasons.append("存在需人工复核的风险词")

    has_chinese_copy = description in DESC_TRANSLATIONS
    status = "selected" if score >= 10 and risk != "high" and has_chinese_copy else "candidate"
    return {
        **item,
        "score": score,
        "status": status,
        "risk_level": risk,
        "score_reasons": reasons,
        "risk_reasons": risk_reasons,
    }


def build_card(item: dict) -> dict:
    text = " ".join(str(item.get(key) or "") for key in ("name", "description", "link", "category")).lower()
    category = "嵌入式" if any(keyword in text for keyword in EMBEDDED_KEYWORDS) else CATEGORY_MAP.get(str(item.get("category") or ""), "工作流")
    name = normalize_name(str(item.get("name") or ""), str(item.get("link") or ""))
    description = translate_description(str(item.get("description") or ""), name)
    raw_tags = [
        owner_from_link(str(item.get("link") or "")),
        repo_from_link(str(item.get("link") or "")),
        skill_slug(str(item.get("name") or ""), str(item.get("link") or "")),
        category,
    ]
    tags = []
    for tag in raw_tags:
        if tag and tag not in tags:
            tags.append(tag)
    return {
        "name": name,
        "description": description,
        "audience": AUDIENCE_BY_CATEGORY.get(category, "工作流"),
        "level": infer_level(str(item.get("category") or ""), str(item.get("description") or "")),
        "category": category,
        "platforms": infer_platforms(str(item.get("link") or ""), str(item.get("name") or ""), str(item.get("description") or "")),
        "tags": tags[:5],
        "github_url": str(item.get("link") or ""),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Score anbeime/skill entries and append suitable cards.")
    parser.add_argument("--source", default=str(DEFAULT_SOURCE))
    parser.add_argument("--report", default=str(DEFAULT_REPORT))
    parser.add_argument("--append-data", action="store_true")
    parser.add_argument("--limit", type=int, default=50, help="Maximum selected cards to append in one batch.")
    args = parser.parse_args()

    source = pathlib.Path(args.source)
    payload = json.loads(source.read_text(encoding="utf-8"))
    skills = payload.get("skills", []) if isinstance(payload, dict) else payload
    if not isinstance(skills, list):
        raise RuntimeError("Source file does not contain a skills list")

    scored = [score_item(item) for item in skills if isinstance(item, dict)]
    scored.sort(key=lambda item: (-int(item.get("score") or 0), str(item.get("name") or "").lower()))
    report = pathlib.Path(args.report)
    report.parent.mkdir(parents=True, exist_ok=True)
    report.write_text(json.dumps(scored, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"[ok] {len(scored)} scored skills written to {report}")

    if not args.append_data:
        return 0

    data = load_data()
    existing_urls = {str(item.get("github_url")) for item in data if isinstance(item, dict)}
    added = 0
    skipped_duplicates = 0
    for item in scored:
        if item.get("status") != "selected":
            continue
        url = str(item.get("link") or "")
        if url in existing_urls:
            skipped_duplicates += 1
            continue
        data.append(build_card(item))
        existing_urls.add(url)
        added += 1
        if added >= args.limit:
            break

    if added:
        write_data(data)
    print(f"[ok] added={added} skipped_duplicates={skipped_duplicates}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
