#!/usr/bin/env python3
from __future__ import annotations

import argparse
import os
import re
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Tuple
from zipfile import ZipFile

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


def slugify(text: str) -> str:
    text = re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")
    return text or "presentation"


def normalize_text(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def format_cv_date_text(date_str: str) -> str:
    try:
        dt = datetime.strptime(date_str, "%Y-%m-%d")
    except ValueError:
        return date_str
    return dt.strftime("%b. %Y")


def date_from_asset_name(asset_rel: str) -> str:
    match = re.match(r"(\d{4}-\d{2}-\d{2})_", Path(asset_rel).name)
    return match.group(1) if match else ""


def sort_slide_names(names: List[str]) -> List[str]:
    def key(name: str) -> Tuple[int, str]:
        match = re.search(r"slide(\d+)\.xml$", name)
        return (int(match.group(1)) if match else 10_000, name)

    return sorted(names, key=key)


def extract_pptx_text_by_slide(path: Path) -> List[List[str]]:
    slides: List[List[str]] = []
    with ZipFile(path) as archive:
        slide_names = sort_slide_names(
            [name for name in archive.namelist() if name.startswith("ppt/slides/slide") and name.endswith(".xml")]
        )
        for slide_name in slide_names:
            xml = archive.read(slide_name).decode("utf-8", "ignore")
            texts = [normalize_text(text) for text in re.findall(r"<a:t>(.*?)</a:t>", xml) if normalize_text(text)]
            slides.append(texts)
    return slides


def infer_title_from_slides(slides: List[List[str]]) -> str:
    if not slides:
        return ""
    first_slide = slides[0]
    for text in first_slide:
        lower = text.lower()
        if re.search(r"\b(january|february|march|april|may|june|july|august|september|october|november|december)\b", lower):
            continue
        if "philip" in lower or "lemaitre" in lower:
            continue
        if "phys. rev." in lower:
            continue
        if len(text) >= 8:
            return text
    return first_slide[0] if first_slide else ""


def infer_event_line_from_slides(slides: List[List[str]]) -> str:
    keywords = ("conference", "workshop", "meeting", "seminar", "congress", "symposium", "school")
    for slide in slides[:12]:
        for text in slide[:8]:
            lower = text.lower()
            if not any(keyword in lower for keyword in keywords):
                continue
            candidate = text
            if " I " in candidate:
                candidate = candidate.split(" I ")[0]
            if " | " in candidate:
                candidate = candidate.split(" | ")[0]
            return normalize_text(candidate)
    return ""


def infer_title_from_filename(asset_rel: str) -> str:
    stem = Path(asset_rel).stem
    stem = re.sub(r"^\d{4}-\d{2}-\d{2}_", "", stem)
    return normalize_text(stem.replace("_", " "))


def auto_entry_from_asset(root_dir: Path, kind: str, asset_rel: str) -> Dict[str, Any]:
    path = root_dir / asset_rel
    date = date_from_asset_name(asset_rel)
    title = ""
    event_line = ""

    if path.suffix.lower() == ".pptx":
        try:
            slides = extract_pptx_text_by_slide(path)
        except Exception:
            slides = []
        title = infer_title_from_slides(slides)
        event_line = infer_event_line_from_slides(slides)

    if not title:
        title = infer_title_from_filename(asset_rel)

    event = event_line.split(",", 1)[0].strip() if event_line else ""
    include_in_site = bool(title and event)
    include_in_cv = bool(title and event_line and date)

    return {
        "id": f"{kind}-{slugify(Path(asset_rel).stem)}",
        "kind": kind,
        "asset": asset_rel,
        "include_in_site": include_in_site,
        "include_in_cv": include_in_cv,
        "title": title,
        "site_title": title if include_in_site else "",
        "cv_title": title if include_in_cv else "",
        "event": event,
        "cv_event_line": event_line,
        "date": date,
        "cv_date_text": format_cv_date_text(date) if include_in_cv else "",
        "site_order": 0 if include_in_site else None,
        "duration": "",
        "links": {},
        "auto_generated": True,
        "needs_review": True,
    }


def merge_discovered_assets(root_dir: Path, entries: List[Dict[str, Any]]) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    asset_inventory = {
        "talk": scan_assets(root_dir, "assets/files/talks"),
        "poster": scan_assets(root_dir, "assets/files/posters"),
    }
    existing_assets = {entry.get("asset"): entry for entry in entries if entry.get("asset")}
    merged = list(entries)
    discovered: List[Dict[str, Any]] = []

    for kind, assets in asset_inventory.items():
        for asset_rel in assets:
            if asset_rel in existing_assets:
                continue
            entry = auto_entry_from_asset(root_dir, kind, asset_rel)
            merged.append(entry)
            discovered.append(entry)

    for entry in merged:
        if entry.get("auto_generated") and entry.get("include_in_site") and entry.get("site_order") is None:
            entry["site_order"] = 0

    return merged, discovered


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


def build_site_item(root_dir: Path, entry: Dict[str, Any]) -> Dict[str, Any]:
    item = {
        "id": entry["id"],
        "kind": entry["kind"],
        "event": entry["event"],
        "title": entry.get("site_title") or entry["title"],
        "date": entry["date"],
        "duration": entry.get("duration", ""),
        "invited": bool(entry.get("invited")),
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
        if talk.get("invited"):
            prefix += " (invited talk)"
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
        event_line = talk["cv_event_line"]
        if talk.get("invited"):
            event_line = f"Invited talk, {event_line}"
        lines.append(
            rf"{event_line} \hfill\textit{{{{{talk['cv_date_text']}}}}}"
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
    def key(item: Dict[str, Any]) -> Tuple[int, int, str]:
        order = item.get("site_order")
        if order is not None:
            return (0, int(order), "")
        date = item.get("date") or "0000-00-00"
        try:
            ordinal = datetime.strptime(date, "%Y-%m-%d").toordinal()
        except ValueError:
            ordinal = 0
        return (1, -ordinal, item.get("title") or "")

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

    entries, discovered = merge_discovered_assets(root_dir, entries)
    save_yaml(Path(args.source), {"entries": entries})

    validate_entries(root_dir, entries, check_online=args.check_online)

    site_talks = sort_items([build_site_item(root_dir, entry) | {"site_order": entry.get("site_order")} for entry in entries if entry.get("include_in_site") and entry["kind"] == "talk"])
    site_posters = sort_items([build_site_item(root_dir, entry) | {"site_order": entry.get("site_order")} for entry in entries if entry.get("include_in_site") and entry["kind"] == "poster"])

    save_yaml(Path(args.out_talks), site_talks)
    save_yaml(Path(args.out_posters), site_posters)
    replace_research_block(Path(args.research_md), render_site_block(site_talks, site_posters))

    cv_entries = sorted(entries, key=lambda item: item.get("date") or "0000-00-00", reverse=True)
    Path(args.cv_tex).write_text(render_cv_block(cv_entries), encoding="utf-8")

    if discovered:
        discovered_assets = ", ".join(entry["asset"] for entry in discovered)
        print(f"Discovered new presentation assets: {discovered_assets}")
    print(f"Updated {args.source}, {args.out_talks}, {args.out_posters}, {args.research_md}, and {args.cv_tex}.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
