#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import pathlib
import re
from urllib.parse import urlparse


ROOT = pathlib.Path(__file__).resolve().parent.parent
COLLECTIONS_DIR = ROOT / "candidates" / "collections"
REPORT_FILE = COLLECTIONS_DIR / "scored_collection_skills.json"
DATA_FILE = ROOT / "data.js"

COLLECTION_REPOS = [
    "VoltAgent/awesome-agent-skills",
    "heilcheng/awesome-agent-skills",
    "skillmatic-ai/awesome-agent-skills",
    "google/skills",
    "github/awesome-copilot",
    "sickn33/antigravity-awesome-skills",
]

COLLECTION_ROOTS = {
    "https://github.com/VoltAgent/awesome-agent-skills",
    "https://github.com/heilcheng/awesome-agent-skills",
    "https://github.com/skillmatic-ai/awesome-agent-skills",
    "https://github.com/google/skills",
    "https://github.com/github/awesome-copilot",
    "https://github.com/sickn33/antigravity-awesome-skills",
    "https://github.com/anthropics/skills",
}

TRUSTED_OWNERS = {
    "anthropics",
    "google",
    "github",
    "vercel-labs",
    "cloudflare",
    "supabase",
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
    "czlonkowski",
    "obra",
    "skillmatic-ai",
}

HIGH_RISK_WORDS = [
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

EMBEDDED_WORDS = [
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
]

CATEGORY_RULES = [
    ("嵌入式", EMBEDDED_WORDS),
    ("开发", ["code", "dev", "developer", "testing", "test", "mcp", "api", "sdk", "react", "next", "cloudflare", "stripe", "auth", "postgres", "github", "copilot", "waf", "cloud", "gke", "firebase", "alloydb", "bigquery"]),
    ("文档", ["doc", "docs", "document", "pdf", "ppt", "pptx", "xlsx", "word", "excel", "markdown", "readme", "notion"]),
    ("图像", ["image", "video", "gif", "design", "ui", "ux", "visual", "canvas", "art", "photo", "remotion", "fal"]),
    ("自动化", ["automation", "n8n", "workflow", "webhook", "scheduler", "batch"]),
    ("研究", ["research", "paper", "deep-research", "evaluation", "dataset", "model", "huggingface", "rag"]),
    ("工作流", ["agent", "skill", "context", "memory", "planning", "review", "commit", "issue", "linear", "productivity"]),
]

AUDIENCE_BY_CATEGORY = {
    "文档": "工作流",
    "开发": "开发",
    "嵌入式": "开发",
    "工作流": "工作流",
    "插件": "开发",
    "图像": "设计",
    "自动化": "开发",
    "研究": "工作流",
}

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
}


def collection_file(repo: str, suffix: str) -> pathlib.Path:
    return COLLECTIONS_DIR / f"{repo.replace('/', '__')}__{suffix}"


def normalize_github_url(url: str) -> str:
    parsed = urlparse(url.strip())
    if parsed.netloc.lower() not in ("github.com", "www.github.com"):
        return ""
    parts = [part for part in parsed.path.strip("/").split("/") if part]
    if len(parts) < 2:
        return ""
    owner, repo = parts[0], parts[1].removesuffix(".git")
    rest = "/".join(parts[2:])
    normalized = f"https://github.com/{owner}/{repo}"
    if rest:
        normalized += f"/{rest}"
    return normalized.rstrip("/")


def canonical_url(url: str) -> str:
    parsed = urlparse(url)
    parts = [part for part in parsed.path.strip("/").split("/") if part]
    if len(parts) >= 5 and parts[2] in ("tree", "blob"):
        return f"https://github.com/{parts[0]}/{parts[1]}/tree/{parts[3]}/{'/'.join(parts[4:])}".rstrip("/")
    if len(parts) >= 2:
        return f"https://github.com/{parts[0]}/{parts[1]}".rstrip("/")
    return url.rstrip("/")


def owner_from_url(url: str) -> str:
    parts = [part for part in urlparse(url).path.strip("/").split("/") if part]
    return parts[0].lower() if parts else ""


def repo_from_url(url: str) -> str:
    parts = [part for part in urlparse(url).path.strip("/").split("/") if part]
    return parts[1].lower() if len(parts) > 1 else ""


def slug_from_url(url: str) -> str:
    parts = [part for part in urlparse(url).path.strip("/").split("/") if part]
    if len(parts) >= 5 and parts[2] in ("tree", "blob"):
        return parts[-1]
    if len(parts) >= 2:
        return parts[1]
    return "unknown-skill"


def display_name_from_source_name(name: str, link: str) -> str:
    value = clean_text(name)
    if "/" in value:
        return value.split("/")[-1].strip() or slug_from_url(link)
    if value.lower() in ("github", "repository", "repo"):
        return slug_from_url(link)
    return value or slug_from_url(link)


def source_from_url(url: str) -> str:
    parts = [part for part in urlparse(url).path.strip("/").split("/") if part]
    if len(parts) >= 5 and parts[2] in ("tree", "blob"):
        return f"{parts[0]}/{parts[1]}/{'/'.join(parts[4:])}"
    if len(parts) >= 2:
        return f"{parts[0]}/{parts[1]}"
    return ""


def clean_text(text: str) -> str:
    value = re.sub(r"`([^`]+)`", r"\1", text)
    value = re.sub(r"\*\*([^*]+)\*\*", r"\1", value)
    value = re.sub(r"\*([^*]+)\*", r"\1", value)
    value = re.sub(r"\*{2,}", " ", value)
    value = re.sub(r"<[^>]+>", "", value)
    value = re.sub(r"\s+", " ", value)
    return value.strip(" -:|")


def extract_readme_items(repo: str) -> list[dict]:
    readme_path = collection_file(repo, "README.md")
    if not readme_path.exists():
        return []
    text = readme_path.read_text(encoding="utf-8", errors="ignore")
    items: dict[str, dict] = {}
    for line in text.splitlines():
        if "github.com/" not in line:
            continue
        for match in re.finditer(r"\[([^\]]+)\]\((https://github\.com/[^)\s]+)\)", line):
            name = clean_text(match.group(1))
            url = normalize_github_url(match.group(2))
            if not url:
                continue
            description = clean_text(line.replace(match.group(0), "").strip())
            items[canonical_url(url)] = {
                "name": name or slug_from_url(url),
                "description": description,
                "link": url,
                "source_collection": repo,
            }
        for raw_url in re.findall(r"https://github\.com/[^\s)\]]+", line):
            url = normalize_github_url(raw_url.rstrip(".,，。"))
            if not url:
                continue
            key = canonical_url(url)
            items.setdefault(
                key,
                {
                    "name": slug_from_url(url),
                    "description": clean_text(line.replace(raw_url, "")),
                    "link": url,
                    "source_collection": repo,
                },
            )
    return list(items.values())


def extract_google_directory_items(repo: str) -> list[dict]:
    contents_path = collection_file(repo, "contents.json")
    if not contents_path.exists():
        return []
    try:
        contents = json.loads(contents_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return []
    if not isinstance(contents, list):
        return []
    items = []
    for entry in contents:
        if not isinstance(entry, dict) or entry.get("type") != "dir":
            continue
        name = str(entry.get("name") or "")
        if not name or name.startswith("."):
            continue
        items.append(
            {
                "name": f"google/{name}",
                "description": "Google Skills 仓库中的官方 Skill 目录。",
                "link": f"https://github.com/{repo}/tree/main/{name}",
                "source_collection": repo,
            }
        )
    return items


def infer_category(item: dict) -> str:
    text = " ".join(str(item.get(key) or "") for key in ("name", "description", "link", "source_collection")).lower()
    scores: dict[str, int] = {}
    for category, words in CATEGORY_RULES:
        score = sum(1 for word in words if word in text)
        if score:
            scores[category] = score
    if scores:
        return max(scores.items(), key=lambda pair: pair[1])[0]
    return "工作流"


def translate_description(item: dict) -> str:
    description = clean_text(str(item.get("description") or "").strip())
    name = str(item.get("name") or slug_from_url(str(item.get("link") or "")))
    if description in DESC_TRANSLATIONS:
        return DESC_TRANSLATIONS[description]
    if description and re.search(r"[\u4e00-\u9fff]", description):
        text = description.rstrip("。")
        if not text.startswith(("用于", "帮助", "适合", "提供", "支持")):
            text = "用于" + text
        return text[:90] + "。"
    if description:
        return normalize_english_description(description, item)
    return f"用于 {name} 相关的 Agent Skill，帮助用户按需调用该仓库提供的能力。"


TOPIC_TRANSLATIONS = [
    ("ab-test", "A/B 测试"),
    ("analytics-tracking", "数据分析埋点"),
    ("churn-prevention", "用户流失预防"),
    ("cold-email", "B2B 冷邮件"),
    ("competitor-alternatives", "竞品对比页面"),
    ("content-strategy", "内容策略"),
    ("copy-editing", "营销文案编辑"),
    ("copywriting", "营销文案写作"),
    ("email-sequence", "邮件序列"),
    ("form-cro", "表单转化优化"),
    ("free-tool-strategy", "免费工具增长策略"),
    ("launch-strategy", "产品发布策略"),
    ("marketing-ideas", "营销创意"),
    ("marketing-psychology", "营销心理学"),
    ("onboarding-cro", "用户激活流程优化"),
    ("page-cro", "页面转化率优化"),
    ("paid-ads", "付费广告"),
    ("paywall-upgrade-cro", "付费升级转化"),
    ("popup-cro", "弹窗转化优化"),
    ("pricing-strategy", "定价策略"),
    ("product-marketing-context", "产品营销上下文"),
    ("programmatic-seo", "程序化 SEO"),
    ("referral-program", "推荐与联盟计划"),
    ("revops", "收入运营"),
    ("sales-enablement", "销售赋能材料"),
    ("schema-markup", "结构化数据标记"),
    ("seo-audit", "SEO 审计"),
    ("signup-flow-cro", "注册流程转化优化"),
    ("site-architecture", "网站信息架构"),
    ("social-content", "社交媒体内容"),
    ("acquisition-channel", "获客渠道评估"),
    ("ai-shaped-readiness", "AI 转型准备度评估"),
    ("altitude-horizon", "产品管理层级转型"),
    ("company-research", "公司与竞品研究"),
    ("context-engineering", "上下文工程诊断"),
    ("customer-journey", "客户旅程地图"),
    ("director-readiness", "产品负责人晋升准备"),
    ("discovery-interview", "用户访谈准备"),
    ("discovery-process", "产品发现流程"),
    ("eol-message", "产品下线沟通"),
    ("epic-breakdown", "史诗任务拆分"),
    ("epic-hypothesis", "产品假设设计"),
    ("executive-onboarding", "高管入职诊断"),
    ("feature-investment", "功能投资评估"),
    ("finance-based-pricing", "财务视角定价评估"),
    ("finance-metrics", "SaaS 财务指标"),
    ("jobs-to-be-done", "JTBD 用户目标分析"),
    ("lean-ux-canvas", "Lean UX 假设画布"),
    ("opportunity-solution-tree", "机会解决方案树"),
    ("pestel-analysis", "PESTEL 外部环境分析"),
    ("pol-probe", "轻量验证实验"),
    ("positioning", "产品定位"),
    ("prd-development", "PRD 编写流程"),
    ("press-release", "未来新闻稿"),
    ("prioritization", "优先级决策"),
    ("problem-framing", "问题框定"),
    ("problem-statement", "问题陈述"),
    ("product-strategy", "产品策略"),
    ("proto-persona", "假设用户画像"),
    ("recommendation-canvas", "AI 推荐方案画布"),
    ("roadmap-planning", "路线图规划"),
    ("saas-economics", "SaaS 单位经济模型"),
    ("saas-revenue", "SaaS 收入增长指标"),
    ("skill-authoring", "Skill 编写流程"),
    ("storyboard", "用户旅程故事板"),
    ("tam-sam-som", "市场规模测算"),
    ("user-story-mapping", "用户故事地图"),
    ("user-story", "用户故事"),
    ("workshop-facilitation", "工作坊引导"),
    ("firecrawl-agent", "Firecrawl Agent 集成"),
    ("firecrawl-scrape", "Firecrawl 网页抓取"),
    ("expo/skills", "Expo 官方 Skill"),
    ("integrate-whatsapp", "WhatsApp 集成"),
    ("build-review-interface", "评审界面搭建"),
    ("generate-synthetic-data", "合成数据生成"),
    ("validate-evaluator", "评估器校验"),
    ("alloydb", "AlloyDB 数据库资源"),
    ("bigquery", "BigQuery 数据分析资源"),
    ("cloud-run", "Cloud Run 服务"),
    ("cloud-sql", "Cloud SQL 资源"),
    ("firebase", "Firebase 产品与服务"),
    ("gemini-agents-api", "Gemini Agent 资源"),
    ("gemini-api", "Gemini API"),
    ("gemini-interactions-api", "Gemini 交互 API"),
    ("gke", "GKE 集群"),
    ("networking-observability", "Google Cloud 网络观测"),
    ("recipe-onboarding", "Google Cloud 新手上手"),
    ("waf-cost-optimization", "Google Cloud 成本优化"),
    ("waf-operational-excellence", "Google Cloud 运维卓越"),
    ("waf-performance-optimization", "Google Cloud 性能优化"),
    ("waf-reliability", "Google Cloud 可靠性"),
    ("waf-security", "Google Cloud 安全"),
    ("waf-sustainability", "Google Cloud 可持续性"),
    ("agent-platform-skill-registry", "Gemini Enterprise Skill 注册表"),
    ("n8n-code-javascript", "n8n JavaScript 代码节点"),
    ("n8n-code-python", "n8n Python 代码节点"),
    ("n8n-expression-syntax", "n8n 表达式语法"),
    ("n8n-node-configuration", "n8n 节点配置"),
    ("n8n-validation", "n8n 校验错误修复"),
    ("n8n-workflow", "n8n 工作流"),
    ("n8n-mcp", "n8n MCP 工具"),
    ("cypress-author", "Cypress 测试编写"),
    ("cypress-docs", "Cypress 文档检索"),
    ("cypress-explain", "Cypress 测试解释"),
    ("swiftui", "SwiftUI 开发"),
    ("redis", "Redis 开发"),
    ("react", "React 开发"),
    ("cuopt-developer", "cuOpt 开发"),
    ("numerical-optimization-api", "数值优化 API"),
    ("numerical-optimization-formulation", "数值优化建模"),
    ("routing-formulation", "路径规划建模"),
    ("deepstream-dev", "DeepStream 开发"),
    ("deepstream-import-vision-model", "DeepStream 视觉模型导入"),
    ("linting-and-formatting", "代码检查与格式化"),
    ("activation-recompute", "激活重计算性能优化"),
    ("cpu-offloading", "CPU 卸载性能优化"),
    ("expert-parallel-overlap", "专家并行重叠优化"),
    ("hierarchical-context-parallel", "分层上下文并行优化"),
    ("moe-hardware-configs", "MoE 硬件配置"),
    ("moe-optimization-workflow", "MoE 优化工作流"),
    ("moe-vlm-training", "MoE 视觉语言模型训练"),
    ("mlm-bridge-training", "MLM Bridge 训练"),
    ("megatron-fsdp", "Megatron FSDP 性能优化"),
    ("parallelism-strategies", "并行策略"),
    ("sequence-packing", "序列打包优化"),
    ("nemo-gym-pivot-datasets", "NeMo Gym 数据集切换"),
    ("nemo-gym-reward-profiling", "NeMo Gym 奖励分析"),
    ("nemo-gym-debugging", "NeMo Gym 调试"),
    ("auto-research", "自动研究流程"),
    ("config-conventions", "配置规范"),
    ("contributor-create-pr", "贡献者 PR 创建"),
    ("contributor-update-docs", "贡献者文档更新"),
    ("maintainer-cross-issue-sweep", "维护者跨 Issue 排查"),
    ("maintainer-cut-release-tag", "维护者发布标签创建"),
    ("maintainer-find-review-pr", "维护者 PR 评审筛选"),
    ("maintainer-day", "维护者日间工作流"),
    ("maintainer-evening", "维护者晚间工作流"),
    ("maintainer-morning", "维护者晨间工作流"),
    ("maintainer-normalize-title-tags", "维护者标题标签规范化"),
    ("maintainer-pr-comparator", "维护者 PR 对比"),
    ("maintainer-security-code-review", "维护者安全代码审查"),
    ("maintainer-triage", "维护者任务分诊"),
    ("user-configure-inference", "用户推理配置"),
    ("user-configure-security", "用户安全配置"),
    ("user-deploy-remote", "用户远程部署"),
    ("user-get-started", "用户上手引导"),
    ("user-manage-policy", "用户策略管理"),
    ("user-overview", "用户概览"),
    ("user-reference", "用户参考资料"),
    ("user-agent-skills", "用户 Agent Skill"),
    ("voice-agent-deploy", "语音 Agent 部署"),
    ("add-fusion-transformation", "算子融合变换"),
    ("kernel-tileir-optimization", "TileIR 内核优化"),
    ("host-optimization", "主机侧性能优化"),
    ("nsight-compute-analysis", "Nsight Compute 性能分析"),
    ("perf-optimization", "性能优化"),
    ("workload-profiling", "工作负载性能分析"),
    ("recipe-recommender", "训练配方推荐"),
    ("code-contribution", "代码贡献"),
    ("codebase-exploration", "代码库探索"),
    ("flashinfer-upgrade", "FlashInfer 升级"),
    ("converting-cutile-to-julia", "CuTe DSL 到 Julia 转换"),
    ("converting-cutile-to-triton", "CuTe DSL 到 Triton 转换"),
    ("cutile-autotuning", "CuTe DSL 自动调优"),
    ("monkey-patch-kernels", "内核猴子补丁改造"),
    ("video-summarization", "视频摘要"),
    ("video-understanding", "视频理解"),
    ("condition-based-waiting", "条件等待"),
    ("dispatching-parallel-agents", "并行 Agent 调度"),
    ("finishing-a-development-branch", "开发分支收尾"),
    ("receiving-code-review", "代码评审接收"),
    ("requesting-code-review", "代码评审请求"),
    ("subagent-driven-development", "子 Agent 驱动开发"),
    ("systematic-debugging", "系统化调试"),
    ("test-driven-development", "测试驱动开发"),
    ("testing-anti-patterns", "测试反模式识别"),
    ("testing-skills-with-subagents", "子 Agent Skill 测试"),
    ("verification-before-completion", "完成前验证"),
    ("using-superpowers", "Superpowers 能力使用"),
    ("analyze-feature-requests", "功能请求分析"),
    ("brainstorm-experiments-existing", "已有实验头脑风暴"),
    ("brainstorm-experiments-new", "新实验头脑风暴"),
    ("brainstorm-ideas-existing", "已有想法头脑风暴"),
    ("brainstorm-ideas-new", "新想法头脑风暴"),
    ("competitive-battlecard", "竞品战卡"),
    ("ideal-customer-profile", "理想客户画像"),
    ("metrics-dashboard", "指标看板"),
    ("identify-assumptions-existing", "已有假设识别"),
    ("identify-assumptions-new", "新假设识别"),
    ("prioritize-assumptions", "假设优先级排序"),
    ("value-prop-statements", "价值主张表达"),
    ("summarize-interview", "访谈总结"),
    ("summarize-meeting", "会议总结"),
    ("test-scenarios", "测试场景"),
    ("user-segmentation", "用户分群"),
    ("ad-angle-multiplier", "广告角度扩展"),
    ("avatar-extraction", "用户画像提取"),
    ("objection-crusher", "销售异议处理"),
    ("conversion-path-builder", "转化路径设计"),
    ("full-funnel-campaign-orchestrator", "全漏斗营销活动编排"),
    ("generic-language-killer", "泛泛表达优化"),
    ("mechanism-builder", "营销机制设计"),
    ("schwartz-awareness-mapper", "Schwartz 认知阶段映射"),
    ("scroll-stopping-creative", "吸引停留的创意内容"),
    ("transloadit", "Transloadit 文件处理"),
    ("venice-api-overview", "Venice API 概览"),
    ("venice-audio-transcription", "Venice 音频转写"),
    ("venice-characters", "Venice 角色配置"),
    ("venice-embeddings", "Venice 向量嵌入"),
    ("venice-image-generate", "Venice 图像生成"),
    ("venice-responses", "Venice 响应接口"),
    ("better-auth", "Better Auth 认证"),
    ("deployment", "模型部署"),
    ("twofactor", "双因素认证"),
    ("two-factor", "双因素认证"),
    ("sanity", "Sanity 内容平台"),
    ("seo-aeo", "SEO 与答案引擎优化"),
    ("content-modeling", "内容模型设计"),
    ("git-worktrees", "Git worktree 多工作区"),
    ("commands", "命令结构管理"),
]


def topic_from_item(item: dict | None, description: str) -> str:
    item = item or {}
    raw = " ".join(str(item.get(key) or "") for key in ("name", "link", "description"))
    lookup = raw.lower()
    for needle, label in TOPIC_TRANSLATIONS:
        if needle in lookup:
            return label

    slug = slug_from_url(str(item.get("link") or "")) if item else ""
    name = str(item.get("name") or slug or "").strip()
    candidate = name.split("/")[-1] if name else ""
    candidate = re.sub(r"(?i)\b(skill|skills|advisor|expert|basics|best-practices)\b", "", candidate)
    candidate = re.sub(r"[-_]+", " ", candidate).strip()
    if candidate:
        return candidate

    words = re.findall(r"[A-Za-z][A-Za-z0-9.+#-]{2,}", description)
    stop = {"the", "and", "for", "with", "using", "create", "manage", "guide", "best", "practices"}
    keywords = [word for word in words if word.lower() not in stop]
    return " ".join(keywords[:3]) or "该仓库"


def polish_chinese_description(text: str) -> str:
    text = text.replace("工作流 工作流", "工作流")
    text = text.replace(" 工作流 工作流", " 工作流")
    text = text.replace("的 Agent 工作流的 Agent 工作流", "的 Agent 工作流")
    text = text.replace(" 相关 API 与服务", " API 与服务")
    text = text.replace(" 相关测试", "测试")
    text = text.replace(" 相关内容", "内容")
    text = text.replace(" 相关研究", "研究")
    text = text.replace(" 相关的 Agent 工作流", "的 Agent 工作流")
    text = re.sub(r"\s+", " ", text)
    text = text.replace("用于调用、集成或管理 Firecrawl Agent 集成 API 与服务。", "用于把 Firecrawl 网页抓取能力接入 Agent 工作流。")
    return text


def normalize_english_description(description: str, item: dict | None = None) -> str:
    text = clean_text(description).rstrip(".")
    lower = text.lower()
    topic = topic_from_item(item, text)
    if len(text) < 18 or text.lower() in {"install from", "start here", "read more", "learn more"}:
        return "用于该仓库提供的 Agent Skill，帮助用户按需调用对应能力。"

    if "best practice" in lower or "guideline" in lower:
        return polish_chinese_description(f"用于提供 {topic} 的最佳实践和规范建议。")
    if any(word in lower for word in ("test", "cypress", "playwright", "e2e")):
        return polish_chinese_description(f"用于编写、检查或解释 {topic} 相关测试。")
    if any(word in lower for word in ("analy", "audit", "diagnos", "evaluate", "assess")):
        return polish_chinese_description(f"用于分析和评估 {topic}，帮助用户发现问题并做出判断。")
    if any(word in lower for word in ("plan", "strategy", "roadmap", "priorit", "launch")):
        return polish_chinese_description(f"用于规划 {topic}，帮助用户明确方向、步骤和优先级。")
    if any(word in lower for word in ("write", "copy", "email", "message", "content", "docs")):
        return polish_chinese_description(f"用于撰写和优化 {topic} 相关内容。")
    if any(word in lower for word in ("create", "build", "generate", "implement", "setup", "set up")):
        return polish_chinese_description(f"用于创建和配置 {topic}，减少从零搭建的整理成本。")
    if any(word in lower for word in ("manage", "configure", "deploy", "integrat")):
        return polish_chinese_description(f"用于管理和配置 {topic}，辅助完成相关开发或运维任务。")
    if any(word in lower for word in ("workflow", "automation", "n8n", "webhook")):
        return polish_chinese_description(f"用于构建和优化 {topic} 工作流。")
    if any(word in lower for word in ("api", "sdk", "server", "mcp")):
        return polish_chinese_description(f"用于调用、集成或管理 {topic} 相关 API 与服务。")
    if any(word in lower for word in ("optimi", "conversion", "cro", "seo")):
        return polish_chinese_description(f"用于优化 {topic}，提升转化、搜索或运营效果。")
    if any(word in lower for word in ("research", "interview", "customer", "journey")):
        return polish_chinese_description(f"用于梳理 {topic} 相关研究，帮助用户形成可执行结论。")

    return polish_chinese_description(f"用于辅助 {topic} 相关的 Agent 工作流，帮助用户快速调用对应能力。")


def risk_level(item: dict) -> tuple[str, list[str]]:
    text = " ".join(str(item.get(key) or "") for key in ("name", "description", "link")).lower()
    reasons = [word for word in HIGH_RISK_WORDS if word in text]
    if reasons:
        return "medium", reasons
    return "low", ["未发现明显高风险关键词"]


def is_generic_collection_url(url: str) -> bool:
    canonical = canonical_url(url)
    if canonical in COLLECTION_ROOTS:
        return True
    return canonical in {
        "https://github.com/google/skills/tree/main/skills",
        "https://github.com/anthropics/skills/tree/main/skills",
    }


def score_item(item: dict) -> dict:
    url = normalize_github_url(str(item.get("link") or ""))
    if not url:
        return {}
    item = {**item, "link": url}
    score = 0
    reasons: list[str] = []
    owner = owner_from_url(url)
    description = str(item.get("description") or "")
    source = str(item.get("source_collection") or "")

    if url.startswith("https://github.com/"):
        score += 3
        reasons.append("GitHub 链接明确")
    if "/tree/" in url:
        score += 2
        reasons.append("指向具体 Skill 目录")
    if owner in TRUSTED_OWNERS:
        score += 2
        reasons.append("来源组织可信度较高")
    if description and len(description) >= 12:
        score += 2
        reasons.append("说明可判断用途")
    if any(word in url.lower() for word in ("skills", "skill", "agents", "copilot")):
        score += 1
        reasons.append("链接包含 Skill/Agent 信号")
    if source in ("google/skills", "github/awesome-copilot"):
        score += 1
        reasons.append("官方或半官方合集来源")

    risk, risk_reasons = risk_level(item)
    if risk != "low":
        score -= 2
        reasons.append("存在需人工复核的风险词")

    if is_generic_collection_url(url):
        score -= 4
        reasons.append("合集首页或泛目录，不直接制成卡片")

    status = "selected" if score > 7 and risk == "low" and not is_generic_collection_url(url) else "candidate"
    return {
        **item,
        "canonical_url": canonical_url(url),
        "category": infer_category(item),
        "score": score,
        "status": status,
        "risk_level": risk,
        "score_reasons": reasons,
        "risk_reasons": risk_reasons,
    }


def build_card(item: dict) -> dict:
    category = str(item.get("category") or "工作流")
    link = str(item.get("link") or "")
    name = display_name_from_source_name(str(item.get("name") or ""), link)
    tags = []
    for tag in (owner_from_url(link), repo_from_url(link), slug_from_url(link), category):
        if tag and tag not in tags:
            tags.append(tag)
    return {
        "name": name,
        "description": translate_description(item),
        "audience": AUDIENCE_BY_CATEGORY.get(category, "工作流"),
        "source": source_from_url(link),
        "category": category,
        "tags": tags[:5],
        "github_url": link,
    }


def load_data() -> list[dict]:
    raw = DATA_FILE.read_text(encoding="utf-8")
    match = re.search(r"window\.skillsData\s*=\s*(\[[\s\S]*\]);?\s*$", raw)
    if not match:
        raise RuntimeError("Unable to parse data.js")
    return json.loads(match.group(1))


def write_data(items: list[dict]) -> None:
    DATA_FILE.write_text("window.skillsData = " + json.dumps(items, ensure_ascii=False, indent=2) + ";\n", encoding="utf-8")


def gather_items() -> list[dict]:
    items = []
    for repo in COLLECTION_REPOS:
        items.extend(extract_readme_items(repo))
        if repo == "google/skills":
            items.extend(extract_google_directory_items(repo))
    by_url: dict[str, dict] = {}
    for item in items:
        scored = score_item(item)
        if not scored:
            continue
        key = str(scored.get("canonical_url") or scored.get("link"))
        existing = by_url.get(key)
        if existing is None or int(scored.get("score") or 0) > int(existing.get("score") or 0):
            by_url[key] = scored
        elif existing:
            sources = set(str(existing.get("source_collection", "")).split(", "))
            sources.add(str(scored.get("source_collection", "")))
            existing["source_collection"] = ", ".join(sorted(source for source in sources if source))
    return sorted(by_url.values(), key=lambda item: (-int(item.get("score") or 0), str(item.get("name") or "").lower()))


def main() -> int:
    parser = argparse.ArgumentParser(description="Import selected skills from awesome skill collection repositories.")
    parser.add_argument("--append-data", action="store_true")
    parser.add_argument("--limit", type=int, default=60)
    args = parser.parse_args()

    scored = gather_items()
    COLLECTIONS_DIR.mkdir(parents=True, exist_ok=True)
    REPORT_FILE.write_text(json.dumps(scored, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"[ok] {len(scored)} scored collection skills written to {REPORT_FILE}")

    if not args.append_data:
        return 0

    data = load_data()
    existing_urls = {canonical_url(str(item.get("github_url") or "")) for item in data if isinstance(item, dict)}
    added = 0
    skipped_duplicates = 0
    for item in scored:
        if item.get("status") != "selected":
            continue
        key = canonical_url(str(item.get("link") or ""))
        if key in existing_urls:
            skipped_duplicates += 1
            continue
        data.append(build_card(item))
        existing_urls.add(key)
        added += 1
        if added >= args.limit:
            break
    if added:
        write_data(data)
    print(f"[ok] added={added} skipped_duplicates={skipped_duplicates}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
