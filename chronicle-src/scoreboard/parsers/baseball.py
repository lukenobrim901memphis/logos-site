"""
Baseball box score from ESPN — the compact version (batting, pitching,
linescore). Your existing MLB Stats API code produces richer notes
(season HR totals, DP, umpires); see README for how to plug it in.
"""

from .common import NameBook, column_map, stat_index, pick, team_by_id, to_int
from .game import game_header

BAT_LABELS = {"AB": "ab", "R": "r", "H": "h", "RBI": "bi", "BB": "bb",
              "K": "so", "SO": "so", "AVG": "avg", "HR": "hr"}
PIT_LABELS = {"IP": "ip", "H": "h", "R": "r", "ER": "er", "BB": "bb",
              "K": "so", "SO": "so", "PC": "np", "ERA": "era", "PC-ST": "pcst"}


def _ip(raw):
    s = str(raw)
    whole = s.split(".")[0] or "0"
    if s.endswith(".1"):
        return ("" if whole == "0" else whole) + "⅓"
    if s.endswith(".2"):
        return ("" if whole == "0" else whole) + "⅔"
    return whole


def _group3(vals):
    return " ".join("".join(vals[i:i + 3]) for i in range(0, len(vals), 3))


def parse(summary, league, event=None, featured=None):
    head = game_header(summary, league, event, featured)
    box = summary.get("boxscore") or {}
    book = NameBook(sep=". ")
    for tp in box.get("players", []):
        for g in tp.get("statistics", []):
            for a in g.get("athletes", []):
                book.add_athlete(a.get("athlete"))

    away_id = str(head["away"]["team"].get("id"))
    order = {away_id: 0, str(head["home"]["team"].get("id")): 1}
    players = sorted(box.get("players", []),
                     key=lambda tp: order.get(str((tp.get("team") or {}).get("id")), 9))

    teams = []
    for tp in players:
        tid = str((tp.get("team") or {}).get("id"))
        city = head["away"]["city"] if tid == away_id else head["home"]["city"]
        batters, pitchers, hrs = [], [], []
        for g in tp.get("statistics", []):
            gname = (g.get("name") or g.get("type") or "").lower()
            if gname.startswith("bat"):
                cols = column_map(g, {}, BAT_LABELS)
                for a in g.get("athletes", []):
                    if not a.get("stats"):
                        continue
                    d = dict(zip(cols, a["stats"]))
                    ath = a.get("athlete") or {}
                    pos = (a.get("position") or ath.get("position") or {}).get("abbreviation", "")
                    nm = book.short(ath.get("displayName", ""))
                    batters.append(dict(name=f"{nm} {pos.lower()}".strip(),
                                        ab=to_int(d.get("ab")), r=to_int(d.get("r")),
                                        h=to_int(d.get("h")), bi=to_int(d.get("bi")),
                                        bb=to_int(d.get("bb")), so=to_int(d.get("so")),
                                        avg=d.get("avg", "")))
                    if to_int(d.get("hr")):
                        n = to_int(d.get("hr"))
                        hrs.append(nm + (f" {n}" if n > 1 else ""))
            elif gname.startswith("pitch"):
                cols = column_map(g, {}, PIT_LABELS)
                for a in g.get("athletes", []):
                    if not a.get("stats"):
                        continue
                    d = dict(zip(cols, a["stats"]))
                    ath = a.get("athlete") or {}
                    note = ""
                    for n in a.get("notes") or []:
                        if n.get("text"):
                            note = n["text"]
                    np_ = d.get("np") or str(d.get("pcst", "")).split("-")[0]
                    pitchers.append(dict(name=(book.short(ath.get("displayName", ""))
                                               + (f" {note}" if note else "")),
                                         ip=_ip(d.get("ip", "0")), h=to_int(d.get("h")),
                                         r=to_int(d.get("r")), er=to_int(d.get("er")),
                                         bb=to_int(d.get("bb")), so=to_int(d.get("so")),
                                         np=to_int(np_), era=d.get("era", "")))
        teams.append(dict(name=city, batters=batters, pitchers=pitchers, hrs=hrs,
                          totals=dict((k, sum(b[k] for b in batters))
                                      for k in ("ab", "r", "h", "bi", "bb", "so"))))

    rhe = {}
    for side in ("away", "home"):
        tid = str(head[side]["team"].get("id"))
        ts = stat_index(team_by_id(summary, tid).get("statistics"))
        rhe[side] = (head[side]["score"], pick(ts, "hits", "H", default=""),
                     pick(ts, "errors", "E", default=""))

    hr_note = "; ".join(f"{t['name']}, " + ", ".join(t["hrs"]) for t in teams if t["hrs"])
    head.update(kind="baseball", teams=teams, rhe=rhe,
                away_line=_group3(head["away"]["line"]),
                home_line=_group3(head["home"]["line"]),
                notes=(f"<b>HR</b>—{hr_note}." if hr_note else ""))
    return head
