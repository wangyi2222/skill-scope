#!/usr/bin/env python3
from __future__ import annotations

import json
import pathlib
import re

from common import DATA_FILE, canonical_url, load_data, write_data
from import_skill_collections import (
    REPORT_FILE,
    clean_text,
    translate_description,
)

MANUAL_DESCRIPTION_FIXES = {
    "web-artifacts-builder": "用于使用 React 和 Tailwind 构建 Claude HTML 交互作品。",
    "cloudflare/building-ai-agent-on-cloudflare": "用于在 Cloudflare 上构建具备状态管理和实时通信能力的 AI Agent。",
    "cloudflare/building-mcp-server-on-cloudflare": "用于在 Cloudflare 上构建支持工具调用和 OAuth 的远程 MCP 服务。",
    "cloudflare/wrangler": "用于部署和管理 Cloudflare Workers、KV、R2、D1、Vectorize、Queues 与工作流资源。",
    "supabase/postgres-best-practices": "用于为 Supabase PostgreSQL 项目提供数据库最佳实践建议。",
    "webapp-testing": "用于通过 Playwright 检查和测试本地 Web 应用。",
    "cloudflare/commands": "用于查询和使用 Cloudflare 命令行相关能力。",
    "firecrawl-agent": "用于把 Firecrawl 网页抓取能力接入 Agent 工作流。",
}


def normalize_existing_description(description: str) -> str:
    value = clean_text(description)
    value = re.sub(r"原始说明为[:：]\s*", "", value)
    value = re.sub(r"\s+", " ", value).strip()
    return value


def main() -> int:
    items = load_data()
    report_items = json.loads(REPORT_FILE.read_text(encoding="utf-8")) if REPORT_FILE.exists() else []
    by_url = {
        canonical_url(str(item.get("link") or "")): item
        for item in report_items
        if isinstance(item, dict) and item.get("link")
    }

    changed = 0
    for item in items:
        url = canonical_url(str(item.get("github_url") or ""))
        old_description = str(item.get("description") or "")
        source = by_url.get(url)
        name = str(item.get("name") or "")
        if name in MANUAL_DESCRIPTION_FIXES:
            new_description = MANUAL_DESCRIPTION_FIXES[name]
        elif source:
            new_description = translate_description(source)
        else:
            new_description = normalize_existing_description(old_description)

        if new_description != old_description:
            item["description"] = new_description
            changed += 1

    write_data(items)
    print(f"[ok] cleaned_descriptions={changed}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
