"""
Builds synthetic fixtures shaped like ESPN responses, so the whole page
can be rendered offline:  AGATE_FIXTURES=tests/fixtures python app.py
Paper date for these fixtures: 2026-11-16 (results from 2026-11-15).
"""

import json
import os
import sys
from datetime import date

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
import espn  # noqa: E402

OUT = os.path.join(os.path.dirname(__file__), "fixtures")
os.makedirs(OUT, exist_ok=True)
Y, T, T2 = date(2026, 11, 15), date(2026, 11, 16), date(2026, 11, 17)


def save(url, data):
    with open(os.path.join(OUT, espn.slug(url) + ".json"), "w") as f:
        json.dump(data, f, indent=1)


def sb_url(path, day=None, extra=None):
    params = dict(extra or {})
    if day:
        params["dates"] = day.strftime("%Y%m%d")
    return espn._url(espn.SITE, path, "scoreboard", params)


def team(tid, loc, name, abbr, display=None):
    return {"id": str(tid), "location": loc, "name": name, "abbreviation": abbr,
            "displayName": display or f"{loc} {name}", "shortDisplayName": name}


def status(state, detail="Final", completed=None, name=None):
    return {"type": {"state": state, "completed": state == "post" if completed is None else completed,
                     "detail": detail, "shortDetail": detail,
                     "name": name or ("STATUS_FINAL" if state == "post" else "STATUS_SCHEDULED")}}


def competitor(t, home, score=None, lines=None, rank=None):
    c = {"homeAway": "home" if home else "away", "team": t}
    if score is not None:
        c["score"] = str(score)
    if lines:
        c["linescores"] = [{"value": float(v)} for v in lines]
    if rank:
        c["curatedRank"] = {"current": rank}
    return c


def event(eid, when, away, home, st, odds=None, neutral=False):
    comp = {"id": eid, "date": when, "competitors": [away, home], "status": st,
            "neutralSite": neutral}
    if odds:
        comp["odds"] = [odds]
    return {"id": eid, "date": when, "name": "", "competitions": [comp], "status": st}


def season(t):
    return [{"season": {"type": {"type": t}}}]


# ══ NBA ══════════════════════════════════════════════════════════════════════
GSW = team(9, "Golden State", "Warriors", "GS")
ORL = team(19, "Orlando", "Magic", "ORL")
DAL = team(6, "Dallas", "Mavericks", "DAL")
OKC = team(25, "Oklahoma City", "Thunder", "OKC")
LAL = team(13, "Los Angeles", "Lakers", "LAL")
SAC = team(23, "Sacramento", "Kings", "SAC")

nba_y = {"leagues": season(2), "events": [
    event("401", "2026-11-16T03:30Z", competitor(ORL, False, 100, [25, 20, 30, 25]),
          competitor(GSW, True, 118, [30, 28, 31, 29]), status("post")),
    event("402", "2026-11-16T01:00Z", competitor(DAL, False, 99, [20, 22, 25, 22, 10]),
          competitor(OKC, True, 112, [18, 26, 30, 16, 22]), status("post", "Final/OT")),
]}
nba_t = {"leagues": season(2), "events": [
    event("403", "2026-11-17T03:00Z", competitor(LAL, False), competitor(SAC, True), status("pre", "Scheduled"),
          odds={"details": "LAL -3.5", "overUnder": 226.5, "awayTeamOdds": {"favorite": True}, "homeTeamOdds": {"favorite": False}}),
    event("404", "2026-11-17T00:00Z", competitor(ORL, False), competitor(OKC, True), status("pre", "Scheduled"),
          odds={"details": "OKC -11", "overUnder": 219.0}),
]}
nba_t2 = {"leagues": season(2), "events": [
    event("405", "2026-11-18T03:30Z", competitor(DAL, False), competitor(GSW, True), status("pre", "Scheduled"))]}
save(sb_url("basketball/nba", Y), nba_y)
save(sb_url("basketball/nba", T), nba_t)
save(sb_url("basketball/nba", T2), nba_t2)

NBA_KEYS = ["minutes", "points", "fieldGoalsMade-fieldGoalsAttempted",
            "threePointFieldGoalsMade-threePointFieldGoalsAttempted",
            "freeThrowsMade-freeThrowsAttempted", "rebounds", "assists", "turnovers",
            "steals", "blocks", "offensiveRebounds", "defensiveRebounds", "fouls", "plusMinus"]
NBA_LABELS = ["MIN", "PTS", "FG", "3PT", "FT", "REB", "AST", "TO", "STL", "BLK", "OREB", "DREB", "PF", "+/-"]


def nba_player(pid, name, mins, fg, tp, ft, oreb, dreb, ast, to, stl, blk, pf, starter=True):
    fgm, fga = fg; tpm, tpa = tp; ftm, fta = ft
    pts = 2 * fgm + tpm + ftm
    return {"athlete": {"id": str(pid), "displayName": name}, "starter": starter, "didNotPlay": False,
            "stats": [str(mins), str(pts), f"{fgm}-{fga}", f"{tpm}-{tpa}", f"{ftm}-{fta}",
                      str(oreb + dreb), str(ast), str(to), str(stl), str(blk), str(oreb), str(dreb), str(pf), "+5"]}


def nba_summary(away, home, a_lines, h_lines, a_players, h_players, att):
    def tp(t, players):
        return {"team": t, "statistics": [{"keys": NBA_KEYS, "labels": NBA_LABELS, "athletes": players + [
            {"athlete": {"id": "999" + t["id"], "displayName": "Bench Guy"}, "didNotPlay": True,
             "reason": "COACH'S DECISION", "stats": []}]}]}
    return {
        "header": {"season": {"type": 2}, "competitions": [{"status": status("post", "Final/OT" if len(a_lines) > 4 else "Final"),
                   "competitors": [competitor(away, False, sum(a_lines), a_lines),
                                   competitor(home, True, sum(h_lines), h_lines)]}]},
        "boxscore": {"teams": [
            {"team": away, "statistics": [{"name": "teamRebounds", "displayValue": "8"},
                                          {"name": "totalTurnovers", "displayValue": "14"},
                                          {"name": "turnoverPoints", "displayValue": "17"}]},
            {"team": home, "statistics": [{"name": "teamRebounds", "displayValue": "10"},
                                          {"name": "totalTurnovers", "displayValue": "11"},
                                          {"name": "turnoverPoints", "displayValue": "12"},
                                          {"name": "technicalFouls", "displayValue": "1"}]}],
            "players": [tp(away, a_players), tp(home, h_players)]},
        "gameInfo": {"attendance": att, "venue": {"fullName": "Arena", "capacity": 18064}},
    }


save(espn._url(espn.SITE, "basketball/nba", "summary", {"event": "401"}), nba_summary(
    ORL, GSW, [25, 20, 30, 25], [30, 28, 31, 29],
    [nba_player(1, "Paolo Banchero", 36, (10, 21), (2, 6), (6, 8), 2, 7, 5, 3, 1, 1, 3),
     nba_player(2, "Franz Wagner", 34, (8, 16), (2, 5), (4, 4), 1, 5, 4, 2, 2, 0, 2),
     nba_player(3, "Moritz Wagner", 18, (3, 7), (1, 2), (0, 0), 2, 3, 1, 1, 0, 0, 4, starter=False),
     nba_player(4, "Jalen Suggs", 30, (4, 11), (2, 7), (2, 2), 0, 3, 6, 2, 3, 1, 3),
     nba_player(5, "Wendell Carter Jr.", 28, (5, 9), (0, 1), (1, 2), 4, 6, 2, 1, 0, 2, 2)],
    [nba_player(11, "Stephen Curry", 33, (11, 20), (6, 12), (5, 5), 0, 5, 7, 3, 2, 0, 1),
     nba_player(12, "Draymond Green", 30, (3, 6), (1, 3), (0, 0), 2, 8, 9, 2, 2, 2, 4),
     nba_player(13, "Jimmy Butler", 32, (7, 12), (0, 1), (8, 9), 1, 4, 5, 1, 1, 0, 2),
     nba_player(14, "Jonathan Kuminga", 26, (6, 11), (1, 3), (2, 4), 2, 3, 1, 2, 0, 1, 3),
     nba_player(15, "Moses Moody", 22, (3, 6), (3, 5), (0, 0), 0, 2, 1, 0, 1, 0, 2, starter=False),
     nba_player(16, "Brandin Podziemski", 21, (2, 5), (1, 3), (2, 2), 1, 3, 3, 1, 1, 0, 1, starter=False)],
    18064))

save(espn._url(espn.SITE, "basketball/nba", "summary", {"event": "402"}), nba_summary(
    DAL, OKC, [20, 22, 25, 22, 10], [18, 26, 30, 16, 22],
    [nba_player(21, "Luka Doncic", 44, (12, 25), (4, 11), (8, 10), 1, 9, 10, 5, 1, 0, 3),
     nba_player(22, "Kyrie Irving", 40, (9, 19), (3, 7), (2, 2), 0, 3, 6, 2, 2, 1, 2),
     nba_player(23, "Dereck Lively II", 30, (4, 5), (0, 0), (2, 4), 5, 6, 1, 1, 0, 3, 4)],
    [nba_player(31, "Shai Gilgeous-Alexander", 42, (13, 22), (2, 5), (14, 15), 0, 5, 7, 2, 3, 1, 2),
     nba_player(32, "Jalen Williams", 39, (8, 17), (2, 6), (3, 4), 1, 6, 5, 3, 2, 1, 3),
     nba_player(33, "Chet Holmgren", 36, (6, 12), (2, 4), (4, 4), 2, 9, 2, 1, 0, 4, 4)],
    0))

nba_st = {"children": [
    {"name": "Western Conference", "children": [
        {"name": "Pacific Division", "standings": {"entries": [
            {"team": SAC, "stats": [{"name": "wins", "value": 6, "displayValue": "6"}, {"name": "losses", "displayValue": "7"}]},
            {"team": GSW, "stats": [{"name": "wins", "displayValue": "10"}, {"name": "losses", "displayValue": "3"}]},
            {"team": LAL, "stats": [{"name": "wins", "displayValue": "7"}, {"name": "losses", "displayValue": "6"}]}]}},
        {"name": "Southwest Division", "standings": {"entries": [
            {"team": DAL, "stats": [{"name": "wins", "displayValue": "8"}, {"name": "losses", "displayValue": "6"}]}]}},
        {"name": "Northwest Division", "standings": {"entries": [
            {"team": OKC, "stats": [{"name": "wins", "displayValue": "12"}, {"name": "losses", "displayValue": "2"}]}]}}]},
    {"name": "Eastern Conference", "children": [
        {"name": "Southeast Division", "standings": {"entries": [
            {"team": ORL, "stats": [{"name": "wins", "displayValue": "7"}, {"name": "losses", "displayValue": "7"}]}]}}]}]}
save(espn._url(espn.SITE_V2, "basketball/nba", "standings", {"level": 3}), nba_st)
save(espn._url(espn.SITE, "basketball/nba", "transactions"), {"transactions": [
    {"date": "2026-11-15T08:00Z", "team": GSW, "description": "Assigned F Gui Santos to Santa Cruz (G League)."},
    {"date": "2026-11-15T08:00Z", "team": SAC, "description": "Recalled G Devin Carter from Stockton (G League)."},
    {"date": "2026-11-14T08:00Z", "team": ORL, "description": "Old transaction."}]})

# ══ NHL ══════════════════════════════════════════════════════════════════════
SJ = team(18, "San Jose", "Sharks", "SJ")
LA = team(8, "Los Angeles", "Kings", "LA")
NJ = team(1, "New Jersey", "Devils", "NJ")
CHI = team(4, "Chicago", "Blackhawks", "CHI")
nhl_y = {"leagues": season(2), "events": [
    event("501", "2026-11-16T03:00Z", competitor(LA, False, 1, [0, 0, 1, 0, 0]),
          competitor(SJ, True, 2, [0, 1, 0, 0, 1]), status("post", "Final/SO")),
    event("502", "2026-11-16T00:00Z", competitor(NJ, False, 4, [2, 1, 1]),
          competitor(CHI, True, 3, [1, 1, 1]), status("post")),
]}
save(sb_url("hockey/nhl", Y), nhl_y)
save(sb_url("hockey/nhl", T), {"leagues": season(2), "events": [
    event("503", "2026-11-17T00:00Z", competitor(CHI, False), competitor(SJ, True), status("pre"),
          odds={"details": "SJ -125", "overUnder": 6.0, "homeTeamOdds": {"favorite": True}})]})


def nhl_ath(pid, name):
    return {"athlete": {"id": str(pid), "displayName": name}, "stats": ["0"] * 5}


def goalie(pid, name, sa, sv):
    return {"athlete": {"id": str(pid), "displayName": name}, "starter": True,
            "stats": [str(sa - sv), str(sa), str(sv), f".{int(sv / sa * 1000)}"]}


def nhl_box(away, home, a_sk, h_sk, a_g, h_g):
    G = {"name": "goalies", "labels": ["GA", "SA", "SV", "SV%"]}
    F = {"name": "forwards", "labels": ["G", "A", "+/-", "S", "TOI"]}
    return {"players": [
        {"team": away, "statistics": [dict(F, athletes=[nhl_ath(*a) for a in a_sk]), dict(G, athletes=[goalie(*a_g)])]},
        {"team": home, "statistics": [dict(F, athletes=[nhl_ath(*a) for a in h_sk]), dict(G, athletes=[goalie(*h_g)])]}],
        "teams": [{"team": away, "statistics": [{"name": "shotsTotal", "displayValue": "30"},
                                                {"name": "powerPlayGoals", "displayValue": "1"},
                                                {"name": "powerPlayOpportunities", "displayValue": "3"}]},
                  {"team": home, "statistics": [{"name": "shotsTotal", "displayValue": "28"},
                                                {"name": "powerPlayGoals", "displayValue": "0"},
                                                {"name": "powerPlayOpportunities", "displayValue": "2"}]}]}


def play(pid, per, clock, tid, text, kind="Goal", scoring=True, participants=None, strength=None):
    p = {"id": pid, "period": {"number": per}, "clock": {"displayValue": clock},
         "team": {"id": str(tid)}, "text": text, "type": {"text": kind}, "scoringPlay": scoring}
    if participants:
        p["participants"] = [{"athlete": {"id": str(x)}} for x in participants]
    if strength:
        p["strength"] = {"text": strength}
    return p


# Devils-Blackhawks: plays with participants, clock counting DOWN (remaining)
nj_plays = [
    play(1, 1, "19:00", 1, "Shot by Hischier", "Shot", False),
    play(2, 1, "17:20", 1, "Jack Hughes (8) Wrist Shot, assists: Jesper Bratt (12), Dougie Hamilton (6)",
         participants=[101, 102, 103], strength="Power Play"),
    play(3, 1, "12:00", 4, "Connor Bedard (6) Snap Shot, assists: Seth Jones (4)", participants=[201, 202]),
    play(4, 1, "05:00", 1, "Nico Hischier (7) Backhand, assists: none", participants=[104]),
    play(5, 2, "10:00", 1, "Jesper Bratt (5) Wrist Shot, assists: Jack Hughes (9)", participants=[102, 101]),
    play(6, 2, "02:00", 4, "Taylor Hall (3) Slap Shot, assists: Connor Bedard (7), Seth Jones (5)", participants=[203, 201, 202]),
    play(7, 3, "15:30", 4, "Connor Bedard (7) Wrist Shot", participants=[201]),
    play(8, 3, "00:45", 1, "Jack Hughes (9) Empty Net, assists: Nico Hischier (4)", participants=[101, 104],
         strength="Empty Net"),
]
save(espn._url(espn.SITE, "hockey/nhl", "summary", {"event": "502"}), {
    "header": {"season": {"type": 2}, "competitions": [{"status": status("post"),
               "competitors": [competitor(NJ, False, 4, [2, 1, 1]), competitor(CHI, True, 3, [1, 1, 1])]}]},
    "boxscore": nhl_box(NJ, CHI, [(101, "Jack Hughes"), (102, "Jesper Bratt"), (103, "Dougie Hamilton"), (104, "Nico Hischier")],
                        [(201, "Connor Bedard"), (202, "Seth Jones"), (203, "Taylor Hall")],
                        (150, "Jacob Markstrom", 28, 25), (250, "Petr Mrazek", 30, 26)),
    "plays": nj_plays, "gameInfo": {"attendance": 18977}})

# Sharks-Kings shootout: scoringPlays only, text-only (no participants)
save(espn._url(espn.SITE, "hockey/nhl", "summary", {"event": "501"}), {
    "header": {"season": {"type": 2}, "competitions": [{"status": status("post", "Final/SO"),
               "competitors": [competitor(LA, False, 1, [0, 0, 1, 0, 0]), competitor(SJ, True, 2, [0, 1, 0, 0, 1])]}]},
    "boxscore": nhl_box(LA, SJ, [(301, "Anze Kopitar"), (302, "Adrian Kempe"), (303, "Drew Doughty")],
                        [(401, "Macklin Celebrini"), (402, "William Eklund"), (403, "Tyler Toffoli")],
                        (350, "Darcy Kuemper", 29, 28), (450, "Yaroslav Askarov", 30, 29)),
    "scoringPlays": [
        play(1, 2, "6:12", 18, "Macklin Celebrini (9) Wrist Shot, assists: William Eklund (7), Tyler Toffoli (5)"),
        play(2, 3, "14:40", 8, "Adrian Kempe (10) Snap Shot, assists: Anze Kopitar (11)", strength="Power Play"),
        play(3, 5, "0:00", 18, "Macklin Celebrini Shootout Goal"),
        play(4, 5, "0:00", 18, "William Eklund Shootout Goal"),
    ], "gameInfo": {"attendance": 17435, "venue": {"capacity": 17562}}})

save(espn._url(espn.SITE_V2, "hockey/nhl", "standings", {"level": 3}), {"children": [
    {"name": "Western Conference", "children": [{"name": "Pacific Division", "standings": {"entries": [
        {"team": SJ, "stats": [{"name": "wins", "displayValue": "9"}, {"name": "losses", "displayValue": "7"},
                               {"name": "otLosses", "displayValue": "2"}, {"name": "points", "displayValue": "20"},
                               {"name": "pointsFor", "displayValue": "55"}, {"name": "pointsAgainst", "displayValue": "50"}]},
        {"team": LA, "stats": [{"name": "wins", "displayValue": "10"}, {"name": "losses", "displayValue": "5"},
                               {"name": "otLosses", "displayValue": "3"}, {"name": "points", "displayValue": "23"},
                               {"name": "pointsFor", "displayValue": "60"}, {"name": "pointsAgainst", "displayValue": "48"}]}]}}]}]})

# ══ NFL ══════════════════════════════════════════════════════════════════════
SF = team(25, "San Francisco", "49ers", "SF")
SEA = team(26, "Seattle", "Seahawks", "SEA")
KC = team(12, "Kansas City", "Chiefs", "KC")
DEN = team(7, "Denver", "Broncos", "DEN")
save(sb_url("football/nfl", Y), {"leagues": season(2), "events": [
    event("601", "2026-11-16T00:25Z", competitor(SEA, False, 20, [7, 3, 0, 10]),
          competitor(SF, True, 27, [7, 10, 7, 3]), status("post")),
    event("602", "2026-11-15T21:05Z", competitor(DEN, False, 17, [0, 10, 7, 0]),
          competitor(KC, True, 24, [7, 7, 3, 7]), status("post"))]})
save(sb_url("football/nfl", None), {"leagues": season(2), "events": [
    event("603", "2026-11-17T01:15Z", competitor(DEN, False), competitor(SF, True), status("pre"),
          odds={"details": "SF -6.5", "overUnder": 44.5}),
    event("601", "2026-11-16T00:25Z", competitor(SEA, False, 20), competitor(SF, True, 27), status("post"))]})
save(espn._url(espn.SITE, "football/nfl", "summary", {"event": "601"}), {
    "header": {"competitions": [{"status": status("post"),
               "competitors": [competitor(SEA, False, 20, [7, 3, 0, 10]), competitor(SF, True, 27, [7, 10, 7, 3])]}]},
    "scoringPlays": [
        {"period": {"number": 1}, "clock": {"displayValue": "9:12"}, "team": SEA,
         "text": "Kenneth Walker III 4 Yd Run (Jason Myers Kick)"},
        {"period": {"number": 1}, "clock": {"displayValue": "2:01"}, "team": SF,
         "text": "George Kittle 22 Yd pass from Brock Purdy (Jake Moody Kick)"},
        {"period": {"number": 2}, "clock": {"displayValue": "11:40"}, "team": SF,
         "text": "Jake Moody 41 Yd Field Goal"},
        {"period": {"number": 2}, "clock": {"displayValue": "0:03"}, "team": SEA,
         "text": "Jason Myers 52 Yd Field Goal"},
        {"period": {"number": 2}, "clock": {"displayValue": "0:45"}, "team": SF,
         "text": "Christian McCaffrey 1 Yd Run (Jake Moody Kick)"},
        {"period": {"number": 3}, "clock": {"displayValue": "6:30"}, "team": SF,
         "text": "Deommodore Lenoir 38 Yd Interception Return (Jake Moody Kick)"},
        {"period": {"number": 4}, "clock": {"displayValue": "12:15"}, "team": SEA,
         "text": "DK Metcalf 15 Yd pass from Sam Darnold (Sam Darnold Pass to Jaxon Smith-Njigba for Two-Point Conversion)"},
        {"period": {"number": 4}, "clock": {"displayValue": "8:00"}, "team": SF,
         "text": "Jake Moody 33 Yd Field Goal"},
        {"period": {"number": 4}, "clock": {"displayValue": "1:10"}, "team": SEA,
         "text": "Jason Myers 28 Yd Field Goal"}],
    "boxscore": {
        "teams": [{"team": SEA, "statistics": [
                    {"name": "firstDowns", "displayValue": "18"}, {"name": "totalYards", "displayValue": "311"},
                    {"name": "netPassingYards", "displayValue": "221"}, {"name": "completionAttempts", "displayValue": "22/35"},
                    {"name": "rushingAttempts", "displayValue": "24"}, {"name": "rushingYards", "displayValue": "90"},
                    {"name": "interceptions", "displayValue": "0"}, {"name": "sacksYardsLost", "displayValue": "3-21"},
                    {"name": "totalPenaltiesYards", "displayValue": "6-45"}, {"name": "possessionTime", "displayValue": "28:40"},
                    {"name": "thirdDownEff", "displayValue": "4-12"}]},
                  {"team": SF, "statistics": [
                    {"name": "firstDowns", "displayValue": "22"}, {"name": "totalYards", "displayValue": "380"},
                    {"name": "netPassingYards", "displayValue": "240"}, {"name": "completionAttempts", "displayValue": "20/28"},
                    {"name": "rushingAttempts", "displayValue": "31"}, {"name": "rushingYards", "displayValue": "140"},
                    {"name": "interceptions", "displayValue": "1"}, {"name": "sacksYardsLost", "displayValue": "1-8"},
                    {"name": "totalPenaltiesYards", "displayValue": "4-30"}, {"name": "possessionTime", "displayValue": "31:20"},
                    {"name": "thirdDownEff", "displayValue": "7-13"}]}],
        "players": [
            {"team": SEA, "statistics": [
                {"name": "passing", "labels": ["C/ATT", "YDS", "AVG", "TD", "INT"], "athletes": [
                    {"athlete": {"displayName": "Sam Darnold"}, "stats": ["22/35", "242", "6.9", "1", "1"]}]},
                {"name": "rushing", "labels": ["CAR", "YDS", "AVG", "TD", "LONG"], "athletes": [
                    {"athlete": {"displayName": "Kenneth Walker III"}, "stats": ["18", "70", "3.9", "1", "12"]},
                    {"athlete": {"displayName": "Sam Darnold"}, "stats": ["6", "20", "3.3", "0", "9"]}]},
                {"name": "receiving", "labels": ["REC", "YDS", "AVG", "TD", "LONG"], "athletes": [
                    {"athlete": {"displayName": "DK Metcalf"}, "stats": ["7", "98", "14", "1", "30"]},
                    {"athlete": {"displayName": "Jaxon Smith-Njigba"}, "stats": ["8", "90", "11.3", "0", "22"]}]}]},
            {"team": SF, "statistics": [
                {"name": "passing", "labels": ["C/ATT", "YDS", "AVG", "TD", "INT"], "athletes": [
                    {"athlete": {"displayName": "Brock Purdy"}, "stats": ["20/28", "248", "8.9", "1", "0"]}]},
                {"name": "rushing", "labels": ["CAR", "YDS", "AVG", "TD", "LONG"], "athletes": [
                    {"athlete": {"displayName": "Christian McCaffrey"}, "stats": ["24", "118", "4.9", "1", "21"]}]},
                {"name": "receiving", "labels": ["REC", "YDS", "AVG", "TD", "LONG"], "athletes": [
                    {"athlete": {"displayName": "George Kittle"}, "stats": ["6", "88", "14.7", "1", "31"]},
                    {"athlete": {"displayName": "Deommodore Lenoir"}, "stats": []}]}]}]},
    "gameInfo": {"attendance": 71623}})
save(espn._url(espn.SITE_V2, "football/nfl", "standings", {"level": 3}), {"children": [
    {"name": "National Football Conference", "children": [{"name": "NFC West", "standings": {"entries": [
        {"team": SF, "stats": [{"name": "wins", "displayValue": "7"}, {"name": "losses", "displayValue": "3"},
                               {"name": "ties", "displayValue": "0"}, {"name": "pointsFor", "displayValue": "260"},
                               {"name": "pointsAgainst", "displayValue": "190"},
                               {"name": "Home", "type": "home", "summary": "4-1"}, {"name": "Road", "type": "road", "summary": "3-2"},
                               {"name": "vs. Div.", "type": "vsdiv", "summary": "2-1"}]},
        {"team": SEA, "stats": [{"name": "wins", "displayValue": "6"}, {"name": "losses", "displayValue": "4"},
                                {"name": "ties", "displayValue": "0"}, {"name": "pointsFor", "displayValue": "230"},
                                {"name": "pointsAgainst", "displayValue": "220"},
                                {"name": "Home", "type": "home", "summary": "3-2"}, {"name": "Road", "type": "road", "summary": "3-2"},
                                {"name": "vs. Div.", "type": "vsdiv", "summary": "1-2"}]}]}}]}]})

# ══ College basketball (men) ═════════════════════════════════════════════════
DUKE = team(150, "Duke", "Blue Devils", "DUKE")
STAN = team(24, "Stanford", "Cardinal", "STAN")
UCLA = team(26, "UCLA", "Bruins", "UCLA")
GONZ = team(2250, "Gonzaga", "Bulldogs", "GONZ")
ARMY = team(349, "Army", "Black Knights", "ARMY")
NAVY = team(2426, "Navy", "Midshipmen", "NAVY")
save(sb_url("basketball/mens-college-basketball", Y, {"groups": 50, "limit": 500}), {"leagues": season(2), "events": [
    event("701", "2026-11-15T20:00Z", competitor(UCLA, False, 70, [35, 35]),
          competitor(DUKE, True, 81, [40, 41], rank=3), status("post")),
    event("702", "2026-11-15T22:00Z", competitor(GONZ, False, 77, [30, 47], rank=12),
          competitor(STAN, True, 79, [38, 41]), status("post")),
    event("703", "2026-11-15T18:00Z", competitor(ARMY, False, 60), competitor(NAVY, True, 64), status("post"))]})
save(sb_url("basketball/mens-college-basketball", T, {"groups": 50, "limit": 500}), {"leagues": season(2), "events": [
    event("704", "2026-11-17T02:00Z", competitor(STAN, False, rank=None), competitor(GONZ, True, rank=12), status("pre"),
          odds={"details": "GONZ -9.5", "overUnder": 151.5})]})
save(espn._url(espn.SITE, "basketball/mens-college-basketball", "summary", {"event": "702"}), nba_summary(
    GONZ, STAN, [30, 47], [38, 41],
    [nba_player(801, "Graham Ike", 34, (9, 15), (0, 0), (5, 6), 4, 6, 1, 2, 0, 1, 3)],
    [nba_player(901, "Maxime Raynaud", 36, (10, 18), (2, 5), (3, 4), 3, 8, 2, 1, 1, 2, 2)], 5214))

# ══ College football rankings (Monday paper) ════════════════════════════════
save(espn._url(espn.SITE, "football/college-football", "rankings"), {"rankings": [
    {"name": "AP Top 25", "type": "ap", "ranks": [
        {"current": 1, "previous": 1, "points": 1550, "firstPlaceVotes": 60, "recordSummary": "10-0",
         "team": {"location": "Ohio State", "displayName": "Ohio State Buckeyes"}},
        {"current": 2, "previous": 3, "points": 1480, "firstPlaceVotes": 2, "recordSummary": "10-0",
         "team": {"location": "Indiana", "displayName": "Indiana Hoosiers"}},
        {"current": 3, "previous": 2, "points": 1400, "recordSummary": "9-1",
         "team": {"location": "Texas", "displayName": "Texas Longhorns"}}],
     "others": [{"team": {"location": "California", "displayName": "California Golden Bears"}, "points": 14},
                {"team": {"location": "Army", "displayName": "Army Black Knights"}, "points": 3}]}]})
save(sb_url("football/college-football", Y, {"groups": 80, "limit": 300}), {"leagues": season(2), "events": []})
save(sb_url("football/college-football", None, {"groups": 80, "limit": 300}), {"leagues": season(2), "events": []})

# ══ MLS ══════════════════════════════════════════════════════════════════════
SJE = team(191, "San Jose", "Earthquakes", "SJ", "San Jose Earthquakes")
SJE["shortDisplayName"] = "San Jose"
LAG = team(187, "LA", "Galaxy", "LA", "LA Galaxy")
LAG["shortDisplayName"] = "LA Galaxy"
save(sb_url("soccer/usa.1", Y), {"leagues": season(3), "events": [
    event("801", "2026-11-16T02:00Z", competitor(LAG, False, 1, [0, 1]), competitor(SJE, True, 2, [1, 1]), status("post", "FT"))]})
save(espn._url(espn.SITE, "soccer/usa.1", "summary", {"event": "801"}), {
    "header": {"competitions": [{"status": status("post", "FT"), "competitors": [
        competitor(LAG, False, 1, [0, 1]), competitor(SJE, True, 2, [1, 1])]}]},
    "rosters": [
        {"team": SJE, "roster": [
            {"starter": True, "formationPlace": "1", "athlete": {"displayName": "Daniel"}},
            {"starter": True, "formationPlace": "9", "athlete": {"displayName": "Cristian Espinoza"}},
            {"starter": True, "formationPlace": "10", "athlete": {"displayName": "Josef Martínez"}},
            {"starter": False, "subbedIn": True, "athlete": {"displayName": "Preston Judd"}}]},
        {"team": LAG, "roster": [
            {"starter": True, "formationPlace": "1", "athlete": {"displayName": "John McCarthy"}},
            {"starter": True, "formationPlace": "10", "athlete": {"displayName": "Riqui Puig"}}]}],
    "keyEvents": [
        {"type": {"text": "Goal"}, "team": SJE, "clock": {"displayValue": "34'"},
         "participants": [{"athlete": {"displayName": "Josef Martínez"}}, {"athlete": {"displayName": "Cristian Espinoza"}}]},
        {"type": {"text": "Yellow Card"}, "team": LAG, "clock": {"displayValue": "41'"},
         "participants": [{"athlete": {"displayName": "Riqui Puig"}}]},
        {"type": {"text": "Penalty - Scored"}, "team": LAG, "clock": {"displayValue": "62'"},
         "participants": [{"athlete": {"displayName": "Riqui Puig"}}]},
        {"type": {"text": "Goal - Header"}, "team": SJE, "clock": {"displayValue": "90'+3'"},
         "participants": [{"athlete": {"displayName": "Preston Judd"}}]}],
    "gameInfo": {"attendance": 18000}})

# ══ MLB: off-season (should be hidden) ══════════════════════════════════════
save(sb_url("baseball/mlb", Y), {"leagues": season(4), "events": []})
save(sb_url("baseball/mlb", T), {"leagues": season(4), "events": []})

# ══ Golf ═════════════════════════════════════════════════════════════════════
save(sb_url("golf/pga"), {"events": [{
    "id": "g1", "name": "The RSM Classic", "date": "2026-11-12T12:00Z", "endDate": "2026-11-15T23:00Z",
    "status": status("post"),
    "competitions": [{"competitors": [
        {"order": 2, "athlete": {"displayName": "Ludvig Åberg"}, "score": "-18",
         "linescores": [{"value": 66}, {"value": 64}, {"value": 67}, {"value": 65}]},
        {"order": 1, "athlete": {"displayName": "Collin Morikawa"}, "score": "-20",
         "linescores": [{"value": 65}, {"value": 64}, {"value": 65}, {"value": 66}]},
        {"order": 3, "athlete": {"displayName": "Max Homa"}, "score": "-18",
         "linescores": [{"value": 67}, {"value": 65}, {"value": 64}, {"value": 66}]},
        {"order": 4, "athlete": {"displayName": "Joel Dahmen"}, "score": "E",
         "linescores": [{"value": 70}, {"value": 70}, {"value": 70}, {"value": 70}]}]}]}]})

# ══ F1 ═══════════════════════════════════════════════════════════════════════
save(sb_url("racing/f1"), {"events": [{
    "id": "f1", "name": "Las Vegas Grand Prix", "date": "2026-11-14T00:00Z",
    "competitions": [
        {"type": {"abbreviation": "Qual"}, "date": "2026-11-14T06:00Z", "status": status("post"), "competitors": []},
        {"type": {"abbreviation": "Race"}, "date": "2026-11-15T06:00Z", "status": status("post"),
         "venue": {"fullName": "Las Vegas Strip Circuit"},
         "competitors": [
             {"order": 2, "athlete": {"displayName": "Lando Norris", "flag": {"alt": "Britain"}}},
             {"order": 1, "athlete": {"displayName": "Max Verstappen", "flag": {"alt": "Netherlands"}}},
             {"order": 3, "athlete": {"displayName": "Charles Leclerc", "flag": {"alt": "Monaco"}}}]}]}]})

# ══ Tennis ═══════════════════════════════════════════════════════════════════
save(sb_url("tennis/atp", Y), {"events": [{
    "id": "t1", "name": "Nitto ATP Finals",
    "groupings": [{"grouping": {"displayName": "Men's Singles"}, "competitions": [
        {"date": "2026-11-15T14:00Z", "status": status("post"), "round": {"displayName": "Final"},
         "competitors": [
             {"winner": True, "athlete": {"displayName": "Jannik Sinner", "flag": {"alt": "Italy"}},
              "linescores": [{"value": 6}, {"value": 7, "tiebreak": 7}]},
             {"winner": False, "athlete": {"displayName": "Carlos Alcaraz", "flag": {"alt": "Spain"}},
              "linescores": [{"value": 4}, {"value": 6, "tiebreak": 5}]}]}]}]}]})

print("fixtures written to", OUT, len(os.listdir(OUT)), "files")
