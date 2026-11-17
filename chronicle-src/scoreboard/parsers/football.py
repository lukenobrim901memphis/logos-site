"""
Football box score (NFL / college) in Chronicle form:

    Lions 38, Browns 24
    Cleveland .....3 10  0 11 — 24
    Detroit .......7 10  14 7 — 38
    First Quarter
    Cle—FG Gonzalez 23, 11:30.
    Det—Abdullah 3 run (Prater kick), 3:55.
    ...
    A—61,524.
                       Cle    Det
    First downs         18     25
    ...
    INDIVIDUAL STATISTICS
    RUSHING—Cleveland, Crowell 16-50 ...
"""

import re

from .common import (NameBook, abbr_style, stat_index, team_by_id, ascii_text,
                     made_att, to_int)
from .game import game_header

QUARTERS = {1: "First Quarter", 2: "Second Quarter", 3: "Third Quarter",
            4: "Fourth Quarter"}

# (ESPN team-stat name, our label), in Chronicle order
TEAM_STAT_ROWS = [
    ("firstDowns", "First downs"),
    ("totalYards", "Total yards"),
    ("rushingAttempts|rushingYards", "Rushes-yds"),
    ("netPassingYards", "Passing"),
    ("completionAttempts", "Comp-Att-Int"),
    ("sacksYardsLost", "Sacked-yds"),
    ("thirdDownEff", "3rd-down eff."),
    ("fourthDownEff", "4th-down eff."),
    ("fumblesLost", "Fumbles-Lost"),
    ("totalPenaltiesYards", "Penalties-yds"),
    ("turnovers", "Turnovers"),
    ("possessionTime", "Time of Possession"),
]

LOWER = {"Run", "Pass", "From", "Kick", "Interception", "Return", "Fumble",
         "Recovery", "Punt", "Kickoff", "Blocked", "Failed", "Rush", "To",
         "For", "Two-Point", "Conversion", "Missed", "Field", "Goal", "Yard",
         "Safety", "Lateral", "Recovered", "In", "End", "Zone", "Kicked"}


def chron_scoring_text(text, book):
    """'Jahmyr Gibbs 5 Yd Run (Jake Bates Kick)' -> 'Gibbs 5 run (Bates kick)'
       'Jake Bates 48 Yd Field Goal'           -> 'FG Bates 48'"""
    t = ascii_text(text)
    fg = re.match(r"^(.+?)\s+(\d+)\s+(?:Yd|Yard)s?\s+Field Goal", t, re.I)
    if fg:
        return f"FG {book.short(fg.group(1).strip())} {fg.group(2)}"
    # names ESPN didn't list in the stat groups (kickers, defenders)
    t = re.sub(r"\(([A-Z][^()]*?) Kick\)", lambda m: f"({book.short(m.group(1))} Kick)", t)
    t = re.sub(r"^([A-Z][\w.'\-]+(?: [A-Z][\w.'\-]+)+) (\d+)",
               lambda m: f"{book.short(m.group(1))} {m.group(2)}", t)
    t = re.sub(r"(pass from) ([A-Z][\w.'\-]+(?: [A-Z][\w.'\-]+)+?)(?=\s*\(|$)",
               lambda m: f"{m.group(1)} {book.short(m.group(2))}", t, flags=re.I)
    t = book.replace_in(t)
    t = re.sub(r"\s+(?:Yd|Yds|Yard|Yards)\b\.?", "", t)
    # two-point tries: '(Goff Pass to St. Brown for Two-Point Conversion)'
    t = re.sub(r"\((.+?) Pass to (.+?) for Two-Point Conversion\)",
               r"(\2 pass from \1)", t, flags=re.I)
    t = re.sub(r"\((.+?) Run for Two-Point Conversion\)", r"(\1 run)", t, flags=re.I)
    t = " ".join(w.lower() if w.strip("()") in LOWER else w for w in t.split())
    t = re.sub(r"\(([^)]*?)\bkick\b\)", r"(\1kick)", t)
    return t


def _groups(tp):
    out = {}
    for g in tp.get("statistics", []):
        out[(g.get("name") or g.get("type") or "").lower()] = g
    return out


def _ath_rows(group, book):
    labels = [str(x).upper() for x in (group.get("labels") or [])]
    for a in group.get("athletes", []):
        stats = a.get("stats") or []
        if not stats:
            continue
        name = book.short((a.get("athlete") or {}).get("displayName", ""))
        yield name, dict(zip(labels, stats))


def parse(summary, league, event=None, featured=None):
    head = game_header(summary, league, event, featured)
    box = summary.get("boxscore") or {}

    book = NameBook(sep=".")
    for tp in box.get("players", []):
        for g in tp.get("statistics", []):
            for a in g.get("athletes", []):
                book.add_athlete(a.get("athlete"))

    # ── Scoring summary ───────────────────────────────────────────────────
    quarters = {}
    for sp in summary.get("scoringPlays", []):
        per = (sp.get("period") or {}).get("number") or 0
        team = sp.get("team") or {}
        ab = abbr_style(team.get("abbreviation", ""))
        clock = (sp.get("clock") or {}).get("displayValue", "")
        text = chron_scoring_text(sp.get("text", ""), book)
        quarters.setdefault(per, []).append(f"{ab}—{text}, {clock}.")
    scoring = [{"name": QUARTERS.get(q, "Overtime" if q == 5 else f"{q - 4}OT"),
                "plays": quarters[q]} for q in sorted(quarters)]

    # ── Team statistics ───────────────────────────────────────────────────
    away_id = str(head["away"]["team"].get("id"))
    home_id = str(head["home"]["team"].get("id"))
    ta = stat_index(team_by_id(summary, away_id).get("statistics"))
    th = stat_index(team_by_id(summary, home_id).get("statistics"))
    ints = {away_id: ta.get("interceptions", "0"), home_id: th.get("interceptions", "0")}

    def val(idx, key, tid):
        if "|" in key:
            a, b = key.split("|")
            if a.lower() in idx or b.lower() in idx:
                return f"{idx.get(a.lower(), '')}-{idx.get(b.lower(), '')}"
            return None
        v = idx.get(key.lower())
        if v is None:
            return None
        if key == "completionAttempts":
            c, at = made_att(v)
            # interceptions *thrown* = the other team's interceptions
            other = home_id if tid == away_id else away_id
            return f"{c}-{at}-{ints.get(other, 0)}"
        return str(v).replace("/", "-")

    team_stats = []
    for key, label in TEAM_STAT_ROWS:
        va, vh = val(ta, key, away_id), val(th, key, home_id)
        if va is None and vh is None:
            continue
        team_stats.append((label, va or "", vh or ""))

    # ── Individual statistics ─────────────────────────────────────────────
    order = {away_id: 0, home_id: 1}
    players = sorted(box.get("players", []),
                     key=lambda tp: order.get(str((tp.get("team") or {}).get("id")), 9))
    sections = {"RUSHING": [], "PASSING": [], "RECEIVING": []}
    for tp in players:
        tid = str((tp.get("team") or {}).get("id"))
        city = head["away"]["city"] if tid == away_id else head["home"]["city"]
        g = _groups(tp)
        rush = [f"{n} {d.get('CAR', 0)}-{d.get('YDS', 0)}"
                for n, d in _ath_rows(g.get("rushing", {}), book)]
        pas = []
        for n, d in _ath_rows(g.get("passing", {}), book):
            c, at = made_att(d.get("C/ATT", "0/0"))
            pas.append(f"{n} {c}-{at}-{to_int(d.get('INT'))}-{d.get('YDS', 0)}")
        rec = [f"{n} {d.get('REC', 0)}-{d.get('YDS', 0)}"
               for n, d in _ath_rows(g.get("receiving", {}), book)
               if to_int(d.get("REC")) > 0]            # only players with a catch
        for key, lst in (("RUSHING", rush), ("PASSING", pas), ("RECEIVING", rec)):
            if lst:
                sections[key].append(f"{city}, " + ", ".join(lst))
    individual = [(k, ". ".join(v) + ".") for k, v in sections.items() if v]

    head.update(kind="football", scoring=scoring, team_stats=team_stats,
                abbr_away=abbr_style(head["away"]["team"].get("abbreviation", "")),
                abbr_home=abbr_style(head["home"]["team"].get("abbreviation", "")),
                individual=individual)
    return head
