#!/usr/bin/env python3
"""
Group the Negro League section on every MLB team page like the Throwback
groups: a heading for each Negro League team, the year(s) it was worn in
smaller text under it, and the uniform element under each logo.

  1926 Chicago American Giants <- "1926 Chicago American Giants Negro League jersey logo 2021.png"
                                  (row "2021", card "Jersey")
  1910s Lelands                <- "Negro League Lelands 1910s jersey logo 2017.png"
  KC Feds                      <- "KC Feds Negro League jersey logo 2014.png"  (no design year)

The heading is the year of the design (anywhere in the name part, not the
years worn at the end) followed by the team. Groups are listed by the first
year the MLB team wore them (the years at the end of the file name).

The team is the text before "Negro League"; if there is none, the text after
it, up to the uniform element (jersey, hat, patch, ...). Files with no team
name go under "Other", at the end. Needs the Negro
League section (add_sections.py) first.

Safe to run more than once; pages already grouped are skipped. Every page it
changes is backed up to tools/backups/ first.

Usage:
  python3 group_negro_league.py --dry-run
  python3 group_negro_league.py
"""

import os
import re
import shutil
import sys
from datetime import datetime

SITE_DIR = "/Users/luke/logos-site"
TOOL_DIR = os.path.dirname(os.path.abspath(__file__))
BACKUP_DIR = os.path.join(TOOL_DIR, "backups")
LEAGUES = {"mlb-teams"}
OTHER_HEADING = "Other"

PATH_LINE = re.compile(r"""(const\s+path\s*=\s*["'][./]*images/([^/"']+)/[^"']*["'];?[ \t]*\n)""")
RULE = "document.getElementById('negro-league').innerHTML += cardHtml;"

HELPERS = r"""// NEGRO_LEAGUE_GROUPS v4: grouped by "<design year> <team>", ordered by when the MLB team wore it
const negroLeagueFiles = [];
function queueNegroLeague(fileName) { negroLeagueFiles.push(fileName); }
document.addEventListener('DOMContentLoaded', () => {
    const section = document.getElementById('negro-league');
    if (!section || !negroLeagueFiles.length) return;
    section.classList.remove('grid');
    const ELEMENT = /\b(home|road|alt|alternate|batting|sleeve|jersey|hat|cap|helmet|patch|pants?|socks?)\b/i;
    const tidy = t => t.replace(/logo\d*/gi, '').replace(/\s+/g, ' ').trim();
    const groups = new Map();          // team -> Map(years worn -> [cards])
    for (const fileName of negroLeagueFiles) {
        const base = fileName.replace(/\.png$/i, '');
        const end = base.match(/\s(\d{4}(?:-(?:\d{4}|present))?(?:,\s*\d{4}(?:-(?:\d{4}|present))?)*)\s*$/i);
        const namePart = end ? base.slice(0, end.index) : base;
        const worn = end ? end[1] : '';
        const nl = namePart.match(/negro leagues?/i);
        let team = '', label = namePart;
        if (nl) {
            const before = tidy(namePart.slice(0, nl.index));
            const after = tidy(namePart.slice(nl.index + nl[0].length));
            // A team name before "Negro League" ("KC Feds Negro League jersey"); if all that's
            // there is a year ("1910s Negro League Lelands jersey"), the team comes after it
            if (tidy(before.replace(/\b\d{4}s?\b/, ''))) { team = before; label = after; }
            else {
                const el = after.match(ELEMENT);
                team = tidy(before + ' ' + (el ? after.slice(0, el.index) : ''));
                label = el ? after.slice(el.index) : after;
            }
        }
        // The design year (in the name, not the years worn at the end) goes first in the heading
        const yr = (team + ' ' + label).match(/\b(\d{4}s?)\b/);
        if (yr) { team = tidy(team.replace(yr[1], '')); label = label.replace(yr[1], ''); }
        team = team ? team[0].toUpperCase() + team.slice(1) : '';
        team = [yr ? yr[1] : '', team].join(' ').trim();
        label = tidy(label);
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
        if (!groups.has(team)) groups.set(team, new Map());
        const rows = groups.get(team);
        if (!rows.has(worn)) rows.set(worn, []);
        rows.get(worn).push(card);
    }
    const byYear = (a, b) => (a === '') - (b === '') || parseInt(a) - parseInt(b) || a.localeCompare(b);
    // Groups are listed by the first year the MLB team wore them; ties by design year, then name
    const firstWorn = t => Math.min(...[...groups.get(t).keys()].map(w => parseInt(w) || Infinity));
    const designYear = t => { const m = t.match(/^(\d{4})/); return m ? parseInt(m[1]) : Infinity; };
    const byTeam = (a, b) => (a === '') - (b === '') || firstWorn(a) - firstWorn(b)
        || designYear(a) - designYear(b) || a.localeCompare(b);
    section.innerHTML = [...groups.keys()].sort(byTeam).map(t =>
        `\n    <h3 class="identity-header">${t || 'OTHER_HEADING'}</h3>` +
        [...groups.get(t).keys()].sort(byYear).map(w => `
    <div class="year-row-label">${w}</div>
    <div class="grid">${groups.get(t).get(w).join('')}</div>`).join('')
    ).join('');
});
""".replace("OTHER_HEADING", OTHER_HEADING)


OLD_HELPERS = re.compile(r"// NEGRO_LEAGUE_GROUPS.*?\n\}\);\n", re.DOTALL)


def group(text):
    if "NEGRO_LEAGUE_GROUPS v4" in text:
        return None, "already grouped"
    if "NEGRO_LEAGUE_GROUPS" in text:      # grouped by the earlier version: swap in the new headings
        return OLD_HELPERS.sub(lambda m: HELPERS, text, count=1), "updated headings"
    if 'id="negro-league"' not in text:
        return None, "has no Negro League section (run add_sections.py first)"
    if RULE not in text:
        return None, "couldn't find the Negro League rule"
    text = text.replace(RULE, "queueNegroLeague(fileName);", 1)
    m = PATH_LINE.search(text)
    return text[:m.end()] + HELPERS + text[m.end():], "grouped"


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
            print(f"{'(dry run) ' if dry_run else ''}{rel}: {'Negro League grouped' if status == 'grouped' else status}")
            if not dry_run:
                os.makedirs(BACKUP_DIR, exist_ok=True)
                shutil.copy2(page, os.path.join(BACKUP_DIR, f"{datetime.now():%Y%m%d-%H%M%S}__{rel.replace(os.sep, '__')}"))
                with open(page, "w", encoding="utf-8") as f:
                    f.write(new)
    print(f"\n{'Would group' if dry_run else 'Grouped'} {done} page(s); {skipped} were already grouped.")
    for p in problems:
        print("  ! " + p)


if __name__ == "__main__":
    main()
