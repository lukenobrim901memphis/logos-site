#!/usr/bin/env python3
"""
MLB Schedule Fetcher
Fetches today's and tomorrow's MLB schedules from the MLB Stats API.
Returns structured data with team names, probable starters (last name only),
and game times in local ET.

Usage:
    python mlb_schedule.py               # prints formatted schedule
    import mlb_schedule; mlb_schedule.fetch_schedule_two_days()  # returns dict
"""

import json
import urllib.request
from datetime import date, timedelta, datetime, timezone


# ── Helpers ───────────────────────────────────────────────────────────────────

# City-only team names (Giants and Athletics kept as-is per Chronicle style)
TEAM_SHORT = {
    "Arizona Diamondbacks":    "Arizona",
    "Atlanta Braves":          "Atlanta",
    "Baltimore Orioles":       "Baltimore",
    "Boston Red Sox":          "Boston",
    "Chicago Cubs":            "Chicago",
    "Chicago White Sox":       "Chicago",
    "Cincinnati Reds":         "Cincinnati",
    "Cleveland Guardians":     "Cleveland",
    "Colorado Rockies":        "Colorado",
    "Detroit Tigers":          "Detroit",
    "Houston Astros":          "Houston",
    "Kansas City Royals":      "Kansas City",
    "Los Angeles Angels":      "L.A. Angels",
    "Los Angeles Dodgers":     "L.A. Dodgers",
    "Miami Marlins":           "Miami",
    "Milwaukee Brewers":       "Milwaukee",
    "Minnesota Twins":         "Minnesota",
    "New York Mets":           "N.Y. Mets",
    "New York Yankees":        "N.Y. Yankees",
    "Oakland Athletics":       "Athletics",
    "Athletics":               "Athletics",
    "Philadelphia Phillies":   "Philadelphia",
    "Pittsburgh Pirates":      "Pittsburgh",
    "San Diego Padres":        "San Diego",
    "San Francisco Giants":    "Giants",
    "Seattle Mariners":        "Seattle",
    "St. Louis Cardinals":     "St. Louis",
    "Tampa Bay Rays":          "Tampa Bay",
    "Texas Rangers":           "Texas",
    "Toronto Blue Jays":       "Toronto",
    "Washington Nationals":    "Washington",
}

# PT offset (UTC-7 during PDT, UTC-8 during PST)
ET_OFFSET = -7


from mlb_boxscore import normalize_name

def last_name(full_name: str) -> str:
    """Return last name only, handling suffixes like Jr., Sr., II, III."""
    if not full_name or full_name == "TBD":
        return "TBD"
    clean = normalize_name(full_name)
    parts = clean.strip().split()
    if len(parts) == 1:
        return parts[0]
    suffixes = {"jr.", "sr.", "ii", "iii", "iv"}
    if parts[-1].lower().rstrip(".") in suffixes:
        return parts[-2] if len(parts) >= 2 else parts[-1]
    return parts[-1]


def fmt_time(utc_str: str) -> str:
    """Convert UTC ISO string to ET time string like '6:40 p.m.'"""
    dt = datetime.fromisoformat(utc_str.replace("Z", "+00:00"))
    et = dt + timedelta(hours=ET_OFFSET)
    hour = et.hour % 12 or 12
    minute = et.minute
    ampm = "a.m." if et.hour < 12 else "p.m."
    if minute == 0:
        return f"{hour} {ampm}"
    return f"{hour}:{minute:02d} {ampm}"


def short_name(full: str) -> str:
    return TEAM_SHORT.get(full, full)


# ── Fetch ─────────────────────────────────────────────────────────────────────


def fetch_pitcher_record(person_id: int) -> str:
    """
    Fetch a pitcher's current season W-L record.
    Returns a string like '6-2', or '0-0' if the pitcher has no
    recorded stats yet this season (e.g. making their MLB debut).
    """
    season = date.today().year
    url = (
        f"https://statsapi.mlb.com/api/v1/people/{person_id}"
        f"?hydrate=stats(group=pitching,type=season,season={season})"
    )
    try:
        with urllib.request.urlopen(url, timeout=5) as resp:
            data = json.loads(resp.read().decode())
        for stat_group in data.get("people", [{}])[0].get("stats", []):
            splits = stat_group.get("splits", [])
            if splits:
                s = splits[0].get("stat", {})
                w = s.get("wins", 0)
                l = s.get("losses", 0)
                return f"{w}-{l}"
        # No splits found at all (no season stats on record) — treat as 0-0
        return "0-0"
    except Exception:
        pass
    return "0-0"


def fetch_day(target_date: date) -> list:
    """
    Fetch schedule for a single date. Returns a list of game dicts:
    [
      {
        "away": "Marlins",
        "away_pitcher": "Gusto",      # last name only, or "TBD"
        "home": "Phillies",
        "home_pitcher": "Wheeler",
        "time": "6:40 p.m.",
        "game_pk": 823452,
      },
      ...
    ]
    Sorted by game time.
    """
    date_str = target_date.strftime("%Y-%m-%d")
    url = (
        f"https://statsapi.mlb.com/api/v1/schedule"
        f"?sportId=1&date={date_str}"
        f"&hydrate=probablePitcher,team"
    )
    with urllib.request.urlopen(url) as resp:
        data = json.loads(resp.read().decode())

    # First pass: collect all games and pitcher IDs
    raw_games = []
    pitcher_ids = set()

    for day in data.get("dates", []):
        for g in day.get("games", []):
            away = g["teams"]["away"]
            home = g["teams"]["home"]
            away_prob = away.get("probablePitcher", {})
            home_prob = home.get("probablePitcher", {})
            away_id = away_prob.get("id")
            home_id = home_prob.get("id")
            if away_id:
                pitcher_ids.add(away_id)
            if home_id:
                pitcher_ids.add(home_id)
            raw_games.append({
                "away":         short_name(away["team"]["name"]),
                "away_pitcher": last_name(away_prob.get("fullName", "TBD")),
                "away_id":      away_id,
                "home":         short_name(home["team"]["name"]),
                "home_pitcher": last_name(home_prob.get("fullName", "TBD")),
                "home_id":      home_id,
                "time":         fmt_time(g["gameDate"]),
                "game_pk":      g["gamePk"],
                "game_date":    g["gameDate"],
            })

    # Batch-fetch pitcher records
    records = {}
    for pid in pitcher_ids:
        records[pid] = fetch_pitcher_record(pid)

    # Second pass: attach records to games
    games = []
    for g in raw_games:
        away_rec = records.get(g["away_id"], "")
        home_rec = records.get(g["home_id"], "")
        away_str = g["away_pitcher"]
        if away_rec:
            away_str += f" {away_rec}"
        home_str = g["home_pitcher"]
        if home_rec:
            home_str += f" {home_rec}"
        games.append({
            "away":         g["away"],
            "away_pitcher": away_str,
            "home":         g["home"],
            "home_pitcher": home_str,
            "time":         g["time"],
            "game_pk":      g["game_pk"],
            "game_date":    g["game_date"],
        })

    games.sort(key=lambda g: g["game_date"])
    return games


def fetch_schedule_two_days() -> dict:
    """
    Returns:
    {
      "today":    { "label": "Monday's Games",    "games": [...] },
      "tomorrow": { "label": "Tuesday's Games",   "games": [...] },
    }
    """
    today    = date.today()
    tomorrow = today + timedelta(days=1)

    day_names = [
        "Sunday", "Monday", "Tuesday", "Wednesday",
        "Thursday", "Friday", "Saturday"
    ]

    return {
        "today": {
            "label": f"{day_names[today.weekday() + 1 if today.weekday() < 6 else 0]}'s Games",
            "games": fetch_day(today),
        },
        "tomorrow": {
            "label": f"{day_names[tomorrow.weekday() + 1 if tomorrow.weekday() < 6 else 0]}'s Games",
            "games": fetch_day(tomorrow),
        },
    }


# ── Print ─────────────────────────────────────────────────────────────────────

def print_schedule(schedule: dict):
    for key in ("today", "tomorrow"):
        section = schedule[key]
        print(f"\n{section['label'].upper()}")
        print("-" * 55)

        include_pitchers = (key == "today")

        if include_pitchers:
            print(f"  {'Visitor':<28} {'Home':<28} {'Time'}")
            print(f"  {'-'*27} {'-'*27} {'-'*10}")
            for g in section["games"]:
                away = f"{g['away']} ({g['away_pitcher']})"
                home = f"{g['home']} ({g['home_pitcher']})"
                print(f"  {away:<28} {home:<28} {g['time']}")
        else:
            # Tomorrow: two-column layout, no pitchers
            games = section["games"]
            mid = (len(games) + 1) // 2
            left  = games[:mid]
            right = games[mid:]
            for i in range(mid):
                l = left[i]
                left_str = f"{l['away']} at {l['home']}, {l['time']}"
                right_str = ""
                if i < len(right):
                    r = right[i]
                    right_str = f"{r['away']} at {r['home']}, {r['time']}"
                print(f"  {left_str:<35} {right_str}")


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    print("Fetching MLB schedule...\n")
    schedule = fetch_schedule_two_days()
    print_schedule(schedule)


if __name__ == "__main__":
    main()
