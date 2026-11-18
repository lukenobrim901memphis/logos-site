"""
builder.py — fetches everything for one page date and assembles the
data the scoreboard template renders.

Page date = the paper's date (today, Pacific). Results are from the day
before; schedules/odds are for the page date (and the day after).
"""

from datetime import date, timedelta

import espn
from leagues import LEAGUES, BY_KEY
from parsers import BOX_PARSERS
from parsers import standings as p_standings
from parsers import rankings as p_rankings
from parsers import slate, individual, spring
from parsers.common import (ascii_text, comp0, sides, status_of, is_featured,
                            day_name)


def featured_set(settings):
    return {ascii_text(x).strip().lower() for x in settings.get("featured", []) if x.strip()}


def _box_mode(lg, settings):
    return (settings["leagues"].get(lg["key"], {}).get("box") or lg.get("box", "none"))


def wants_box(ev, lg, settings, featured, use_override=True):
    ov = settings.get("box_overrides", {}).get(str(ev.get("id")))
    if use_override and ov is not None:
        return bool(ov)
    mode = _box_mode(lg, settings)
    if mode == "all":
        return True
    if mode == "featured":
        a, h = sides(comp0(ev))
        return is_featured(a.get("team"), featured) or is_featured(h.get("team"), featured)
    return False


def _season_active(*sbs):
    for sb in sbs:
        if not sb:
            continue
        if sb.get("events"):
            return True
        for lgd in sb.get("leagues", []):
            t = ((lgd.get("season") or {}).get("type") or {}).get("type")
            if t in (2, 3, "2", "3"):
                return True
    return False


def _completed(sb):
    for ev in (sb or {}).get("events", []):
        st = status_of(comp0(ev) if comp0(ev).get("status") else ev)
        if st["completed"]:
            yield ev


def fetch_scoreboards(page_date, settings, leagues):
    results_date = page_date - timedelta(days=1)
    jobs = {}
    for lg in leagues:
        k, p, extra = lg["key"], lg["path"], lg.get("scoreboard_params")
        if lg["kind"] in ("golf", "racing"):
            jobs[(k, "cur")] = lambda p=p: espn.scoreboard(p, None)
        elif lg["kind"] == "spring":
            season_start = date(page_date.year, 2, 10)
            span = f"{season_start:%Y%m%d}-{results_date:%Y%m%d}"
            jobs[(k, "y")] = lambda p=p: espn.scoreboard(p, results_date, ttl=espn.TTL_PAST)
            jobs[(k, "t")] = lambda p=p: espn.scoreboard(p, page_date)
            jobs[(k, "range")] = lambda p=p, sp=span: espn.scoreboard(
                p, None, {"dates": sp, "limit": 1000}, ttl=espn.TTL_PAST)
        elif lg["kind"] == "tennis":
            jobs[(k, "y")] = lambda p=p: espn.scoreboard(p, results_date, ttl=espn.TTL_PAST)
        else:
            jobs[(k, "y")] = lambda p=p, e=extra: espn.scoreboard(p, results_date, e, ttl=espn.TTL_PAST)
            for name, params in lg.get("extra_groups", []):
                jobs[(k, "y+" + name)] = lambda p=p, e=params: espn.scoreboard(p, results_date, e, ttl=espn.TTL_PAST)
            if lg.get("nfl_weeks"):            # every game from 9 days back to 9 ahead
                span = f"{page_date - timedelta(days=9):%Y%m%d}-{page_date + timedelta(days=9):%Y%m%d}"
                jobs[(k, "weeks")] = lambda p=p, sp=span: espn.scoreboard(p, None, {"dates": sp, "limit": 300})
            if lg.get("weekly"):
                jobs[(k, "wk")] = lambda p=p, e=extra: espn.scoreboard(p, None, e)
            else:
                jobs[(k, "t")] = lambda p=p, e=extra: espn.scoreboard(p, page_date, e)
                jobs[(k, "t2")] = lambda p=p, e=extra: espn.scoreboard(p, page_date + timedelta(days=1), e)
    out = espn.run_parallel(jobs)

    # NFL: read the season calendar, then fetch the weeks around this paper
    # by week number (seasontype + week), stamping each game with its week
    week_jobs = {}
    for lg in leagues:
        if not lg.get("nfl_weeks"):
            continue
        k, p = lg["key"], lg["path"]
        cal, year = slate.nfl_calendar(out.get((k, "wk")) or {})
        lo, hi = page_date - timedelta(days=9), page_date + timedelta(days=9)
        for key, first, last in cal:
            if key[0] in (2, 3) and first <= hi and last >= lo:
                params = {"seasontype": key[0], "week": key[1]}
                if year:
                    params["dates"] = year
                week_jobs[(k, key)] = lambda p=p, pr=params: espn.scoreboard(p, None, pr)
    if week_jobs:
        fetched = espn.run_parallel(week_jobs)
        by_league = {}
        for (k, key), sbw in fetched.items():
            for ev in (sbw or {}).get("events", []):
                ev["_wk"] = list(key)
                by_league.setdefault(k, {})[ev.get("id")] = ev
        for k, evs in by_league.items():
            out[(k, "weeks")] = {"events": list(evs.values())}

    # merge extra divisions (college football FCS) into the results-day scoreboard
    for lg in leagues:
        if not lg.get("extra_groups"):
            continue
        k = lg["key"]
        main = out.get((k, "y")) or {}
        events, seen = [], set()
        for ev in main.get("events", []):
            ev["_division"] = "FBS"
            events.append(ev)
            seen.add(ev.get("id"))
        for name, _ in lg["extra_groups"]:
            for ev in (out.get((k, "y+" + name)) or {}).get("events", []):
                if ev.get("id") not in seen:            # FBS-vs-FCS games appear in both
                    ev["_division"] = name
                    events.append(ev)
                    seen.add(ev.get("id"))
        if events or main:
            out[(k, "y")] = {**main, "events": events}
    return out


def build(page_date, settings):
    results_date = page_date - timedelta(days=1)
    featured = featured_set(settings)
    lmode = lambda k: settings["leagues"].get(k, {}).get("mode", "auto")
    leagues = [BY_KEY[k] for k in settings["order"] if k in BY_KEY and lmode(k) != "off"]

    sb = fetch_scoreboards(page_date, settings, leagues)
    get = lambda k, w: sb.get((k, w)) or {}

    # ── Which team-sport leagues are in season? ──────────────────────────
    active = []
    for lg in leagues:
        k = lg["key"]
        if lg["kind"] in ("golf", "racing", "tennis"):
            active.append(lg)
        elif lg["kind"] == "spring":
            if lmode(k) == "on" or spring.is_preseason(get(k, "y"), get(k, "t")):
                active.append(lg)
        elif lmode(k) == "on" or _season_active(get(k, "y"), get(k, "t"),
                                                 get(k, "t2"), get(k, "wk")):
            active.append(lg)

    # ── Phase 2: standings, rankings, transactions, box-score summaries ──
    jobs = {}
    for lg in active:
        k, p = lg["key"], lg["path"]
        if lg.get("standings"):
            jobs[(k, "standings")] = lambda p=p, e=lg.get("standings_params"): espn.standings(p, e)
        if lg.get("college") and (page_date.weekday() in lg.get("rankings_weekdays", [])
                                  or lmode(k) == "on"):
            jobs[(k, "rankings")] = lambda p=p: espn.rankings(p)
        if lg.get("transactions") and settings.get("show_transactions"):
            jobs[(k, "txn")] = lambda p=p: espn.transactions(p)
        if lg["kind"] in BOX_PARSERS:
            for ev in _completed(get(k, "y")):
                if wants_box(ev, lg, settings, featured):
                    jobs[(k, "box", ev["id"])] = lambda p=p, i=ev["id"]: espn.summary(p, i)
    more = espn.run_parallel(jobs)

    # ── Assemble sections ────────────────────────────────────────────────
    sections, odds, txns = [], [], []
    for lg in active:
        k = lg["key"]
        sec = {"key": k, "label": lg["label"], "sublabel": lg.get("sublabel", ""),
               "kind": lg["kind"], "college": bool(lg.get("college")),
               "results_day": f"{day_name(results_date)}'s Games"}

        if lg["kind"] == "golf":
            sec["golf"] = individual.golf(get(k, "cur"), lg, results_date,
                                          settings.get("golf_limit", 30))
            if sec["golf"]:
                sections.append(sec)
            continue
        if lg["kind"] == "racing":
            sec["racing"] = individual.racing(get(k, "cur"), lg, results_date)
            if sec["racing"]:
                sections.append(sec)
            continue
        if lg["kind"] == "tennis":
            sec["tennis"] = individual.tennis(get(k, "y"), lg, results_date)
            if sec["tennis"]:
                sections.append(sec)
            continue
        if lg["kind"] == "spring":
            sec["standings"] = spring.standings(get(k, "range"), lg, featured)
            sec["results"] = spring.results(get(k, "y"), lg, featured)
            sec["spring_schedule"] = spring.schedule(get(k, "t"), lg, featured, on_date=page_date)
            if sec["standings"] or sec["results"] or sec["spring_schedule"]:
                sections.append(sec)
            continue

        st = more.get((k, "standings"))
        sec["standings"] = p_standings.parse(st, lg, featured) if st else None
        if sec["standings"] and not sec["standings"]["groups"]:
            sec["standings"] = None
        rk = more.get((k, "rankings"))
        sec["rankings"] = p_rankings.parse(rk, lg, featured) if rk else None

        res = slate.results(get(k, "y"), lg, featured)
        if lg.get("college"):
            sec["top25"] = [r for r in res if r.get("ranked")]
            sec["featured_results"] = [r for r in res if r.get("featured") and not r.get("ranked")]
            rest = ([r for r in res if not r.get("ranked") and not r.get("featured")]
                    if lg.get("all_scores") or settings.get("college_results") == "all" else [])
            by_winner = lambda r: (r.get("w") or {}).get("name", r.get("text", ""))
            sec["other_results"] = sorted([r for r in rest if r.get("division") != "FCS"], key=by_winner)
            sec["fcs_results"] = sorted([r for r in rest if r.get("division") == "FCS"], key=by_winner)
        else:
            sec["results"] = res

        if lg.get("nfl_weeks") and get(k, "weeks").get("events"):
            sec["nfl_blocks"], odd_src = slate.nfl_week_view(get(k, "weeks"), lg, featured, page_date)
            sec["results"], sched = [], []
            odd_kw = {"on_or_after": page_date}
        elif lg.get("weekly"):
            sched = slate.schedule(get(k, "wk"), lg, featured, on_or_after=page_date)
            odd_src, odd_kw = get(k, "wk"), {"on_or_after": page_date}
        else:
            sched = (slate.schedule(get(k, "t"), lg, featured, only_dates={page_date})
                     + slate.schedule(get(k, "t2"), lg, featured,
                                      only_dates={page_date + timedelta(days=1)}))
            odd_src, odd_kw = get(k, "t"), {"only_dates": {page_date}}
        if lg.get("college"):                   # keep college schedules to ranked/featured
            for d in sched:
                d["games"] = [g for g in d["games"] if g["ranked"] or g["featured"]]
            sched = [d for d in sched if d["games"]]
            for d in sched:
                d["day"] = d["day"].replace("Game", "Top 25 Game")
        sec["schedule"] = sched

        if lg.get("odds") and settings.get("show_odds"):
            lines = slate.odds_lines(odd_src, lg, featured,
                                     ranked_only=bool(lg.get("college")), **odd_kw)
            if lines:
                odds.append({"label": lg["label"] + (f" — {lg['sublabel']}" if lg.get("sublabel") else ""),
                             "lines": lines})

        boxes = []
        parser = BOX_PARSERS.get(lg["kind"])
        for ev in _completed(get(k, "y")):
            summ = more.get((k, "box", ev["id"]))
            if not summ or not parser:
                continue
            try:
                b = parser(summ, lg, ev, featured)
                b["id"] = ev["id"]
                boxes.append(b)
            except Exception as e:
                import traceback
                print(f"  box parse error {k} {ev.get('id')}: {e}")
                traceback.print_exc()
        boxes.sort(key=lambda b: not (b["away"]["featured"] or b["home"]["featured"]))
        sec["boxes"] = boxes

        if (more.get((k, "txn"))):
            t = individual.transactions(more[(k, "txn")], lg, results_date)
            if t:
                txns.append({"label": lg["label"], "rows": t})

        has_content = any(sec.get(x) for x in ("standings", "rankings", "results", "nfl_blocks", "top25",
                                               "featured_results", "other_results", "fcs_results",
                                               "schedule", "boxes"))
        if has_content:
            sections.append(sec)

    return {
        "page_date": page_date,
        "prev_date": page_date - timedelta(days=1),
        "next_date": page_date + timedelta(days=1),
        "results_date": results_date,
        "date_str": page_date.strftime("%A, %B %-d, %Y"),
        "sections": sections,
        "odds": odds,
        "transactions": txns,
        "custom": [c for c in settings.get("custom_sections", []) if c.get("title") or c.get("body")],
    }


def admin_games(page_date, settings):
    """Yesterday's completed games per league, for the box-score picker."""
    featured = featured_set(settings)
    results_date = page_date - timedelta(days=1)
    team_leagues = [lg for lg in LEAGUES if lg["kind"] in BOX_PARSERS]
    jobs = {lg["key"]: (lambda p=lg["path"], e=lg.get("scoreboard_params"):
                        espn.scoreboard(p, results_date, e, ttl=espn.TTL_PAST))
            for lg in team_leagues}
    sbs = espn.run_parallel(jobs)
    out = []
    for lg in team_leagues:
        games = []
        for ev in _completed(sbs.get(lg["key"])):
            r = slate.result_line(ev, lg, featured)
            if not r or r.get("ppd"):
                continue
            txt = f"{r['w']['name']} {r['ws']}, {r['l']['name']} {r['ls']}"
            games.append({"id": ev["id"], "text": txt,
                          "on": wants_box(ev, lg, settings, featured),
                          "default": wants_box(ev, lg, settings, featured, use_override=False),
                          "featured": r["featured"], "ranked": r.get("ranked")})
        if lg.get("college") and settings.get("college_results") != "all":
            games = [g for g in games if g["featured"] or g["ranked"]]
        if games:
            out.append({"key": lg["key"], "label": lg["label"] +
                        (f" — {lg['sublabel']}" if lg.get("sublabel") else ""),
                        "games": games})
    return out
