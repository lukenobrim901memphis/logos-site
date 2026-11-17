#!/usr/bin/env python3
"""
Run this on your own machine (it needs to reach ESPN) to confirm the
parsers line up with today's live JSON:

    python tools/check_live.py                 # paper date = today (PT)
    python tools/check_live.py 2026-11-16      # any paper date
    python tools/check_live.py 2026-11-16 nhl  # one league, verbose

For each league it prints: events found, the stat-group labels ESPN sent,
whether the fields each parser relies on are present, and the parsed box
score. Anything marked MISSING is where ESPN's shape differs from what
the code expects — send me that output and it's a quick fix.
Raw JSON lands in cache/ so you can open it.
"""

import os
import sys
from datetime import date, timedelta

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
import espn                                   # noqa: E402
from leagues import LEAGUES                   # noqa: E402
from parsers import BOX_PARSERS               # noqa: E402
from parsers import standings as p_st         # noqa: E402
from parsers.common import today_pt, comp0, status_of  # noqa: E402

EXPECT = {
    "basketball": ["boxscore.players", "boxscore.teams", "header"],
    "hockey": ["boxscore.players", "boxscore.teams", "header", "plays|scoringPlays"],
    "football": ["boxscore.players", "boxscore.teams", "header", "scoringPlays"],
    "baseball": ["boxscore.players", "boxscore.teams", "header"],
    "soccer": ["rosters", "keyEvents|commentary", "header"],
}


def has(d, path):
    for alt in path.split("|"):
        cur, ok = d, True
        for part in alt.split("."):
            if isinstance(cur, dict) and cur.get(part):
                cur = cur[part]
            else:
                ok = False
                break
        if ok:
            return True
    return False


def main():
    pd = date.fromisoformat(sys.argv[1]) if len(sys.argv) > 1 else today_pt()
    only = sys.argv[2] if len(sys.argv) > 2 else None
    yd = pd - timedelta(days=1)
    print(f"Paper date {pd}, results from {yd}\n")
    for lg in LEAGUES:
        if only and lg["key"] != only:
            continue
        print(f"══ {lg['key']} ({lg['path']})")
        sb = espn.scoreboard(lg["path"], None if lg["kind"] in ("golf", "racing") else yd,
                             lg.get("scoreboard_params"))
        evs = sb.get("events", [])
        print(f"   scoreboard events: {len(evs)}")
        if lg.get("standings"):
            st = espn.standings(lg["path"], lg.get("standings_params"))
            parsed = p_st.parse(st, lg)
            print(f"   standings groups: {len(parsed['groups'])}"
                  + (f" (first: {parsed['groups'][0]['name']}, "
                     f"{[ (r['name'], [r[c] for c in parsed['columns']]) for r in parsed['groups'][0]['rows'][:2]]})"
                     if parsed["groups"] else "  <-- MISSING"))
        if lg["kind"] not in BOX_PARSERS:
            continue
        done = [e for e in evs if status_of(comp0(e) if comp0(e).get("status") else e)["completed"]]
        if not done:
            print("   no completed games to test a box score")
            continue
        ev = done[0]
        summ = espn.summary(lg["path"], ev["id"])
        for path in EXPECT[lg["kind"]]:
            print(f"   {path:28s} {'ok' if has(summ, path) else 'MISSING'}")
        for tp in (summ.get("boxscore") or {}).get("players", [])[:1]:
            for g in tp.get("statistics", []):
                print(f"   group {g.get('name') or g.get('type')!r}: labels={g.get('labels')}")
        try:
            b = BOX_PARSERS[lg["kind"]](summ, lg, ev, set())
            print(f"   parsed: {b['title']}")
            if only:
                import json
                print(json.dumps(b, indent=1, default=str)[:6000])
        except Exception as e:
            import traceback
            traceback.print_exc()
            print(f"   PARSE ERROR: {e}")
        print()


if __name__ == "__main__":
    main()
