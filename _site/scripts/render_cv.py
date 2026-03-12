#!/usr/bin/env python3
from __future__ import annotations

import argparse
import os
import re
from typing import Dict, List

import bibtexparser
from jinja2 import Environment, FileSystemLoader

LATEX_ESCAPE = {
    "&": r"\&",
    "%": r"\%",
    "$": r"\$",
    "#": r"\#",
    "_": r"\_",
    "{": r"\{",
    "}": r"\}",
    "~": r"\textasciitilde{}",
    "^": r"\textasciicircum{}",
    "\\": r"\textbackslash{}",
}

JOURNAL_ABBREVIATIONS = {
    "Physical Review D": "Phys. Rev. D",
    "Physical Review Letters": "Phys. Rev. Lett.",
    "Physical Review A": "Phys. Rev. A",
    "Artificial Intelligence": "Artificial Intelligence",
    "The Journal of Chemical Physics": "J. Chem. Phys.",
    "International Journal of Quantum Chemistry": "Int. J. Quantum Chem.",
    "American Journal of Physics": "Am. J. Phys.",
}

TARGET_AUTHOR_FAMILIES = {"lemaitre"}
TARGET_AUTHOR_GIVENS = {"philip", "phil"}


def tex_escape(s: str) -> str:
    if not s:
        return ""
    return "".join(LATEX_ESCAPE.get(ch, ch) for ch in s)


def clean_bib_value(value: str) -> str:
    return re.sub(r"[{}]", "", value or "").strip()


def split_bib_authors(author_field: str) -> List[str]:
    return [part.strip() for part in re.split(r"\s+and\s+", author_field or "") if part.strip()]


def format_given_names(given: str) -> str:
    parts = [part for part in re.split(r"[\s.-]+", given.strip()) if part]
    if not parts:
        return ""
    return " ".join(f"{part[0]}." for part in parts)


def format_author(author: str) -> str:
    author = clean_bib_value(author)
    if "," in author:
        family, given = [part.strip() for part in author.split(",", 1)]
    else:
        parts = author.split()
        family = parts[-1]
        given = " ".join(parts[:-1])

    rendered = f"{format_given_names(given)} {family}".strip()
    family_key = family.lower()
    first_given = given.split()[0].lower() if given.split() else ""
    if family_key in TARGET_AUTHOR_FAMILIES and first_given in TARGET_AUTHOR_GIVENS:
        rendered = rf"\textbf{{{rendered}}}"
    return rendered


def format_authors(author_field: str) -> str:
    authors = [format_author(author) for author in split_bib_authors(author_field)]
    if not authors:
        return ""
    if len(authors) == 1:
        return authors[0]
    if len(authors) == 2:
        return f"{authors[0]} and {authors[1]}"
    return ", ".join(authors[:-1]) + f", and {authors[-1]}"


def journal_name(entry: Dict[str, str]) -> str:
    override = clean_bib_value(entry.get("cv_journal", ""))
    if override:
        return override
    journal = clean_bib_value(entry.get("journal") or entry.get("booktitle") or "")
    return JOURNAL_ABBREVIATIONS.get(journal, journal)


def entry_url(entry: Dict[str, str]) -> str:
    for field in ("cv_url", "url"):
        value = clean_bib_value(entry.get(field, ""))
        if value:
            return value
    doi = clean_bib_value(entry.get("doi", ""))
    if doi:
        return f"https://doi.org/{doi}"
    return ""


def include_issue(entry: Dict[str, str]) -> bool:
    return clean_bib_value(entry.get("cv_include_issue", "")).lower() in {"1", "true", "yes"}


def format_venue(entry: Dict[str, str]) -> str:
    journal = journal_name(entry)
    volume = clean_bib_value(entry.get("volume", ""))
    number = clean_bib_value(entry.get("number", ""))
    pages = clean_bib_value(entry.get("pages", ""))
    year = clean_bib_value(entry.get("year", ""))

    parts = []
    if journal:
        parts.append(rf"\textit{{{tex_escape(journal)}}}")

    volume_part = tex_escape(volume)
    if volume_part:
        if number and include_issue(entry):
            volume_part = f"{volume_part}({tex_escape(number)})"
        parts.append(volume_part)

    if pages:
        page_text = tex_escape(pages.replace("--", "-").replace("–", "-").replace("—", "-"))
        if parts:
            parts[-1] = f"{parts[-1]}, {page_text}"
        else:
            parts.append(page_text)

    venue = " ".join(parts).strip()
    if year:
        venue = f"{venue} ({tex_escape(year)})" if venue else f"({tex_escape(year)})"
    return venue + "."


def strip_terminal_punctuation(text: str) -> str:
    return re.sub(r"[.]+$", "", clean_bib_value(text))


def format_entry(entry: Dict[str, str]) -> Dict[str, str]:
    title = clean_bib_value(entry.get("cv_title", "") or entry.get("title", ""))
    return {
        "citation_tex": (
            f"{format_authors(entry.get('author', ''))}, "
            f"``{tex_escape(strip_terminal_punctuation(title))}''."
            f" {format_venue(entry)}"
        ),
        "url": entry_url(entry),
    }


def sort_key(entry: Dict[str, str]) -> tuple[int, int, str]:
    order = clean_bib_value(entry.get("cv_order", ""))
    if order.isdigit():
        return (10_000 - int(order), 0, "")
    year = int(clean_bib_value(entry.get("year", "0")) or 0)
    month = clean_bib_value(entry.get("month", ""))
    month_value = int(month) if month.isdigit() else 0
    return (year, month_value, clean_bib_value(entry.get("title", "")).lower())


def render_publications(bib_path: str, out_path: str, template_path: str, limit: int = 200) -> None:
    with open(bib_path, "r", encoding="utf-8") as handle:
        db = bibtexparser.load(handle)

    entries = sorted(db.entries, key=sort_key, reverse=True)[:limit]
    rendered_entries = [format_entry(entry) for entry in entries]

    env = Environment(loader=FileSystemLoader("."))
    tpl = env.get_template(template_path)
    rendered = tpl.render(entries=rendered_entries)

    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as handle:
        handle.write(rendered)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--bib", required=True)
    ap.add_argument("--template", default="templates/cv_publications_section.tex.j2")
    ap.add_argument("--out", required=True)
    ap.add_argument("--limit", type=int, default=200)
    args = ap.parse_args()
    render_publications(args.bib, args.out, args.template, args.limit)


if __name__ == "__main__":
    main()
