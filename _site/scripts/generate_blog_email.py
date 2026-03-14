#!/usr/bin/env python3

from __future__ import annotations

import argparse
import json
import re
from datetime import datetime
from pathlib import Path
from typing import Any

import markdown
import yaml


ROOT = Path(__file__).resolve().parents[1]
CONFIG_PATH = ROOT / "_config.yml"
OUTBOX_DIR = ROOT / "newsletter_outbox"


HTML_TEMPLATE = """<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>{subject}</title>
  </head>
  <body style="margin:0;padding:0;background:#f8fafc;color:#0f172a;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;">
    <table role="presentation" width="100%" cellspacing="0" cellpadding="0" style="background:#f8fafc;padding:24px 0;">
      <tr>
        <td align="center">
          <table role="presentation" width="100%" cellspacing="0" cellpadding="0" style="max-width:680px;background:#ffffff;border-radius:18px;overflow:hidden;border:1px solid #e2e8f0;">
            {hero}
            <tr>
              <td style="padding:32px 32px 12px 32px;">
                <div style="font-size:12px;letter-spacing:0.08em;text-transform:uppercase;color:#64748b;font-weight:700;">New blog post</div>
                <h1 style="margin:10px 0 12px 0;font-size:32px;line-height:1.15;color:#0f172a;">{title}</h1>
                <p style="margin:0 0 18px 0;font-size:17px;line-height:1.7;color:#334155;">{excerpt}</p>
                <p style="margin:0 0 20px 0;">
                  <a href="{post_url}" style="display:inline-block;background:#0f172a;color:#ffffff;text-decoration:none;padding:12px 18px;border-radius:999px;font-weight:700;">Read the full post</a>
                </p>
              </td>
            </tr>
            <tr>
              <td style="padding:0 32px 8px 32px;font-size:16px;line-height:1.75;color:#1e293b;">
                {body_html}
              </td>
            </tr>
            <tr>
              <td style="padding:24px 32px 32px 32px;border-top:1px solid #e2e8f0;font-size:14px;line-height:1.7;color:#64748b;">
                <p style="margin:0 0 10px 0;">You are receiving this because you subscribed for updates from {site_title}.</p>
                <p style="margin:0;">Website: <a href="{site_url}" style="color:#0f172a;">{site_url}</a></p>
              </td>
            </tr>
          </table>
        </td>
      </tr>
    </table>
  </body>
</html>
"""


def parse_front_matter(path: Path) -> tuple[dict[str, Any], str]:
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---\n"):
        return {}, text
    _, remainder = text.split("---\n", 1)
    if "\n---\n" not in remainder:
        return {}, text
    raw_front_matter, body = remainder.split("\n---\n", 1)
    data = yaml.safe_load(raw_front_matter) or {}
    return data if isinstance(data, dict) else {}, body.strip()


def load_config() -> dict[str, Any]:
    data = yaml.safe_load(CONFIG_PATH.read_text(encoding="utf-8")) or {}
    return data if isinstance(data, dict) else {}


def derive_post_url(config: dict[str, Any], post_path: Path, front_matter: dict[str, Any]) -> str:
    site_url = str(config.get("url", "")).rstrip("/")
    if front_matter.get("permalink"):
        permalink = str(front_matter["permalink"])
        return f"{site_url}{permalink}" if site_url else permalink

    stem = post_path.stem
    date_part = stem[:10]
    slug_part = stem[11:]
    year, month, day = date_part.split("-")
    categories = front_matter.get("categories") or []
    if isinstance(categories, str):
        categories = [categories]
    category_prefix = "/".join(str(item).strip("/") for item in categories if item)
    prefix = f"/{category_prefix}" if category_prefix else ""
    return f"{site_url}{prefix}/{year}/{month}/{day}/{slug_part}.html"


def first_nonempty_paragraph(text: str) -> str:
    for block in re.split(r"\n\s*\n", text):
        cleaned = re.sub(r"^#+\s*", "", block.strip())
        if cleaned:
            return cleaned
    return ""


def derive_excerpt(front_matter: dict[str, Any], body: str) -> str:
    excerpt = str(front_matter.get("excerpt") or "").strip()
    if excerpt:
        return excerpt
    paragraph = first_nonempty_paragraph(body)
    if len(paragraph) > 240:
        return paragraph[:237].rstrip() + "..."
    return paragraph


def normalize_image_url(config: dict[str, Any], image_path: str | None) -> str | None:
    if not image_path:
        return None
    image_path = str(image_path)
    if image_path.startswith("http://") or image_path.startswith("https://"):
        return image_path
    site_url = str(config.get("url", "")).rstrip("/")
    if not image_path.startswith("/"):
        image_path = "/" + image_path
    return f"{site_url}{image_path}" if site_url else image_path


def derive_hero_image(config: dict[str, Any], front_matter: dict[str, Any]) -> str | None:
    header = front_matter.get("header") or {}
    if isinstance(header, dict):
        for key in ("overlay_image", "image"):
            if header.get(key):
                return normalize_image_url(config, header.get(key))
    if front_matter.get("image"):
        return normalize_image_url(config, front_matter.get("image"))
    return None


def strip_markdown_image_lines(body: str) -> str:
    lines = []
    for line in body.splitlines():
        if re.match(r"^\s*!\[.*\]\(.*\)\s*$", line):
            continue
        lines.append(line)
    return "\n".join(lines).strip()


def body_to_html(body: str, post_url: str) -> str:
    prepared = strip_markdown_image_lines(body)
    html = markdown.markdown(prepared, extensions=["extra", "sane_lists"])
    return f'{html}<p><a href="{post_url}">Continue reading on the site.</a></p>'


def body_to_text(body: str, post_url: str) -> str:
    cleaned = re.sub(r"!\[[^\]]*\]\([^)]+\)", "", body)
    cleaned = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", cleaned)
    cleaned = re.sub(r"`([^`]+)`", r"\1", cleaned)
    cleaned = re.sub(r"^#+\s*", "", cleaned, flags=re.MULTILINE)
    cleaned = re.sub(r"\n{3,}", "\n\n", cleaned).strip()
    return f"{cleaned}\n\nContinue reading: {post_url}\n"


def ensure_outbox_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)
    keep = path / ".gitkeep"
    if not keep.exists():
        keep.write_text("", encoding="utf-8")


def subject_for(config: dict[str, Any], title: str) -> str:
    newsletter = config.get("newsletter") or {}
    prefix = newsletter.get("campaign_subject_prefix") or f"New on {config.get('title', 'the blog')}:"
    return f"{prefix} {title}".strip()


def process_post(post_path: Path, config: dict[str, Any], outbox_dir: Path) -> dict[str, Any]:
    front_matter, body = parse_front_matter(post_path)
    title = str(front_matter.get("title") or post_path.stem[11:].replace("-", " "))
    post_url = derive_post_url(config, post_path, front_matter)
    excerpt = derive_excerpt(front_matter, body)
    hero_image = derive_hero_image(config, front_matter)
    subject = subject_for(config, title)

    hero = ""
    if hero_image:
        hero = (
            "<tr><td>"
            f'<img src="{hero_image}" alt="{title}" style="display:block;width:100%;height:auto;max-height:360px;object-fit:cover;">'
            "</td></tr>"
        )

    html_body = body_to_html(body, post_url)
    text_body = body_to_text(body, post_url)
    slug = post_path.stem
    post_out_dir = outbox_dir / slug
    post_out_dir.mkdir(parents=True, exist_ok=True)

    html_output = HTML_TEMPLATE.format(
        subject=subject,
        hero=hero,
        title=title,
        excerpt=excerpt,
        post_url=post_url,
        body_html=html_body,
        site_title=config.get("title", "the site"),
        site_url=str(config.get("url", "")).rstrip("/"),
    )

    metadata = {
        "subject": subject,
        "title": title,
        "excerpt": excerpt,
        "post_url": post_url,
        "source_post": post_path.relative_to(ROOT).as_posix(),
        "generated_at": datetime.utcnow().isoformat(timespec="seconds") + "Z",
        "hero_image": hero_image,
    }

    (post_out_dir / "campaign.html").write_text(html_output, encoding="utf-8")
    (post_out_dir / "campaign.txt").write_text(text_body, encoding="utf-8")
    (post_out_dir / "metadata.json").write_text(json.dumps(metadata, indent=2), encoding="utf-8")
    return metadata


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate EmailOctopus-ready newsletter content for blog posts.")
    parser.add_argument("posts", nargs="+", help="Paths to post markdown files.")
    parser.add_argument("--outdir", default=str(OUTBOX_DIR), help="Output directory for generated campaign packages.")
    args = parser.parse_args()

    config = load_config()
    outbox_dir = Path(args.outdir).resolve()
    ensure_outbox_dir(outbox_dir)

    generated = []
    for post_arg in args.posts:
        post_path = Path(post_arg).resolve()
        generated.append(process_post(post_path, config, outbox_dir))

    print(json.dumps(generated, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
