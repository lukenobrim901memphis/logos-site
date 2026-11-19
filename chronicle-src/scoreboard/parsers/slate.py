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
        suf = f"{suf} inn." if league.get("kind") == "baseball" or league.get("innings") else suf
    return {"w": w, "ws": ws, "l": l, "ls": ls, "suffix": suf,
            "featured": w["featured"] or l["featured"],
            "ranked": bool(w["rank"] or l["rank"]), "id": ev.get("id"),
            "division": ev.get("_division", "")}


def results(sb, league, featured=None):
    out = []
    for ev in (sb or {}).get("events", []):
        r = result_line(ev, league, featured)
        if r:
            out.append(r)
    out.sort(key=lambda r: (not r["featured"], r.get("ppd", False)))
    return out


def schedule(sb, league, featured=None, on_or_after=None, only_dates=None, by_date_only=False):
    """Group upcoming games by PT day: [{'day': "Monday's Games", 'games': [...]}]"""
    days = {}
    college = bool(league.get("college"))
    for ev in (sb or {}).get("events", []):
        comp = comp0(ev)
        st = status_of(comp if comp.get("status") else ev)
        if not by_date_only and (st["completed"] or st["state"] == "post"):
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


# ── NFL weeks ────────────────────────────────────────────────────────────────
# Between weeks: last week's scores + next week's schedule.
# Once a week's first game is played: that week's scores + its remaining games.

def _week_key(ev):
    if ev.get("_wk"):
        return tuple(ev["_wk"])
    season = ev.get("season") or {}
    week = ev.get("week") or {}
    try:
        return (int(season.get("type", 2)), int(week.get("number", 0)))
    except (TypeError, ValueError):
        return None


def nfl_calendar(sb):
    """[(season type, week), first day, last day] from ESPN's NFL calendar,
    plus the season year."""
    weeks, year = [], None
    for lg in (sb or {}).get("leagues", []):
        year = year or (lg.get("season") or {}).get("year")
        for sect in lg.get("calendar") or []:
            if not isinstance(sect, dict):
                continue
            try:
                stype = int(sect.get("value"))
            except (TypeError, ValueError):
                continue
            for e in sect.get("entries") or []:
                start, end = to_pt(e.get("startDate")), to_pt(e.get("endDate"))
                try:
                    num = int(e.get("value"))
                except (TypeError, ValueError):
                    continue
                if start and end:
                    weeks.append(((stype, num), start.date(), end.date()))
    return weeks, year


_POST_WEEKS = {1: "WILD CARD", 2: "DIVISIONAL PLAYOFFS", 3: "CONFERENCE CHAMPIONSHIPS",
               4: "PRO BOWL", 5: "SUPER BOWL"}


def week_label(key):
    if not key:
        return ""
    stype, num = key
    if stype == 3:
        return _POST_WEEKS.get(num, "PLAYOFFS")
    if stype == 1:
        return f"PRESEASON WEEK {num}"
    return f"WEEK {num}"


def _scores_by_day(games, league, featured):
    by_day = {}
    for dt, ev in games:
        r = result_line(ev, league, featured)
        if r:
            r["_t"] = dt
            by_day.setdefault(dt.date(), []).append(r)
    out = []
    for d in sorted(by_day):
        rows = sorted(by_day[d], key=lambda r: (not r["featured"], r["_t"]))
        for r in rows:
            r.pop("_t", None)
        out.append({"day": f"{day_name(d)}'s Game{'s' if len(rows) != 1 else ''}", "rows": rows})
    return out


def nfl_week_view(sb, league, featured, page_date):
    """Monday paper: the current week only — its scores so far + Monday night.
    Tuesday paper: the week that just ended (all its scores), then next week's
    full schedule. Wednesday-Sunday: the current week — scores so far +
    remaining games (on Wednesday that's just the new week's schedule).

    Returns (blocks, upcoming_events). Each block: {"label", "results_by_day",
    "schedule"}; labels are only set when two weeks are shown.
    A game counts as played if it was before page_date, so rebuilding an old
    paper shows that day's view."""
    games = {}
    for ev in (sb or {}).get("events", []):
        key = _week_key(ev)
        dt = to_pt(ev.get("date") or comp0(ev).get("date"))
        if key is None or dt is None:
            continue
        games.setdefault(key, []).append((dt, ev))
    if not games:
        return [], {"events": []}

    played_keys = [k for k, gs in games.items() if any(dt.date() < page_date for dt, _ in gs)]
    upcoming_keys = sorted(k for k, gs in games.items() if any(dt.date() >= page_date for dt, _ in gs))
    last = max(played_keys) if played_keys else None

    if page_date.weekday() == 0 and last:               # Monday: this week only
        weeks = [last]                                  # (scores + Monday night)
    elif page_date.weekday() == 1 and last:             # Tuesday: the week that just
        weeks = [last] + [k for k in upcoming_keys if k > last][:1]   # ended + next week
    else:                                               # Wednesday through Sunday
        weeks = upcoming_keys[:1] or ([last] if last else [])

    blocks, upcoming = [], []
    for k in weeks:
        gs = sorted(games.get(k, []), key=lambda g: g[0])
        played = [(dt, ev) for dt, ev in gs if dt.date() < page_date]
        ahead = [ev for dt, ev in gs if dt.date() >= page_date]
        upcoming += ahead
        blocks.append({"label": week_label(k),
                       "results_by_day": _scores_by_day(played, league, featured),
                       "schedule": schedule({"events": ahead}, league, featured,
                                            on_or_after=page_date, by_date_only=True)})
    if len(blocks) < 2:
        for b in blocks:
            b["label"] = ""
    return blocks, {"events": upcoming}


# ── The Monday NFL page ──────────────────────────────────────────────────────

_AP_MONTH = {1: "Jan.", 2: "Feb.", 3: "March", 4: "April", 5: "May", 6: "June",
             7: "July", 8: "Aug.", 9: "Sept.", 10: "Oct.", 11: "Nov.", 12: "Dec."}


def ap_date(d):
    """'Thursday, Nov. 26' (AP style)."""
    return f"{day_name(d)}, {_AP_MONTH[d.month]} {d.day}"


def _games_by_week(sb):
    games = {}
    for ev in (sb or {}).get("events", []):
        key = _week_key(ev)
        dt = to_pt(ev.get("date") or comp0(ev).get("date"))
        if key is not None and dt is not None:
            games.setdefault(key, []).append((dt, ev))
    for k in games:
        games[k].sort(key=lambda g: g[0])
    return games


def _team_ids(gs):
    ids = set()
    for _, ev in gs:
        for c in comp0(ev).get("competitors", []):
            ids.add(str((c.get("team") or {}).get("id")))
    return ids


def nfl_monday_view(sb, league, featured, page_date, teams=None):
    """This week's scores (Thursday, Sunday …), Monday night's game, the teams
    with byes, and next week's schedule under dated headings."""
    games = _games_by_week(sb)
    played_keys = [k for k, gs in games.items() if any(dt.date() < page_date for dt, _ in gs)]
    if not played_keys:
        return None
    week = max(played_keys)
    this = games[week]
    later = sorted(k for k in games if k > week)
    nxt_key = later[0] if later else None
    nxt = games.get(nxt_key, [])

    def open_teams(gs):
        if not teams or not gs:
            return ""
        playing = _team_ids(gs)
        return ", ".join(sorted(n for tid, n in teams.items() if tid not in playing))

    next_days = schedule({"events": [ev for _, ev in nxt]}, league, featured,
                         on_or_after=page_date, by_date_only=True)
    for d in next_days:
        d["day"] = ap_date(d["date"])
    return {
        "seasontype": week[0],
        "label": week_label(week),
        "scores": _scores_by_day([(dt, ev) for dt, ev in this if dt.date() < page_date],
                                 league, featured),
        "tonight": schedule({"events": [ev for dt, ev in this if dt.date() >= page_date]},
                            league, featured, on_or_after=page_date, by_date_only=True),
        "open": open_teams(this),
        "next_label": week_label(nxt_key),
        "next": next_days,
        "next_open": open_teams(nxt),
    }
