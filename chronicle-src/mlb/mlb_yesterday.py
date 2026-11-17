#!/usr/bin/env python3
"""
MLB Yesterday's Box Scores
Fetches all games from yesterday and prints a box score for each.

Usage:
    python mlb_yesterday.py
"""

import json
import urllib.request
from datetime import date, timedelta

# ── shared display helpers from mlb_boxscore.py ──────────────────────────────

import unicodedata


def normalize_name(name: str) -> str:
    return "".join(
        c for c in unicodedata.normalize("NFD", name)
        if unicodedata.category(c) != "Mn"
    )


def print_separator(char="─", width=60):
    print(char * width)


def print_team_batting(team_label: str, team_data: dict):
    players = team_data.get("players", {})
    batting_order = team_data.get("battingOrder", [])

    batters = []
    for pid in batting_order:
        key = f"ID{pid}"
        player = players.get(key)
        if not player:
            continue
        raw_name = player["person"]["boxscoreName"]
        pos = player.get("allPositions", [{}])[0].get("abbreviation", "?")
        bat = player["stats"].get("batting", {})
        avg = player.get("seasonStats", {}).get("batting", {}).get("avg", ".---")
        label = f"{normalize_name(raw_name)}, {pos.lower()}"
        batters.append((raw_name, label, bat, avg))

    seen_names = {b[0] for b in batters}
    for key, player in players.items():
        bat = player["stats"].get("batting", {})
        if not bat:
            continue
        raw_name = player["person"]["boxscoreName"]
        if raw_name in seen_names:
            continue
        pos = player.get("allPositions", [{}])[0].get("abbreviation", "?")
        avg = player.get("seasonStats", {}).get("batting", {}).get("avg", ".---")
        label = f"{normalize_name(raw_name)}, {pos.lower()}"
        batters.append((raw_name, label, bat, avg))

    print(f"\n  {'BATTING':<32} {'AB':<4} {'R':<4} {'H':<4} {'RBI':<5} {'BB':<4} {'K':<4} {'AVG'}")
    print(f"  {'─'*32} {'─'*3} {'─'*3} {'─'*3} {'─'*4} {'─'*3} {'─'*3} {'─'*5}")
    for raw_name, label, bat, avg in batters:
        ab  = bat.get("atBats", 0)
        r   = bat.get("runs", 0)
        h   = bat.get("hits", 0)
        rbi = bat.get("rbi", 0)
        bb  = bat.get("baseOnBalls", 0)
        k   = bat.get("strikeOuts", 0)
        print(f"  {label:<32} {ab:<4} {r:<4} {h:<4} {rbi:<5} {bb:<4} {k:<4} {avg}")


def print_team_pitching(team_label: str, team_data: dict):
    pitchers = team_data.get("pitchers", [])
    players  = team_data.get("players", {})

    print(f"\n  {'PITCHING':<28} {'IP':<7} {'H':<4} {'R':<4} {'ER':<4} "
          f"{'BB':<4} {'K':<4} {'HR':<4} {'NOTE'}")
    print(f"  {'─'*28} {'─'*6} {'─'*3} {'─'*3} {'─'*3} "
          f"{'─'*3} {'─'*3} {'─'*3} {'─'*15}")

    for pid in pitchers:
        key = f"ID{pid}"
        player = players.get(key)
        if not player:
            continue
        name = normalize_name(player["person"]["boxscoreName"])
        p = player["stats"].get("pitching", {})
        if not p:
            continue
        ip   = p.get("inningsPitched", "0.0")
        h    = p.get("hits", 0)
        r    = p.get("runs", 0)
        er   = p.get("earnedRuns", 0)
        bb   = p.get("baseOnBalls", 0)
        k    = p.get("strikeOuts", 0)
        hr   = p.get("homeRuns", 0)
        note = p.get("note", "")
        print(f"  {name:<28} {ip:<7} {h:<4} {r:<4} {er:<4} "
              f"{bb:<4} {k:<4} {hr:<4} {note}")

    ts = team_data.get("teamStats", {}).get("pitching", {})
    print(f"\n  Totals: {ts.get('inningsPitched','0.0')} IP, "
          f"{ts.get('hits',0)} H, {ts.get('runs',0)} R, "
          f"{ts.get('earnedRuns',0)} ER, {ts.get('baseOnBalls',0)} BB, "
          f"{ts.get('strikeOuts',0)} K")


def print_team_notes(team_data: dict):
    notes = team_data.get("notes", [])
    if notes:
        print("\n  Notes:")
        for note in notes:
            print(f"    {note}")


def print_boxscore(data: dict):
    teams = data.get("teams", {})
    away  = teams.get("away", {})
    home  = teams.get("home", {})

    away_name = away.get("team", {}).get("name", "Away")
    home_name = home.get("team", {}).get("name", "Home")
    away_runs = away.get("teamStats", {}).get("batting", {}).get("runs", "?")
    home_runs = home.get("teamStats", {}).get("batting", {}).get("runs", "?")

    print_separator("═")
    print(f"  MLB BOX SCORE")
    print(f"  {away_name} ({away_runs})  vs  {home_name} ({home_runs})")
    print_separator("═")

    print(f"\n{'━'*60}")
    print(f"  {away_name.upper()} — BATTING")
    print_team_batting("AWAY", away)
    print(f"\n  {away_name.upper()} — PITCHING")
    print_team_pitching("AWAY", away)
    print_team_notes(away)

    print(f"\n{'━'*60}")
    print(f"  {home_name.upper()} — BATTING")
    print_team_batting("HOME", home)
    print(f"\n  {home_name.upper()} — PITCHING")
    print_team_pitching("HOME", home)
    print_team_notes(home)

    info = data.get("info", [])
    if info:
        print(f"\n{'━'*60}")
        print("  GAME INFO\n")
        for item in info:
            label = item.get("label", "")
            value = item.get("value", "")
            if label and value:
                print(f"  {label}: {value}")

    print_separator("═")


# ── schedule + main ──────────────────────────────────────────────────────────

def fetch_json(url: str) -> dict:
    with urllib.request.urlopen(url) as resp:
        return json.loads(resp.read().decode())


TEAM_CITY = {
    "Arizona Diamondbacks":  "Arizona",
    "Atlanta Braves":        "Atlanta",
    "Baltimore Orioles":     "Baltimore",
    "Boston Red Sox":        "Boston",
    "Chicago Cubs":          "Chicago",
    "Chicago White Sox":     "Chicago",
    "Cincinnati Reds":       "Cincinnati",
    "Cleveland Guardians":   "Cleveland",
    "Colorado Rockies":      "Colorado",
    "Detroit Tigers":        "Detroit",
    "Houston Astros":        "Houston",
    "Kansas City Royals":    "Kansas City",
    "Los Angeles Angels":    "L.A. Angels",
    "Los Angeles Dodgers":   "L.A. Dodgers",
    "Miami Marlins":         "Miami",
    "Milwaukee Brewers":     "Milwaukee",
    "Minnesota Twins":       "Minnesota",
    "New York Mets":         "N.Y. Mets",
    "New York Yankees":      "N.Y. Yankees",
    "Oakland Athletics":     "Athletics",
    "Athletics":             "Athletics",
    "Philadelphia Phillies": "Philadelphia",
    "Pittsburgh Pirates":    "Pittsburgh",
    "San Diego Padres":      "San Diego",
    "San Francisco Giants":  "Giants",
    "Seattle Mariners":      "Seattle",
    "St. Louis Cardinals":   "St. Louis",
    "Tampa Bay Rays":        "Tampa Bay",
    "Texas Rangers":         "Texas",
    "Toronto Blue Jays":     "Toronto",
    "Washington Nationals":  "Washington",
}


def fetch_schedule(target_date: date) -> list:
    """Return list of game dicts for target_date.
    Each dict has: game_pk, status ('Final' or 'Postponed'), away_name, home_name.
    """
    date_str = target_date.strftime("%Y-%m-%d")
    url = f"https://statsapi.mlb.com/api/v1/schedule?sportId=1&date={date_str}"
    data = fetch_json(url)

    games = []
    for day in data.get("dates", []):
        for game in day.get("games", []):
            state    = game.get("status", {}).get("abstractGameState", "")
            detailed = game.get("status", {}).get("detailedState", "")
            away_full = game["teams"]["away"]["team"]["name"]
            home_full = game["teams"]["home"]["team"]["name"]
            away_city = TEAM_CITY.get(away_full, away_full)
            home_city = TEAM_CITY.get(home_full, home_full)

            game_number = game.get("gameNumber", 1)

            if "Postponed" in detailed or "Suspended" in detailed:
                games.append({
                    "game_pk":    game["gamePk"],
                    "status":     "Postponed",
                    "away_city":  away_city,
                    "home_city":  home_city,
                })
            elif state == "Final":
                games.append({
                    "game_pk":    game["gamePk"],
                    "status":     "Final",
                    "away_city":  away_city,
                    "home_city":  home_city,
                })
    return games


def fetch_boxscore(game_pk: int) -> dict:
    url = f"https://statsapi.mlb.com/api/v1/game/{game_pk}/boxscore"
    return fetch_json(url)


def fetch_linescore(game_pk: int) -> dict:
    url = f"https://statsapi.mlb.com/api/v1/game/{game_pk}/linescore"
    return fetch_json(url)


def main():
    yesterday = date.today() - timedelta(days=1)
    print(f"Fetching MLB schedule for {yesterday.strftime('%B %d, %Y')}...\n")

    game_pks = fetch_schedule(yesterday)

    if not game_pks:
        print("No completed games found for yesterday.")
        return

    print(f"Found {len(game_pks)} game(s). Fetching box scores...\n")

    for i, game_pk in enumerate(game_pks, 1):
        print(f"\n[Game {i} of {len(game_pks)} — gamePk: {game_pk}]")
        try:
            data = fetch_boxscore(game_pk)
            print_boxscore(data)
        except Exception as e:
            print(f"  Error fetching box score for gamePk {game_pk}: {e}")

    print(f"\nDone. {len(game_pks)} game(s) processed.")


if __name__ == "__main__":
    main()
