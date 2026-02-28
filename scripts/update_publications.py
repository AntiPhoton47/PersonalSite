#!/usr/bin/env python3
"""
Update publications.bib from ORCID (+ Crossref DOI content negotiation, optional arXiv).
- Source of truth: ORCID works list
- Prefer DOI->BibTeX via content negotiation
- Fallback: build BibTeX from ORCID metadata
"""

from __future__ import annotations

import argparse
import dataclasses
import json
import os
import re
import sys
import base64
from typing import Any, Dict, List, Optional, Tuple

import requests
import bibtexparser
from bibtexparser.bwriter import BibTexWriter
from bibtexparser.bibdatabase import BibDatabase

ORCID_API = "https://pub.orcid.org/v3.0"

DOI_RE = re.compile(r"10\.\d{4,9}/[-._;()/:A-Z0-9]+", re.I)

def norm(s: str) -> str:
    return re.sub(r"\s+", " ", (s or "")).strip()

def slug_key(title: str, year: str) -> str:
    t = re.sub(r"[^a-z0-9]+", "-", title.lower()).strip("-")
    return f"{t}-{year}" if year else t

def get_orcid_works(orcid_id: str, token: str):
    """
    Read public works from ORCID. If you have a public API token, include it.
    ORCID supports reading public data; for robust usage use tokens/credentials.  [oai_citation:4‡ORCID](https://info.orcid.org/documentation/api-tutorials/api-tutorial-read-data-on-a-record/?utm_source=chatgpt.com)
    """
    url = f"https://api.orcid.org/v3.0/{orcid_id}/works"
    headers = {
        "Accept": "application/json",
        "Authorization": f"Bearer {token}"
    }
    r = requests.get(url, headers=headers, timeout=30)
    r.raise_for_status()
    data = r.json()
    groups = data.get("group", [])
    items: List[Dict[str, Any]] = []
    for g in groups:
        summaries = g.get("work-summary", [])
        for s in summaries:
            items.append(s)
    return items

def get_orcid_token(client_id: str, client_secret: str) -> str:
    token_url = "https://orcid.org/oauth/token"

    auth = (client_id, client_secret)

    data = {
        "grant_type": "client_credentials",
        "scope": "/read-public"
    }

    r = requests.post(token_url, auth=auth, data=data)

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

def doi_to_bibtex(doi: str) -> Optional[str]:
    """
    Use DOI content negotiation to get BibTeX. Crossref supports content negotiation with Accept header.  [oai_citation:5‡www.crossref.org](https://www.crossref.org/documentation/retrieve-metadata/content-negotiation/?utm_source=chatgpt.com)
    """
    url = f"https://doi.org/{doi}"
    headers = {"Accept": "application/x-bibtex"}  # content negotiation
    r = requests.get(url, headers=headers, timeout=30, allow_redirects=True)
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
        fields["archivePrefix"] = "arXiv"
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
    arx = (e.get("eprint") or "").strip().lower()
    title = norm(e.get("title", "")).lower()
    return doi, arx, title

def merge_entry(db: BibDatabase, new_entry: Dict[str, str]) -> None:
    new_doi, new_arx, new_title = entry_idents(new_entry)

    for i, e in enumerate(db.entries):
        doi, arx, title = entry_idents(e)
        if new_doi and doi and new_doi == doi:
            db.entries[i] = {**e, **new_entry}
            return
        if new_arx and arx and new_arx == arx:
            db.entries[i] = {**e, **new_entry}
            return
        if new_title and title and new_title == title and (e.get("year") == new_entry.get("year")):
            db.entries[i] = {**e, **new_entry}
            return

    db.entries.append(new_entry)

def parse_single_bib_entry(bib: str) -> Dict[str, str]:
    db = bibtexparser.loads(bib)
    if not db.entries:
        raise ValueError("No entries parsed from BibTeX")
    return db.entries[0]

def main() -> int:
    client_id = os.getenv("ORCID_CLIENT_ID")
    client_secret = os.getenv("ORCID_CLIENT_SECRET")
    
    if not client_id or not client_secret:
        raise RuntimeError("Missing ORCID credentials")
    
    ap = argparse.ArgumentParser()
    ap.add_argument("--orcid", required=True, help="Your ORCID iD (e.g. 0000-0002-....)")
    ap.add_argument("--bib", required=True, help="Path to publications.bib")
    args = ap.parse_args()

    token = get_orcid_token(client_id, client_secret)
    works = get_orcid_works(args.orcid, token=token)
    db = load_bib(args.bib)

    for w in works:
        doi = extract_doi(w)
        if doi:
            bib = doi_to_bibtex(doi)
            if bib:
                try:
                    ent = parse_single_bib_entry(bib)
                    # Ensure DOI URL present
                    ent.setdefault("url", f"https://doi.org/{doi}")
                    merge_entry(db, ent)
                    continue
                except Exception:
                    pass

        # fallback
        bib = orcid_work_to_min_bibtex(w)
        ent = parse_single_bib_entry(bib)
        merge_entry(db, ent)

    write_bib(db, args.bib)
    print(f"Updated {args.bib} with {len(db.entries)} entries.")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
