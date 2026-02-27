#!/usr/bin/env python3
from __future__ import annotations
import argparse, os
import bibtexparser
from jinja2 import Environment, FileSystemLoader
import re

LATEX_ESCAPE = {
    "&": r"\&", "%": r"\%", "$": r"\$", "#": r"\#", "_": r"\_",
    "{": r"\{", "}": r"\}", "~": r"\textasciitilde{}", "^": r"\textasciicircum{}",
    "\\": r"\textbackslash{}",
}

def tex_escape(s: str) -> str:
    if not s:
        return ""
    return "".join(LATEX_ESCAPE.get(ch, ch) for ch in s)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--bib", required=True)
    ap.add_argument("--template", default="templates/cv_publications_section.tex.j2")
    ap.add_argument("--out", required=True)
    ap.add_argument("--limit", type=int, default=200)
    args = ap.parse_args()

    with open(args.bib, "r", encoding="utf-8") as f:
        db = bibtexparser.load(f)

    # Sort newest first
    def sort_key(e):
        y = int(e.get("year") or 0)
        m = int(e.get("month") or 0) if str(e.get("month") or "").isdigit() else 0
        return (y, m)

    entries = sorted(db.entries, key=sort_key, reverse=True)[: args.limit]

    normed = []
    for e in entries:
        title = e.get("title", "")
        author = e.get("author", "")
        venue = e.get("journal") or e.get("booktitle") or ""

        url = e.get("url")
        if not url and e.get("doi"):
            url = f"https://doi.org/{e['doi']}"

        normed.append({
            "title_tex": tex_escape(title),
            "authors_tex": tex_escape(author),
            "venue_tex": tex_escape(venue),
            "year": e.get("year", ""),
            "url": url,
        })

    env = Environment(loader=FileSystemLoader("."))
    tpl = env.get_template(args.template)
    rendered = tpl.render(entries=normed)

    os.makedirs(os.path.dirname(args.out), exist_ok=True)
    with open(args.out, "w", encoding="utf-8") as f:
        f.write(rendered)

if __name__ == "__main__":
    main()
