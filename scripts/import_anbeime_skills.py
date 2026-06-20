#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import pathlib
import re
from urllib.parse import urlparse

from common import (
    AUDIENCE_BY_CATEGORY,
    CATEGORY_MAP,
    DATA_FILE,
    DESC_TRANSLATIONS,
    EMBEDDED_KEYWORDS,
    HIGH_RISK_WORDS,
    TRUSTED_OWNERS,
    load_data,
    owner_from_url,
    repo_from_url,
    source_from_link,
    write_data,
)

ROOT = pathlib.Path(__file__).resolve().parent.parent
DEFAULT_SOURCE = ROOT / "candidates" / "anbeime_skills.json"
DEFAULT_REPORT = ROOT / "candidates" / "anbeime_scored_skills.json"


def skill_slug(name: str, link: str) -> str:
    if "/" in name:
        return name.split("/")[-1]
    parts = [part for part in urlparse(link).path.strip("/").split("/") if part]
    return parts[-1] if parts else name


def normalize_name(name: str, link: str) -> str:
    slug = skill_slug(name, link)
    if "/" in name:
        return slug
    return name.strip() or slug


def translate_description(description: str, name: str) -> str:
    if description in DESC_TRANSLATIONS:
        return DESC_TRANSLATIONS[description]
    text = description.strip().rstrip(".")
    if not text:
        return f"用于辅助 {name} 相关的 Agent 工作流。"
    return f"用于{text}。"


def risk_level(item: dict) -> tuple[str, list[str]]:
    text = f"{item.get('name', '')} {item.get('description', '')} {item.get('category', '')}".lower()
    reasons = [word for word in HIGH_RISK_WORDS if re.search(rf"\b{re.escape(word)}\b", text)]
    if reasons:
        return "medium", reasons
    return "low", ["结构化来源明确，未发现明显高风险信号"]


def score_item(item: dict) -> dict:
    link = str(item.get("link") or "")
    name = str(item.get("name") or "")
    description = str(item.get("description") or "")
    category = str(item.get("category") or "")
    owner = owner_from_url(link)
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
        owner_from_url(str(item.get("link") or "")),
        repo_from_url(str(item.get("link") or "")),
        skill_slug(str(item.get("name") or ""), str(item.get("link") or "")),
        category,
    ]
    tags = []
    for tag in raw_tags:
        if tag and tag not in tags:
            tags.append(tag)
    return {
        "name": {
            "zh": name,
            "en": name,
        },
        "description": {
            "zh": description,
            "en": description,
        },
        "audience": AUDIENCE_BY_CATEGORY.get(category, "工作流"),
        "source": source_from_link(str(item.get("link") or "")),
        "category": category,
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
