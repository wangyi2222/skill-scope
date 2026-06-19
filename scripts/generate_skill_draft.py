#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import pathlib
import re
import subprocess
import sys
import urllib.error
import urllib.parse
import urllib.request


ROOT = pathlib.Path(__file__).resolve().parent.parent
DRAFTS_DIR = ROOT / "drafts"
DATA_FILE = ROOT / "data.js"
STOP_WORDS = {
    "the", "and", "for", "that", "this", "with", "from", "into", "your", "you",
    "are", "not", "use", "using", "used", "readme", "github", "project", "skill",
    "code", "local", "viewer", "development", "account", "creating", "contribute",
    "\u4e00\u4e2a", "\u8fd9\u4e2a", "\u9879\u76ee", "\u7528\u4e8e", "\u4ee5\u53ca", "\u53ef\u4ee5",
    "\u8fdb\u884c", "\u76f8\u5173", "\u652f\u6301", "\u529f\u80fd", "\u5de5\u5177",
}
PLATFORM_RULES = {
    "Claude": ["claude", "claude code"],
    "Codex": ["codex", "codex cli", ".codex"],
    "Cursor": ["cursor"],
    "Gemini": ["gemini"],
}
CHINESE_PREFIX_PATTERNS = [
    r"^\u8fd9\u662f\u4e00\u4e2a",
    r"^\u8fd9\u662f\u7528\u4e8e",
    r"^\u4e00\u4e2a\u7528\u4e8e",
    r"^\u672c\u9879\u76ee\u662f",
    r"^\u8be5\u9879\u76ee\u662f",
]
ENGLISH_PREFIX_PATTERNS = [
    r"^the all-in-one manager for\s+",
    r"^all-in-one manager for\s+",
    r"^an?\s+",
]


def decode_escapes(text: str) -> str:
    return text



ZH_FOR_INTRO = decode_escapes("\u7528\u4e8e\u4ecb\u7ecd")
ZH_PENDING_DESC = decode_escapes("\u4f5c\u7528\u7684 Skill\uff0c\u5177\u4f53\u7b80\u4ecb\u5f85\u8865\u5145\u3002")
ZH_FOR = decode_escapes("\u7528\u4e8e")
ZH_PERIOD = decode_escapes("\u3002")
ZH_HELP = decode_escapes("\u5e2e\u52a9")
ZH_FIT = decode_escapes("\u9002\u5408")
ZH_PROVIDE = decode_escapes("\u63d0\u4f9b")
ZH_INTEGRATE = decode_escapes("\u96c6\u6210")
ZH_SUPPORT = decode_escapes("\u652f\u6301")
ZH_DEV = decode_escapes("\u5f00\u53d1")
ZH_WORKFLOW = decode_escapes("\u5de5\u4f5c\u6d41")
ZH_DESIGN = decode_escapes("\u8bbe\u8ba1")
ZH_PENDING = decode_escapes("\u5f85\u8865\u5145")
ZH_SESSION = decode_escapes("\u4f1a\u8bdd")
ZH_VISUAL = decode_escapes("\u53ef\u89c6\u5316")
ZH_BROWSER = decode_escapes("\u6d4f\u89c8\u5668")
ZH_FLOW = decode_escapes("\u6d41\u7a0b")
ZH_TASK = decode_escapes("\u4efb\u52a1")
ZH_ORGANIZE = decode_escapes("\u6574\u7406")
ZH_BROWSE = decode_escapes("\u6d4f\u89c8")
ZH_AGGREGATE = decode_escapes("\u805a\u5408")
ZH_IMAGE = decode_escapes("\u56fe\u50cf")
ZH_VISION = decode_escapes("\u89c6\u89c9")
ZH_MATERIAL = decode_escapes("\u7d20\u6750")
ZH_CODE = decode_escapes("\u4ee3\u7801")
ZH_PLUGIN = decode_escapes("\u63d2\u4ef6")
ZH_API = decode_escapes("\u63a5\u53e3")
ZH_CONFIG = decode_escapes("\u914d\u7f6e")
ZH_DOC = decode_escapes("\u6587\u6863")
ZH_AUTO = decode_escapes("\u81ea\u52a8\u5316")
ZH_RESEARCH = decode_escapes("\u7814\u7a76")
ZH_EMBEDDED = decode_escapes("\u5d4c\u5165\u5f0f")
ZH_ADVANCED = decode_escapes("\u8fdb\u9636")
ZH_EXPERT = decode_escapes("\u9ad8\u7ea7")
ZH_BASIC = decode_escapes("\u57fa\u7840")

CATEGORY_RULES = [
    (ZH_EMBEDDED, ["embedded", "stm32", "gd32", "mspm0", "firmware", "probe", "openocd", "rtt", "ble", "spice", "multisim", "ngspice", "simulink", "\u5d4c\u5165\u5f0f", "\u56fa\u4ef6", "\u70e7\u5f55", "\u7535\u8def", "\u4eff\u771f"]),
    (ZH_DOC, ["docs", "documentation", "readme", "markdown", "wiki", ZH_DOC]),
    (ZH_DEV, ["debug", "debugger", "sdk", "api", "cli", "code", "compiler", "build", "test", "config", ZH_DEV, ZH_CODE, ZH_CONFIG]),
    (ZH_WORKFLOW, ["workflow", "session", "memory", "viewer", "dashboard", "manager", "switch", "process", ZH_WORKFLOW, ZH_SESSION, ZH_ORGANIZE]),
    (ZH_PLUGIN, ["plugin", "extension", "vscode", "cursor", "marketplace", ZH_PLUGIN]),
    (ZH_IMAGE, ["image", "photo", "picture", "visual", "design", "mockup", ZH_IMAGE, ZH_DESIGN, ZH_VISION]),
    (ZH_AUTO, ["automation", "auto", "batch", "script", "scheduler", "pipeline", ZH_AUTO]),
    (ZH_RESEARCH, ["research", "search", "paper", "analysis", "knowledge", "rag", ZH_RESEARCH]),
]

ADVANCED_KEYWORDS = [
    "embedded", "stm32", "probe", "debugger", "openocd", "rtt", "ble", "firmware",
    "compiler", "kernel", "driver", "schema", "infrastructure",
]
INTERMEDIATE_KEYWORDS = [
    "cli", "api", "sdk", "config", "plugin", "extension", "provider", "agent",
    "workflow", "automation", "vscode", "token", "environment",
]
LEVEL_ALIASES = {
    ZH_BASIC: ZH_BASIC,
    "basic": ZH_BASIC,
    "beginner": ZH_BASIC,
    "easy": ZH_BASIC,
    ZH_ADVANCED: ZH_ADVANCED,
    "intermediate": ZH_ADVANCED,
    "advanced": ZH_ADVANCED,
    "medium": ZH_ADVANCED,
    ZH_EXPERT: ZH_EXPERT,
    "expert": ZH_EXPERT,
    "hard": ZH_EXPERT,
    "professional": ZH_EXPERT,
    ZH_PENDING: ZH_PENDING,
    "unknown": ZH_PENDING,
    "todo": ZH_PENDING,
}

def http_get(url: str, headers: dict[str, str] | None = None) -> str | None:
    request = urllib.request.Request(url, headers=headers or {})
    try:
        with urllib.request.urlopen(request, timeout=20) as response:
            return response.read().decode("utf-8")
    except urllib.error.HTTPError as error:
        if error.code == 404:
            return None
        raise
    except urllib.error.URLError:
        return curl_get(url, headers)


def curl_get(url: str, headers: dict[str, str] | None = None) -> str | None:
    command = ["curl.exe", "-L", "--silent", "--show-error", url]
    for key, value in (headers or {}).items():
        command.extend(["-H", f"{key}: {value}"])

    try:
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            timeout=30,
            check=False,
        )
    except (subprocess.SubprocessError, FileNotFoundError):
        return None

    if result.returncode != 0:
        return None

    return result.stdout


def parse_repo_url(url: str) -> tuple[str, str]:
    parsed = urllib.parse.urlparse(url)
    if parsed.netloc not in ("github.com", "www.github.com"):
        raise ValueError("Only github.com repository URLs are supported in this version.")

    parts = [part for part in parsed.path.strip("/").split("/") if part]
    if len(parts) < 2:
        raise ValueError("Repository URL must look like https://github.com/<owner>/<repo>.")

    owner = parts[0]
    repo = parts[1].removesuffix(".git")
    return owner, repo


def github_api_get(path: str) -> dict | list | None:
    url = f"https://api.github.com{path}"
    try:
        raw = http_get(url, headers={"Accept": "application/vnd.github+json"})
    except urllib.error.HTTPError as error:
        if error.code == 403:
            return None
        raise
    if raw is None:
        return None
    return json.loads(raw)


def fetch_text_file(owner: str, repo: str, path: str) -> str | None:
    return http_get(f"https://raw.githubusercontent.com/{owner}/{repo}/HEAD/{path}")


def fetch_repo_html(owner: str, repo: str) -> str | None:
    return http_get(f"https://github.com/{owner}/{repo}")


def first_non_empty(*values: str | None) -> str:
    for value in values:
        if value and value.strip():
            return value.strip()
    return ""


def clean_markdown(text: str) -> str:
    cleaned = re.sub(r"```.*?```", "", text, flags=re.DOTALL)
    cleaned = re.sub(r"<img[^>]*>", "", cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r"</?p[^>]*>", "", cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r"</?div[^>]*>", "", cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r"</?br\s*/?>", "\n", cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r"<[^>]+>", "", cleaned)
    cleaned = re.sub(r"`([^`]+)`", r"\1", cleaned)
    cleaned = re.sub(r"\*\*([^*]+)\*\*", r"\1", cleaned)
    cleaned = re.sub(r"\*([^*]+)\*", r"\1", cleaned)
    cleaned = re.sub(r"!\[[^\]]*\]\([^)]+\)", "", cleaned)
    cleaned = re.sub(r"\[[^\]]+\]\([^)]+\)", lambda m: m.group(0).split("](")[0][1:], cleaned)
    cleaned = re.sub(r"^#{1,6}\s*", "", cleaned, flags=re.MULTILINE)
    cleaned = re.sub(r"^\s*[-*+]\s+", "", cleaned, flags=re.MULTILINE)
    cleaned = re.sub(r"\r", "", cleaned)
    cleaned = re.sub(r"\n{2,}", "\n\n", cleaned)
    return cleaned.strip()


def extract_readme_paragraphs(text: str | None) -> list[str]:
    if not text:
        return []

    cleaned = clean_markdown(text)
    paragraphs = [part.strip() for part in cleaned.split("\n\n") if part.strip()]
    filtered: list[str] = []
    for paragraph in paragraphs:
        lower = paragraph.lower()
        if lower.startswith(("license", "installation", "usage", "contributing")):
            continue
        if paragraph.startswith(("http://", "https://", "![", "[![")):
            continue
        if len(paragraph.split()) <= 3 and len(paragraph) <= 40:
            continue
        if len(paragraph) < 16:
            continue
        filtered.append(paragraph)
    return filtered


def is_github_fallback_description(text: str) -> bool:
    lower = text.strip().lower()
    return lower.startswith("contribute to ") and "development by creating an account on github" in lower


def is_mostly_chinese(text: str) -> bool:
    chinese_count = len(re.findall(r"[\u4e00-\u9fff]", text))
    latin_count = len(re.findall(r"[A-Za-z]", text))
    return chinese_count >= max(6, latin_count)


def strip_trailing_noise(text: str) -> str:
    text = text.strip()
    text = re.sub(r"\s+", " ", text)
    text = re.sub(r"^[\-:?,?.?;?]+", "", text)
    text = re.sub(r"[\s,?;?:?]+$", "", text)
    return text.strip()


def normalize_sentence(text: str, repo_name: str) -> str:
    value = clean_markdown(text)
    value = strip_trailing_noise(value)
    if not value:
        return f"{ZH_FOR_INTRO} {repo_name} {ZH_PENDING_DESC}"

    value = value.split("\n")[0].strip()
    value = re.split(r"(?<=[???!?])\s+|(?<=[.!?])\s+", value)[0].strip()

    if is_mostly_chinese(value):
        for pattern in CHINESE_PREFIX_PATTERNS:
            value = re.sub(pattern, "", value).strip()
        value = value.lstrip("?,?: ")
        if not value.startswith((ZH_FOR, ZH_HELP, ZH_FIT, ZH_PROVIDE, ZH_INTEGRATE, ZH_SUPPORT)):
            value = ZH_FOR + value
        value = value.rstrip("?.!??;?,") + ZH_PERIOD
        return value[:90]

    english = value
    for pattern in ENGLISH_PREFIX_PATTERNS:
        english = re.sub(pattern, "", english, flags=re.IGNORECASE).strip()
    english = english.strip(" .,:;!?")
    english = re.sub(r"\s+", " ", english)
    if not english:
        english = repo_name
    return f"{ZH_FOR}{english}{ZH_PERIOD}"[:90]


def infer_description(project_meta: dict | None, readme_text: str | None, repo_description: str, repo_name: str) -> str:
    if project_meta and isinstance(project_meta.get("summary"), str) and project_meta["summary"].strip():
        return normalize_sentence(project_meta["summary"].strip(), repo_name)

    paragraphs = extract_readme_paragraphs(readme_text)
    if paragraphs:
        return normalize_sentence(paragraphs[0], repo_name)

    if repo_description and not is_github_fallback_description(repo_description):
        return normalize_sentence(repo_description, repo_name)

    return f"{ZH_FOR_INTRO} {repo_name} {ZH_PENDING_DESC}"


def infer_tags(project_meta: dict | None, repo_topics: list[str]) -> list[str]:
    if project_meta and isinstance(project_meta.get("tags"), list) and project_meta["tags"]:
        return [str(tag).strip() for tag in project_meta["tags"] if str(tag).strip()]
    if repo_topics:
        return [str(topic).strip() for topic in repo_topics if str(topic).strip()][:4]
    return []


def infer_tags_from_readme(readme_text: str | None, existing_tags: list[str]) -> list[str]:
    if existing_tags:
        return existing_tags
    if not readme_text:
        return []

    cleaned = clean_markdown(readme_text).lower()
    tokens = re.findall(r"[a-zA-Z][a-zA-Z0-9-]{2,}|[\u4e00-\u9fff]{2,8}", cleaned)
    scores: dict[str, int] = {}
    for token in tokens:
        normalized = token.strip("-")
        if normalized in {decode_escapes(word) for word in STOP_WORDS}:
            continue
        if normalized.isdigit():
            continue
        scores[normalized] = scores.get(normalized, 0) + 1

    ranked = sorted(scores.items(), key=lambda item: (-item[1], item[0]))
    return [token for token, _count in ranked[:4]]


def normalize_logo_url(owner: str, repo: str, value: str) -> str:
    value = value.strip()
    if value.startswith(("http://", "https://")):
        return value
    if value.startswith("/"):
        return f"https://raw.githubusercontent.com/{owner}/{repo}/HEAD{value}"
    return f"https://raw.githubusercontent.com/{owner}/{repo}/HEAD/{value.lstrip('./')}"


def infer_logo_url(owner: str, repo: str, readme_text: str | None) -> str:
    if readme_text:
        image_match = re.search(r'<img[^>]+src=["\']([^"\']+)["\']', readme_text, flags=re.IGNORECASE)
        if image_match:
            return normalize_logo_url(owner, repo, image_match.group(1))

        markdown_match = re.search(r'!\[[^\]]*\]\(([^)]+)\)', readme_text)
        if markdown_match:
            return normalize_logo_url(owner, repo, markdown_match.group(1).split()[0])

    for candidate in (
        "src-tauri/icons/icon.png",
        "src-tauri/icons/128x128.png",
        "public/logo.png",
        "assets/logo.png",
        "logo.png",
        "icon.png",
    ):
        if fetch_text_file(owner, repo, candidate) is not None:
            return normalize_logo_url(owner, repo, candidate)

    return ""


def joined_content(*values: str | None) -> str:
    return " ".join(value for value in values if value).lower()


def normalize_level(value: str) -> str:
    normalized = value.strip().lower()
    return LEVEL_ALIASES.get(value.strip(), LEVEL_ALIASES.get(normalized, ZH_PENDING))


def infer_level(project_meta: dict | None, repo_description: str, readme_text: str | None, category: str) -> str:
    if project_meta and isinstance(project_meta.get("level"), str) and project_meta["level"].strip():
        return normalize_level(project_meta["level"])

    text = joined_content(repo_description, readme_text)
    if any(keyword in text for keyword in ADVANCED_KEYWORDS):
        return ZH_EXPERT
    if any(keyword in text for keyword in INTERMEDIATE_KEYWORDS):
        return ZH_ADVANCED
    if category in (ZH_DEV, ZH_AUTO, ZH_EMBEDDED):
        return ZH_ADVANCED
    return ZH_BASIC


def infer_category(project_meta: dict | None, repo_description: str, readme_text: str | None, repo_topics: list[str]) -> str:
    if project_meta and isinstance(project_meta.get("category"), str) and project_meta["category"].strip():
        return project_meta["category"].strip()

    text = joined_content(repo_description, readme_text, " ".join(repo_topics))
    scores: dict[str, int] = {}
    for category, keywords in CATEGORY_RULES:
        score = sum(1 for keyword in keywords if keyword.lower() in text)
        if score:
            scores[category] = score

    if scores:
        return max(scores.items(), key=lambda item: item[1])[0]

    return ZH_PENDING


def infer_platforms(project_meta: dict | None, repo_description: str, readme_text: str | None) -> list[str]:
    if project_meta and isinstance(project_meta.get("platforms"), list) and project_meta["platforms"]:
        return [str(item).strip() for item in project_meta["platforms"] if str(item).strip()]

    text = " ".join(part for part in [repo_description or "", readme_text or ""] if part).lower()
    matched: list[str] = []
    for platform, keywords in PLATFORM_RULES.items():
        if any(keyword in text for keyword in keywords):
            matched.append(platform)
    return matched


def infer_audience_from_content(project_meta: dict | None, repo_description: str, readme_text: str | None, platforms: list[str]) -> str:
    if project_meta and isinstance(project_meta.get("audience"), str) and project_meta["audience"].strip():
        return project_meta["audience"].strip()

    text = " ".join(part for part in [repo_description or "", readme_text or ""] if part).lower()
    design_keywords = ["image", "bitmap", "illustration", "texture", "mockup", ZH_DESIGN, ZH_IMAGE, ZH_VISION, ZH_MATERIAL]
    workflow_keywords = [
        "workflow", "task", "planning", "process", "browser", "viewer", "memory", "session",
        "visualization", "dashboard", ZH_SESSION, ZH_VISUAL, ZH_BROWSER,
        ZH_WORKFLOW, ZH_FLOW, ZH_TASK, ZH_ORGANIZE, ZH_BROWSE, ZH_AGGREGATE,
    ]
    developer_keywords = [
        "api", "sdk", "plugin", "config", "schema", "repo", "cli", "code", "docs",
        ZH_DEV, ZH_CODE, ZH_PLUGIN, ZH_API, ZH_CONFIG, ZH_DOC,
    ]

    if any(keyword in text for keyword in developer_keywords):
        return ZH_DEV
    if any(keyword in text for keyword in workflow_keywords):
        return ZH_WORKFLOW
    if any(keyword in text for keyword in design_keywords):
        return ZH_DESIGN
    if platforms:
        return ZH_DEV
    return ZH_PENDING


def load_project_meta(owner: str, repo: str) -> dict | None:
    for candidate in ("skill.yaml", "project.yaml", "skill.json", "project.json"):
        raw = fetch_text_file(owner, repo, candidate)
        if not raw:
            continue

        if candidate.endswith(".json"):
            try:
                data = json.loads(raw)
                return data if isinstance(data, dict) else None
            except json.JSONDecodeError:
                continue

        simple_meta: dict[str, object] = {}
        for line in raw.splitlines():
            if ":" not in line or line.strip().startswith("#"):
                continue
            key, value = line.split(":", 1)
            key = key.strip()
            value = value.strip()
            if key in ("name", "summary", "category", "audience", "level"):
                simple_meta[key] = value.strip("'\"")
            if key == "tags":
                tags = re.findall(r"[\w\u4e00-\u9fff-]+", value)
                simple_meta[key] = tags
        return simple_meta if simple_meta else None

    return None


def build_draft(repo_url: str) -> dict:
    owner, repo = parse_repo_url(repo_url)
    repo_meta = github_api_get(f"/repos/{owner}/{repo}")
    repo_html = fetch_repo_html(owner, repo)
    if repo_meta is None and not repo_html:
        raise RuntimeError("Unable to fetch GitHub repository metadata.")

    project_meta = load_project_meta(owner, repo)
    readme_text = first_non_empty(
        fetch_text_file(owner, repo, "SKILL.md"),
        fetch_text_file(owner, repo, "README.md"),
    )

    html_description = ""
    html_topics: list[str] = []
    if repo_html:
        desc_match = re.search(r'<meta name="description" content="([^"]+)"', repo_html, flags=re.IGNORECASE)
        if desc_match:
            html_description = desc_match.group(1).strip()
        html_topics = re.findall(r'/topics/([^"#?]+)', repo_html)

    repo_description = first_non_empty(
        str(repo_meta.get("description") or "") if isinstance(repo_meta, dict) else "",
        html_description,
    )
    repo_topics = repo_meta.get("topics") or [] if isinstance(repo_meta, dict) else html_topics

    name = first_non_empty(
        str(project_meta.get("name")) if project_meta else "",
        str(repo_meta.get("name") or repo) if isinstance(repo_meta, dict) else repo,
    )

    inferred_tags = infer_tags(project_meta, [str(topic) for topic in repo_topics])
    inferred_tags = infer_tags_from_readme(readme_text, inferred_tags)
    inferred_platforms = infer_platforms(project_meta, repo_description, readme_text)
    inferred_audience = infer_audience_from_content(project_meta, repo_description, readme_text, inferred_platforms)
    inferred_category = infer_category(project_meta, repo_description, readme_text, [str(topic) for topic in repo_topics])
    inferred_level = infer_level(project_meta, repo_description, readme_text, inferred_category)

    return {
        "name": name,
        "description": infer_description(project_meta, readme_text, repo_description, name),
        "audience": inferred_audience,
        "level": inferred_level,
        "category": inferred_category,
        "platforms": inferred_platforms,
        "tags": inferred_tags,
        "logo_url": infer_logo_url(owner, repo, readme_text),
        "github_url": f"https://github.com/{owner}/{repo}",
        "_source": {
            "repo_description": repo_description,
            "readme_used": bool(readme_text),
            "structured_meta_used": bool(project_meta),
        },
    }


def extract_existing_data_array() -> list[dict]:
    raw = DATA_FILE.read_text(encoding="utf-8")
    match = re.search(r"window\.skillsData\s*=\s*(\[[\s\S]*\]);?\s*$", raw)
    if not match:
        raise RuntimeError("Unable to locate window.skillsData array in data.js")
    return json.loads(match.group(1))


def write_data_array(items: list[dict]) -> None:
    DATA_FILE.write_text("window.skillsData = " + json.dumps(items, ensure_ascii=False, indent=2) + ";\n", encoding="utf-8")


def save_skill(items: list[dict], draft: dict, allow_update: bool) -> tuple[list[dict], str]:
    url = draft["github_url"]
    for index, item in enumerate(items):
        if item.get("github_url") == url:
            if allow_update:
                items[index] = draft
                return items, "updated"
            return items, "skipped"
    items.append(draft)
    return items, "appended"


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate a Skill card draft from a GitHub URL.")
    parser.add_argument("repo_url", help="GitHub repository URL")
    parser.add_argument("--stdout", action="store_true", help="Print the generated draft JSON to stdout instead of saving only to a file.")
    parser.add_argument("--append-data", action="store_true", help="Append the generated card draft into data.js. Existing github_url entries are not overwritten.")
    parser.add_argument("--update-data", action="store_true", help="Update an existing data.js card with the same github_url, or append it if missing.")
    args = parser.parse_args()

    draft = build_draft(args.repo_url)

    DRAFTS_DIR.mkdir(parents=True, exist_ok=True)
    owner, repo = parse_repo_url(args.repo_url)
    output_path = DRAFTS_DIR / f"{owner}__{repo}.json"
    output_path.write_text(json.dumps(draft, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"[ok] Draft written to {output_path}")

    if args.append_data or args.update_data:
        public_draft = {key: value for key, value in draft.items() if not key.startswith("_")}
        current_items = extract_existing_data_array()
        current_items, action = save_skill(current_items, public_draft, allow_update=args.update_data)
        if action != "skipped":
            write_data_array(current_items)
        print(f"[ok] Draft {action} in {DATA_FILE}")

    if args.stdout:
        print(json.dumps(draft, ensure_ascii=False, indent=2))

    return 0


if __name__ == "__main__":
    sys.exit(main())
