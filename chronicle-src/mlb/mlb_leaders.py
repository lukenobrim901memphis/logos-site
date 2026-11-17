#!/usr/bin/env python3
"""
MLB League Leaders Fetcher
Fetches NL and AL statistical leaders from the MLB Stats API.

Usage:
    python mlb_leaders.py
    import mlb_leaders; mlb_leaders.fetch_leaders()
"""

import json
import urllib.request
from datetime import date


# ── Config ────────────────────────────────────────────────────────────────────

LEAGUE_IDS = {"NL": 104, "AL": 103}

# Categories to fetch, in display order
# (api_name, display_label, stat_group)
BATTING_CATEGORIES = [
    ("battingAverage",   "BATTING AVG",  "hitting"),
    ("runs",             "RUNS",         "hitting"),
    ("hits",             "HITS",         "hitting"),
    ("homeRuns",         "HOME RUNS",    "hitting"),
    ("rbi",              "RBI",          "hitting"),
]

PITCHING_CATEGORIES = [
    ("wins",             "WINS",         "pitching"),
    ("era",              "ERA",          "pitching"),
    ("strikeOuts",       "STRIKEOUTS",   "pitching"),
]

ALL_CATEGORIES = BATTING_CATEGORIES + PITCHING_CATEGORIES

LIMIT = 5  # top N per category

# Short team abbreviations
TEAM_SHORT = {
    "Arizona Diamondbacks":  "Ari",
    "Atlanta Braves":        "Atl",
    "Baltimore Orioles":     "Bal",
    "Boston Red Sox":        "Bos",
    "Chicago Cubs":          "ChC",
    "Chicago White Sox":     "ChS",
    "Cincinnati Reds":       "Cin",
    "Cleveland Guardians":   "Cle",
    "Colorado Rockies":      "Col",
    "Detroit Tigers":        "Det",
    "Houston Astros":        "Hou",
    "Kansas City Royals":    "KC",
    "Los Angeles Angels":    "LAA",
    "Los Angeles Dodgers":   "LAD",
    "Miami Marlins":         "Mia",
    "Milwaukee Brewers":     "Mil",
    "Minnesota Twins":       "Min",
    "New York Mets":         "NYM",
    "New York Yankees":      "NYY",
    "Athletics":             "Oak",
    "Oakland Athletics":     "Oak",
    "Philadelphia Phillies": "Phi",
    "Pittsburgh Pirates":    "Pit",
    "San Diego Padres":      "SD",
    "San Francisco Giants":  "SF",
    "Seattle Mariners":      "Sea",
    "St. Louis Cardinals":   "StL",
    "Tampa Bay Rays":        "TB",
    "Texas Rangers":         "Tex",
    "Toronto Blue Jays":     "Tor",
    "Washington Nationals":  "Was",
}


# ── Helpers ───────────────────────────────────────────────────────────────────

def full_last_name(full_name: str) -> str:
    """Return full last name only."""
    parts = full_name.strip().split()
    if not parts:
        return full_name
    # Drop suffixes
    suffixes = {"jr.", "sr.", "ii", "iii", "iv"}
    if parts[-1].lower().rstrip(".") in suffixes and len(parts) >= 2:
        return parts[-2]
    return parts[-1]


def fmt_value(category: str, value: str) -> str:
    if category == "battingAverage" or category == "era":
        return value
    return str(value)


def fetch_player_stats(person_id: int, season: int) -> dict:
    """Fetch a single player's season hitting stats."""
    url = (
        f"https://statsapi.mlb.com/api/v1/people/{person_id}"
        f"?hydrate=stats(group=hitting,type=season,season={season})"
    )
    try:
        with urllib.request.urlopen(url, timeout=5) as resp:
            data = json.loads(resp.read().decode())
        for sg in data.get("people", [{}])[0].get("stats", []):
            splits = sg.get("splits", [])
            if splits:
                s = splits[0].get("stat", {})
                return {
                    "g":  s.get("gamesPlayed", ""),
                    "ab": s.get("atBats", ""),
                    "r":  s.get("runs", ""),
                    "h":  s.get("hits", ""),
                }
    except Exception:
        pass
    return {}


def fetch_category(league_id: int, category: str, stat_group: str) -> list:
    """
    Fetch top LIMIT leaders for one category/league.
    For battingAverage, also fetches G, AB, R, H per player.
    """
    season = date.today().year
    url = (
        f"https://statsapi.mlb.com/api/v1/stats/leaders"
        f"?leaderCategories={category}"
        f"&sportId=1"
        f"&limit={LIMIT}"
        f"&season={season}"
        f"&statGroup={stat_group}"
        f"&leagueId={league_id}"
        f"&hydrate=person,team"
    )
    with urllib.request.urlopen(url, timeout=10) as resp:
        data = json.loads(resp.read().decode())

    results = []
    for league_block in data.get("leagueLeaders", []):
        for leader in league_block.get("leaders", []):
            full_name  = leader.get("person", {}).get("fullName", "")
            person_id  = leader.get("person", {}).get("id")
            team_name  = leader.get("team", {}).get("name", "")
            value      = leader.get("value", "")
            entry = {
                "name":  full_last_name(full_name),
                "team":  TEAM_SHORT.get(team_name, team_name[:3]),
                "value": fmt_value(category, value),
            }
            # For batting average, fetch G/AB/R/H from player stats endpoint
            if category == "battingAverage" and person_id:
                pstats = fetch_player_stats(person_id, season)
                entry.update(pstats)
            results.append(entry)
    return results


def fetch_leaders() -> dict:
    """
    Returns:
    {
      "NL": {
        "BATTING AVG": [{"name": "Murphy", "team": "Was", "value": ".333"}, ...],
        "RUNS":        [...],
        ...
      },
      "AL": { ... }
    }
    """
    leaders = {"NL": {}, "AL": {}}
    for league, league_id in LEAGUE_IDS.items():
        for api_name, label, stat_group in ALL_CATEGORIES:
            try:
                leaders[league][label] = fetch_category(league_id, api_name, stat_group)
            except Exception as e:
                print(f"  Warning: could not fetch {league} {label}: {e}")
                leaders[league][label] = []
    return leaders


# ── Print ─────────────────────────────────────────────────────────────────────

def print_leaders(leaders: dict):
    for league in ("NL", "AL"):
        print(f"\n{'='*50}")
        print(f"  {league} Leaders")
        print(f"{'='*50}")
        for label, entries in leaders[league].items():
            print(f"\n  {label}—", end="")
            parts = [f"{e['name']}, {e['team']}, {e['value']}" for e in entries]
            print("; ".join(parts))


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    print("Fetching MLB league leaders...\n")
    leaders = fetch_leaders()
    print_leaders(leaders)


if __name__ == "__main__":
    main()
