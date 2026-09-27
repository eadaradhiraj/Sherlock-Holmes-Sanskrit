#!/usr/bin/env python3
"""
Auto-generate index.html TOC from filesystem.

Scans:
  adventures-sherlock-holmes/<story-slug>/*.html -> collapsible multi-part stories
  adventures-sherlock-holmes/*.html              -> single-page stories
  memoirs/*.html                                 -> single-page stories
"""

import argparse
import re
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
INDEX = ROOT / "index.html"

ADVENTURES_DIR = ROOT / "adventures-sherlock-holmes"
MEMOIRS_DIR = ROOT / "memoirs"

SLUG_TITLES = {
    "beryl-coronet": "The Adventure of the Beryl Coronet",
    "scandal-in-bohemia": "A Scandal in Bohemia",
    "naval-treaty": "The Naval Treaty",
    "red-headed-league": "The Red-Headed League",
    "yellow-face": "The Yellow Face",
    "gold-tooth": "The Adventure of the Gold Tooth",
}

MEMOIR_TITLES = {
    "greek_interpretter.html": "The Greek Interpreter",
    "greek_interpreter.html": "The Greek Interpreter",
    "silverblaze.html": "Silver Blaze",
    "silver_blaze.html": "Silver Blaze",
    "cardboard_box.html": "The Adventure of the Cardboard Box",
    "gloria_scott.html": "The Adventure of the Gloria Scott",
}

ADVENTURES_ORDER = [
    "scandal-in-bohemia",
    "red-headed-league",
    "beryl-coronet",
    "naval-treaty",
    "yellow-face",
    "gold-tooth",
]

MEMOIRS_ORDER = [
    "silverblaze.html",
    "cardboard_box.html",
    "gloria_scott.html",
    "greek_interpretter.html",
]


def slug_to_title(slug: str) -> str:
    if slug in SLUG_TITLES:
        return SLUG_TITLES[slug]
    return slug.replace("-", " ").replace("_", " ").title()


def extract_title_from_html(path: Path) -> str | None:
    try:
        text = path.read_text(encoding="utf-8", errors="ignore")
        m = re.search(r"<title>(.*?)</title>", text, re.IGNORECASE | re.DOTALL)
        if m:
            return m.group(1).strip()
        m2 = re.search(r"<h1[^>]*>(.*?)</h1>", text, re.IGNORECASE | re.DOTALL)
        if m2:
            return re.sub(r"<[^>]+>", "", m2.group(1)).strip()
    except Exception:
        pass
    return None


def scan_adventures():
    """Return list of multi-part or single-part adventure stories."""
    if not ADVENTURES_DIR.exists():
        return []

    entries = []

    # 1. Multi-part directory stories
    for p in ADVENTURES_DIR.iterdir():
        if p.is_dir():
            files = list(p.glob("*.html"))
            def num_key(f):
                try:
                    return int(f.stem)
                except ValueError:
                    return float("inf")
            files.sort(key=num_key)
            if files:
                title = slug_to_title(p.name)
                entries.append({"type": "multi", "slug": p.name, "title": title, "files": files})

    # 2. Single-file stories directly under adventures-sherlock-holmes/
    for p in ADVENTURES_DIR.glob("*.html"):
        slug = p.stem
        title = SLUG_TITLES.get(slug) or extract_title_from_html(p) or slug_to_title(slug)
        entries.append({"type": "single", "slug": slug, "title": title, "file": p})

    def order_key(item):
        s = item["slug"]
        if s in ADVENTURES_ORDER:
            return (0, ADVENTURES_ORDER.index(s))
        return (1, s)

    entries.sort(key=order_key)
    return entries


def scan_memoirs():
    if not MEMOIRS_DIR.exists():
        return []
    files = list(MEMOIRS_DIR.glob("*.html"))

    def order_key(p):
        n = p.name
        if n in MEMOIRS_ORDER:
            return (0, MEMOIRS_ORDER.index(n))
        return (1, n)

    files.sort(key=order_key)
    result = []
    for f in files:
        title = MEMOIR_TITLES.get(f.name)
        if not title:
            raw = extract_title_from_html(f)
            title = raw.title() if raw else f.stem.replace("_", " ").replace("-", " ").title()
        result.append((f, title))
    return result


def build_adventures_html(adventures):
    lines = []
    for item in adventures:
        if item["type"] == "multi":
            slug, title, files = item["slug"], item["title"], item["files"]
            count = len(files)
            meta = f"{count} part{'s' if count != 1 else ''}"
            lines.append("      <li>")
            lines.append(f'        <span class="story-heading">{title} <span class="story-meta">{meta}</span></span>')
            lines.append('        <ul class="parts-list">')
            for f in files:
                href = f"adventures-sherlock-holmes/{slug}/{f.name}"
                label = f"Part {f.stem}" if f.stem.isdigit() else f.stem
                lines.append(f'          <li><a href="{href}" class="chapter-link">{label}</a></li>')
            lines.append("        </ul>")
            lines.append("      </li>")
        else:
            f, title = item["file"], item["title"]
            href = f"adventures-sherlock-holmes/{f.name}"
            lines.append("      <li>")
            lines.append(f'        <span class="story-heading">{title} <span class="story-meta">single</span></span>')
            lines.append('        <ul class="parts-list">')
            lines.append(f'          <li><a href="{href}" class="chapter-link">Read — {title}</a></li>')
            lines.append("        </ul>")
            lines.append("      </li>")
    return "\n".join(lines)


def build_memoirs_html(memoirs):
    lines = []
    for f, title in memoirs:
        href = f"memoirs/{f.name}"
        lines.append("      <li>")
        lines.append(f'        <span class="story-heading">{title} <span class="story-meta">single</span></span>')
        lines.append('        <ul class="parts-list">')
        lines.append(f'          <li><a href="{href}" class="chapter-link">Read — {title}</a></li>')
        lines.append("        </ul>")
        lines.append("      </li>")
    return "\n".join(lines)


def render_home(adventures, memoirs):
    adv_html = build_adventures_html(adventures)
    mem_html = build_memoirs_html(memoirs)

    total_stories = len(adventures) + len(memoirs)
    total_parts = sum(
        len(item["files"]) if item["type"] == "multi" else 1 for item in adventures
    ) + len(memoirs)
    today = date.today().isoformat()

    if INDEX.exists():
        original = INDEX.read_text(encoding="utf-8")
    else:
        original = ""

    if "<!-- AUTO-GENERATED:START" in original:
        new_block = (
            f'    <h2 class="collection-title">The Adventures of Sherlock Holmes</h2>\n'
            f'    <ul class="chapter-list">\n{adv_html}\n    </ul>\n\n'
            f'    <h2 class="collection-title">The Memoirs of Sherlock Holmes</h2>\n'
            f'    <ul class="chapter-list">\n{mem_html}\n    </ul>'
        )
        updated = re.sub(
            r"<!-- AUTO-GENERATED:START.*?AUTO-GENERATED:END -->",
            f"<!-- AUTO-GENERATED:START — Do not edit manually. Run: python3 scripts/update_home.py -->\n"
            f"{new_block}\n\n    <!-- AUTO-GENERATED:END -->",
            original,
            flags=re.DOTALL,
        )
        stats_re = r"<!-- AUTO-GENERATED-STATS:START -->.*?<!-- AUTO-GENERATED-STATS:END -->"
        stats_new = (
            f"<!-- AUTO-GENERATED-STATS:START -->\n"
            f"      {total_stories} stories &middot; {total_parts} parts &middot; Last updated: {today}\n"
            f"      <!-- AUTO-GENERATED-STATS:END -->"
        )
        if re.search(stats_re, updated, re.DOTALL):
            updated = re.sub(stats_re, stats_new, updated, flags=re.DOTALL)
        return updated

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Table of Contents - Sherlock Holmes in Sanskrit</title>
  <link rel="stylesheet" href="style.css">
</head>
<body>
  <div class="toc-container">
    <h1>शेर्लक् होम्सः संस्कृते</h1>
    <p class="site-subtitle">Sherlock Holmes in Sanskrit — parallel English &amp; Sanskrit texts</p>
    <div class="stats-bar">
      <!-- AUTO-GENERATED-STATS:START -->
      {total_stories} stories &middot; {total_parts} parts &middot; Last updated: {today}
      <!-- AUTO-GENERATED-STATS:END -->
    </div>
    <!-- AUTO-GENERATED:START — Do not edit manually. Run: python3 scripts/update_home.py -->
    <h2 class="collection-title">The Adventures of Sherlock Holmes</h2>
    <ul class="chapter-list">
{adv_html}
    </ul>

    <h2 class="collection-title">The Memoirs of Sherlock Holmes</h2>
    <ul class="chapter-list">
{mem_html}
    </ul>

    <!-- AUTO-GENERATED:END -->
    <p style="margin-top:40px; color:#888; font-size:0.9rem;">
      Source: <a href="https://github.com/eadaradhiraj/Sherlock-Holmes-Sanskrit" style="color:#2196f3;">GitHub</a>
      &middot; Updated automatically by <code>scripts/update_home.py</code>
    </p>
  </div>
  <script src="script.js"></script>
</body>
</html>
"""


def main():
    parser = argparse.ArgumentParser(description="Regenerate index.html")
    parser.add_argument("--check", action="store_true", help="Check if index.html is up to date (for CI)")
    args = parser.parse_args()

    adventures = scan_adventures()
    memoirs = scan_memoirs()

    rendered = render_home(adventures, memoirs)

    if args.check:
        if not INDEX.exists() or INDEX.read_text(encoding="utf-8") != rendered:
            print("index.html is OUT OF DATE. Run: python3 scripts/update_home.py", file=sys.stderr)
            sys.exit(1)
        print("index.html is up to date.")
        return

    INDEX.write_text(rendered, encoding="utf-8")
    print(f"Wrote {INDEX} ({len(rendered)} bytes) — {len(adventures)} adventures, {len(memoirs)} memoirs.")


if __name__ == "__main__":
    main()