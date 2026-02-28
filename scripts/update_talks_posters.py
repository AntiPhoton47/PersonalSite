#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import os
import re
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import requests
import yaml
from pypdf import PdfReader

DOI_RE = re.compile(r"\b10\.\d{4,9}/[-._;()/:A-Z0-9]+\b", re.I)
ARXIV_RE = re.compile(r"\b(?:arXiv:)?\s*([0-9]{4}\.[0-9]{4,5})(v\d+)?\b", re.I)

OPENALEX_API = "https://api.openalex.org/works"
ARXIV_API = "https://export.arxiv.org/api/query"


def norm(s: str) -> str:
    return re.sub(r"\s+", " ", (s or "").strip())


def stable_id_from_path(path: Path) -> str:
    stem = path.stem
    h = hashlib.sha1(stem.encode("utf-8")).hexdigest()[:8]
    return f"{stem}_{h}"


def parse_filename(stem: str) -> Dict[str, str]:
    """
    Expected: YYYY-MM-DD_title_event (event optional)
    """
    out: Dict[str, str] = {}
    m = re.match(r"(?P<date>\d{4}-\d{2}-\d{2})_(?P<rest>.+)", stem)
    if m:
        out["date"] = m.group("date")
        rest = m.group("rest")
        parts = rest.split("_")
        if len(parts) >= 2:
            out["event_guess"] = parts[-1].replace("-", " ")
            out["slug_title"] = "_".join(parts[:-1])
        else:
            out["slug_title"] = rest
    else:
        out["slug_title"] = stem
    return out


def guess_title_from_slug(slug: str) -> str:
    return slug.replace("-", " ").replace("_", " ").strip().title()


def safe_get(url: str, headers: Optional[Dict[str, str]] = None, params: Optional[Dict[str, str]] = None) -> Optional[requests.Response]:
    try:
        r = requests.get(url, headers=headers or {}, params=params or {}, timeout=25, allow_redirects=True)
        if r.status_code >= 400:
            return None
        return r
    except Exception:
        return None


def pdf_extract(path: Path) -> Dict[str, Any]:
    reader = PdfReader(str(path))
    meta = reader.metadata or {}

    def mget(k: str) -> str:
        v = meta.get(k)
        return v.strip() if isinstance(v, str) else ""

    title = mget("/Title")
    author = mget("/Author")
    subject = mget("/Subject")
    creation = mget("/CreationDate")

    first_page_text = ""
    try:
        first_page_text = (reader.pages[0].extract_text() or "").strip()
    except Exception:
        pass

    doi = None
    arxiv = None
    if first_page_text:
        md = DOI_RE.search(first_page_text)
        if md:
            doi = md.group(0)
        ma = ARXIV_RE.search(first_page_text)
        if ma:
            arxiv = ma.group(1)

    created_iso = None
    if creation.startswith("D:"):
        raw = creation[2:]
        try:
            created_iso = datetime.strptime(raw[:14], "%Y%m%d%H%M%S").date().isoformat()
        except Exception:
            pass

    return {
        "pdf_title": title,
        "pdf_author": author,
        "pdf_subject": subject,
        "first_page": first_page_text,
        "doi": doi,
        "arxiv": arxiv,
        "created": created_iso,
    }


def load_yaml_list(path: Path) -> List[Dict[str, Any]]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8") as f:
        data = yaml.safe_load(f) or []
        return data if isinstance(data, list) else []


def save_yaml_list(path: Path, items: List[Dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        yaml.safe_dump(items, f, sort_keys=False, allow_unicode=True)


def load_sidecar_override(pdf_path: Path) -> Dict[str, Any]:
    """
    Optional per-file override: same name as pdf but .yml
    Example: assets/media/talks/foo.pdf -> assets/media/talks/foo.yml
    """
    yml = pdf_path.with_suffix(".yml")
    if not yml.exists():
        return {}
    with yml.open("r", encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}
        return data if isinstance(data, dict) else {}


def merge_preserve(existing: Dict[str, Any], incoming: Dict[str, Any]) -> Dict[str, Any]:
    """
    Preserve existing non-empty fields; fill missing from incoming.
    For dicts like links: merge keys.
    """
    out = dict(existing)

    for k, v in incoming.items():
        if k == "links" and isinstance(v, dict):
            out.setdefault("links", {})
            for lk, lv in v.items():
                if lk not in out["links"] or not out["links"][lk]:
                    out["links"][lk] = lv
            continue

        if k not in out or out[k] in ("", None, [], {}):
            out[k] = v

    return out


# -----------------------
# Enrichment sources
# -----------------------

def enrich_from_doi(doi: str) -> Dict[str, Any]:
    r = safe_get(
        f"https://doi.org/{doi}",
        headers={"Accept": "application/vnd.citationstyles.csl+json"},
    )
    if not r:
        return {}
    try:
        data = r.json()
    except Exception:
        return {}

    title = ""
    t = data.get("title")
    if isinstance(t, str):
        title = t
    elif isinstance(t, list) and t:
        title = t[0]

    authors = []
    for a in data.get("author", []) or []:
        given = a.get("given", "")
        family = a.get("family", "")
        name = norm(" ".join([given, family]))
        if name:
            authors.append(name)

    issued = data.get("issued", {}).get("date-parts", [])
    date_iso = ""
    if issued and isinstance(issued, list) and issued[0]:
        parts = issued[0]
        if len(parts) >= 3:
            date_iso = f"{parts[0]:04d}-{parts[1]:02d}-{parts[2]:02d}"
        elif len(parts) == 2:
            date_iso = f"{parts[0]:04d}-{parts[1]:02d}-01"
        elif len(parts) == 1:
            date_iso = f"{parts[0]:04d}-01-01"

    venue = data.get("container-title", "")
    url = data.get("URL") or f"https://doi.org/{doi}"

    out: Dict[str, Any] = {"links": {"doi": url}, "doi": doi}
    if title:
        out["title"] = title
    if authors:
        out["authors"] = authors
    if venue:
        out["venue"] = venue
    if date_iso:
        out["date"] = date_iso
    return out


def enrich_from_arxiv(arxiv_id: str) -> Dict[str, Any]:
    r = safe_get(ARXIV_API, params={"search_query": f"id:{arxiv_id}", "start": "0", "max_results": "1"})
    if not r:
        return {}
    txt = r.text

    titles = re.findall(r"<title[^>]*>(.*?)</title>", txt, re.S)
    title = norm(re.sub(r"<.*?>", "", titles[1])) if len(titles) >= 2 else ""

    authors = []
    for m in re.finditer(r"<author>\s*<name>(.*?)</name>\s*</author>", txt, re.S):
        nm = norm(re.sub(r"<.*?>", "", m.group(1)))
        if nm:
            authors.append(nm)

    published = ""
    m = re.search(r"<published>(.*?)</published>", txt, re.S)
    if m:
        published = norm(re.sub(r"<.*?>", "", m.group(1)))
    date_iso = published[:10] if published else ""

    out: Dict[str, Any] = {"links": {"arxiv": f"https://arxiv.org/abs/{arxiv_id}"}, "arxiv": arxiv_id}
    if title:
        out["title"] = title
    if authors:
        out["authors"] = authors
    if date_iso:
        out["date"] = date_iso
    return out


def title_similarity(a: str, b: str) -> float:
    A = {t for t in re.findall(r"[a-z0-9]+", (a or "").lower()) if len(t) > 2}
    B = {t for t in re.findall(r"[a-z0-9]+", (b or "").lower()) if len(t) > 2}
    if not A or not B:
        return 0.0
    return len(A & B) / len(A | B)


def enrich_from_openalex(title: str, author_hint: Optional[str] = None) -> Dict[str, Any]:
    if not title or len(title) < 8:
        return {}

    r = safe_get(OPENALEX_API, params={"search": title, "per-page": "5"})
    if not r:
        return {}
    try:
        data = r.json()
    except Exception:
        return {}

    best_score, best = 0.0, None
    for w in (data.get("results") or [])[:5]:
        wt = w.get("title") or ""
        score = title_similarity(title, wt)
        if author_hint:
            auths = " ".join([a.get("author", {}).get("display_name", "") for a in (w.get("authorships") or [])])
            if author_hint.lower() in auths.lower():
                score += 0.05
        if score > best_score:
            best_score, best = score, w

    if not best or best_score < 0.60:
        return {}

    out: Dict[str, Any] = {"links": {}}
    if best.get("title"):
        out["title"] = best["title"]
    if best.get("publication_date"):
        out["date"] = best["publication_date"]
    authors = [a.get("author", {}).get("display_name", "") for a in (best.get("authorships") or [])]
    authors = [a for a in authors if a]
    if authors:
        out["authors"] = authors

    doi = best.get("doi")
    if doi and doi.lower().startswith("https://doi.org/"):
        doi = doi.replace("https://doi.org/", "")
    if doi:
        out["doi"] = doi
        out["links"]["doi"] = f"https://doi.org/{doi}"

    out["links"]["openalex"] = best.get("id", "")
    return out


# -----------------------
# SerpAPI conference-page search enrichment
# -----------------------

def serpapi_search(query: str, api_key: str, num: int = 5) -> List[Dict[str, str]]:
    url = "https://serpapi.com/search.json"
    params = {
        "engine": "google",
        "q": query,
        "api_key": api_key,
        "num": str(num),
    }
    r = safe_get(url, params=params)
    if not r:
        return []
    try:
        data = r.json()
    except Exception:
        return []

    out = []
    for item in (data.get("organic_results") or [])[:num]:
        out.append({
            "title": item.get("title", "") or "",
            "link": item.get("link", "") or "",
            "snippet": item.get("snippet", "") or "",
        })
    return out


def fetch_page_text(url: str) -> str:
    r = safe_get(url, headers={"User-Agent": "Mozilla/5.0"})
    if not r:
        return ""
    html = r.text

    # Prefer og:description (often the abstract/summary)
    og_desc = re.search(r'<meta[^>]+property=["\']og:description["\'][^>]+content=["\'](.*?)["\']', html, re.I)
    if og_desc:
        return norm(og_desc.group(1))

    # Otherwise strip to text (crude but dependency-free)
    html = re.sub(r"(?is)<(script|style).*?>.*?</\1>", " ", html)
    text = re.sub(r"(?s)<.*?>", " ", html)
    return norm(text)


def validate_candidate(entry: Dict[str, Any], candidate: Dict[str, str], your_name: str) -> float:
    title = entry.get("title", "")
    event = entry.get("event", "")
    cand_title = candidate.get("title", "")
    cand_snip = candidate.get("snippet", "")
    blob = f"{cand_title} {cand_snip}".lower()

    score = title_similarity(title, cand_title)

    surname = (your_name.split()[-1] if your_name else "").lower()
    if surname and surname in blob:
        score += 0.15

    # event boost if any meaningful overlap
    if event:
        ev_tokens = [t for t in re.findall(r"[a-z0-9]+", event.lower()) if len(t) > 3]
        if any(t in blob for t in ev_tokens[:4]):
            score += 0.10

    # slight penalty for common aggregators (not conference pages)
    link = (candidate.get("link") or "").lower()
    if any(x in link for x in ["scholar.google", "researchgate", "semanticscholar", "dblp.org"]):
        score -= 0.10

    return score


def enrich_from_conference_web(entry: Dict[str, Any], your_name: str, api_key: str) -> Dict[str, Any]:
    title = entry.get("title", "")
    event = entry.get("event", "")
    if not title or not your_name:
        return {}

    query_parts = [f"\"{title}\"", f"\"{your_name}\""]
    if event:
        query_parts.append(f"\"{event}\"")
    query = " ".join(query_parts)

    results = serpapi_search(query, api_key=api_key, num=5)
    if not results:
        return {}

    scored = [(validate_candidate(entry, c, your_name), c) for c in results if c.get("link")]
    scored.sort(key=lambda x: x[0], reverse=True)

    if not scored or scored[0][0] < 0.70:
        return {}

    best = scored[0][1]
    url = best["link"]
    text = fetch_page_text(url)
    if not text:
        return {"links": {"listing": url}}

    # Abstract heuristic: try to find region near the title; else first chunk
    abstract = ""
    low = text.lower()
    t_low = title.lower()
    anchor = t_low[: min(40, len(t_low))]
    pos = low.find(anchor)
    if pos != -1:
        abstract = text[pos: pos + 900]
    else:
        abstract = text[:900]

    abstract = abstract.strip()
    if abstract:
        abstract = abstract[:500].rsplit(" ", 1)[0] + "…"

    out: Dict[str, Any] = {"links": {"listing": url}}
    if abstract and not entry.get("abstract"):
        out["abstract"] = abstract
    return out


# -----------------------
# Entry build + enrich
# -----------------------

def build_base_entry(kind: str, pdf_path: Path, baseurl: str) -> Dict[str, Any]:
    fid = stable_id_from_path(pdf_path)

    fn = parse_filename(pdf_path.stem)
    pdf = pdf_extract(pdf_path)
    sidecar = load_sidecar_override(pdf_path)

    date = sidecar.get("date") or fn.get("date") or pdf.get("created") or ""
    title = sidecar.get("title") or pdf.get("pdf_title") or guess_title_from_slug(fn.get("slug_title", pdf_path.stem))
    event = sidecar.get("event") or fn.get("event_guess") or ""

    doi = sidecar.get("doi") or pdf.get("doi")
    arxiv = sidecar.get("arxiv") or pdf.get("arxiv")

    # Link building
    pdf_link = f"/{pdf_path.as_posix()}"
    if baseurl:
        pdf_link = f"{baseurl.rstrip('/')}/{pdf_path.as_posix()}"

    entry: Dict[str, Any] = {
        "id": fid,
        "type": kind,  # talk/poster
        "title": title,
        "event": event,
        "date": date,
        "duration": sidecar.get("duration", ""),
        "kind": sidecar.get("kind", "Talk" if kind == "talk" else "Poster"),
        "location": sidecar.get("location", ""),
        "authors": sidecar.get("authors", []),
        "tags": sidecar.get("tags", []),
        "links": {"pdf": pdf_link},
        "abstract": sidecar.get("abstract", ""),
    }

    if doi:
        entry["doi"] = doi
        entry["links"].setdefault("doi", f"https://doi.org/{doi}")

    if arxiv:
        entry["arxiv"] = arxiv
        entry["links"].setdefault("arxiv", f"https://arxiv.org/abs/{arxiv}")

    # Bring in extra links from sidecar (slides/video etc.)
    if "links" in sidecar and isinstance(sidecar["links"], dict):
        entry["links"].update(sidecar["links"])

    return entry


def enrich_entry(entry: Dict[str, Any], your_name: str, serpapi_key: Optional[str]) -> Dict[str, Any]:
    enriched: Dict[str, Any] = {}

    doi = entry.get("doi")
    arxiv = entry.get("arxiv")

    if doi:
        enriched = merge_preserve(enriched, enrich_from_doi(doi))

    if arxiv and (not enriched.get("title") or not enriched.get("authors") or not enriched.get("date")):
        enriched = merge_preserve(enriched, enrich_from_arxiv(arxiv))

    if not doi and not arxiv:
        if (not entry.get("authors")) or (not entry.get("date")):
            hint = None
            if entry.get("authors"):
                hint = entry["authors"][0].split()[-1]
            enriched = merge_preserve(enriched, enrich_from_openalex(entry.get("title", ""), author_hint=hint))

    # Final fallback: conference listing/abstract page search
    if serpapi_key and your_name:
        if (not entry.get("abstract")) or (not entry.get("links", {}).get("listing")):
            enriched = merge_preserve(enriched, enrich_from_conference_web(entry, your_name=your_name, api_key=serpapi_key))

    return merge_preserve(entry, enriched)


def upsert_by_id(items: List[Dict[str, Any]], new_item: Dict[str, Any]) -> List[Dict[str, Any]]:
    idx = next((i for i, x in enumerate(items) if x.get("id") == new_item.get("id")), None)
    if idx is None:
        items.append(new_item)
    else:
        items[idx] = merge_preserve(items[idx], new_item)
    return items


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--talks_dir", default="assets/media/talks")
    ap.add_argument("--posters_dir", default="assets/media/posters")
    ap.add_argument("--out_talks", default="_data/talks.yml")
    ap.add_argument("--out_posters", default="_data/posters.yml")
    ap.add_argument("--baseurl", default="")  # "" for custom domain; "/PersonalSite" for project sites
    ap.add_argument("--enrich", action="store_true")
    ap.add_argument("--your_name", default=os.getenv("AUTHOR_NAME", ""))
    ap.add_argument("--serpapi_key", default=os.getenv("SERPAPI_KEY", ""))
    args = ap.parse_args()

    talks = load_yaml_list(Path(args.out_talks))
    posters = load_yaml_list(Path(args.out_posters))

    for p in sorted(Path(args.talks_dir).glob("*.pdf")):
        e = build_base_entry("talk", p, args.baseurl)
        if args.enrich:
            e = enrich_entry(e, your_name=args.your_name, serpapi_key=(args.serpapi_key or None))
        talks = upsert_by_id(talks, e)

    for p in sorted(Path(args.posters_dir).glob("*.pdf")):
        e = build_base_entry("poster", p, args.baseurl)
        if args.enrich:
            e = enrich_entry(e, your_name=args.your_name, serpapi_key=(args.serpapi_key or None))
        posters = upsert_by_id(posters, e)

    def sort_key(x: Dict[str, Any]) -> str:
        return x.get("date") or "0000-00-00"

    talks = sorted(talks, key=sort_key, reverse=True)
    posters = sorted(posters, key=sort_key, reverse=True)

    save_yaml_list(Path(args.out_talks), talks)
    save_yaml_list(Path(args.out_posters), posters)

    print(f"Updated {args.out_talks} ({len(talks)} items) and {args.out_posters} ({len(posters)} items).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
