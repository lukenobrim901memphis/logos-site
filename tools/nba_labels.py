#!/usr/bin/env python3
"""
Turn on logo name labels for every NBA team page, the same way the MLB pages
show them: the file name without its years, without "logo", and without
"alternate" (the section heading already says that). For example
"Alternate ATL logo 2021-present.png" -> label "ATL", years "2021-present".

Safe to run more than once: pages that already show labels are skipped.
Every page it changes is backed up to tools/backups/ first.

Usage:
  python3 nba_labels.py --dry-run
  python3 nba_labels.py
"""

import os
import re
import shutil
import sys
from datetime import datetime

SITE_DIR = "/Users/luke/logos-site"
TOOL_DIR = os.path.dirname(os.path.abspath(__file__))
BACKUP_DIR = os.path.join(TOOL_DIR, "backups")

PATH_LINE = re.compile(r"""const\s+path\s*=\s*["'][./]*images/nba-teams/""")
YEARS_LINE = re.compile(r"(\n([ \t]*)const yearText = matches \? matches\.join\(', '\) : \"\";)")
CAPTION = re.compile(r'(<div class="logo-caption">\s*\n)([ \t]*)(<div class="logo-year">\$\{yearText\}</div>)')

LABEL_CODE = '''
{ind}let nameWithoutYear = fullName.replace(/logo\\d*/gi, '');
{ind}(matches || []).forEach(m => {{ nameWithoutYear = nameWithoutYear.replace(m, ''); }});
{ind}nameWithoutYear = nameWithoutYear.replace(/alternate/gi, '').replace(/,/g, '')
{ind}    .replace(/\\s+/g, ' ').replace(/^-+|-+$/g, '').trim();'''


def add_labels(text):
    if "logo-name" in text:
        return None, "already shows labels"
    m = YEARS_LINE.search(text)
    c = CAPTION.search(text)
    if not m or not c:
        return None, "couldn't find the caption code"
    text = text[:m.end()] + LABEL_CODE.format(ind=m.group(2)) + text[m.end():]
    c = CAPTION.search(text)
    ind = c.group(2)
    label = f"{ind}${{nameWithoutYear ? `<div class=\"logo-name\">${{nameWithoutYear}}</div>` : ''}}\n"
    return text[:c.start(2)] + label + text[c.start(2):], "added"


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
            if not PATH_LINE.search(text):
                continue
            rel = os.path.relpath(page, SITE_DIR)
            new, status = add_labels(text)
            if new is None:
                if status.startswith("already"):
                    skipped += 1
                else:
                    problems.append(f"{rel}: {status} — not changed")
                continue
            done += 1
            print(f"{'(dry run) ' if dry_run else ''}{rel}: labels turned on")
            if not dry_run:
                os.makedirs(BACKUP_DIR, exist_ok=True)
                shutil.copy2(page, os.path.join(BACKUP_DIR, f"{datetime.now():%Y%m%d-%H%M%S}__{rel.replace(os.sep, '__')}"))
                with open(page, "w", encoding="utf-8") as f:
                    f.write(new)
    print(f"\n{'Would change' if dry_run else 'Changed'} {done} NBA page(s); {skipped} already had labels.")
    for p in problems:
        print("  ! " + p)


if __name__ == "__main__":
    main()
