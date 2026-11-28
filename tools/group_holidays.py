#!/usr/bin/env python3
"""
Group the Holiday section on every MLB and NBA team page like the Theme Night
groups on the Triple-A pages: a heading for each holiday, the year(s) it was
worn in smaller text under it, and the uniform element under each logo.

  Mother's Day          <- "Mother's Day hat logo 2016.png"          (row "2016", card "Hat")
  4th of July           <- "Home 4th of July jersey logo 2017.png"   (row "2017", card "Home jersey")
  Memorial Day          <- "Road gray Memorial Day jersey logo 2014.png"

Holidays are listed in calendar order (HOLIDAYS below — add more there).
Anything in the Holiday section that matches none of them goes under "Other".

It also copies the theme night heading styles from triple-a-style.css into
mlb-style.css and nba-style.css (once), so the groups look the same.

Safe to run more than once; pages already grouped are skipped. Every file it
changes is backed up to tools/backups/ first.

Usage:
  python3 group_holidays.py --dry-run
  python3 group_holidays.py
"""

import json
import os
import re
import shutil
import sys
from datetime import datetime

SITE_DIR = "/Users/luke/logos-site"
TOOL_DIR = os.path.dirname(os.path.abspath(__file__))
BACKUP_DIR = os.path.join(TOOL_DIR, "backups")
LEAGUES = {"mlb-teams", "nba-teams"}

# (heading, pattern that finds it in a file name — removed from the card label)
# in the order they should appear on the page
HOLIDAYS = [
    ("Chinese New Year",  r"chinese new year"),
    ("Lunar New Year",    r"lunar new year"),
    ("Mardi Gras",        r"mardi gras"),
    ("St. Patrick's Day", r"st\.? ?patrick'?s?(?: day)?"),
    ("Mother's Day",      r"mother'?s?(?: day)?"),
    ("Armed Forces",      r"armed forces(?: day| weekend)?"),
    ("Memorial Day",      r"memorial day"),
    ("Father's Day",      r"father'?s?(?: day)?"),
    ("4th of July",       r"(?:4th of )?july|independence day"),
    ("Noche Latina",      r"noche latina"),
    ("Military",          r"military(?: appreciation)?"),
    ("Christmas",         r"christmas"),
]
OTHER_HEADING = "Other"

PATH_LINE = re.compile(r"""(const\s+path\s*=\s*["'][./]*images/([^/"']+)/[^"']*["'];?[ \t]*\n)""")
RULE = "document.getElementById('holiday').innerHTML += cardHtml;"

HELPERS = r"""// HOLIDAY_GROUPS v1: the Holiday section is grouped by holiday, then by the year worn
const HOLIDAY_LIST = HOLIDAY_JSON;
const holidayFiles = [];
function queueHoliday(fileName) { holidayFiles.push(fileName); }
document.addEventListener('DOMContentLoaded', () => {
    const section = document.getElementById('holiday');
    if (!section || !holidayFiles.length) return;
    section.classList.remove('grid');
    const groups = new Map();          // holiday index -> Map(years worn -> [cards])
    for (const fileName of holidayFiles) {
        const base = fileName.replace(/\.png$/i, '');
        const end = base.match(/\s(\d{4}(?:-(?:\d{4}|present))?(?:,\s*\d{4}(?:-(?:\d{4}|present))?)*)\s*$/i);
        const namePart = end ? base.slice(0, end.index) : base;
        const worn = end ? end[1] : '';
        let idx = HOLIDAY_LIST.findIndex(h => new RegExp(h[1], 'i').test(namePart));
        let label = namePart;
        if (idx >= 0) label = label.replace(new RegExp(HOLIDAY_LIST[idx][1], 'i'), '');
        else idx = HOLIDAY_LIST.length;
        label = label.replace(/logo\d*/gi, '').replace(/\s+/g, ' ').trim();
        label = label ? label[0].toUpperCase() + label.slice(1) : '';
        const card = `
        <div class="logo-card" onclick="openLightbox('${path}${fileName}')">
            <div class="logo-image-wrapper">
                <img src="${path}${fileName}" alt="${base}" loading="lazy">
            </div>
            <div class="logo-caption">
                <div class="logo-name">${label}</div>
            </div>
        </div>`;
        if (!groups.has(idx)) groups.set(idx, new Map());
        const rows = groups.get(idx);
        if (!rows.has(worn)) rows.set(worn, []);
        rows.get(worn).push(card);
    }
    const byYear = (a, b) => (a === '') - (b === '') || parseInt(a) - parseInt(b) || a.localeCompare(b);
    section.innerHTML = [...groups.keys()].sort((a, b) => a - b).map(i =>
        `\n    <h3 class="identity-header">${i < HOLIDAY_LIST.length ? HOLIDAY_LIST[i][0] : 'OTHER_HEADING'}</h3>` +
        [...groups.get(i).keys()].sort(byYear).map(w => `
    <div class="year-row-label">${w}</div>
    <div class="grid">${groups.get(i).get(w).join('')}</div>`).join('')
    ).join('');
});
""".replace("HOLIDAY_JSON", json.dumps(HOLIDAYS)).replace("OTHER_HEADING", OTHER_HEADING)

STYLE_SOURCE = os.path.join(SITE_DIR, "triple-a-style.css")
STYLE_TARGETS = [os.path.join(SITE_DIR, "mlb-style.css"), os.path.join(SITE_DIR, "nba-style.css")]
STYLE_RULE = re.compile(r"[^{}]*\.(?:identity-header|year-row-label)\b[^{}]*\{[^{}]*\}")


def group(text):
    if "HOLIDAY_GROUPS" in text:
        return None, "already grouped"
    if 'id="holiday"' not in text:
        return None, "has no Holiday section"
    if RULE not in text:
        return None, "couldn't find the Holiday rule"
    text = text.replace(RULE, "queueHoliday(fileName);", 1)
    m = PATH_LINE.search(text)
    return text[:m.end()] + HELPERS + text[m.end():], "grouped"


def copy_styles(dry_run):
    if not os.path.exists(STYLE_SOURCE):
        print(f"  ! {os.path.basename(STYLE_SOURCE)} not found — group headings use the page's default style")
        return
    rules = [r.strip() for r in STYLE_RULE.findall(open(STYLE_SOURCE, encoding="utf-8").read())]
    if not rules:
        print(f"  ! no .identity-header / .year-row-label styles in {os.path.basename(STYLE_SOURCE)} to copy")
        return
    for target in STYLE_TARGETS:
        if not os.path.exists(target):
            continue
        css = open(target, encoding="utf-8").read()
        if ".identity-header" in css or ".year-row-label" in css:
            continue
        print(f"{'(dry run) ' if dry_run else ''}{os.path.basename(target)}: added the theme night heading styles")
        if not dry_run:
            os.makedirs(BACKUP_DIR, exist_ok=True)
            shutil.copy2(target, os.path.join(BACKUP_DIR, f"{datetime.now():%Y%m%d-%H%M%S}__{os.path.basename(target)}"))
            with open(target, "a", encoding="utf-8") as f:
                f.write("\n\n/* Holiday / throwback groups (same look as the Triple-A theme nights) */\n"
                        + "\n\n".join(rules) + "\n")


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
            new, status = group(text)
            if new is None:
                if status == "already grouped":
                    skipped += 1
                else:
                    problems.append(f"{rel}: {status} — not changed")
                continue
            done += 1
            print(f"{'(dry run) ' if dry_run else ''}{rel}: holidays grouped")
            if not dry_run:
                os.makedirs(BACKUP_DIR, exist_ok=True)
                shutil.copy2(page, os.path.join(BACKUP_DIR, f"{datetime.now():%Y%m%d-%H%M%S}__{rel.replace(os.sep, '__')}"))
                with open(page, "w", encoding="utf-8") as f:
                    f.write(new)
    print(f"\n{'Would group' if dry_run else 'Grouped'} {done} page(s); {skipped} were already grouped.")
    for p in problems:
        print("  ! " + p)
    copy_styles(dry_run)


if __name__ == "__main__":
    main()
