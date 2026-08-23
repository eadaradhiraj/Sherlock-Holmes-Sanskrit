#!/usr/bin/env python3
"""
Auto-generate index.html TOC from filesystem.

Scans:
  adventures-sherlock-holmes/<story-slug>/*.html   -> collapsible multi-part stories
  memoirs/*.html                                  -> single-page stories

Usage:
  python3 scripts/update_home.py                  # regenerate index.html
  python3 scripts/update_home.py --check          # exit 1 if out-of-date (for CI)
  python3 scripts/update_home.py --install-hook   # install git pre-commit hook
"""

import argparse
import re
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent  # repo root
INDEX = ROOT / "index.html"
# HOME kept as alias for backwards compat but not used
HOME = INDEX

ADVENTURES_DIR = ROOT / "adventures-sherlock-holmes"
MEMOIRS_DIR = ROOT / "memoirs"

# Human-readable titles for slugs that don't title-case nicely.
SLUG_TITLES = {
    "beryl-coronet": "The Adventure of the Beryl Coronet",
    "scandal-in-bohemia": "A Scandal in Bohemia",
    "naval-treaty": "The Naval Treaty",
    # add future slugs here; fallback is Title Case
}

MEMOIR_TITLES = {
    "greek_interpretter.html": "The Greek Interpreter",  # filename has typo, keep mapping
    "greek_interpreter.html": "The Greek Interpreter",
    "silverblaze.html": "Silver Blaze",
    "silver_blaze.html": "Silver Blaze",
}

# Order for Adventures (if you want a custom order, list slugs here).
# Any slug not listed will be appended alphabetically.
ADVENTURES_ORDER = ["beryl-coronet", "scandal-in-bohemia", "naval-treaty"]

# Order for Memoirs
MEMOIRS_ORDER = ["greek_interpretter.html", "silverblaze.html"]


def slug_to_title(slug: str) -> str:
    if slug in SLUG_TITLES:
        return SLUG_TITLES[slug]
    # fallback: "my-story_slug" -> "My Story Slug"
    return slug.replace("-", " ").replace("_", " ").title()


def extract_title_from_html(path: Path) -> str | None:
    try:
        text = path.read_text(encoding="utf-8", errors="ignore")
        m = re.search(r"<title>(.*?)</title>", text, re.IGNORECASE | re.DOTALL)
        if m:
            t = m.group(1).strip()
            # Clean common prefixes like "The adventure of the ..."
            return t
        m2 = re.search(r"<h1[^>]*>(.*?)</h1>", text, re.IGNORECASE | re.DOTALL)
        if m2:
            return re.sub(r"<[^>]+>", "", m2.group(1)).strip()
    except Exception:
        pass
    return None


def scan_adventures():
    """Return list of (slug, title, [Path, ...]) sorted by desired order + numeric file order."""
    if not ADVENTURES_DIR.exists():
        return []
    slugs = [p.name for p in ADVENTURES_DIR.iterdir() if p.is_dir()]
    # sort by custom order, then alphabetically for unknowns
    def order_key(s):
        if s in ADVENTURES_ORDER:
            return (0, ADVENTURES_ORDER.index(s))
        return (1, s)
    slugs.sort(key=order_key)

    result = []
    for slug in slugs:
        d = ADVENTURES_DIR / slug
        files = list(d.glob("*.html"))
        # numeric sort: 1.html, 2.html, 10.html correctly
        def num_key(p):
            try:
                return int(p.stem)
            except ValueError:
                return float("inf")
        files.sort(key=num_key)
        if not files:
            continue
        title = slug_to_title(slug)
        result.append((slug, title, files))
    return result


def scan_memoirs():
    if not MEMOIRS_DIR.exists():
        return []
    files = [p for p in MEMOIRS_DIR.glob("*.html")]
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
            if raw:
                # Normalize: "The adventure of the Silver Blaze" -> "Silver Blaze" etc.
                # Keep raw title but Title-Case it
                title = raw.strip()
                # If title is ALL CAPS H1 bug, convert
                if title.isupper():
                    title = title.title()
            else:
                title = f.stem.replace("_", " ").replace("-", " ").title()
        result.append((f, title))
    return result


def build_adventures_html(adventures):
    lines = []
    for slug, title, files in adventures:
        count = len(files)
        meta = f"{count} part{'s' if count != 1 else ''}"
        lines.append(f'      <li>')
        lines.append(f'        <span class="story-heading">{title} <span class="story-meta">{meta}</span></span>')
        lines.append(f'        <ul class="parts-list">')
        for f in files:
            # keep relative href from repo root
            href = f"adventures-sherlock-holmes/{slug}/{f.name}"
            label = f"Part {f.stem}" if f.stem.isdigit() else f.stem
            lines.append(f'          <li><a href="{href}" class="chapter-link">{label}</a></li>')
        lines.append(f'        </ul>')
        lines.append(f'      </li>')
    return "\n".join(lines)


def build_memoirs_html(memoirs):
    lines = []
    for f, title in memoirs:
        href = f"memoirs/{f.name}"
        lines.append(f'      <li>')
        lines.append(f'        <span class="story-heading">{title} <span class="story-meta">single</span></span>')
        lines.append(f'        <ul class="parts-list">')
        lines.append(f'          <li><a href="{href}" class="chapter-link">Read — {title}</a></li>')
        lines.append(f'        </ul>')
        lines.append(f'      </li>')
    return "\n".join(lines)


def render_home(adventures, memoirs):
    adv_html = build_adventures_html(adventures)
    mem_html = build_memoirs_html(memoirs)

    total_stories = len(adventures) + len(memoirs)
    total_parts = sum(len(files) for _, _, files in adventures) + len(memoirs)
    today = date.today().isoformat()

    # Read existing index.html as template to preserve <head> if edited manually.
    # We only replace the auto-generated blocks if markers exist.
    if INDEX.exists():
        original = INDEX.read_text(encoding="utf-8")
    else:
        original = ""

    # If markers exist, do surgical replacement (safer for manual edits)
    if "<!-- AUTO-GENERATED:START" in original:
        new_block = (
            f"    <h2 class=\"collection-title\">The Adventures of Sherlock Holmes</h2>\n"
            f"    <ul class=\"chapter-list\">\n{adv_html}\n    </ul>\n\n"
            f"    <h2 class=\"collection-title\">The Memoirs of Sherlock Holmes</h2>\n"
            f"    <ul class=\"chapter-list\">\n{mem_html}\n    </ul>"
        )
        updated = re.sub(
            r"<!-- AUTO-GENERATED:START.*?AUTO-GENERATED:END -->",
            f"<!-- AUTO-GENERATED:START — Do not edit manually. Run: python3 scripts/update_home.py -->\n"
            f"{new_block}\n\n    <!-- AUTO-GENERATED:END -->",
            original,
            flags=re.DOTALL,
        )
        # update stats bar too
        stats_re = r"<!-- AUTO-GENERATED-STATS:START -->.*?<!-- AUTO-GENERATED-STATS:END -->"
        stats_new = f"<!-- AUTO-GENERATED-STATS:START -->\n      {total_stories} stories &middot; {total_parts} parts &middot; Last updated: {today}\n      <!-- AUTO-GENERATED-STATS:END -->"
        if re.search(stats_re, updated, re.DOTALL):
            updated = re.sub(stats_re, stats_new, updated, flags=re.DOTALL)
        return updated

    # Fallback: generate full file from scratch (no inline <style>/<script>, uses style.css + script.js)
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
    <p style="margin-top:40px; color:#888; font-size:0.9rem;">Source: <a href="https://github.com/eadaradhiraj/Sherlock-Holmes-Sanskrit" style="color:#2196f3;">GitHub</a> &middot; Updated automatically by <code>scripts/update_home.py</code></p>
  </div>
  <script src="script.js"></script>
</body>
</html>
"""


def install_hook():
    hook_path = ROOT / ".git" / "hooks" / "pre-commit"
    hook_path.parent.mkdir(parents=True, exist_ok=True)
    content = """#!/bin/sh
# Auto-update index.html before commit
# Generated by scripts/update_home.py --install-hook
python3 scripts/update_home.py
# re-stage if file changed
if ! git diff --quiet -- index.html 2>/dev/null; then
  git add index.html
  echo "[pre-commit] index.html auto-updated and re-staged."
fi
"""
    hook_path.write_text(content, encoding="utf-8")
    hook_path.chmod(0o755)
    print(f"Installed pre-commit hook -> {hook_path}")


def main():
    parser = argparse.ArgumentParser(description="Regenerate index.html")
    parser.add_argument("--check", action="store_true", help="Check if index.html is up to date (for CI)")
    parser.add_argument("--install-hook", action="store_true", help="Install git pre-commit hook")
    args = parser.parse_args()

    if args.install_hook:
        install_hook()
        # also run once to ensure up to date
        adventures = scan_adventures()
        memoirs = scan_memoirs()
        rendered = render_home(adventures, memoirs)
        INDEX.write_text(rendered, encoding="utf-8")
        # remove legacy home.html if present
        if (ROOT / "home.html").exists():
            (ROOT / "home.html").unlink()
            print("Removed legacy home.html")
        print("Regenerated index.html")
        return

    adventures = scan_adventures()
    memoirs = scan_memoirs()
    print(f"Found {len(adventures)} adventure stories, {len(memoirs)} memoir stories")
    for slug, title, files in adventures:
        print(f"  - {title}: {len(files)} parts")
    for f, title in memoirs:
        print(f"  - {title}: {f.name}")

    rendered = render_home(adventures, memoirs)

    if args.check:
        if not INDEX.exists():
            print("index.html missing", file=sys.stderr)
            sys.exit(1)
        current = INDEX.read_text(encoding="utf-8")
        if current != rendered:
            print("index.html is OUT OF DATE. Run: python3 scripts/update_home.py", file=sys.stderr)
            sys.exit(1)
        print("index.html is up to date.")
        return

    INDEX.write_text(rendered, encoding="utf-8")
    # cleanup legacy duplicate if it still exists
    legacy = ROOT / "home.html"
    if legacy.exists():
        legacy.unlink()
        print(f"Removed legacy {legacy}")
    print(f"Wrote {INDEX} ({len(rendered)} bytes)")


if __name__ == "__main__":
    main()
