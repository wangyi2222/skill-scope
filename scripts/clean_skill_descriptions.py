#!/usr/bin/env python3
from __future__ import annotations

import json
import pathlib
import re

from import_skill_collections import (
    REPORT_FILE,
    canonical_url,
    clean_text,
    translate_description,
)


ROOT = pathlib.Path(__file__).resolve().parent.parent
DATA_FILE = ROOT / "data.js"


def load_data() -> list[dict]:
    raw = DATA_FILE.read_text(encoding="utf-8")
    match = re.search(r"window\.skillsData\s*=\s*(\[[\s\S]*\]);?\s*$", raw)
    if not match:
        raise RuntimeError("Unable to parse data.js")
    return json.loads(match.group(1))


def write_data(items: list[dict]) -> None:
    DATA_FILE.write_text(
        "window.skillsData = " + json.dumps(items, ensure_ascii=False, indent=2) + ";\n",
        encoding="utf-8",
    )


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
        if source:
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
