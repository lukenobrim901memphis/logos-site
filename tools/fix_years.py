#!/usr/bin/env python3
"""
Make every team page show only the years at the END of a logo's file name
(the ones after "logo", "patch", "texture", "pattern", ...), and use the rest
as the logo's name:

  "1968 throwback jersey logo 2018.png"       -> name "1968 throwback jersey",  years "2018"
  "Throwback jersey logo 2011, 2015-2016.png" -> name "Throwback jersey",       years "2011, 2015-2016"
  "Road gray 2007-2013.png"                   -> name "Road gray",              years "2007-2013"

Also sorts Triple-A pages by those years, so a 2018 throwback of a 1968 design
sorts with 2018, not 1968. (MLB and NBA pages already sort by the last year.)

Works on MLB, Triple-A and NBA pages (add more league folders to LEAGUES).
Safe to run more than once; pages already fixed are skipped. Every page it
changes is backed up to tools/backups/ first.

Usage:
  python3 fix_years.py --dry-run
  python3 fix_years.py
"""

import os
import re
import shutil
import sys
from datetime import datetime

SITE_DIR = "/Users/luke/logos-site"
TOOL_DIR = os.path.dirname(os.path.abspath(__file__))
BACKUP_DIR = os.path.join(TOOL_DIR, "backups")
LEAGUES = {"mlb-teams", "triple-a-teams", "nba-teams"}

PATH_LINE = re.compile(r"""(const\s+path\s*=\s*["'][./]*images/([^/"']+)/[^"']*["'];?[ \t]*\n)""")

HELPERS = r'''// Years shown = only the years at the end of the file name; the rest is the name
const YEARS_AT_END = /\s(\d{4}(?:-(?:\d{4}|present))?(?:,\s*\d{4}(?:-(?:\d{4}|present))?)*)\s*$/i;
function splitYears(fileName) {
    const base = fileName.replace(/\.png$/i, '');
    const m = base.match(YEARS_AT_END);
    return m ? { name: base.slice(0, m.index), years: m[1] } : { name: base, years: '' };
}
function labelFrom(name) {
    return name.replace(/logo\d*/gi, '').replace(/alternate/gi, '').replace(/,/g, '')
               .replace(/\s+/g, ' ').replace(/^-+|-+$/g, '').trim();
}
'''

# MLB / NBA style: a `const cardHtml = \`...\`;` template using ${yearText} / ${nameWithoutYear}
CARD_TEMPLATE = re.compile(r"(\n([ \t]*)const cardHtml = `)(.*?)(`;)", re.DOTALL)
# Triple-A style
MILB_YEAR_LINE = re.compile(r'const yearText = yearMatch \? yearMatch\[0\] : "";')
MILB_SORT_LINE = re.compile(r"const yearMatch = file\.match\(/\\d\{4\}/\);")


def fix(text):
    if "YEARS_AT_END" in text:
        return None, "already fixed"
    m = PATH_LINE.search(text)
    text = text[:m.end()] + HELPERS + text[m.end():]

    c = CARD_TEMPLATE.search(text)
    if c and "${yearText}" in c.group(3):
        ind = c.group(2)
        body = c.group(3).replace("${yearText}", "${shownYears}").replace("${nameWithoutYear}", "${shownName}")
        prep = (f"\n{ind}const shown = splitYears(fileName);"
                f"\n{ind}const shownYears = shown.years || yearText;"
                f"\n{ind}const shownName = labelFrom(shown.name);")
        return text[:c.start()] + prep + c.group(1) + body + c.group(4) + text[c.end():], "fixed"

    if MILB_YEAR_LINE.search(text):
        text = MILB_YEAR_LINE.sub(
            'const yearText = splitYears(fileName).years || (yearMatch ? yearMatch[0] : "");', text, count=1)
        text = MILB_SORT_LINE.sub(
            r"const yearMatch = (splitYears(file).years || file).match(/\\d{4}/);", text, count=1)
        return text, "fixed"
    return None, "couldn't find the caption code"


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
            if not m or m.group(2) not in LEAGUES:
                continue
            rel = os.path.relpath(page, SITE_DIR)
            new, status = fix(text)
            if new is None:
                if status == "already fixed":
                    skipped += 1
                else:
                    problems.append(f"{rel}: {status} — not changed")
                continue
            done += 1
            print(f"{'(dry run) ' if dry_run else ''}{rel}: fixed")
            if not dry_run:
                os.makedirs(BACKUP_DIR, exist_ok=True)
                shutil.copy2(page, os.path.join(BACKUP_DIR, f"{datetime.now():%Y%m%d-%H%M%S}__{rel.replace(os.sep, '__')}"))
                with open(page, "w", encoding="utf-8") as f:
                    f.write(new)
    print(f"\n{'Would fix' if dry_run else 'Fixed'} {done} page(s); {skipped} were already fixed.")
    for p in problems:
        print("  ! " + p)


if __name__ == "__main__":
    main()
