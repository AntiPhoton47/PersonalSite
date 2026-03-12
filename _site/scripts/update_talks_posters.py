#!/usr/bin/env python3
from __future__ import annotations

import argparse
import os
import re
from pathlib import Path
from typing import Any, Dict, List, Tuple

import requests
import yaml

RESEARCH_MARKER_START = "<!-- presentations:start -->"
RESEARCH_MARKER_END = "<!-- presentations:end -->"
LEGACY_INCLUDE = "{% include talks_posters_compact.html %}"


def tex_escape(text: str) -> str:
    mapping = {
        "&": r"\&",
        "%": r"\%",
        "$": r"\$",
        "#": r"\#",
        "_": r"\_",
        "{": r"\{",
        "}": r"\}",
    }
    return "".join(mapping.get(ch, ch) for ch in text)


def load_yaml(path: Path) -> Dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        return yaml.safe_load(handle) or {}


def save_yaml(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        yaml.safe_dump(payload, handle, sort_keys=False, allow_unicode=True)


def relative_asset_link(root_dir: Path, asset_path: str) -> str:
    rel = Path(asset_path)
    if rel.is_absolute():
        rel = rel.relative_to(root_dir)
    return "/" + rel.as_posix().lstrip("/")


def scan_assets(root_dir: Path, folder: str) -> List[str]:
    base = root_dir / folder
    if not base.exists():
        return []
    return sorted(str(path.relative_to(root_dir)) for path in base.iterdir() if path.is_file())


def verify_youtube_title(session: requests.Session, url: str) -> str:
    response = session.get(
        "https://www.youtube.com/oembed",
        params={"url": url, "format": "json"},
        timeout=20,
    )
    if not response.ok:
        return ""
    data = response.json()
    return data.get("title", "")


def verify_url(session: requests.Session, url: str) -> bool:
    try:
        response = session.get(url, timeout=20, allow_redirects=True)
        return response.ok
    except requests.RequestException:
        return False


def validate_entries(root_dir: Path, entries: List[Dict[str, Any]], check_online: bool) -> None:
    asset_inventory = {
        "talk": set(scan_assets(root_dir, "assets/files/talks")),
        "poster": set(scan_assets(root_dir, "assets/files/posters")),
    }
    referenced_assets = {"talk": set(), "poster": set()}
    session = requests.Session()

    for entry in entries:
        kind = entry["kind"]
        asset = entry.get("asset")
        if asset:
            if asset not in asset_inventory[kind]:
                raise RuntimeError(f"Missing asset for {entry['id']}: {asset}")
            referenced_assets[kind].add(asset)

        if check_online:
            video = entry.get("links", {}).get("video", "")
            if video:
                title = verify_youtube_title(session, video)
                if not title:
                    raise RuntimeError(f"Unresolvable YouTube link for {entry['id']}: {video}")
            for key in ("listing",):
                url = entry.get("links", {}).get(key, "")
                if url and not verify_url(session, url):
                    raise RuntimeError(f"Unreachable URL for {entry['id']}: {url}")

    for kind, assets in asset_inventory.items():
        unconfigured = sorted(assets - referenced_assets[kind])
        if unconfigured:
            raise RuntimeError(f"Unconfigured {kind} assets: {', '.join(unconfigured)}")


def build_site_item(root_dir: Path, entry: Dict[str, Any]) -> Dict[str, Any]:
    item = {
        "id": entry["id"],
        "kind": entry["kind"],
        "event": entry["event"],
        "title": entry.get("site_title") or entry["title"],
        "date": entry["date"],
        "duration": entry.get("duration", ""),
        "links": dict(entry.get("links", {})),
    }
    asset = entry.get("asset")
    if asset:
        rel = relative_asset_link(root_dir, asset)
        if entry["kind"] == "talk":
            item["links"].setdefault("slides", rel)
        else:
            item["links"].setdefault("poster", rel)
    return item


def render_site_block(talks: List[Dict[str, Any]], posters: List[Dict[str, Any]]) -> str:
    lines = [RESEARCH_MARKER_START, "## Conference Talks"]
    for talk in talks:
        prefix = f"- {talk['event']}"
        title = (talk.get("title") or "").strip()
        video = talk.get("links", {}).get("video", "")
        slides = talk.get("links", {}).get("slides", "")
        duration = str(talk.get("duration") or "").strip()

        if title:
            if video:
                line = f"{prefix}: [{title}]({video})"
            else:
                line = f"{prefix}: {title}"
        else:
            line = prefix

        if duration:
            line += f" ({duration})"
        if slides:
            line += f" / [slides]({slides})"
        lines.append(line)

    lines.append("")
    lines.append("## Conference Posters")
    for poster in posters:
        prefix = f"- {poster['event']}: {poster['title']}"
        poster_link = poster.get("links", {}).get("poster", "")
        if poster_link:
            prefix += f" / [poster]({poster_link})"
        lines.append(prefix)
    lines.append(RESEARCH_MARKER_END)
    return "\n".join(lines)


def replace_research_block(research_md: Path, new_block: str) -> None:
    content = research_md.read_text(encoding="utf-8")
    pattern = re.compile(
        rf"{re.escape(RESEARCH_MARKER_START)}.*?{re.escape(RESEARCH_MARKER_END)}",
        re.DOTALL,
    )
    if pattern.search(content):
        updated = pattern.sub(new_block, content)
    elif LEGACY_INCLUDE in content:
        updated = content.replace(LEGACY_INCLUDE, new_block)
    else:
        raise RuntimeError("Could not find presentations block or legacy include in research.md")
    research_md.write_text(updated, encoding="utf-8")


def render_cv_block(entries: List[Dict[str, Any]]) -> str:
    talks = [entry for entry in entries if entry.get("include_in_cv") and entry["kind"] == "talk"]
    posters = [entry for entry in entries if entry.get("include_in_cv") and entry["kind"] == "poster"]

    lines = [r"\begin{rSection}{Presentations}", "", r"\textbf{Talks:}", ""]
    for talk in talks:
        lines.append(
            rf"\textbf{{LeMaitre, Philip A.}}. “{talk['cv_title']}”. \\"
        )
        lines.append(
            rf"{talk['cv_event_line']} \hfill\textit{{{{{talk['cv_date_text']}}}}}"
        )
        lines.append("")

    lines.append(r"\textbf{Posters:}")
    lines.append("")
    for poster in posters:
        lines.append(
            rf"\textbf{{LeMaitre, Philip A.}}. “{poster['cv_title']}”. \\"
        )
        lines.append(
            rf"{poster['cv_event_line']} \hfill\textit{{{{{poster['cv_date_text']}}}}}"
        )
        lines.append("")

    lines.append(r"\end{rSection}")
    return "\n".join(lines)


def sort_items(items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    def key(item: Dict[str, Any]) -> Tuple[int, str]:
        order = item.get("site_order")
        if order is not None:
            return (int(order), "")
        return (10_000, "-" + (item.get("date") or "0000-00-00"))

    return sorted(items, key=key)


def main() -> int:
    root_dir = Path(__file__).resolve().parent.parent
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--source",
        default=str(root_dir / "_data" / "presentations_source.yml"),
    )
    parser.add_argument(
        "--out-talks",
        default=str(root_dir / "_data" / "talks.yml"),
    )
    parser.add_argument(
        "--out-posters",
        default=str(root_dir / "_data" / "posters.yml"),
    )
    parser.add_argument(
        "--research-md",
        default=str(root_dir / "research.md"),
    )
    parser.add_argument(
        "--cv-tex",
        default=str(root_dir / "assets" / "files" / "CV" / "auto_presentations.tex"),
    )
    parser.add_argument(
        "--check-online",
        action="store_true",
        help="Validate configured external links such as YouTube or listing pages.",
    )
    args = parser.parse_args()

    source = load_yaml(Path(args.source))
    entries = source.get("entries", [])
    if not isinstance(entries, list):
        raise RuntimeError("presentations_source.yml must contain an 'entries' list")

    validate_entries(root_dir, entries, check_online=args.check_online)

    site_talks = sort_items([build_site_item(root_dir, entry) | {"site_order": entry.get("site_order")} for entry in entries if entry.get("include_in_site") and entry["kind"] == "talk"])
    site_posters = sort_items([build_site_item(root_dir, entry) | {"site_order": entry.get("site_order")} for entry in entries if entry.get("include_in_site") and entry["kind"] == "poster"])

    save_yaml(Path(args.out_talks), site_talks)
    save_yaml(Path(args.out_posters), site_posters)
    replace_research_block(Path(args.research_md), render_site_block(site_talks, site_posters))

    cv_entries = sorted(entries, key=lambda item: item.get("date") or "0000-00-00", reverse=True)
    Path(args.cv_tex).write_text(render_cv_block(cv_entries), encoding="utf-8")

    print(
        f"Updated {args.out_talks}, {args.out_posters}, {args.research_md}, and {args.cv_tex}."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
