#!/usr/bin/env python3
from __future__ import annotations

import argparse
import os
import re
from difflib import SequenceMatcher
from typing import Dict, List, Tuple

import bibtexparser
import requests
import yaml
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

DEFAULT_TIMEOUT = 30
SECTION_START = "## Publication Codes"
SECTION_END = "## Current Projects"
AUTO_MARKER_START = "<!-- publication-codes:start -->"
AUTO_MARKER_END = "<!-- publication-codes:end -->"


def make_session() -> requests.Session:
    session = requests.Session()
    retries = Retry(
        total=5,
        connect=5,
        read=5,
        status=5,
        backoff_factor=1,
        status_forcelist=(429, 500, 502, 503, 504),
        allowed_methods=("GET",),
        raise_on_status=False,
    )
    adapter = HTTPAdapter(max_retries=retries)
    session.mount("https://", adapter)
    session.headers.update(
        {
            "User-Agent": "PersonalSite publication code updater/1.0",
        }
    )
    return session


def norm(text: str) -> str:
    text = text or ""
    text = re.sub(r"[“”\"'`]", "", text)
    text = text.lower()
    text = re.sub(r"[^a-z0-9]+", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def load_bib(path: str) -> List[Dict[str, str]]:
    with open(path, "r", encoding="utf-8") as handle:
        db = bibtexparser.load(handle)
    return db.entries


def load_overrides(path: str) -> Dict[str, object]:
    with open(path, "r", encoding="utf-8") as handle:
        return yaml.safe_load(handle) or {}


def get_repo_readme(session: requests.Session, owner: str, repo: str, branch: str = "main") -> str:
    candidates = [
        f"https://raw.githubusercontent.com/{owner}/{repo}/{branch}/README.md",
        f"https://raw.githubusercontent.com/{owner}/{repo}/{branch}/readme.md",
        f"https://raw.githubusercontent.com/{owner}/{repo}/{branch}/README.rst",
    ]
    for url in candidates:
        response = session.get(url, timeout=DEFAULT_TIMEOUT)
        if response.ok and response.text:
            return response.text
    return ""


def repo_url(owner: str, repo: str) -> str:
    return f"https://github.com/{owner}/{repo}"


def repo_text(full_name: str, readme: str) -> str:
    return "\n".join(
        part
        for part in [
            full_name.split("/", 1)[-1],
            full_name,
            readme,
        ]
        if part
    )


def title_variants(entry: Dict[str, str], aliases: Dict[str, List[str]]) -> List[str]:
    titles = []
    for field in ("cv_title", "title"):
        value = (entry.get(field) or "").strip()
        if value and value not in titles:
            titles.append(value)
    for alias in aliases.get(entry["ID"], []):
        if alias not in titles:
            titles.append(alias)
    return titles


def is_repo_match(title: str, haystack: str) -> bool:
    n_title = norm(title)
    n_haystack = norm(haystack)
    if not n_title or not n_haystack:
        return False
    if n_title in n_haystack:
        return True
    words = n_title.split()
    if len(words) >= 6 and " ".join(words[:6]) in n_haystack:
        return True
    return SequenceMatcher(None, n_title, n_haystack).ratio() >= 0.78


def discover_publication_codes(
    entries: List[Dict[str, str]],
    owners: List[str],
    candidate_repos: List[str],
    aliases: Dict[str, List[str]],
    manual_repos: Dict[str, str],
    display_titles: Dict[str, str],
    display_order: List[str],
) -> List[Tuple[str, str]]:
    session = make_session()
    readmes: Dict[str, str] = {}
    inspected_repos = candidate_repos[:]

    results: List[Tuple[str, str]] = []
    order_index = {entry_id: idx for idx, entry_id in enumerate(display_order)}
    for entry in entries:
        display_title = (
            display_titles.get(entry["ID"])
            or (entry.get("cv_title") or entry.get("title") or "").strip()
        )
        if not display_title:
            continue

        matched_url = manual_repos.get(entry["ID"], "")
        if not matched_url:
            for full_name in inspected_repos:
                owner, repo_name = full_name.split("/", 1)
                if full_name not in readmes:
                    readmes[full_name] = get_repo_readme(session, owner, repo_name)
                haystack = repo_text(full_name, readmes.get(full_name, ""))
                if any(is_repo_match(title, haystack) for title in title_variants(entry, aliases)):
                    matched_url = repo_url(owner, repo_name)
                    break

        if matched_url:
            results.append((entry["ID"], display_title, matched_url))

    results.sort(key=lambda item: (order_index.get(item[0], 10_000), item[1].lower()))
    return [(title, url) for _, title, url in results]


def render_lines(matches: List[Tuple[str, str]]) -> str:
    lines = [
        "The following publications have an associated GitHub repository that contains the code used to obtain some or all of the results and to generate the plots:",
        AUTO_MARKER_START,
    ]
    for title, url in matches:
        lines.append(f"- {title} / [repo]({url})")
    lines.append(AUTO_MARKER_END)
    return "\n".join(lines)


def replace_section(content: str, replacement: str) -> str:
    pattern = re.compile(
        rf"({re.escape(SECTION_START)}\n\n)(.*?)(\n\n{re.escape(SECTION_END)})",
        re.DOTALL,
    )
    match = pattern.search(content)
    if not match:
        raise RuntimeError("Could not find the Publication Codes section in research.md")
    return content[: match.start(2)] + replacement + content[match.end(2) :]


def update_publication_codes(bib_path: str, research_md_path: str, config_path: str) -> int:
    entries = load_bib(bib_path)
    config = load_overrides(config_path)
    owners = config.get("owners", [])
    candidate_repos = config.get("candidate_repos", [])
    aliases = config.get("title_aliases", {})
    manual_repos = config.get("manual_repos", {})
    display_titles = config.get("display_titles", {})
    display_order = config.get("display_order", [])

    matches = discover_publication_codes(
        entries,
        owners,
        candidate_repos,
        aliases,
        manual_repos,
        display_titles,
        display_order,
    )

    with open(research_md_path, "r", encoding="utf-8") as handle:
        research_md = handle.read()
    updated = replace_section(research_md, render_lines(matches))
    with open(research_md_path, "w", encoding="utf-8") as handle:
        handle.write(updated)

    print(f"Updated {research_md_path} with {len(matches)} publication code links.")
    return 0


def main() -> int:
    root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--bib",
        default=os.path.join(root_dir, "_bibliography", "publications.bib"),
    )
    parser.add_argument(
        "--research-md",
        default=os.path.join(root_dir, "research.md"),
    )
    parser.add_argument(
        "--config",
        default=os.path.join(root_dir, "_data", "publication_codes.yml"),
    )
    args = parser.parse_args()
    return update_publication_codes(args.bib, args.research_md, args.config)


if __name__ == "__main__":
    raise SystemExit(main())
