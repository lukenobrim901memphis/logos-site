"""
Basketball box score (NBA, WNBA, men's/women's college) in Chronicle form:

    INDIANA
                  FG    FT   Reb
           Min   M-A   M-A   O-T  A PF Pts
    Turner  26  6-11   1-2   1-8  2  4  13
    ...
    Totals 240 37-83 13-21  7-41 18 15  95
    Percentages: FG .446, FT .619. 3-Point Goals: 8-22, .364 (Collison 2-2,
    Leaf 2-3 ...). Team Rebounds: 10. Team Turnovers: 13 (13 PTS).
    Blocked shots: 7 (Turner 3, Joseph 2, Bogdanovic, Leaf). Turnovers: 13.
    Steals: 5.
"""

import re

from .common import (NameBook, column_map, made_att, pct3, to_int,
                     stat_index, pick, team_by_id, team_city, ordinal, ascii_text)
from .game import game_header

KEY_ALIASES = {
    "minutes": "min", "points": "pts",
    "fieldGoalsMade-fieldGoalsAttempted": "fg",
    "threePointFieldGoalsMade-threePointFieldGoalsAttempted": "tp",
    "freeThrowsMade-freeThrowsAttempted": "ft",
    "offensiveRebounds": "oreb", "defensiveRebounds": "dreb",
    "rebounds": "reb", "assists": "a", "steals": "stl", "blocks": "blk",
    "turnovers": "to", "fouls": "pf", "plusMinus": "pm",
}
LABEL_ALIASES = {
    "MIN": "min", "PTS": "pts", "FG": "fg", "3PT": "tp", "FT": "ft",
    "OREB": "oreb", "DREB": "dreb", "REB": "reb", "AST": "a", "STL": "stl",
    "BLK": "blk", "TO": "to", "PF": "pf", "+/-": "pm",
}


def _counted(items):
    """[('Turner', 3), ('Leaf', 1)] -> 'Turner 3, Leaf'."""
    return ", ".join(f"{n} {c}" if c > 1 else n for n, c in items)


# ── Technicals, flagrants, ejections (from ESPN play-by-play) ────────────────

_PERIOD_WORDS = {1: "first", 2: "second", 3: "third", 4: "fourth", 5: "fifth",
                 6: "sixth", 7: "seventh", 8: "eighth"}


def _period_label(n, league):
    """4 -> 'fourth', OT -> 'overtime', 2OT -> 'second overtime';
    men's college halves -> 'first half', 'second half'."""
    reg = league.get("periods", 4)
    if n <= reg:
        word = _PERIOD_WORDS.get(n, ordinal(n))
        return f"{word} half" if reg == 2 else word
    k = n - reg
    return "overtime" if k == 1 else f"{_PERIOD_WORDS.get(k, ordinal(k))} overtime"


_FOUL_NAME_SPLIT = re.compile(
    r"\s+(?:technical|flagrant|ejected|defensive 3|delay|double technical|hanging|"
    r"away from play|taunt)", re.I)
_SHOT_NAME_SPLIT = re.compile(r"\s+(?:makes|misses)\b", re.I)


def _is_free_throw(both):
    """'Klay Thompson makes technical free throw' is the reward, not the foul."""
    return "free throw" in both


def _charged(play, book, ath_team, name_team):
    """[(full name, team id or None)] for everyone charged with this foul.
    team None = not on either roster (a coach)."""
    out = []
    parts = play.get("participants") or []
    for p in parts[:1] if "double" not in ((play.get("type") or {}).get("text") or "").lower() else parts:
        ath = p.get("athlete") or {}
        aid = str(ath.get("id") or "")
        full = book.by_id.get(aid) or ascii_text(ath.get("displayName", ""))
        if full:
            out.append((full, ath_team.get(aid) or name_team.get(full)))
    if out:
        return out
    text = ascii_text(play.get("text", ""))
    m = re.match(r"(?i)double technical,?\s*(.+)", text)
    if m:                                         # 'Double technical, Green, Embiid'
        return [(n.strip(), name_team.get(n.strip()))
                for n in re.split(r",| and ", m.group(1)) if n.strip()]
    head = _FOUL_NAME_SPLIT.split(text)[0].strip(" .")
    return [(head, name_team.get(head))] if head else []


def _team_in_text(text, teams):
    """'Magic defensive 3-seconds' -> the Magic's team id."""
    low = text.lower()
    for tid, t in teams.items():
        for word in (t.get("name"), t.get("location"), t.get("displayName"), t.get("shortDisplayName")):
            if word and word.lower() in low:
                return tid
    return None


def _fouling_team_from_free_throw(plays, i, ath_team, name_team, team_ids, book):
    """The team that committed a technical is the opponent of whoever shoots
    the technical free throw right after it (same period and clock)."""
    per = (plays[i].get("period") or {}).get("number")
    clock = (plays[i].get("clock") or {}).get("displayValue")
    for nxt in plays[i + 1:i + 6]:
        if (nxt.get("period") or {}).get("number") != per or \
                (nxt.get("clock") or {}).get("displayValue") != clock:
            break
        both = (((nxt.get("type") or {}).get("text") or "") + " " + (nxt.get("text") or "")).lower()
        if not _is_free_throw(both):
            continue
        shooter_team = None
        for p in nxt.get("participants") or []:
            aid = str((p.get("athlete") or {}).get("id") or "")
            shooter_team = ath_team.get(aid)
            break
        if not shooter_team:
            name = _SHOT_NAME_SPLIT.split(ascii_text(nxt.get("text", "")))[0].strip()
            shooter_team = name_team.get(name)
        if shooter_team:
            others = [t for t in team_ids if t != shooter_team]
            return others[0] if others else None
    return None


def foul_notes(summary, league, book, ath_team, name_team, teams):
    """Per team id: {'tech': [...], 'flag': [...], 'eject': [...]},
    each entry like 'Sengun, 9:56 1st'."""
    team_ids = list(teams)
    out = {tid: {"tech": [], "flag": [], "eject": []} for tid in team_ids}
    plays = summary.get("plays") or []
    seen = set()
    for i, play in enumerate(plays):
        kind = ((play.get("type") or {}).get("text") or "").lower()
        text = (play.get("text") or "").lower()
        both = kind + " " + text
        if _is_free_throw(both):
            continue
        three_sec = "3-second" in both or "3 second" in both
        if "eject" in both:
            bucket = "eject"
        elif "flagrant" in both:
            bucket = "flag"
        elif "technical" in both or three_sec:
            bucket = "tech"
        else:
            continue
        per = (play.get("period") or {}).get("number") or 0
        clock = (play.get("clock") or {}).get("displayValue", "")
        when = f"{clock} {_period_label(per, league)}".strip() if per else clock

        def fallback_team():
            return (_fouling_team_from_free_throw(plays, i, ath_team, name_team, team_ids, book)
                    or str((play.get("team") or {}).get("id") or "") or None)

        if three_sec:                             # charged to the team, not a player
            tid = _team_in_text(play.get("text", ""), teams) or fallback_team()
            entries = [("defensive 3 seconds", tid)]
        else:
            entries = []
            for full, tid in _charged(play, book, ath_team, name_team):
                if tid:                            # a player on one of the rosters
                    entries.append((book.short(full), tid))
                elif _team_in_text(full, teams):   # 'Warriors delay of game'
                    entries.append(("team", _team_in_text(full, teams)))
                else:                              # not on a roster: a coach
                    entries.append((f"coach {book.short(full)}", fallback_team()))
        if bucket == "flag":
            m = re.search(r"type\s*(\d)", both)
            if m:
                entries = [(f"{n} ({m.group(1)})", t) for n, t in entries]
        for name, tid in entries:
            if tid not in out:
                continue
            key = (bucket, name, when)
            if key not in seen:
                seen.add(key)
                out[tid][bucket].append(f"{name}, {when}")
    return out


def parse(summary, league, event=None, featured=None):
    head = game_header(summary, league, event, featured)
    box = summary.get("boxscore") or {}

    book = NameBook(sep=".")
    ath_team, name_team = {}, {}
    for tp in box.get("players", []):
        tid = str((tp.get("team") or {}).get("id"))
        for grp in tp.get("statistics", []):
            for a in grp.get("athletes", []):
                ath = a.get("athlete") or {}
                book.add_athlete(ath)
                if ath.get("id"):
                    ath_team[str(ath["id"])] = tid
                if ath.get("displayName"):
                    name_team[ascii_text(ath["displayName"]).strip()] = tid

    # team order: away first, like the linescore
    order = {str(head["away"]["team"].get("id")): 0,
             str(head["home"]["team"].get("id")): 1}
    players = sorted(box.get("players", []),
                     key=lambda tp: order.get(str((tp.get("team") or {}).get("id")), 9))

    n_periods = max(len(head["away"]["line"]), len(head["home"]["line"]))
    reg = league.get("periods", 4)
    team_minutes = 5 * (reg * league.get("period_min", 12)
                        + max(0, n_periods - reg) * league.get("ot_min", 5))

    teams = []
    ejected_flags = {}
    for tp in players:
        team = tp.get("team") or {}
        grp = (tp.get("statistics") or [{}])[0]
        cols = column_map(grp, KEY_ALIASES, LABEL_ALIASES)

        rows = []
        tot = dict(fgm=0, fga=0, ftm=0, fta=0, tpm=0, tpa=0, oreb=0, reb=0,
                   a=0, pf=0, pts=0, stl=0, blk=0, to=0)
        threes, blocks = [], []
        for ath in grp.get("athletes", []):
            stats = ath.get("stats") or []
            if ath.get("didNotPlay") or not stats:
                continue
            d = dict(zip(cols, stats))
            name = book.short((ath.get("athlete") or {}).get("displayName", ""))
            fgm, fga = made_att(d.get("fg"))
            ftm, fta = made_att(d.get("ft"))
            tpm, tpa = made_att(d.get("tp"))
            oreb = to_int(d.get("oreb"))
            reb = to_int(d.get("reb")) or oreb + to_int(d.get("dreb"))
            row = dict(name=name, min=to_int(d.get("min")), fg=f"{fgm}-{fga}",
                       ft=f"{ftm}-{fta}", reb=f"{oreb}-{reb}",
                       a=to_int(d.get("a")), pf=to_int(d.get("pf")),
                       pts=to_int(d.get("pts")),
                       starter=bool(ath.get("starter")))
            rows.append(row)
            for k, v in (("fgm", fgm), ("fga", fga), ("ftm", ftm), ("fta", fta),
                         ("tpm", tpm), ("tpa", tpa), ("oreb", oreb), ("reb", reb),
                         ("a", row["a"]), ("pf", row["pf"]), ("pts", row["pts"]),
                         ("stl", to_int(d.get("stl"))), ("blk", to_int(d.get("blk"))),
                         ("to", to_int(d.get("to")))):
                tot[k] += v
            if tpa:
                threes.append((name, tpm, tpa))
            if to_int(d.get("blk")):
                blocks.append((name, to_int(d.get("blk"))))
            if ath.get("ejected"):
                ejected_flags.setdefault(str(team.get("id")), []).append(name)

        ts = stat_index(team_by_id(summary, team.get("id")).get("statistics"))
        threes.sort(key=lambda x: (-x[1], x[2]))
        blocks.sort(key=lambda x: -x[1])

        notes = [f"<b>Percentages:</b> FG {pct3(tot['fgm'], tot['fga'])}, "
                 f"FT {pct3(tot['ftm'], tot['fta'])}."]
        if tot["tpa"]:
            notes.append(
                f"<b>3-Point Goals:</b> {tot['tpm']}-{tot['tpa']}, "
                f"{pct3(tot['tpm'], tot['tpa'])} ("
                + ", ".join(f"{n} {m}-{a}" for n, m, a in threes) + ").")
        team_reb = pick(ts, "teamRebounds")
        if team_reb:
            notes.append(f"<b>Team Rebounds:</b> {team_reb}.")
        team_to = pick(ts, "totalTurnovers", "turnovers", default=str(tot["to"]))
        to_pts = pick(ts, "turnoverPoints", "pointsOffTurnovers")
        notes.append(f"<b>Team Turnovers:</b> {team_to}"
                     + (f" ({to_pts} PTS)" if to_pts else "") + ".")
        notes.append(f"<b>Blocked shots:</b> {tot['blk']}"
                     + (f" ({_counted(blocks)})" if blocks else "") + ".")
        notes.append(f"<b>Turnovers:</b> {tot['to']}.")
        notes.append(f"<b>Steals:</b> {tot['stl']}.")

        teams.append({
            "id": str(team.get("id")),
            "name": team_city(team, league).upper(),
            "rows": rows,
            "totals": dict(min=team_minutes, fg=f"{tot['fgm']}-{tot['fga']}",
                           ft=f"{tot['ftm']}-{tot['fta']}",
                           reb=f"{tot['oreb']}-{tot['reb']}", a=tot["a"],
                           pf=tot["pf"], pts=tot["pts"]),
            "notes": " ".join(notes),
        })

    # technicals / flagrants / ejections go in the notes of the team charged
    team_objs = {str(head["away"]["team"].get("id")): head["away"]["team"],
                 str(head["home"]["team"].get("id")): head["home"]["team"]}
    fouls = foul_notes(summary, league, book, ath_team, name_team, team_objs)
    for t in teams:
        f = fouls.get(t["id"], {"tech": [], "flag": [], "eject": []})
        for n in ejected_flags.get(t["id"], []):  # ejected but missing from play-by-play
            if not any(e.startswith(n + ",") for e in f["eject"]):
                f["eject"].append(n)
        extra = []
        for key, label in (("tech", "Technical fouls"), ("flag", "Flagrant fouls"),
                           ("eject", "Ejections")):
            if f[key]:
                extra.append(f"<b>{label}:</b> " + "; ".join(f[key]) + ".")
        if extra:
            t["notes"] += " " + " ".join(extra)

    head.update(kind="basketball", teams=teams)
    return head
