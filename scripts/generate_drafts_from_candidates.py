#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import pathlib
import sys

from generate_skill_draft import (
    DRAFTS_DIR,
    build_draft,
    extract_existing_data_array,
    parse_repo_url,
    save_skill,
    write_data_array,
)


ROOT = pathlib.Path(__file__).resolve().parent.parent
DEFAULT_CANDIDATES_FILE = ROOT / "candidates" / "skills_candidates.json"
CONFIDENCE_ORDER = {"low": 1, "medium": 2, "high": 3}


def load_candidates(path: pathlib.Path) -> list[dict]:
    if not path.exists():
        raise FileNotFoundError(f"Candidates file not found: {path}")

    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, list):
        raise ValueError("Candidates file must contain a JSON array.")
    return [item for item in data if isinstance(item, dict)]


def should_include(
    candidate: dict,
    min_confidence: str,
    include_high_risk: bool,
    include_published: bool,
) -> bool:
    url = str(candidate.get("github_url") or "").strip()
    if not url:
        return False

    status = str(candidate.get("status") or "candidate").lower()
    if status == "published" and not include_published:
        return False
    if status == "blocked_high_risk" and not include_high_risk:
        return False

    confidence = str(candidate.get("confidence") or "low").lower()
    if CONFIDENCE_ORDER.get(confidence, 0) < CONFIDENCE_ORDER[min_confidence]:
        return False

    risk_level = str(candidate.get("risk_level") or "unknown").lower()
    if risk_level == "high" and not include_high_risk:
        return False

    return True


def sort_candidates(candidates: list[dict]) -> list[dict]:
    return sorted(
        candidates,
        key=lambda item: (
            str(item.get("risk_level") or "unknown").lower() == "high",
            -int(item.get("score") or 0),
            str(item.get("full_name") or item.get("github_url") or "").lower(),
        ),
    )


def write_draft_file(repo_url: str, draft: dict) -> pathlib.Path:
    owner, repo = parse_repo_url(repo_url)
    DRAFTS_DIR.mkdir(parents=True, exist_ok=True)
    output_path = DRAFTS_DIR / f"{owner}__{repo}.json"
    output_path.write_text(json.dumps(draft, ensure_ascii=False, indent=2), encoding="utf-8")
    return output_path


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate Skill drafts from discovered candidate repositories.")
    parser.add_argument("--candidates", default=str(DEFAULT_CANDIDATES_FILE), help="Candidates JSON file path.")
    parser.add_argument("--min-confidence", choices=("low", "medium", "high"), default="high")
    parser.add_argument("--limit", type=int, default=10, help="Maximum number of candidates to process.")
    parser.add_argument("--include-high-risk", action="store_true", help="Allow candidates with risk_level=high.")
    parser.add_argument("--include-published", action="store_true", help="Also process candidates already published in data.js.")
    parser.add_argument("--append-data", action="store_true", help="Append accepted drafts to data.js without overwriting existing URLs.")
    parser.add_argument("--update-data", action="store_true", help="Update existing data.js entries with the same github_url, or append if missing.")
    parser.add_argument("--dry-run", action="store_true", help="Show which candidates would be processed without generating drafts.")
    parser.add_argument("--stdout", action="store_true", help="Print generated draft summaries to stdout.")
    args = parser.parse_args()

    if args.limit < 1:
        raise ValueError("--limit must be greater than 0.")

    candidates = load_candidates(pathlib.Path(args.candidates))
    selected = [
        candidate
        for candidate in sort_candidates(candidates)
        if should_include(candidate, args.min_confidence, args.include_high_risk, args.include_published)
    ][: args.limit]

    if args.dry_run:
        print(json.dumps(selected, ensure_ascii=False, indent=2))
        print(f"[ok] {len(selected)} candidates selected")
        return 0

    current_items = extract_existing_data_array() if (args.append_data or args.update_data) else []
    summaries: list[dict] = []

    for candidate in selected:
        repo_url = str(candidate["github_url"])
        try:
            draft = build_draft(repo_url)
            output_path = write_draft_file(repo_url, draft)
            action = "drafted"

            if args.append_data or args.update_data:
                public_draft = {key: value for key, value in draft.items() if not key.startswith("_")}
                current_items, action = save_skill(current_items, public_draft, allow_update=args.update_data)

            summaries.append(
                {
                    "github_url": repo_url,
                    "draft": str(output_path),
                    "action": action,
                    "confidence": candidate.get("confidence"),
                    "risk_level": candidate.get("risk_level"),
                }
            )
            print(f"[ok] {action}: {repo_url}")
        except Exception as error:
            summaries.append({"github_url": repo_url, "action": "failed", "error": str(error)})
            print(f"[error] failed: {repo_url}: {error}", file=sys.stderr)

    if args.append_data or args.update_data:
        write_data_array(current_items)

    if args.stdout:
        print(json.dumps(summaries, ensure_ascii=False, indent=2))

    print(f"[ok] processed {len(selected)} candidates")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
