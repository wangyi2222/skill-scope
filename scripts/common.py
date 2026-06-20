"""Shared utilities for SkillScope maintenance scripts."""

from __future__ import annotations

import json
import pathlib
import re
import tempfile
from urllib.parse import urlparse

ROOT = pathlib.Path(__file__).resolve().parent.parent
DATA_FILE = ROOT / "data.js"
CANDIDATES_DIR = ROOT / "candidates"
COLLECTIONS_DIR = CANDIDATES_DIR / "collections"
DRAFTS_DIR = ROOT / "drafts"

# ---------------------------------------------------------------------------
# Trusted GitHub owners — used by scoring and risk assessment
# ---------------------------------------------------------------------------
TRUSTED_OWNERS: set[str] = {
    "anthropics",
    "better-auth",
    "cloudflare",
    "czlonkowski",
    "expo",
    "fal-ai-community",
    "getsentry",
    "github",
    "google",
    "google-labs-code",
    "huggingface",
    "neondatabase",
    "notiondevs",
    "obra",
    "remotion-dev",
    "sanity-io",
    "skillmatic-ai",
    "stripe",
    "supabase",
    "tinybirdco",
    "trailofbits",
    "vercel-labs",
}

# ---------------------------------------------------------------------------
# Embedded-specific keywords — used across category inference
# ---------------------------------------------------------------------------
EMBEDDED_KEYWORDS: list[str] = [
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
    "circuit",
    "嵌入式",
    "固件",
    "烧录",
    "电路",
    "仿真",
]

# ---------------------------------------------------------------------------
# Category mapping — anbeime/collection category strings → site category keys
# ---------------------------------------------------------------------------
CATEGORY_MAP: dict[str, str] = {
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

# ---------------------------------------------------------------------------
# Audience defaults per category
# ---------------------------------------------------------------------------
AUDIENCE_BY_CATEGORY: dict[str, str] = {
    "文档": "工作流",
    "开发": "开发",
    "嵌入式": "开发",
    "工作流": "工作流",
    "插件": "开发",
    "图像": "设计",
    "自动化": "开发",
    "研究": "工作流",
}

# ---------------------------------------------------------------------------
# Risk screening — simple word-list check
# ---------------------------------------------------------------------------
HIGH_RISK_WORDS: list[str] = [
    "token",
    "secret",
    "password",
    "credential",
    "apk",
    "medical",
    "health",
    "wallet",
    "private key",
]

# ---------------------------------------------------------------------------
# Description translations — English source → Chinese
# ---------------------------------------------------------------------------
DESC_TRANSLATIONS: dict[str, str] = {
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

# ─────────────────────────────────────────────────────────────────────────
# Data I/O helpers
# ─────────────────────────────────────────────────────────────────────────

def load_data(data_file: pathlib.Path | None = None) -> list[dict]:
    """Parse window.skillsData array from data.js. Returns list of dicts."""
    target = data_file or DATA_FILE
    raw = target.read_text(encoding="utf-8")
    match = re.search(r"window\.skillsData\s*=\s*(\[[\s\S]*\]);?\s*$", raw)
    if not match:
        raise RuntimeError(f"Unable to locate window.skillsData array in {target}")
    return json.loads(match.group(1))


def write_data(items: list[dict], data_file: pathlib.Path | None = None) -> None:
    """Atomically write skills data back to data.js (temp file + rename)."""
    target = data_file or DATA_FILE
    payload = "window.skillsData = " + json.dumps(items, ensure_ascii=False, indent=2) + ";\n"
    tmp = pathlib.Path(tempfile.mktemp(dir=target.parent, prefix=".data.js.", suffix=".tmp"))
    try:
        tmp.write_text(payload, encoding="utf-8")
        tmp.replace(target)
    except BaseException:
        if tmp.exists():
            tmp.unlink(missing_ok=True)
        raise


# ─────────────────────────────────────────────────────────────────────────
# URL helpers
# ─────────────────────────────────────────────────────────────────────────

def canonical_url(url: str) -> str:
    """Normalize a GitHub URL to its canonical owner/repo[/tree/branch/...] form."""
    parsed = urlparse(url)
    parts = [p for p in parsed.path.strip("/").split("/") if p]
    if len(parts) >= 5 and parts[2] in ("tree", "blob"):
        return f"https://github.com/{parts[0]}/{parts[1]}/tree/{parts[3]}/{'/'.join(parts[4:])}".rstrip("/")
    if len(parts) >= 2:
        return f"https://github.com/{parts[0]}/{parts[1]}".rstrip("/")
    return url.rstrip("/")


def owner_from_url(url: str) -> str:
    parts = [p for p in urlparse(url).path.strip("/").split("/") if p]
    return parts[0].lower() if parts else ""


def repo_from_url(url: str) -> str:
    parts = [p for p in urlparse(url).path.strip("/").split("/") if p]
    return parts[1].lower() if len(parts) > 1 else ""


def slug_from_url(url: str) -> str:
    parts = [p for p in urlparse(url).path.strip("/").split("/") if p]
    if len(parts) >= 5 and parts[2] in ("tree", "blob"):
        return parts[-1]
    if len(parts) >= 2:
        return parts[1]
    return "unknown-skill"


def source_from_link(link: str) -> str:
    """Derive `source` field from a full GitHub URL."""
    parts = [p for p in urlparse(link).path.strip("/").split("/") if p]
    if len(parts) >= 5 and parts[2] in ("tree", "blob"):
        return f"{parts[0]}/{parts[1]}/{'/'.join(parts[4:])}"
    if len(parts) >= 2:
        return f"{parts[0]}/{parts[1]}"
    return ""


# ─────────────────────────────────────────────────────────────────────────
# Text helpers
# ─────────────────────────────────────────────────────────────────────────

def clean_text(value: str) -> str:
    """Collapse whitespace and strip surrounding punctuation/noise."""
    value = re.sub(r"\s+", " ", value).strip()
    value = value.strip("·•-–—|/\\ ")
    return value


def first_sentence(text: str) -> str:
    """Return up to the first sentence-ending punctuation."""
    match = re.match(r"([^。.!！?？\n]+)", text.strip())
    return match.group(1).strip() if match else text.strip()
