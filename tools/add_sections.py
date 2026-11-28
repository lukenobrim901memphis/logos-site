#!/usr/bin/env python3
"""
Add sections to every team page at once.

To add a new section later, add a line to SECTIONS below and run the script.
Lines already on a page are skipped, so the old lines can stay in the list.

For each page it adds the section heading + grid, and one rule to the page's
sorting code so matching logos go there (checked before Primary / Alternate /
Jersey / Hat, so a "Throwback hat logo" lands in Throwback, not Hat Logos).

Safe to run more than once: pages that already have the section are skipped.
Pages that don't look like the usual layout are listed, not changed. Every
page it edits is backed up to tools/backups/ first.

Usage:
  python3 add_sections.py --dry-run   # show what it would do
  python3 add_sections.py             # do it
"""

import os
import re
import shutil
import sys
from datetime import datetime

SITE_DIR = "/Users/luke/logos-site"
TOOL_DIR = os.path.dirname(os.path.abspath(__file__))
BACKUP_DIR = os.path.join(TOOL_DIR, "backups")

# One line per section:
#   (league folder in images/, heading on the page, word in the file name,
#    put it before the first of these headings that the page has,
#    optional: words that keep a file OUT of the section)
# The section's id is made from the heading ("Classic Edition" -> classic-edition).
SECTIONS = [
    ("mlb-teams",      "Throwback",       "throwback", ["Holiday", "Spring Training", "Batting Practice", "Other"], ["throwback weekend"]),
    ("triple-a-teams", "Throwback",       "throwback", ["Theme Night Logos", "Copa de la Diversión Logos", "Batting Practice", "Other"], ["throwback weekend"]),
    ("nba-teams",      "Classic Edition", "classic",   ["Holiday", "Court Logos", "Other"]),
    ("mlb-teams",      "Negro League",    "negro league", ["Holiday", "Spring Training", "Batting Practice", "Other"]),
    # Example of a new one:
    # ("mlb-teams",    "All-Star Game",   "all star",  ["Holiday", "Other"]),
]


def section_id(heading):
    return re.sub(r"[^a-z0-9]+", "-", heading.lower()).strip("-")

PATH_LINE = re.compile(r"""const\s+path\s*=\s*["'][./]*images/([^/"']+)/""")

# The two kinds of sorting code your pages use
CARD_STYLE = re.compile(r'(\n([ \t]*)else if \(lowerName\.includes\("primary logo"\)\) \{)')            # MLB / NBA
GRID_STYLE = re.compile(r'(\n([ \t]*)if \(lowerName\.includes\("primary logo"\)\) targetGrid = \'primary-logos\';)')  # Triple-A


def add_section(text, heading, word, before, exclude=()):
    sid = section_id(heading)
    if f'id="{sid}"' in text:
        return None, "already has it"

    # 1. heading + grid, before the first of the listed headings that exists
    block = (f'<div class="category-header">{heading}</div>\n'
             f'    <div id="{sid}" class="grid"></div>\n\n    ')
    for name in before:
        anchor = f'<div class="category-header">{name}</div>'
        if anchor in text:
            text = text.replace(anchor, block + anchor, 1)
            break
    else:
        return None, "couldn't find where to put the section"

    cond = f'lowerName.includes("{word}")' + "".join(f' && !lowerName.includes("{x}")' for x in exclude)
    if exclude:
        cond = f"({cond})"

    # 2. the sorting rule, just before the "primary logo" rule
    m = CARD_STYLE.search(text)
    if m:
        ind = m.group(2)
        rule = (f'\n{ind}else if ({cond}) {{\n'
                f"{ind}    document.getElementById('{sid}').innerHTML += cardHtml;\n"
                f'{ind}}}')
        return text[:m.start()] + rule + text[m.start():], "added"
    m = GRID_STYLE.search(text)
    if m:
        ind = m.group(2)
        rule = f"\n{ind}if ({cond}) targetGrid = '{sid}';\n{ind}else"
        # turn  "if (primary...)"  into  "if (word...) ... else if (primary...)"
        original = m.group(1)
        return text[:m.start()] + rule + original.replace("\n" + ind, " ", 1) + text[m.end():], "added"
    return None, "couldn't find the sorting code"


def main():
    dry_run = "--dry-run" in sys.argv
    done, skipped, problems = 0, 0, []
    for root, dirs, files in os.walk(SITE_DIR):
        dirs[:] = [d for d in dirs if not d.startswith(".") and os.path.join(root, d) != TOOL_DIR]
        for name in sorted(files):
            if not name.endswith(".html"):
                continue
            page = os.path.join(root, name)
            text = open(page, encoding="utf-8").read()
            m = PATH_LINE.search(text)
            if not m:
                continue
            rel = os.path.relpath(page, SITE_DIR)
            changed = []
            for folder, heading, word, before, *rest in SECTIONS:
                if folder != m.group(1):
                    continue
                new, status = add_section(text, heading, word, before, rest[0] if rest else ())
                if new is None:
                    if status == "already has it":
                        skipped += 1
                    else:
                        problems.append(f"{rel} ({heading}): {status} — not changed")
                    continue
                text = new
                changed.append(heading)
            if not changed:
                continue
            done += 1
            print(f"{'(dry run) ' if dry_run else ''}{rel}: added {', '.join(changed)}")
            if not dry_run:
                os.makedirs(BACKUP_DIR, exist_ok=True)
                shutil.copy2(page, os.path.join(BACKUP_DIR, f"{datetime.now():%Y%m%d-%H%M%S}__{rel.replace(os.sep, '__')}"))
                with open(page, "w", encoding="utf-8") as f:
                    f.write(text)
    print(f"\n{'Would change' if dry_run else 'Changed'} {done} page(s); "
          f"{skipped} section(s) were already there.")
    for p in problems:
        print("  ! " + p)


if __name__ == "__main__":
    main()
