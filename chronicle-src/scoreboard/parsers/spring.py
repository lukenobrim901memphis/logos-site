"""
MLB spring training, Chronicle style:

    Spring Training
    NATIONAL LEAGUE            W  L  Pct
    Pittsburgh                 7  2  .778
    ...
    Saturday's Games
    Kansas City (ss) 2, Giants 0
    Washington 1, St. Louis 1
    Sunday's Games
    Kansas City vs. Giants at Scottsdale, Ariz., 12:05 p.m.

Standings are counted from every spring game so far (ESPN scoreboard date
range), only games between two major league teams, ties left out of W-L.
"""

from .common import (comp0, sides, status_of, to_int, team_city, is_featured,
                     to_pt, fmt_time, day_name, ascii_text)

# Every MLB club by ESPN displayName -> league (spring games against college,
# national or minor league teams don't count in the standings)
LEAGUE_OF = {
    "Arizona Diamondbacks": "NL", "Atlanta Braves": "NL", "Chicago Cubs": "NL",
    "Cincinnati Reds": "NL", "Colorado Rockies": "NL", "Los Angeles Dodgers": "NL",
    "Miami Marlins": "NL", "Milwaukee Brewers": "NL", "New York Mets": "NL",
    "Philadelphia Phillies": "NL", "Pittsburgh Pirates": "NL", "San Diego Padres": "NL",
    "San Francisco Giants": "NL", "St. Louis Cardinals": "NL", "Washington Nationals": "NL",
    "Athletics": "AL", "Oakland Athletics": "AL", "Baltimore Orioles": "AL",
    "Boston Red Sox": "AL", "Chicago White Sox": "AL", "Cleveland Guardians": "AL",
    "Detroit Tigers": "AL", "Houston Astros": "AL", "Kansas City Royals": "AL",
    "Los Angeles Angels": "AL", "Minnesota Twins": "AL", "New York Yankees": "AL",
    "Seattle Mariners": "AL", "Tampa Bay Rays": "AL", "Texas Rangers": "AL",
    "Toronto Blue Jays": "AL",
}

# AP state abbreviations (spring sites are almost all Ariz./Fla., but
# exhibitions turn up elsewhere)
AP_STATE = {
    "AZ": "Ariz.", "ARIZONA": "Ariz.", "FL": "Fla.", "FLORIDA": "Fla.",
    "CA": "Calif.", "CALIFORNIA": "Calif.", "NV": "Nev.", "NEVADA": "Nev.",
    "TX": "Texas", "TEXAS": "Texas", "NY": "N.Y.", "NEW YORK": "N.Y.",
    "GA": "Ga.", "GEORGIA": "Ga.", "LA": "La.", "LOUISIANA": "La.",
    "NC": "N.C.", "NORTH CAROLINA": "N.C.", "TN": "Tenn.", "TENNESSEE": "Tenn.",
    "UT": "Utah", "UTAH": "Utah", "CO": "Colo.", "COLORADO": "Colo.",
    "OK": "Okla.", "OKLAHOMA": "Okla.", "NM": "N.M.", "NEW MEXICO": "N.M.",
}


def is_preseason(*sbs):
    """True if ESPN says MLB is in spring training (season type 1)."""
    for sb in sbs:
        for lg in (sb or {}).get("leagues", []):
            t = ((lg.get("season") or {}).get("type") or {}).get("type")
            if str(t) == "1":
                return True
        for ev in (sb or {}).get("events", []):
            st = ev.get("season") or {}
            if str(st.get("type")) == "1" or st.get("slug") == "preseason":
                return True
    return False


def _spring_events(sb):
    for ev in (sb or {}).get("events", []):
        st = ev.get("season") or {}
        if st and str(st.get("type", "1")) != "1" and st.get("slug") not in (None, "preseason"):
            continue                                   # regular season / postseason
        yield ev


def standings(range_sb, league, featured=None):
    rec = {}
    for ev in _spring_events(range_sb):
        comp = comp0(ev)
        if not status_of(comp if comp.get("status") else ev)["completed"]:
            continue
        away, home = sides(comp)
        ta, th = away.get("team") or {}, home.get("team") or {}
        na, nh = ascii_text(ta.get("displayName", "")), ascii_text(th.get("displayName", ""))
        if na not in LEAGUE_OF or nh not in LEAGUE_OF:
            continue                                   # vs. a non-MLB team
        sa, sh = to_int(away.get("score")), to_int(home.get("score"))
        if sa == sh:
            continue                                   # ties don't count
        for t, name, won in ((ta, na, sa > sh), (th, nh, sh > sa)):
            r = rec.setdefault(name, {"team": t, "W": 0, "L": 0})
            r["W" if won else "L"] += 1

    groups = []
    for lg_code, title in (("NL", "National League"), ("AL", "American League")):
        rows = []
        for name, r in rec.items():
            if LEAGUE_OF[name] != lg_code:
                continue
            gp = r["W"] + r["L"]
            pct = r["W"] / gp if gp else 0
            rows.append({"name": team_city(r["team"], league),
                         "featured": is_featured(r["team"], featured),
                         "W": r["W"], "L": r["L"],
                         "Pct": "1.000" if pct >= 1 else f".{round(pct * 1000):03d}",
                         "_pct": pct})
        rows.sort(key=lambda x: (-x["_pct"], -x["W"], x["name"]))
        if rows:
            groups.append({"conference": title, "name": "", "rows": rows})
    return {"columns": ["W", "L", "Pct"], "groups": groups, "note": ""} if groups else None


def _split_squads(events):
    """Team ids that play more than once that day -> '(ss)'."""
    count = {}
    for ev in events:
        for c in comp0(ev).get("competitors", []):
            tid = str((c.get("team") or {}).get("id"))
            count[tid] = count.get(tid, 0) + 1
    return {tid for tid, n in count.items() if n > 1}


def _label(c, league, featured, ss):
    team = c.get("team") or {}
    return {"name": team_city(team, league), "featured": is_featured(team, featured),
            "ss": str(team.get("id")) in ss}


def results(sb, league, featured=None):
    events = list(_spring_events(sb))
    ss = _split_squads(events)
    out = []
    for ev in events:
        comp = comp0(ev)
        st = status_of(comp if comp.get("status") else ev)
        away, home = sides(comp)
        a, h = _label(away, league, featured, ss), _label(home, league, featured, ss)
        if "postponed" in st["detail"].lower() or "cancel" in st["detail"].lower():
            out.append({"ppd": True, "text": f"{a['name']} vs. {h['name']}, "
                                             f"{'ccd.' if 'cancel' in st['detail'].lower() else 'ppd.'}",
                        "featured": a["featured"] or h["featured"]})
            continue
        if not st["completed"]:
            continue
        sa, sh = to_int(away.get("score")), to_int(home.get("score"))
        if sh > sa:
            w, ws, l, ls = h, sh, a, sa
        else:                                          # away win, or a tie as listed
            w, ws, l, ls = a, sa, h, sh
        out.append({"w": w, "ws": ws, "l": l, "ls": ls, "suffix": "",
                    "featured": a["featured"] or h["featured"]})
    out.sort(key=lambda r: not r["featured"])          # Bay Area first
    return out


def _where(comp):
    addr = (comp.get("venue") or {}).get("address") or {}
    city = ascii_text(addr.get("city", ""))
    state = addr.get("state", "")
    state = AP_STATE.get(state.upper(), state)
    return ", ".join(x for x in (city, state) if x)


def schedule(sb, league, featured=None, on_date=None):
    events = [ev for ev in _spring_events(sb)]
    ss = _split_squads(events)
    games = []
    for ev in events:
        comp = comp0(ev)
        st = status_of(comp if comp.get("status") else ev)
        if st["completed"] or st["state"] == "post":
            continue
        dt = to_pt(ev.get("date") or comp.get("date"))
        if on_date and dt and dt.date() != on_date:
            continue
        away, home = sides(comp)
        games.append({"away": _label(away, league, featured, ss),
                      "home": _label(home, league, featured, ss),
                      "where": _where(comp),
                      "time": "TBA" if comp.get("timeValid") is False
                              else fmt_time(ev.get("date") or comp.get("date")),
                      "featured": is_featured(away.get("team"), featured)
                                  or is_featured(home.get("team"), featured),
                      "sort": dt})
    games.sort(key=lambda g: (not g["featured"], g["sort"].timestamp() if g["sort"] else 0))
    if not games:
        return []
    n = len(games)
    return [{"day": f"{day_name(on_date)}'s Game{'s' if n != 1 else ''}" if on_date else "Today's Games",
             "games": games}]
