#!/usr/bin/env python3
from __future__ import annotations

import argparse
import re
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parent.parent
POSTS_DIR = ROOT / "_posts"
RULES_PATH = ROOT / "_data" / "post_taxonomy.yml"


def load_front_matter(path: Path) -> tuple[dict, str]:
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---\n"):
        raise ValueError(f"{path} does not start with YAML front matter")
    _, fm_text, body = text.split("---\n", 2)
    data = yaml.safe_load(fm_text) or {}
    return data, body


def dump_front_matter(path: Path, data: dict, body: str) -> None:
    rendered = "---\n" + yaml.safe_dump(data, sort_keys=False, allow_unicode=True).strip() + "\n---\n" + body
    path.write_text(rendered, encoding="utf-8")


def normalize(text: str) -> str:
    return re.sub(r"\s+", " ", text.lower())


def score_rules(text: str, rules: dict[str, dict]) -> list[tuple[str, int]]:
    scored: list[tuple[str, int]] = []
    for name, config in rules.items():
        score = 0
        for keyword in config.get("keywords", []):
            if keyword.lower() in text:
                score += max(1, len(keyword.split()))
        if score:
            scored.append((name, score))
    scored.sort(key=lambda item: (-item[1], item[0]))
    return scored


def suggest_for_post(path: Path, rules: dict) -> dict:
    data, body = load_front_matter(path)
    source = normalize(" ".join([
        str(data.get("title", "")),
        str(data.get("excerpt", "")),
        body,
    ]))

    category_scores = score_rules(source, rules.get("categories", {}))
    tag_scores = score_rules(source, rules.get("tags", {}))

    categories = [name for name, _ in category_scores[:2]]
    tags = [name for name, _ in tag_scores[:5]]

    return {
        "path": path,
        "data": data,
        "body": body,
        "categories": categories,
        "tags": tags,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Suggest categories and tags for blog posts.")
    parser.add_argument("--apply-missing", action="store_true", help="Write suggestions into posts that do not already define categories or tags.")
    parser.add_argument("paths", nargs="*", help="Optional specific post files.")
    args = parser.parse_args()

    rules = yaml.safe_load(RULES_PATH.read_text(encoding="utf-8")) or {}
    paths = [Path(p) for p in args.paths] if args.paths else sorted(POSTS_DIR.glob("*.md"))

    for path in paths:
        post = suggest_for_post(path, rules)
        rel_path = post["path"].relative_to(ROOT)
        print(rel_path)
        print(f"  suggested categories: {post['categories'] or '[]'}")
        print(f"  suggested tags: {post['tags'] or '[]'}")

        if args.apply_missing:
            updated = False
            data = post["data"]
            if not data.get("categories") and post["categories"]:
                data["categories"] = post["categories"]
                updated = True
            if not data.get("tags") and post["tags"]:
                data["tags"] = post["tags"]
                updated = True
            if updated:
                dump_front_matter(path, data, post["body"])
                print("  applied suggestions")


if __name__ == "__main__":
    main()
