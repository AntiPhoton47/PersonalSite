#!/usr/bin/env python3
"""
Update publication metadata from ORCID and DOI records.

- Source of truth: ORCID works list
- Prefer DOI -> BibTeX via content negotiation
- Fallback: build BibTeX from ORCID metadata
- Preserve manual CV-specific override fields across updates
"""

from __future__ import annotations

import argparse
import json
import os
import re
import xml.etree.ElementTree as ET
from typing import Any, Dict, List, Optional, Tuple

import requests
import bibtexparser
from bibtexparser.bwriter import BibTexWriter
from bibtexparser.bibdatabase import BibDatabase
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

ORCID_API = "https://pub.orcid.org/v3.0"
ARXIV_API = "https://export.arxiv.org/api/query"
DEFAULT_TIMEOUT = 30
MANUAL_FIELDS = {
    "cv_order",
    "cv_title",
    "cv_url",
    "cv_journal",
    "cv_include_issue",
}

DOI_RE = re.compile(r"10\.\d{4,9}/[-._;()/:A-Z0-9]+", re.I)
ARXIV_ID_RE = re.compile(r"(?:abs/)?([^/]+?)(?:v\d+)?$")
ARXIV_NS = {
    "atom": "http://www.w3.org/2005/Atom",
    "arxiv": "http://arxiv.org/schemas/atom",
}
DEFAULT_ARXIV_AUTHOR_QUERIES = [
    "LeMaitre, Philip A",
    "LeMaitre, Philip",
    "LeMaitre, Phil A",
    "LeMaitre, Phil",
]

def norm(s: str) -> str:
    return re.sub(r"\s+", " ", (s or "")).strip()

def slug_key(title: str, year: str) -> str:
    t = re.sub(r"[^a-z0-9]+", "-", title.lower()).strip("-")
    return f"{t}-{year}" if year else t


def parse_person_name(name: str) -> Tuple[str, str]:
    cleaned = re.sub(r"[.,]", " ", name or "")
    parts = [part for part in cleaned.split() if part]
    if not parts:
        return "", ""
    return parts[0].lower(), parts[-1].lower()


def matches_target_author(name: str) -> bool:
    given, family = parse_person_name(name)
    return family == "lemaitre" and given.startswith("phil")


def make_session() -> requests.Session:
    session = requests.Session()
    retries = Retry(
        total=5,
        connect=5,
        read=5,
        status=5,
        backoff_factor=1,
        status_forcelist=(429, 500, 502, 503, 504),
        allowed_methods=("GET", "POST"),
        raise_on_status=False,
    )
    adapter = HTTPAdapter(max_retries=retries)
    session.mount("https://", adapter)
    session.mount("http://", adapter)
    session.headers.update(
        {
            "User-Agent": "PersonalSite publications updater/1.0",
        }
    )
    return session


def get_orcid_works(orcid_id: str, session: requests.Session, token: Optional[str] = None):
    url = f"{ORCID_API}/{orcid_id}/works"
    headers = {"Accept": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    r = session.get(url, headers=headers, timeout=DEFAULT_TIMEOUT)
    r.raise_for_status()
    data = r.json()
    groups = data.get("group", [])
    items: List[Dict[str, Any]] = []
    for g in groups:
        summaries = g.get("work-summary", [])
        for s in summaries:
            items.append(s)
    return items

def get_orcid_token(client_id: str, client_secret: str, session: requests.Session) -> str:
    token_url = "https://orcid.org/oauth/token"
    data = {
        "grant_type": "client_credentials",
        "scope": "/read-public"
    }
    r = session.post(token_url, auth=(client_id, client_secret), data=data, timeout=DEFAULT_TIMEOUT)

    if r.status_code != 200:
        raise RuntimeError(f"Failed to obtain ORCID token: {r.text}")

    token = r.json().get("access_token")
    if not token:
        raise RuntimeError("No access token returned by ORCID")

    return token

def extract_doi(work: Dict[str, Any]) -> Optional[str]:
    ext_ids = work.get("external-ids", {}).get("external-id", [])
    # ORCID external IDs can include DOI, arXiv, etc.
    for eid in ext_ids:
        t = (eid.get("external-id-type") or "").lower()
        val = eid.get("external-id-value")
        if t == "doi" and val:
            return val.strip()
    # fallback scan
    s = json.dumps(work)
    m = DOI_RE.search(s)
    return m.group(0) if m else None

def extract_arxiv(work: Dict[str, Any]) -> Optional[str]:
    ext_ids = work.get("external-ids", {}).get("external-id", [])
    for eid in ext_ids:
        t = (eid.get("external-id-type") or "").lower()
        val = eid.get("external-id-value")
        if t in ("arxiv", "arxiv-id") and val:
            return val.strip()
    return None


def normalize_arxiv_id(value: str) -> str:
    text = norm(value)
    if not text:
        return ""
    match = ARXIV_ID_RE.search(text)
    return match.group(1).lower() if match else text.lower()


def get_arxiv_entries(
    session: requests.Session,
    author_queries: List[str],
    max_results: int,
) -> List[Dict[str, str]]:
    seen_ids = set()
    collected: List[Dict[str, str]] = []

    for author_query in author_queries:
        params = {
            "search_query": f'au:"{author_query}"',
            "start": 0,
            "max_results": max_results,
            "sortBy": "submittedDate",
            "sortOrder": "descending",
        }
        response = session.get(ARXIV_API, params=params, timeout=DEFAULT_TIMEOUT)
        response.raise_for_status()
        root = ET.fromstring(response.text)

        for entry in root.findall("atom:entry", ARXIV_NS):
            authors = [
                author.findtext("atom:name", default="", namespaces=ARXIV_NS).strip()
                for author in entry.findall("atom:author", ARXIV_NS)
            ]
            if not any(matches_target_author(author) for author in authors):
                continue

            raw_id = entry.findtext("atom:id", default="", namespaces=ARXIV_NS).strip()
            arxiv_id = normalize_arxiv_id(raw_id)
            if not arxiv_id or arxiv_id in seen_ids:
                continue

            seen_ids.add(arxiv_id)
            published = entry.findtext("atom:published", default="", namespaces=ARXIV_NS).strip()
            year = published[:4] if len(published) >= 4 else ""
            categories = [
                category.attrib.get("term", "").strip()
                for category in entry.findall("atom:category", ARXIV_NS)
                if category.attrib.get("term")
            ]
            collected.append(
                {
                    "ENTRYTYPE": "misc",
                    "ID": slug_key(
                        entry.findtext("atom:title", default="work", namespaces=ARXIV_NS).strip(),
                        year,
                    ),
                    "title": norm(entry.findtext("atom:title", default="", namespaces=ARXIV_NS)),
                    "author": " and ".join(authors),
                    "year": year,
                    "month": published[5:7] if len(published) >= 7 else "",
                    "eprint": arxiv_id,
                    "archiveprefix": "arXiv",
                    "primaryclass": categories[0] if categories else "",
                    "url": f"https://arxiv.org/abs/{arxiv_id}",
                    "doi": norm(entry.findtext("arxiv:doi", default="", namespaces=ARXIV_NS)),
                    "journal": norm(
                        entry.findtext("arxiv:journal_ref", default="", namespaces=ARXIV_NS)
                    ),
                }
            )

    return collected

def doi_to_bibtex(doi: str) -> Optional[str]:
    return doi_to_bibtex_with_session(doi, make_session())


def doi_to_bibtex_with_session(doi: str, session: requests.Session) -> Optional[str]:
    url = f"https://doi.org/{doi}"
    headers = {"Accept": "application/x-bibtex"}
    r = session.get(url, headers=headers, timeout=DEFAULT_TIMEOUT, allow_redirects=True)
    if r.status_code >= 400:
        return None
    txt = r.text.strip()
    if txt.startswith("@"):
        return txt
    return None

def orcid_work_to_min_bibtex(work: Dict[str, Any]) -> str:
    """Fallback BibTeX built from ORCID summary."""
    title = norm((work.get("title") or {}).get("title", {}).get("value", ""))
    year = ""
    pub_date = work.get("publication-date") or {}
    if pub_date.get("year", {}).get("value"):
        year = str(pub_date["year"]["value"])
    journal = norm((work.get("journal-title") or {}).get("value", ""))
    wtype = (work.get("type") or "").lower()

    doi = extract_doi(work)
    arx = extract_arxiv(work)

    # ORCID summary doesn't always include authors. You can fetch full work record if needed.
    # We'll keep author empty unless you later enrich via DOI BibTeX.
    key = slug_key(title or "work", year)

    fields = {
        "title": title,
        "year": year,
    }
    if journal:
        fields["journal"] = journal
    if doi:
        fields["doi"] = doi
        fields["url"] = f"https://doi.org/{doi}"
    if arx and "url" not in fields:
        fields["eprint"] = arx
        fields["archiveprefix"] = "arXiv"
        fields["url"] = f"https://arxiv.org/abs/{arx}"

    entry_type = "article" if wtype in ("journal-article", "article") else "misc"

    bib = f"@{entry_type}{{{key},\n"
    for k, v in fields.items():
        if v:
            bib += f"  {k} = {{{v}}},\n"
    bib += "}\n"
    return bib

def load_bib(path: str) -> BibDatabase:
    if not os.path.exists(path):
        db = BibDatabase()
        db.entries = []
        return db
    with open(path, "r", encoding="utf-8") as f:
        return bibtexparser.load(f)

def write_bib(db: BibDatabase, path: str) -> None:
    writer = BibTexWriter()
    writer.indent = "  "
    writer.order_entries_by = ("year", "ID")
    with open(path, "w", encoding="utf-8") as f:
        f.write(writer.write(db))

def entry_idents(e: Dict[str, str]) -> Tuple[str, str, str]:
    doi = (e.get("doi") or "").strip().lower()
    arx = normalize_arxiv_id(e.get("eprint") or "")
    title_source = e.get("cv_title") or e.get("title", "")
    title = re.sub(r"[^a-z0-9]+", " ", norm(title_source).lower()).strip()
    return doi, arx, title


def entry_rank(entry: Dict[str, str]) -> int:
    entry_type = (entry.get("ENTRYTYPE") or "").lower()
    has_journal = bool(entry.get("journal"))
    has_doi = bool(entry.get("doi"))
    rank = 0
    if entry_type == "article":
        rank += 4
    if has_journal:
        rank += 2
    if has_doi:
        rank += 1
    return rank


def canonical_entry_id(entry: Dict[str, str]) -> str:
    title = norm(entry.get("cv_title") or entry.get("title", "") or "work")
    year = norm(entry.get("year", ""))
    return slug_key(title, year) or "work"

def merge_entry(db: BibDatabase, new_entry: Dict[str, str]) -> None:
    new_entry["ID"] = canonical_entry_id(new_entry)
    new_doi, new_arx, new_title = entry_idents(new_entry)

    for i, e in enumerate(db.entries):
        doi, arx, title = entry_idents(e)
        if new_doi and doi and new_doi == doi:
            preserved = {field: e[field] for field in MANUAL_FIELDS if e.get(field)}
            db.entries[i] = {**e, **new_entry, **preserved}
            db.entries[i]["ID"] = e.get("ID") or canonical_entry_id(db.entries[i])
            return
        if new_arx and arx and new_arx == arx:
            preserved = {field: e[field] for field in MANUAL_FIELDS if e.get(field)}
            db.entries[i] = {**e, **new_entry, **preserved}
            db.entries[i]["ID"] = e.get("ID") or canonical_entry_id(db.entries[i])
            return
        if new_title and title and new_title == title and (e.get("year") == new_entry.get("year")):
            preserved = {field: e[field] for field in MANUAL_FIELDS if e.get(field)}
            db.entries[i] = {**e, **new_entry, **preserved}
            db.entries[i]["ID"] = e.get("ID") or canonical_entry_id(db.entries[i])
            return
        if new_title and title and new_title == title:
            preserved = {field: e[field] for field in MANUAL_FIELDS if e.get(field)}
            if entry_rank(new_entry) >= entry_rank(e):
                db.entries[i] = {**e, **new_entry, **preserved}
                db.entries[i]["ID"] = e.get("ID") or canonical_entry_id(db.entries[i])
            return

    db.entries.append(new_entry)

def parse_single_bib_entry(bib: str) -> Dict[str, str]:
    db = bibtexparser.loads(bib)
    if not db.entries:
        raise ValueError("No entries parsed from BibTeX")
    return db.entries[0]


def sync_bib_outputs(source_path: str, targets: List[str]) -> None:
    source_db = load_bib(source_path)
    for target in targets:
        write_bib(source_db, target)


def dedupe_entries(db: BibDatabase) -> None:
    best_by_title: Dict[str, Dict[str, str]] = {}
    ordered: List[Dict[str, str]] = []
    for entry in db.entries:
        _, _, title = entry_idents(entry)
        if not title:
            ordered.append(entry)
            continue
        current = best_by_title.get(title)
        if current is None:
            best_by_title[title] = entry
            ordered.append(entry)
            continue
        if entry_rank(entry) > entry_rank(current):
            idx = ordered.index(current)
            ordered[idx] = entry
            best_by_title[title] = entry
    seen_titles = set()
    deduped: List[Dict[str, str]] = []
    for entry in ordered:
        _, _, title = entry_idents(entry)
        if title and title in seen_titles:
            continue
        if title:
            seen_titles.add(title)
        entry["ID"] = canonical_entry_id(entry)
        deduped.append(entry)
    db.entries = deduped


def count_entries(db: BibDatabase) -> int:
    return len(db.entries)

def main() -> int:
    root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    client_id = os.getenv("ORCID_CLIENT_ID")
    client_secret = os.getenv("ORCID_CLIENT_SECRET")

    ap = argparse.ArgumentParser()
    ap.add_argument("--orcid", required=True, help="Your ORCID iD (e.g. 0000-0002-....)")
    ap.add_argument(
        "--bib",
        default=os.path.join(root_dir, "_bibliography", "publications.bib"),
        help="Primary path to publications.bib",
    )
    ap.add_argument(
        "--sync-bib",
        action="append",
        default=[],
        help="Additional BibTeX output path(s) to keep in sync",
    )
    ap.add_argument(
        "--cv-tex",
        default=os.path.join(root_dir, "assets", "files", "CV", "auto_publications.tex"),
        help="Optional output path for rendered CV publications TeX",
    )
    ap.add_argument(
        "--research-md",
        default=os.path.join(root_dir, "research.md"),
        help="Optional research.md file to refresh the Publication Codes section",
    )
    ap.add_argument(
        "--arxiv-author-query",
        action="append",
        default=[],
        help="arXiv author query variant(s), e.g. 'LeMaitre, Philip A'",
    )
    ap.add_argument(
        "--arxiv-max-results",
        type=int,
        default=10,
        help="Max results per arXiv author query",
    )
    args = ap.parse_args()

    session = make_session()
    token = None
    if client_id and client_secret:
        token = get_orcid_token(client_id, client_secret, session=session)

    works = get_orcid_works(args.orcid, session=session, token=token)
    db = load_bib(args.bib)
    before_count = count_entries(db)

    for w in works:
        doi = extract_doi(w)
        if doi:
            bib = doi_to_bibtex_with_session(doi, session=session)
            if bib:
                try:
                    ent = parse_single_bib_entry(bib)
                    ent.setdefault("url", f"https://doi.org/{doi}")
                    merge_entry(db, ent)
                    continue
                except Exception:
                    pass

        # fallback
        bib = orcid_work_to_min_bibtex(w)
        ent = parse_single_bib_entry(bib)
        merge_entry(db, ent)

    arxiv_queries = args.arxiv_author_query or DEFAULT_ARXIV_AUTHOR_QUERIES
    arxiv_entries = get_arxiv_entries(
        session=session,
        author_queries=arxiv_queries,
        max_results=args.arxiv_max_results,
    )
    for arxiv_entry in arxiv_entries:
        merge_entry(db, arxiv_entry)

    dedupe_entries(db)
    write_bib(db, args.bib)
    sync_targets = [
        target
        for target in args.sync_bib
        if os.path.abspath(target) != os.path.abspath(args.bib)
    ]
    if sync_targets:
        sync_bib_outputs(args.bib, sync_targets)
    if args.cv_tex:
        from render_cv import render_publications  # type: ignore

        render_publications(
            bib_path=args.bib,
            out_path=args.cv_tex,
            template_path="templates/cv_publications_section.tex.j2",
        )
    if args.research_md:
        from update_publication_codes import update_publication_codes  # type: ignore

        update_publication_codes(
            bib_path=args.bib,
            research_md_path=args.research_md,
            config_path=os.path.join(root_dir, "_data", "publication_codes.yml"),
        )
    print(
        f"Updated {args.bib} with {len(db.entries)} entries "
        f"(started with {before_count}, processed {len(works)} ORCID works, "
        f"considered {len(arxiv_entries)} arXiv entries)."
    )
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
