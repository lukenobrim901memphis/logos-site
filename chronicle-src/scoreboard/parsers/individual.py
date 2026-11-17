"""
Golf leaderboards, auto racing results, tennis results, transactions —
all read from ESPN scoreboards (plus /transactions).
"""

import re
from datetime import timedelta

from .common import (ascii_text, comp0, status_of, to_pt, to_float, to_int,
                     team_city, split_name)


def _within(ev, start, end):
    s, e = to_pt(ev.get("date")), to_pt(ev.get("endDate") or ev.get("date"))
    if not s:
        return False
    e = e or s
    return s.date() <= end and e.date() >= start


# ── Golf ──────────────────────────────────────────────────────────────────────

def _to_par(v):
    if isinstance(v, dict):
        v = v.get("displayValue", v.get("value"))
    s = str(v or "").strip()
    if s.upper() in ("E", "EVEN"):
        return 0
    f = to_float(s)
    return int(f) if f is not None else None


def _par_str(n):
    if n is None:
        return ""
    return "E" if n == 0 else (f"+{n}" if n > 0 else str(n))


def golf(sb, league, results_date, limit=40):
    out = []
    for ev in (sb or {}).get("events", []):
        st = status_of(ev)
        if st["state"] not in ("in", "post"):
            continue
        if not _within(ev, results_date - timedelta(days=1), results_date):
            continue
        comp = comp0(ev)
        players = []
        for c in comp.get("competitors", []):
            ath = c.get("athlete") or {}
            rounds = []
            for ls in c.get("linescores") or []:
                v = to_float(ls.get("value"))
                if v and v > 50:                        # a completed round's strokes
                    rounds.append(int(v))
            players.append({"name": ascii_text(ath.get("displayName", "")),
                            "country": (ath.get("flag") or {}).get("alt", ""),
                            "par": _to_par(c.get("score")),
                            "rounds": rounds,
                            "order": to_int(c.get("order") or c.get("sortOrder"), 999)})
        players = [p for p in players if p["par"] is not None] or players
        players.sort(key=lambda p: (p["par"] if p["par"] is not None else 999, p["order"]))
        # positions with ties
        for i, p in enumerate(players):
            same = [q for q in players if q["par"] == p["par"]]
            first = players.index(same[0]) + 1
            p["pos"] = (f"T{first}" if len(same) > 1 else str(first))
            p["total"] = sum(p["rounds"]) if p["rounds"] else ""
            p["line"] = "-".join(str(r) for r in p["rounds"])
            p["par_str"] = _par_str(p["par"])
        rnd = max((len(p["rounds"]) for p in players), default=0)
        out.append({"name": ev.get("name") or ev.get("shortName", ""),
                    "status": "Final" if st["completed"] else
                              (f"Round {rnd} leaders" if rnd else st["detail"]),
                    "players": players[:limit]})
    return out


# ── Racing ────────────────────────────────────────────────────────────────────

def racing(sb, league, results_date, limit=40):
    out = []
    for ev in (sb or {}).get("events", []):
        comps = ev.get("competitions") or []
        race = None
        for c in comps:
            ab = ((c.get("type") or {}).get("abbreviation") or
                  (c.get("type") or {}).get("text") or "").lower()
            if ab.startswith("race") or ab == "r":
                race = c
        race = race or (comps[-1] if comps else None)
        if not race:
            continue
        st = status_of(race if race.get("status") else ev)
        if not st["completed"]:
            continue
        dt = to_pt(race.get("date") or ev.get("date"))
        if not dt or not (results_date - timedelta(days=1) <= dt.date() <= results_date):
            continue
        drivers = []
        for c in race.get("competitors", []):
            ath = c.get("athlete") or {}
            veh = c.get("vehicle") or {}
            extra = veh.get("manufacturer") or (ath.get("flag") or {}).get("alt", "")
            team = (c.get("team") or {}).get("displayName", "")
            drivers.append({"pos": to_int(c.get("order"), 999),
                            "name": ascii_text(ath.get("displayName", "")),
                            "num": veh.get("number", ""),
                            "extra": ", ".join(x for x in (extra, ascii_text(team)) if x)})
        drivers.sort(key=lambda d: d["pos"])
        venue = (race.get("venue") or ev.get("venue") or {})
        out.append({"name": ev.get("name") or ev.get("shortName", ""),
                    "where": venue.get("fullName", ""),
                    "day": dt.strftime("%A"),
                    "drivers": drivers[:limit]})
    return out


# ── Tennis ────────────────────────────────────────────────────────────────────

def _player_name(c):
    ath = c.get("athlete") or {}
    if ath.get("displayName"):
        nm = ascii_text(ath["displayName"])
        ctry = (ath.get("flag") or {}).get("alt", "")
        return f"{nm} ({ctry})" if ctry else nm
    roster = (c.get("roster") or {}).get("athletes") or c.get("athletes") or []
    if roster:
        return "-".join(split_name((r.get("athlete") or r).get("displayName", ""))[1]
                        for r in roster)
    return ascii_text((c.get("team") or {}).get("displayName", "") or c.get("displayName", ""))


def _sets(w, l):
    out = []
    for a, b in zip(w.get("linescores") or [], l.get("linescores") or []):
        av, bv = to_int(a.get("value")), to_int(b.get("value"))
        s = f"{av}-{bv}"
        tb = a.get("tiebreak") if av < bv else b.get("tiebreak")
        if tb is not None and {av, bv} in ({7, 6}, {6, 7}):
            s += f" ({to_int(tb)})"
        out.append(s)
    return ", ".join(out)


def tennis(sb, league, results_date):
    out = []
    for ev in (sb or {}).get("events", []):
        groups = ev.get("groupings") or [{"grouping": {"displayName": ""},
                                          "competitions": ev.get("competitions", [])}]
        sections = []
        for g in groups:
            label = ascii_text((g.get("grouping") or {}).get("displayName", ""))
            lines = []
            for c in g.get("competitions", []):
                st = status_of(c if c.get("status") else ev)
                if not st["completed"]:
                    continue
                dt = to_pt(c.get("date") or c.get("startDate"))
                if dt and dt.date() not in (results_date, results_date + timedelta(days=1)):
                    continue
                cs = c.get("competitors") or []
                if len(cs) != 2:
                    continue
                w = next((x for x in cs if x.get("winner")), cs[0])
                l = cs[1] if w is cs[0] else cs[0]
                rnd = ascii_text((c.get("round") or {}).get("displayName", ""))
                lines.append({"round": rnd, "text":
                              f"{_player_name(w)} def. {_player_name(l)}, {_sets(w, l)}"
                              + (" (ret.)" if "retire" in st["detail"].lower() else "")})
            if lines:
                sections.append({"label": label, "lines": lines})
        if sections:
            out.append({"name": ev.get("name") or ev.get("shortName", ""),
                        "sections": sections})
    return out


# ── Transactions ──────────────────────────────────────────────────────────────

def transactions(data, league, results_date):
    rows = []
    for t in (data or {}).get("transactions", []):
        d = str(t.get("date", ""))[:10]
        if d != results_date.isoformat():
            continue
        team = t.get("team") or {}
        desc = ascii_text(t.get("description", "")).strip()
        if desc:
            rows.append({"team": ascii_text(team.get("displayName", "")).upper(),
                         "text": desc})
    rows.sort(key=lambda r: r["team"])
    # merge same-team rows into one paragraph, Chronicle style
    merged = []
    for r in rows:
        if merged and merged[-1]["team"] == r["team"]:
            merged[-1]["text"] += " " + r["text"]
        else:
            merged.append(dict(r))
    return merged
