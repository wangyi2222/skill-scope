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


def clean_text(text: str) -> str:
    value = re.sub(r"`([^`]+)`", r"\1", text)
    value = re.sub(r"\*\*([^*]+)\*\*", r"\1", value)
    value = re.sub(r"\*([^*]+)\*", r"\1", value)
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


def infer_platforms(item: dict) -> list[str]:
    text = " ".join(str(item.get(key) or "") for key in ("name", "description", "link", "source_collection")).lower()
    platforms = []
    if "anthropic" in text or "claude" in text:
        platforms.append("Claude")
    if "copilot" in text or "github/awesome-copilot" in text:
        platforms.append("Copilot")
    if "codex" in text:
        platforms.append("Codex")
    if "cursor" in text:
        platforms.append("Cursor")
    if "gemini" in text or "google/skills" in text:
        platforms.append("Gemini")
    if "antigravity" in text:
        platforms.append("Antigravity")
    return platforms or ["Claude"]


def infer_level(category: str, description: str) -> str:
    text = f"{category} {description}".lower()
    if any(word in text for word in ("security", "mcp", "infrastructure", "evaluation", "training", "cloudflare", "stripe", "postgres", "auth")):
        return "高级"
    if category in ("开发", "嵌入式", "自动化", "研究"):
        return "进阶"
    return "基础"


def translate_description(item: dict) -> str:
    description = str(item.get("description") or "").strip()
    name = str(item.get("name") or slug_from_url(str(item.get("link") or "")))
    if description in DESC_TRANSLATIONS:
        return DESC_TRANSLATIONS[description]
    if description and re.search(r"[\u4e00-\u9fff]", description):
        text = description.rstrip("。")
        if not text.startswith(("用于", "帮助", "适合", "提供", "支持")):
            text = "用于" + text
        return text[:90] + "。"
    if description:
        return f"用于{name} 相关的 Agent Skill 场景，原始说明为：{description[:48].rstrip('.')}。"
    return f"用于{name} 相关的 Agent Skill 场景，适合按需跳转到原仓库继续了解。"


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
        reasons.append("平台官方或半官方合集来源")

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
    name = str(item.get("name") or slug_from_url(str(item.get("link") or ""))).strip()
    if name.lower() in ("github", "repository", "repo"):
        name = slug_from_url(str(item.get("link") or ""))
    tags = []
    for tag in (owner_from_url(str(item.get("link") or "")), repo_from_url(str(item.get("link") or "")), slug_from_url(str(item.get("link") or "")), category):
        if tag and tag not in tags:
            tags.append(tag)
    return {
        "name": name,
        "description": translate_description(item),
        "audience": AUDIENCE_BY_CATEGORY.get(category, "工作流"),
        "level": infer_level(category, str(item.get("description") or "")),
        "category": category,
        "platforms": infer_platforms(item),
        "tags": tags[:5],
        "github_url": str(item.get("link") or ""),
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
