#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import pathlib
import re
import urllib.parse
from datetime import datetime, timezone

from generate_skill_draft import DATA_FILE, fetch_text_file, github_api_get


ROOT = pathlib.Path(__file__).resolve().parent.parent
CANDIDATES_DIR = ROOT / "candidates"
DEFAULT_OUTPUT = CANDIDATES_DIR / "skills_candidates.json"
DEFAULT_QUERIES = [
    '"Claude Code skill"',
    '"Codex skill"',
    '"agent skill"',
    '"SKILL.md"',
    'topic:claude-code',
    'topic:codex',
    'topic:ai-agent',
    'topic:skills',
]
DEFAULT_OWNER_REPO_LIMIT = 100

STRONG_KEYWORDS = [
    "claude code skill",
    "codex skill",
    "agent skill",
    "skill.md",
]
MEDIUM_KEYWORDS = [
    "claude code",
    "codex cli",
    "cursor",
    "gemini cli",
    "ai agent",
    "agent workflow",
    "prompt",
    "automation",
]
WEAK_KEYWORDS = [
    "workflow",
    "assistant",
    "tools",
    "mcp",
]
TOPIC_KEYWORDS = {
    "skill",
    "skills",
    "claude-code",
    "codex",
    "ai-agent",
    "agent-tools",
}
HIGH_RISK_PATTERNS = [
    (r"curl\s+[^|&;\n]+\|\s*(sh|bash|zsh|powershell|pwsh)", "pipes remote script into shell"),
    (r"wget\s+[^|&;\n]+\|\s*(sh|bash|zsh|powershell|pwsh)", "pipes remote script into shell"),
    (r"irm\s+[^|&;\n]+\|\s*iex", "PowerShell remote execution pattern"),
    (r"iwr\s+[^|&;\n]+\|\s*iex", "PowerShell remote execution pattern"),
    (r"invoke-expression|iex\s*\(", "uses Invoke-Expression"),
    (r"chmod\s+\+x\s+[^&;\n]+(&&|;)\s*\./", "asks to execute downloaded file"),
    (r"(api[_-]?key|token|secret|password)\s*[:=]", "mentions sensitive credential fields"),
    (r"paste\s+.*(token|secret|api key|password)", "asks user to paste sensitive credentials"),
    (r"download\s+.*(exe|dll|bat|ps1|sh)\b", "mentions downloading executable scripts or binaries"),
]
MEDIUM_RISK_PATTERNS = [
    (r"\bobfuscat(ed|ion)\b|minified\s+source", "mentions obfuscated or minified source"),
    (r"\bbase64\b.*\bdecode\b", "mentions base64 decode behavior"),
    (r"\beval\s*\(", "mentions eval usage"),
    (r"\badmin\b|\bsudo\b|\broot\b", "mentions elevated permissions"),
]


def search_repositories(query: str, per_page: int) -> list[dict]:
    encoded = urllib.parse.quote_plus(query)
    data = github_api_get(f"/search/repositories?q={encoded}&sort=updated&order=desc&per_page={per_page}")
    if not isinstance(data, dict):
        return []
    items = data.get("items")
    return items if isinstance(items, list) else []


def fetch_owner_repositories(owner: str, limit: int) -> list[dict]:
    repos: list[dict] = []
    page = 1
    per_page = min(100, max(1, limit))
    while len(repos) < limit:
        data = github_api_get(
            f"/users/{urllib.parse.quote(owner)}/repos"
            f"?sort=updated&direction=desc&per_page={per_page}&page={page}"
        )
        if not isinstance(data, list) or not data:
            break
        repos.extend(item for item in data if isinstance(item, dict))
        if len(data) < per_page:
            break
        page += 1
    return repos[:limit]


def fetch_repo_topics(owner: str, repo: str) -> list[str]:
    data = github_api_get(f"/repos/{owner}/{repo}/topics")
    if isinstance(data, dict) and isinstance(data.get("names"), list):
        return [str(item).lower() for item in data["names"]]
    return []


def path_exists(owner: str, repo: str, path: str) -> bool:
    return fetch_text_file(owner, repo, path) is not None


def parse_github_datetime(value: object) -> datetime | None:
    if not isinstance(value, str) or not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None


def has_license(repo: dict) -> bool:
    license_info = repo.get("license")
    return isinstance(license_info, dict) and bool(license_info.get("spdx_id") or license_info.get("name"))


def infer_risk(repo: dict, readme: str, skill_file: str | None) -> tuple[str, list[str]]:
    reasons: list[str] = []
    text = " ".join([str(repo.get("description") or ""), readme, skill_file or ""]).lower()

    for pattern, reason in HIGH_RISK_PATTERNS:
        if re.search(pattern, text, flags=re.IGNORECASE):
            reasons.append(reason)

    high_signal_count = len(reasons)

    for pattern, reason in MEDIUM_RISK_PATTERNS:
        if re.search(pattern, text, flags=re.IGNORECASE):
            reasons.append(reason)

    if not readme.strip():
        reasons.append("missing README")

    if not has_license(repo):
        reasons.append("missing license metadata")

    pushed_at = parse_github_datetime(repo.get("pushed_at"))
    if pushed_at is None:
        reasons.append("unknown maintenance activity")
    else:
        days_since_push = (datetime.now(timezone.utc) - pushed_at).days
        if days_since_push > 730:
            reasons.append("repository appears inactive for over two years")

    if int(repo.get("stargazers_count") or 0) == 0 and int(repo.get("forks_count") or 0) == 0:
        reasons.append("very low public activity")

    if high_signal_count:
        return "high", reasons
    if any(reason in reasons for reason in (
        "missing README",
        "missing license metadata",
        "repository appears inactive for over two years",
        "unknown maintenance activity",
    )):
        return "medium", reasons
    if reasons:
        return "medium", reasons
    return "low", ["no obvious risk signals from metadata and README"]


def score_repository(repo: dict, check_paths: bool = False) -> dict:
    full_name = str(repo.get("full_name") or "")
    if "/" not in full_name:
        return {}

    owner, name = full_name.split("/", 1)
    description = str(repo.get("description") or "")
    html_url = str(repo.get("html_url") or f"https://github.com/{owner}/{name}")
    topics = fetch_repo_topics(owner, name)
    readme = fetch_text_file(owner, name, "README.md") or ""
    skill_file = fetch_text_file(owner, name, "SKILL.md")
    risk_level, risk_reasons = infer_risk(repo, readme, skill_file)

    text = " ".join([description, readme, " ".join(topics)]).lower()
    score = 0
    reasons: list[str] = []

    if skill_file is not None:
        score += 5
        reasons.append("found SKILL.md")

    matched_topics = sorted(set(topics) & TOPIC_KEYWORDS)
    if matched_topics:
        score += 4
        reasons.append("topics: " + ", ".join(matched_topics))

    for keyword in STRONG_KEYWORDS:
        if keyword in text:
            score += 3
            reasons.append(f"strong keyword: {keyword}")

    for keyword in MEDIUM_KEYWORDS:
        if keyword in text:
            score += 2
            reasons.append(f"medium keyword: {keyword}")

    for keyword in WEAK_KEYWORDS:
        if keyword in text:
            score += 1
            reasons.append(f"weak keyword: {keyword}")

    if check_paths:
        for path in (".codex", ".claude", "skills", "agents"):
            if path_exists(owner, name, path):
                score += 2
                reasons.append(f"found path: {path}")

    if not re.search(r"skill|agent|claude|codex|cursor|gemini|workflow|prompt", text):
        score -= 3
        reasons.append("missing core skill or agent signals")

    if score >= 6:
        confidence = "high"
    elif score >= 3:
        confidence = "medium"
    else:
        confidence = "low"

    return {
        "name": name,
        "full_name": full_name,
        "github_url": html_url,
        "score": score,
        "confidence": confidence,
        "description": description,
        "topics": topics,
        "reasons": reasons,
        "risk_level": risk_level,
        "risk_reasons": risk_reasons,
    }


def dedupe_candidates(candidates: list[dict]) -> list[dict]:
    by_url: dict[str, dict] = {}
    for candidate in candidates:
        url = candidate.get("github_url")
        if not url:
            continue
        existing = by_url.get(url)
        if existing is None or candidate.get("score", 0) > existing.get("score", 0):
            by_url[url] = candidate
    return sorted(by_url.values(), key=lambda item: (-item["score"], item["full_name"].lower()))


def load_published_urls() -> set[str]:
    if not DATA_FILE.exists():
        return set()
    raw = DATA_FILE.read_text(encoding="utf-8")
    match = re.search(r"window\.skillsData\s*=\s*(\[[\s\S]*\]);?\s*$", raw)
    if not match:
        return set()
    items = json.loads(match.group(1))
    if not isinstance(items, list):
        return set()
    return {str(item.get("github_url")) for item in items if isinstance(item, dict) and item.get("github_url")}


def attach_candidate_status(candidates: list[dict], published_urls: set[str]) -> list[dict]:
    for candidate in candidates:
        url = str(candidate.get("github_url") or "")
        risk_level = str(candidate.get("risk_level") or "unknown").lower()
        if url in published_urls:
            candidate["status"] = "published"
            candidate["status_label"] = "已上卡片"
        elif risk_level == "high":
            candidate["status"] = "blocked_high_risk"
            candidate["status_label"] = "高风险，需人工复核"
        else:
            candidate["status"] = "candidate"
            candidate["status_label"] = "候选，待确认"
    return candidates


def main() -> int:
    parser = argparse.ArgumentParser(description="Discover candidate Skill repositories from GitHub search.")
    parser.add_argument("--query", action="append", help="GitHub repository search query. Can be provided multiple times.")
    parser.add_argument("--owner", help="Discover candidate Skill repositories from one GitHub user or organization.")
    parser.add_argument("--owner-limit", type=int, default=DEFAULT_OWNER_REPO_LIMIT, help="Maximum repositories to fetch for --owner.")
    parser.add_argument("--per-page", type=int, default=10, help="Repositories to fetch per query.")
    parser.add_argument("--min-score", type=int, default=3, help="Minimum score to keep.")
    parser.add_argument("--output", default=str(DEFAULT_OUTPUT), help="Output JSON file path.")
    parser.add_argument("--stdout", action="store_true", help="Print candidates to stdout.")
    parser.add_argument(
        "--check-paths",
        action="store_true",
        help="Also check .codex/.claude/skills/agents paths. More accurate but slower.",
    )
    args = parser.parse_args()

    candidates: list[dict] = []

    if args.owner:
        source_repos = fetch_owner_repositories(args.owner, args.owner_limit)
        for repo in source_repos:
            candidate = score_repository(repo, check_paths=args.check_paths)
            if candidate and candidate["score"] >= args.min_score:
                candidates.append(candidate)
    else:
        queries = args.query or DEFAULT_QUERIES
        for query in queries:
            for repo in search_repositories(query, args.per_page):
                candidate = score_repository(repo, check_paths=args.check_paths)
                if candidate and candidate["score"] >= args.min_score:
                    candidates.append(candidate)

    results = attach_candidate_status(dedupe_candidates(candidates), load_published_urls())
    output_path = pathlib.Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(results, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    print(f"[ok] {len(results)} candidates written to {output_path}")
    if args.stdout:
        print(json.dumps(results, ensure_ascii=False, indent=2))

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
