"""
Everything that comes straight off a scoreboard: result lines, today's
schedule, and betting lines.
"""

import re
from datetime import date, datetime, timezone

from .common import (comp0, sides, status_of, final_suffix, team_city,
                     is_featured, to_int, to_float, rank_of, fmt_time, to_pt,
                     day_name, halves)


def _label(c, league, featured, with_rank):
    team = c.get("team") or {}
    name = team_city(team, league)
    r = rank_of(c) if with_rank else None
    return {"name": name, "rank": r, "featured": is_featured(team, featured)}


def result_line(ev, league, featured=None):
    """Winner first: {'w': {...}, 'ws': 7, 'l': {...}, 'ls': 5, 'suffix': 'OT'}"""
    comp = comp0(ev)
    st = status_of(comp if comp.get("status") else ev)
    away, home = sides(comp)
    college = bool(league.get("college"))
    a, h = _label(away, league, featured, college), _label(home, league, featured, college)
    if st["name"] in ("STATUS_POSTPONED", "STATUS_CANCELED", "STATUS_SUSPENDED") \
            or "postponed" in st["detail"].lower():
        return {"ppd": True, "text": f"{a['name']} at {h['name']}, ppd.",
                "featured": a["featured"] or h["featured"],
                "ranked": bool(a["rank"] or h["rank"])}
    if not st["completed"]:
        return None
    asc, hsc = to_int(away.get("score")), to_int(home.get("score"))
    w, ws, l, ls = (h, hsc, a, asc) if hsc > asc else (a, asc, h, hsc)
    if hsc == asc:                                       # soccer draws
        w, ws, l, ls = a, asc, h, hsc
    suf = final_suffix(st["detail"])
    if suf and suf.isdigit():
        suf = f"{suf} inn." if league.get("kind") == "baseball" else suf
    return {"w": w, "ws": ws, "l": l, "ls": ls, "suffix": suf,
            "featured": w["featured"] or l["featured"],
            "ranked": bool(w["rank"] or l["rank"]), "id": ev.get("id")}


def results(sb, league, featured=None):
    out = []
    for ev in (sb or {}).get("events", []):
        r = result_line(ev, league, featured)
        if r:
            out.append(r)
    out.sort(key=lambda r: (not r["featured"], r.get("ppd", False)))
    return out


def schedule(sb, league, featured=None, on_or_after=None, only_dates=None):
    """Group upcoming games by PT day: [{'day': "Monday's Games", 'games': [...]}]"""
    days = {}
    college = bool(league.get("college"))
    for ev in (sb or {}).get("events", []):
        comp = comp0(ev)
        st = status_of(comp if comp.get("status") else ev)
        if st["completed"] or st["state"] == "post":
            continue
        dt = to_pt(ev.get("date") or comp.get("date"))
        if not dt:
            continue
        d = dt.date()
        if on_or_after and d < on_or_after:
            continue
        if only_dates and d not in only_dates:
            continue
        away, home = sides(comp)
        a, h = _label(away, league, featured, college), _label(home, league, featured, college)
        tbd = comp.get("timeValid") is False or "TBD" in st["detail"]
        days.setdefault(d, []).append({
            "away": a, "home": h,
            "time": "TBA" if tbd else fmt_time(ev.get("date") or comp.get("date")),
            "sort": dt, "featured": a["featured"] or h["featured"],
            "ranked": bool(a["rank"] or h["rank"]),
            "neutral": comp.get("neutralSite", False),
        })
    out = []
    for d in sorted(days):
        games = sorted(days[d], key=lambda g: (not g["featured"], g["sort"]))   # Bay Area first
        n = len(games)
        out.append({"day": f"{day_name(d)}'s Game{'s' if n != 1 else ''}",
                    "date": d, "games": games})
    return out


def odds_lines(sb, league, featured=None, on_or_after=None, only_dates=None,
               ranked_only=False):
    """[{'fav': 'WARRIORS', 'line': '11½', 'ou': '226½', 'dog': 'Orlando'}]
    Home team in CAPS (Chronicle odds style)."""
    out = []
    college = bool(league.get("college"))
    for ev in (sb or {}).get("events", []):
        comp = comp0(ev)
        if status_of(comp if comp.get("status") else ev)["state"] != "pre":
            continue
        dt = to_pt(ev.get("date") or comp.get("date"))
        if dt and on_or_after and dt.date() < on_or_after:
            continue
        if dt and only_dates and dt.date() not in only_dates:
            continue
        odds = (comp.get("odds") or [None])[0]
        if not odds:
            continue
        away, home = sides(comp)
        a, h = _label(away, league, featured, college), _label(home, league, featured, college)
        if ranked_only and not (a["rank"] or h["rank"] or a["featured"] or h["featured"]):
            continue

        details = str(odds.get("details") or "")
        fav_home = None
        if (odds.get("homeTeamOdds") or {}).get("favorite"):
            fav_home = True
        elif (odds.get("awayTeamOdds") or {}).get("favorite"):
            fav_home = False
        else:
            ab = details.split(" ")[0].upper()
            if ab == ((home.get("team") or {}).get("abbreviation") or "").upper():
                fav_home = True
            elif ab == ((away.get("team") or {}).get("abbreviation") or "").upper():
                fav_home = False

        if details.upper() in ("EVEN", "PK", "PICK"):
            line, fav_home = "Pk", True if fav_home is None else fav_home
        else:
            m = re.search(r"([-+]?\d+(?:\.\d+)?)\s*$", details)
            num = to_float(m.group(1)) if m else to_float(odds.get("spread"))
            if num is None:
                continue
            # moneyline sports (MLB/NHL): keep the sign, e.g. -150
            line = (str(int(num)) if abs(num) >= 100 else halves(abs(num)))
        if fav_home is None:
            continue
        ou = to_float(odds.get("overUnder"))
        hname = h["name"].upper()
        fav_side, dog_side = (h, a) if fav_home else (a, h)
        fav, dog = (hname, a["name"]) if fav_home else (a["name"], hname)
        out.append({"fav": fav, "line": line, "ou": halves(ou) if ou else "",
                    "dog": dog, "day": day_name(dt.date()) if dt else "",
                    "fav_feat": fav_side["featured"], "dog_feat": dog_side["featured"],
                    "featured": a["featured"] or h["featured"],
                    "_date": dt.date() if dt else None, "_time": dt})
    # group by day, Bay Area games first within each day, then by start time
    out.sort(key=lambda o: (o["_date"] or date.min, not o["featured"],
                            o["_time"] or datetime.min.replace(tzinfo=timezone.utc)))
    for o in out:
        del o["_date"], o["_time"]
    return out
