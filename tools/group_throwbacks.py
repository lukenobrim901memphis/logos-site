#!/usr/bin/env python3
"""
Group the Throwback section on every MLB and Triple-A team page like the
Theme Night groups on the Triple-A pages: a heading for the year of the
design, the year(s) it was worn in smaller text under it, and the uniform
element ("Jersey", "Hat", ...) under each logo.

  1968 throwback      <- "1968 throwback jersey logo 2018.png"  (row "2018", card "Jersey")
  1969 throwback      <- "Throwback 1969 jersey logo 2014, 2019.png"
  1990s throwback     <- "1990s throwback jersey logo 2014.png"
  Other throwbacks    <- "Throwback weekend hat logo 2025.png"  (no design year)

The design year is the year in the NAME part of the file (not the years at the
end, which are when it was worn). Groups go oldest design first; files with no
design year come last. Needs the Throwback section (add_sections.py) first.

It also copies the theme night heading styles from triple-a-style.css into
mlb-style.css (once), so the MLB groups look the same.

Safe to run more than once; pages already grouped are skipped, and pages
grouped by the earlier version are switched to this layout. Every file it
changes is backed up to tools/backups/ first.

Usage:
  python3 group_throwbacks.py --dry-run
  python3 group_throwbacks.py
"""

import os
import re
import shutil
import sys
from datetime import datetime

SITE_DIR = "/Users/luke/logos-site"
TOOL_DIR = os.path.dirname(os.path.abspath(__file__))
BACKUP_DIR = os.path.join(TOOL_DIR, "backups")
LEAGUES = {"mlb-teams", "triple-a-teams"}
OTHER_HEADING = "Other throwbacks"

PATH_LINE = re.compile(r"""(const\s+path\s*=\s*["'][./]*images/([^/"']+)/[^"']*["'];?[ \t]*\n)""")
MLB_RULE = "document.getElementById('throwback').innerHTML += cardHtml;"
MILB_RULE = re.compile(r"""if \(lowerName\.includes\("throwback"\)\) targetGrid = 'throwback';[ \t]*\n([ \t]*)else if""")

HELPERS = r"""// THROWBACK_GROUPS v2: grouped by the year of the design, then by the year worn
const throwbackFiles = [];
function queueThrowback(fileName) { throwbackFiles.push(fileName); }
document.addEventListener('DOMContentLoaded', () => {
    const section = document.getElementById('throwback');
    if (!section || !throwbackFiles.length) return;
    section.classList.remove('grid');
    const groups = new Map();          // design year -> Map(years worn -> [cards])
    for (const fileName of throwbackFiles) {
        const base = fileName.replace(/\.png$/i, '');
        const end = base.match(/\s(\d{4}(?:-(?:\d{4}|present))?(?:,\s*\d{4}(?:-(?:\d{4}|present))?)*)\s*$/i);
        const namePart = end ? base.slice(0, end.index) : base;
        const worn = end ? end[1] : '';
        const design = namePart.match(/\b(\d{4}s?)\b/);
        const key = design ? design[1] : '';
        let label = namePart.replace(design ? design[1] : '', '').replace(/throwback/gi, '')
            .replace(/logo\d*/gi, '').replace(/\s+/g, ' ').trim();
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
        if (!groups.has(key)) groups.set(key, new Map());
        const rows = groups.get(key);
        if (!rows.has(worn)) rows.set(worn, []);
        rows.get(worn).push(card);
    }
    const byYear = (a, b) => (a === '') - (b === '') || parseInt(a) - parseInt(b) || a.localeCompare(b);
    section.innerHTML = [...groups.keys()].sort(byYear).map(k =>
        `\n    <h3 class="identity-header">${k ? k + ' throwback' : 'OTHER_HEADING'}</h3>` +
        [...groups.get(k).keys()].sort(byYear).map(w => `
    <div class="year-row-label">${w}</div>
    <div class="grid">${groups.get(k).get(w).join('')}</div>`).join('')
    ).join('');
});
""".replace("OTHER_HEADING", OTHER_HEADING)
OLD_HELPERS = re.compile(r"// THROWBACK_GROUPS.*?\n\}\);\n", re.DOTALL)

# Theme-night styles copied into mlb-style.css if it doesn't have them
STYLE_SOURCE = os.path.join(SITE_DIR, "triple-a-style.css")
STYLE_TARGETS = [os.path.join(SITE_DIR, "mlb-style.css")]
STYLE_RULE = re.compile(r"[^{}]*\.(?:identity-header|year-row-label)\b[^{}]*\{[^{}]*\}")


def group(text):
    if "THROWBACK_GROUPS v2" in text:
        return None, "already grouped"
    if "THROWBACK_GROUPS" in text:      # grouped by an earlier version: swap in the new layout
        return OLD_HELPERS.sub(lambda m: HELPERS, text, count=1), "updated to the theme-night layout"
    if 'id="throwback"' not in text:
        return None, "has no Throwback section (run add_sections.py first)"
    if MLB_RULE in text:
        text = text.replace(MLB_RULE, "queueThrowback(fileName);", 1)
    elif MILB_RULE.search(text):
        text = MILB_RULE.sub(lambda m: 'if (lowerName.includes("throwback")) { queueThrowback(fileName); return; }\n'
                                       + m.group(1) + "if", text, count=1)
    else:
        return None, "couldn't find the Throwback rule"
    m = PATH_LINE.search(text)
    return text[:m.end()] + HELPERS + text[m.end():], "grouped"


def copy_styles(dry_run):
    """Gives the MLB pages the same group heading / year-row look as the
    Triple-A theme nights, by copying those style rules across once."""
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
                f.write("\n\n/* Throwback groups (same look as the Triple-A theme nights) */\n" + "\n\n".join(rules) + "\n")


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
            print(f"{'(dry run) ' if dry_run else ''}{rel}: {'throwbacks grouped' if status == 'grouped' else status}")
            if not dry_run:
                os.makedirs(BACKUP_DIR, exist_ok=True)
                shutil.copy2(page, os.path.join(BACKUP_DIR, f"{datetime.now():%Y%m%d-%H%M%S}__{rel.replace(os.sep, '__')}"))
                with open(page, "w", encoding="utf-8") as f:
                    f.write(new)
    print(f"\n{'Would group' if dry_run else 'Grouped'} {done} page(s); {skipped} were already grouped.")
    copy_styles(dry_run)
    for p in problems:
        print("  ! " + p)


if __name__ == "__main__":
    main()
