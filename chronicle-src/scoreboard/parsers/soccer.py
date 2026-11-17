"""
Soccer match summary in agate form:

    Earthquakes 2, Galaxy 1
    San Jose ............1 1 — 2
    Galaxy ..............0 1 — 1
    Goals—San Jose, Espinoza 4 (Wondolowski), 34th minute; ...
    Cautions—Galaxy, Pavon, 23rd.  Ejections—None.
    Lineups—San Jose: Marcinkowski; Beason, ... Subs: Lopez, Ebobisse.
"""

import re

from .common import NameBook, ordinal, ascii_text
from .game import game_header


def _minute(clock):
    """"34'" -> '34th', "90'+3'" -> '90th+3'."""
    nums = re.findall(r"\d+", str(clock or ""))
    if not nums:
        return ""
    s = ordinal(int(nums[0]))
    if len(nums) > 1:
        s += f"+{nums[1]}"
    return s


def parse(summary, league, event=None, featured=None):
    head = game_header(summary, league, event, featured)
    book = NameBook(sep=".")
    for r in summary.get("rosters", []):
        for p in r.get("roster", []):
            book.add_athlete(p.get("athlete"))

    teams = {str(head["away"]["team"].get("id")): head["away"]["city"],
             str(head["home"]["team"].get("id")): head["home"]["city"]}

    goals, cards, ejections = [], [], []
    for ev in summary.get("keyEvents") or summary.get("commentary") or []:
        t = ((ev.get("type") or {}).get("text") or "").lower()
        tid = str((ev.get("team") or {}).get("id"))
        names = [book.short((p.get("athlete") or {}).get("displayName", ""))
                 for p in ev.get("participants") or []]
        minute = _minute((ev.get("clock") or {}).get("displayValue"))
        city = teams.get(tid, "")
        if "goal" in t or "penalty - scored" in t:
            if not names:
                continue
            who = names[0]
            if "own goal" in t:
                who += " (own goal)"
            elif "penalty" in t:
                who += " (penalty kick)"
            elif len(names) > 1:
                who += f" ({names[1]})"
            goals.append(f"{city}, {who}, {minute}")
        elif ("red card" in t or "second yellow" in t) and names:
            ejections.append(f"{city}, {names[0]}, {minute}")
        elif "yellow" in t and names:
            cards.append(f"{city}, {names[0]}, {minute}")

    lineups = []
    for r in summary.get("rosters", []):
        city = teams.get(str((r.get("team") or {}).get("id")), "")
        roster = r.get("roster", [])
        starters = [p for p in roster if p.get("starter")]
        starters.sort(key=lambda p: (int(p.get("formationPlace") or 99)))
        subs = [p for p in roster if not p.get("starter") and p.get("subbedIn")]
        if not starters:
            continue
        s = ", ".join(book.short((p.get("athlete") or {}).get("displayName", ""))
                      for p in starters)
        if subs:
            s += ". Subs: " + ", ".join(
                book.short((p.get("athlete") or {}).get("displayName", "")) for p in subs)
        lineups.append(f"{city}: {s}")

    head.update(kind="soccer",
                goals="; ".join(goals) + "." if goals else "None.",
                cards="; ".join(cards) + "." if cards else "None.",
                ejections="; ".join(ejections) + "." if ejections else "None.",
                lineups=". ".join(lineups) + "." if lineups else "")
    return head
