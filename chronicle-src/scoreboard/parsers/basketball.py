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

def _period_label(n, league):
    reg = league.get("periods", 4)
    if n <= reg:
        if reg == 2:
            return f"{ordinal(n)} half"
        return ordinal(n)
    k = n - reg
    return "OT" if k == 1 else f"{k}OT"


_FOUL_NAME_SPLIT = re.compile(
    r"\s+(?:technical|flagrant|ejected|defensive 3|delay|double technical|hanging|"
    r"away from play|taunt)", re.I)


def _who(play, book):
    """Short names of everyone charged in this play."""
    names = []
    for p in play.get("participants") or []:
        ath = p.get("athlete") or {}
        if ath.get("id") and str(ath["id"]) in book.by_id:
            names.append(book.short_id(ath["id"]))
        elif ath.get("displayName"):
            names.append(book.short(ath["displayName"]))
    if names:
        return names
    text = ascii_text(play.get("text", ""))
    m = re.match(r"(?i)double technical,?\s*(.+)", text)
    if m:                                     # 'Double technical, Green, Embiid'
        return [book.short(n.strip()) for n in re.split(r",| and ", m.group(1)) if n.strip()]
    head = _FOUL_NAME_SPLIT.split(text)[0].strip(" .")
    if not head:
        return []
    if head not in book.people:               # not a player in this game: a coach
        return ["\x00coach " + book.short(head)]
    return [book.short(head)]


def foul_notes(summary, league, book, teams_by_id):
    """{'tech': [...], 'flag': [...], 'eject': [...]} as 'Green, 4:12 2nd'."""
    out = {"tech": [], "flag": [], "eject": []}
    seen = set()
    for play in summary.get("plays") or []:
        kind = ((play.get("type") or {}).get("text") or "").lower()
        text = (play.get("text") or "").lower()
        both = kind + " " + text
        if "eject" in both:
            bucket = "eject"
        elif "flagrant" in both:
            bucket = "flag"
        elif "technical" in both or "3-second" in both or "3 second" in both:
            bucket = "tech"
        else:
            continue
        per = (play.get("period") or {}).get("number") or 0
        clock = (play.get("clock") or {}).get("displayValue", "")
        when = f"{clock} {_period_label(per, league)}".strip() if per else clock
        names = _who(play, book)
        if bucket == "tech" and ("3-second" in both or "3 second" in both or not names):
            team = teams_by_id.get(str((play.get("team") or {}).get("id")), "")
            names = [f"{team} defensive 3 seconds" if "second" in both else f"{team} team"]
        if bucket == "flag":
            m = re.search(r"type\s*(\d)", both)
            if m:
                names = [f"{n} ({m.group(1)})" for n in names]
        team = teams_by_id.get(str((play.get("team") or {}).get("id")), "")
        names = [f"{team} {n[1:]}".strip() if n.startswith("\x00") else n for n in names]
        for n in names:
            key = (bucket, n, when)
            if key not in seen:
                seen.add(key)
                out[bucket].append(f"{n}, {when}")
    return out


def parse(summary, league, event=None, featured=None):
    head = game_header(summary, league, event, featured)
    box = summary.get("boxscore") or {}

    book = NameBook(sep=".")
    for tp in box.get("players", []):
        for grp in tp.get("statistics", []):
            for a in grp.get("athletes", []):
                book.add_athlete(a.get("athlete"))

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
    ejected_flags = []
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
                ejected_flags.append(name)

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
            "name": team_city(team, league).upper(),
            "rows": rows,
            "totals": dict(min=team_minutes, fg=f"{tot['fgm']}-{tot['fga']}",
                           ft=f"{tot['ftm']}-{tot['fta']}",
                           reb=f"{tot['oreb']}-{tot['reb']}", a=tot["a"],
                           pf=tot["pf"], pts=tot["pts"]),
            "notes": " ".join(notes),
        })

    tb = {str(head["away"]["team"].get("id")): head["away"]["city"],
          str(head["home"]["team"].get("id")): head["home"]["city"]}
    fouls = foul_notes(summary, league, book, tb)
    for n in ejected_flags:                       # ejected but not in the play-by-play
        if not any(e.startswith(n + ",") for e in fouls["eject"]):
            fouls["eject"].append(n)
    game_notes = []
    for key, label in (("tech", "Technical fouls"), ("flag", "Flagrant fouls"), ("eject", "Ejections")):
        if fouls[key]:
            game_notes.append(f"<b>{label}:</b> " + "; ".join(fouls[key]) + ".")

    head.update(kind="basketball", teams=teams, game_notes=" ".join(game_notes))
    return head
