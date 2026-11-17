#!/usr/bin/env python3
"""
MLB Standings Fetcher
Fetches current MLB standings from the MLB Stats API and returns
structured data ready for the web frontend.

Usage:
    python mlb_standings.py               # prints formatted standings
    import mlb_standings; mlb_standings.fetch_standings()  # returns dict

API endpoint:
    https://statsapi.mlb.com/api/v1/standings?leagueId=103,104&season=YYYY
"""

import json
import urllib.request
from datetime import date


# ── Division metadata ─────────────────────────────────────────────────────────

LEAGUE_IDS = {
    103: "AL",
    104: "NL",
}

DIVISION_NAMES = {
    200: "West",
    201: "East",
    202: "Central",
    203: "West",
    204: "East",
    205: "Central",
}

# Display order: West, Central, East for both leagues
DIVISION_ORDER = {
    "AL": [200, 202, 201],
    "NL": [203, 205, 204],
}

LEAGUE_FOR_DIVISION = {
    200: "AL", 201: "AL", 202: "AL",
    203: "NL", 204: "NL", 205: "NL",
}

# City-only names; Giants and Athletics stay as-is
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


# ── Fetch ─────────────────────────────────────────────────────────────────────

def fetch_standings(season: int = None) -> dict:
    """
    Fetch standings from the MLB API and return a structured dict:
    {
      "AL": {
        200: { "name": "West", "teams": [ {...}, ... ] },
        202: { ... },
        201: { ... },
      },
      "NL": { ... }
    }
    """
    if season is None:
        season = date.today().year

    url = (
        f"https://statsapi.mlb.com/api/v1/standings"
        f"?leagueId=103,104&season={season}"
        f"&standingsTypes=regularSeason"
        f"&hydrate=team,league,division,sport,record(splits(metaData(parent),team,division))"
    )

    with urllib.request.urlopen(url) as resp:
        data = json.loads(resp.read().decode())

    standings = {"AL": {}, "NL": {}}

    for record in data.get("records", []):
        div_id = record["division"]["id"]
        league = LEAGUE_FOR_DIVISION.get(div_id)
        if not league:
            continue

        teams = []
        for t in record["teamRecords"]:
            splits = t["records"].get("splitRecords", [])

            def get_split(split_type):
                s = next((x for x in splits if x["type"] == split_type), None)
                return f"{s['wins']}-{s['losses']}" if s else "-"

            streak_code = t["streak"]["streakCode"]
            streak_type = "Won" if streak_code.startswith("W") else "Lost"
            streak_num  = streak_code[1:]

            gb = t["gamesBack"]
            if gb == "-":
                gb = "—"
            else:
                # Format: "0.5" -> "½", "16.0" -> "16", "8.5" -> "8½"
                try:
                    gb_float = float(gb)
                    whole = int(gb_float)
                    half  = gb_float - whole
                    if half == 0.5:
                        gb = f"{whole}½" if whole > 0 else "½"
                    else:
                        gb = str(whole)
                except (ValueError, TypeError):
                    pass


            teams.append({
                "name":    TEAM_CITY.get(t["team"]["name"], t["team"]["name"]),
                "wins":    t["leagueRecord"]["wins"],
                "losses":  t["leagueRecord"]["losses"],
                "pct":     t["leagueRecord"]["pct"],
                "gb":      gb,
                "streak":  f"{streak_type} {streak_num}",
                "l10":     get_split("lastTen"),
                "home":    get_split("home"),
                "away":    get_split("away"),
            })

        standings[league][div_id] = {
            "name":  DIVISION_NAMES[div_id],
            "teams": teams,
        }

    return standings


# ── Print ─────────────────────────────────────────────────────────────────────

def print_standings(standings: dict):
    col_widths = {
        "name": 18, "wins": 3, "losses": 3, "pct": 5,
        "gb": 5, "streak": 7, "l10": 5, "home": 6, "away": 6,
    }

    def row(team):
        return (
            f"  {team['name']:<{col_widths['name']}}"
            f"  {team['wins']:>{col_widths['wins']}}"
            f"  {team['losses']:>{col_widths['losses']}}"
            f"  {team['pct']:>{col_widths['pct']}}"
            f"  {team['gb']:>{col_widths['gb']}}"
            f"  {team['streak']:<{col_widths['streak']}}"
            f"  {team['l10']:>{col_widths['l10']}}"
            f"  {team['home']:>{col_widths['home']}}"
            f"  {team['away']:>{col_widths['away']}}"
        )

    header = (
        f"  {'':>{col_widths['name']}}"
        f"  {'W':>{col_widths['wins']}}"
        f"  {'L':>{col_widths['losses']}}"
        f"  {'Pct':>{col_widths['pct']}}"
        f"  {'GB':>{col_widths['gb']}}"
        f"  {'Streak':<{col_widths['streak']}}"
        f"  {'L10':>{col_widths['l10']}}"
        f"  {'Home':>{col_widths['home']}}"
        f"  {'Away':>{col_widths['away']}}"
    )

    for league in ["NL", "AL"]:
        print("=" * 70)
        print(f"  {league}")
        print("=" * 70)

        for div_id in DIVISION_ORDER[league]:
            if div_id not in standings[league]:
                continue
            div = standings[league][div_id]
            print(f"\n  {div['name'].upper()}")
            print(header)
            print("  " + "-" * 68)
            for team in div["teams"]:
                print(row(team))

        print()


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    season = date.today().year
    print(f"Fetching MLB standings for {season}...\n")
    standings = fetch_standings(season)
    print_standings(standings)


if __name__ == "__main__":
    main()
