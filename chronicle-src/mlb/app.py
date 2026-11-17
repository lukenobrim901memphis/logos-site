#!/usr/bin/env python3
"""
MLB Chronicle — Flask application
"""

import json
import os
import re
import unicodedata
from datetime import date, timedelta, datetime
from flask import Flask, render_template, jsonify, request, redirect, url_for
from werkzeug.utils import secure_filename
 
from mlb_yesterday  import fetch_schedule, fetch_boxscore, fetch_linescore
from mlb_standings  import fetch_standings
from mlb_schedule   import fetch_schedule_two_days
from mlb_leaders    import fetch_leaders
from mlb_boxscore   import normalize_name
from mlb_transactions import fetch_transactions

app = Flask(__name__)
app.config["UPLOAD_FOLDER"] = os.path.join("static", "uploads")
app.config["MAX_CONTENT_LENGTH"] = 16 * 1024 * 1024
app.config["SEND_FILE_MAX_AGE_DEFAULT"] = 0

BOTD_FILE    = "botd.json"
NOTES_FILE   = "notes.json"
RECAPS_FILE  = "recaps.json"
ARCHIVE_DIR  = "archive"
OTD_FILE     = "otd.json"

ALLOWED_EXTENSIONS = {"jpg", "jpeg", "png", "gif", "webp"}

# ── Cache ─────────────────────────────────────────────────────────────────────
_cache = {
    "boxscores":  None,
    "standings":  None,
    "standings_date": None,
    "cache_date": None,
}

def get_cached_date():
    from datetime import timezone
    pt_now = datetime.now(timezone.utc) - timedelta(hours=7)
    return (pt_now - timedelta(days=1)).date()

def cache_is_fresh():
    return (
        _cache["boxscores"] is not None and
        _cache["cache_date"] == get_cached_date()
    )

CACHE_FILE = "cache.json"

def save_cache_to_disk():
    """Persist _cache to disk so a Flask restart during development
    doesn't force a fresh refetch (which can desync boxscores/standings
    since standings have no 'as of yesterday' API option)."""
    try:
        serializable = dict(_cache)
        if serializable.get("cache_date"):
            serializable["cache_date"] = serializable["cache_date"].isoformat()
        with open(CACHE_FILE, "w") as f:
            json.dump(serializable, f)
    except Exception as e:
        print(f"  Cache save error: {e}")

def load_cache_from_disk():
    """On startup, restore _cache from disk ONLY if the saved cache_date
    still matches today's target date — otherwise leave _cache empty so
    a normal fresh fetch happens (e.g. after midnight rollover)."""
    if not os.path.exists(CACHE_FILE):
        return
    try:
        with open(CACHE_FILE) as f:
            saved = json.load(f)
        saved_date_str = saved.get("cache_date")
        if not saved_date_str:
            return
        saved_date = date.fromisoformat(saved_date_str)
        if saved_date == get_cached_date():
            _cache["boxscores"]  = saved.get("boxscores")
            standings_raw = saved.get("standings")
            if standings_raw:
                # JSON forces dict keys to strings; convert division IDs
                # back to ints so lookups like standings[league].get(201)
                # (an int from div_order) work correctly.
                fixed_standings = {}
                for league, divs in standings_raw.items():
                    fixed_standings[league] = {
                        int(div_id): div_data for div_id, div_data in divs.items()
                    }
                _cache["standings"] = fixed_standings
            else:
                _cache["standings"] = standings_raw

            _cache["cache_date"]    = saved_date
            print(f"  Restored cache from disk for {saved_date}")
    except Exception as e:
        print(f"  Cache load error: {e}")

load_cache_from_disk()

# ── Team names ────────────────────────────────────────────────────────────────
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

TEAM_SHORT = {
    "Arizona":     "D-backs",
    "Atlanta":     "Braves",
    "Baltimore":   "O's",
    "Boston":      "Red Sox",
    "Chicago":     "Cubs",
    "Cincinnati":  "Reds",
    "Cleveland":   "Guards",
    "Colorado":    "Rockies",
    "Detroit":     "Tigers",
    "Houston":     "Stros",
    "Kansas City": "Royals",
    "L.A. Angels": "Angels",
    "L.A. Dodgers":"Dodgers",
    "Miami":       "Marlins",
    "Milwaukee":   "Brewers",
    "Minnesota":   "Twins",
    "N.Y. Mets":   "Mets",
    "N.Y. Yankees":"Yankees",
    "Athletics":   "A's",
    "Philadelphia":"Phils",
    "Pittsburgh":  "Pirates",
    "San Diego":   "Padres",
    "Giants":      "Giants",
    "Seattle":     "M's",
    "St. Louis":   "Cards",
    "Tampa Bay":   "Rays",
    "Texas":       "Rangers",
    "Toronto":     "Jays",
    "Washington":  "Nats",
}

def city_name(full_name):
    return TEAM_CITY.get(full_name, full_name)

# ── File helpers ──────────────────────────────────────────────────────────────
def load_recaps():
    if not os.path.exists(RECAPS_FILE):
        return {}
    with open(RECAPS_FILE) as f:
        return json.load(f)

def save_recaps(data):
    with open(RECAPS_FILE, "w") as f:
        json.dump(data, f, indent=2)

def load_botd():
    if not os.path.exists(BOTD_FILE):
        return {}
    with open(BOTD_FILE) as f:
        return json.load(f)

def save_botd_data(data):
    with open(BOTD_FILE, "w") as f:
        json.dump(data, f, indent=2)

def load_notes():
    if not os.path.exists(NOTES_FILE):
        return {}
    with open(NOTES_FILE) as f:
        return json.load(f)

def save_notes_data(data):
    with open(NOTES_FILE, "w") as f:
        json.dump(data, f, indent=2)

def load_otd():
    if not os.path.exists(OTD_FILE):
        return {}
    with open(OTD_FILE) as f:
        return json.load(f)

def save_otd_data(data):
    with open(OTD_FILE, "w") as f:
        json.dump(data, f, indent=2)

def archive_boxscores(target_date, boxscores):
    os.makedirs(ARCHIVE_DIR, exist_ok=True)
    path = os.path.join(ARCHIVE_DIR, f"{target_date}.json")
    if not os.path.exists(path):
        with open(path, "w") as f:
            json.dump(boxscores, f, indent=2)

def load_archive(target_date):
    path = os.path.join(ARCHIVE_DIR, f"{target_date}.json")
    if os.path.exists(path):
        with open(path) as f:
            return json.load(f)
    return None

def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS

# ── Innings pitched format ────────────────────────────────────────────────────
def fmt_ip(raw):
    s = str(raw)
    if s.endswith(".1"):
        whole = int(float(s))
        return f"{whole}⅓" if whole > 0 else "⅓"
    if s.endswith(".2"):
        whole = int(float(s))
        return f"{whole}⅔" if whole > 0 else "⅔"
    return str(int(float(s)))

def strip_to_last_name(boxscore_name):
    """
    Always extract just the surname, discarding any initial the API
    may have already appended — we rebuild disambiguation ourselves
    since the API's comma format isn't reliably tied to actual
    in-game collisions. Also strips accented characters here so every
    caller of format_player_name() gets clean ASCII automatically.
    """
    clean = normalize_name(boxscore_name)
    return clean.split(",")[0].strip()


def build_last_name_counts(away_raw, home_raw):
    """
    Count how many times each last name appears across BOTH teams'
    full rosters (every player object present in 'players', batters
    and pitchers alike) for this specific game.
    """
    counts = {}
    for team_raw in (away_raw, home_raw):
        for key, player in team_raw.get("players", {}).items():
            last = strip_to_last_name(player["person"]["boxscoreName"])
            counts[last] = counts.get(last, 0) + 1
    return counts


def format_player_name(player_person, last_name_counts):
    """
    Show just the last name unless another player in this same game
    (either team, batter or pitcher) shares that last name — in which
    case prefix with the first initial pulled from fullName.
    """
    last = strip_to_last_name(player_person["boxscoreName"])
    if last_name_counts.get(last, 0) > 1:
        full_name = normalize_name(player_person.get("fullName", "")).strip()
        initial = full_name[0] if full_name else ""
        return f"{initial}. {last}" if initial else last
    return last

def get_team_info_field(team_raw, label):
    """
    Look up a label (e.g. 'HR', 'DP', '2B') inside a team's OWN grouped
    info block: team_raw['info'] = [{'title': 'BATTING', 'fieldList': [...]}].
    Each team's info block already only contains that team's own stats,
    so no name-matching against rosters is needed.
    """
    for group in team_raw.get("info", []):
        for item in group.get("fieldList", []):
            if item.get("label") == label:
                return item.get("value", "")
    return ""


def build_name_lookup(team_raw):
    """
    Map every raw boxscoreName fragment (full 'Lastname, X' form, and
    the plain last-name-only form) to that player's actual person
    object, so freeform DP/other parsers can resolve names properly
    through format_player_name() instead of using raw API text as-is.
    """
    lookup = {}
    for key, player in team_raw.get("players", {}).items():
        person = player["person"]
        bn = person["boxscoreName"]
        lookup[bn] = person
        last_only = bn.split(",")[0].strip()
        lookup.setdefault(last_only, person)
    return lookup

def parse_hr_detail_single_team(info_value):
    """
    Parse one team's HR info value into 'Name (total) off Pitcher'
    entries, one per home run, with the season total incrementing
    correctly for players who hit multiple home runs in the game.
    Handles 'Lastname, X' format for both batter and pitcher names,
    multi-word names like 'De Los Santos', and accented characters.
    """
    entries = [e.strip().rstrip(".") for e in info_value.split(";") if e.strip()]
    results = []
    for entry in entries:
        m = re.match(
            r'^([A-Za-z.\',\u00C0-\u017F\- ]+?)(?:\s+(\d+))?\s*\((\d+),\s*(.+)\)$',
            entry,
        )
        if not m:
            continue
        raw_name     = m.group(1).strip()
        name         = strip_to_last_name(raw_name)
        game_count   = int(m.group(2)) if m.group(2) else 1
        season_total = int(m.group(3))
        details      = m.group(4)
        pitcher_matches = re.findall(
            r'off\s+((?:[A-Za-z.\u00C0-\u017F\-]+)(?:\s+[A-Za-z.\u00C0-\u017F\-]+)*(?:,\s*[A-Za-z]+)?)',
            details,
        )
        pitchers = [strip_to_last_name(p) for p in pitcher_matches]
        start = season_total - game_count + 1
        for i, pitcher in enumerate(pitchers):
            results.append(f"{name} ({start+i}) off {pitcher}")
    return ", ".join(results)

def parse_dp_detail_single_team(dp_value, team_city, name_lookup, last_name_counts):
    """
    Parse one team's DP info value into a count-prefixed note.

    Raw format: an optional leading count, then one or more parenthetical
    groups, where each group may itself contain multiple double plays
    separated by semicolons (e.g. when a strikeout-throw-out and a
    lined-into DP both happen), and each double play's fielders are
    dash-joined. Fielder names may themselves contain a comma+initial
    (e.g. "Perez, S"), which must NOT be treated as a separator.

    Input:  "2 (Witt Jr.-Massey-Caglianone; Perez, S-Witt Jr.)."
    Output: "Kansas City 2 (Witt Jr., Massey, Caglianone), (Perez, Witt Jr.)"
    """
    dp_value = dp_value.strip()

    leading_count = 1
    m = re.match(r'^(\d+)\s*\(', dp_value)
    if m:
        leading_count = int(m.group(1))

    paren_groups = re.findall(r'\(([^)]+)\)', dp_value)
    all_dp_groups = []

    for g in paren_groups:
        g = g.strip()
        inner_m = re.match(r'^(\d+)\s+(.+)$', g)
        if inner_m:
            inner_count = int(inner_m.group(1))
            g_body = inner_m.group(2)
        else:
            inner_count = 1
            g_body = g

        sub_dps = [s.strip() for s in g_body.split(";") if s.strip()]
        for sub in sub_dps:
            raw_names = [n.strip() for n in sub.split("-")]
            for _ in range(inner_count):
                all_dp_groups.append(raw_names)

    if leading_count > len(all_dp_groups) and len(all_dp_groups) == 1:
        all_dp_groups = all_dp_groups * leading_count

    formatted_groups = []
    for raw_names in all_dp_groups:
        formatted_names = []
        for raw in raw_names:
            person = name_lookup.get(raw)
            if person:
                formatted_names.append(format_player_name(person, last_name_counts))
            else:
                formatted_names.append(raw.split(",")[0].strip())
        formatted_groups.append("(" + ", ".join(formatted_names) + ")")

    if not formatted_groups:
        return ""
    return f"{team_city} {len(formatted_groups)} " + ", ".join(formatted_groups)

def fix_names_in_freeform_text(text, away_raw, home_raw, last_name_counts):
    name_map = {}
    for team_raw in (away_raw, home_raw):
        for key, player in team_raw.get("players", {}).items():
            person = player["person"]
            raw_bn = person["boxscoreName"]
            full_name = person.get("fullName", "")
            correct = format_player_name(person, last_name_counts)

            for form in (raw_bn, normalize_name(raw_bn), full_name, normalize_name(full_name)):
                if form:
                    name_map[form] = correct

    for raw_form in sorted(name_map.keys(), key=len, reverse=True):
        if raw_form in text:
            text = text.replace(raw_form, name_map[raw_form])

    # Catch-all: strip any remaining accented characters in the text
    # that weren't part of a matched player name (e.g. names spelled
    # slightly differently than boxscoreName/fullName).
    text = normalize_name(text)
    return text
    
def parse_umpires_detail(value):
    """
    Parse the Umpires info value from positional abbreviations into
    full position names.

    Input:  "HP: Tripp Gibson. 1B: Marvin Hudson. 2B: Nick Mahrley. 3B: Ryan Blakney. "
    Output: "Home, Tripp Gibson; First, Marvin Hudson; Second, Nick Mahrley; Third, Ryan Blakney"
    """
    position_map = {
        "HP": "Home",
        "1B": "First",
        "2B": "Second",
        "3B": "Third",
        "LF": "Left field",
        "RF": "Right field",
    }
    entries = re.findall(r'([A-Z0-9]+):\s*([^.]+)\.', value)
    parts = []
    for code, name in entries:
        position = position_map.get(code, code)
        parts.append(f"{position}, {name.strip()}")
    return "; ".join(parts)

# ── Parse boxscore ────────────────────────────────────────────────────────────
def parse_boxscore(data, game_pk, away_city=None, home_city=None, linescore=None, game_number=1):
    teams    = data.get("teams", {})
    away_raw = teams.get("away", {})
    home_raw = teams.get("home", {})

    last_name_counts = build_last_name_counts(away_raw, home_raw)

    away_full = away_raw.get("team", {}).get("name", "")
    home_full = home_raw.get("team", {}).get("name", "")
    away_city = away_city or city_name(away_full)
    home_city = home_city or city_name(home_full)

    def parse_team(team_data, team_city):
        players     = team_data.get("players", {})
        bat_order   = team_data.get("battingOrder", [])
        pitcher_ids = team_data.get("pitchers", [])

        batter_records = []
        for key, player in players.items():
            order = player.get("battingOrder")
            if not order:
                continue
            bat = player["stats"].get("batting", {})
            pid = int(key.replace("ID", ""))
            if bat.get("plateAppearances", 0) > 0 or pid in bat_order:
                batter_records.append((int(order), player))
        batter_records.sort(key=lambda x: x[0])

        batters = []
        for order_num, player in batter_records:
            all_pos  = player.get("allPositions", [])
            pos      = "-".join(p.get("abbreviation", "?").lower() for p in all_pos) if all_pos else "?"
            bat      = player["stats"].get("batting", {})
            avg      = player.get("seasonStats", {}).get("batting", {}).get("avg", ".---")
            season_ab = player.get("seasonStats", {}).get("batting", {}).get("atBats", 0)
            label    = f"{format_player_name(player['person'], last_name_counts)} {pos}"
            batters.append({
                "name": label,
                "ab":   bat.get("atBats", 0),
                "r":    bat.get("runs", 0),
                "h":    bat.get("hits", 0),
                "bi":   bat.get("rbi", 0),
                "bb":   bat.get("baseOnBalls", 0),
                "so":   bat.get("strikeOuts", 0),
                "avg":  avg,
                "season_ab": season_ab,
            })

        ts = team_data.get("teamStats", {}).get("batting", {})
        tot = {
            "ab": ts.get("atBats", 0),
            "r":  ts.get("runs", 0),
            "h":  ts.get("hits", 0),
            "bi": ts.get("rbi", 0),
            "bb": ts.get("baseOnBalls", 0),
            "so": ts.get("strikeOuts", 0),
        }

        pitchers = []
        for pid in pitcher_ids:
            player = players.get(f"ID{pid}")
            if not player:
                continue
            last_name = format_player_name(player["person"], last_name_counts)
            p   = player["stats"].get("pitching", {})
            if not p:
                continue
            era  = player.get("seasonStats", {}).get("pitching", {}).get("era", "-.--")
            sp   = player.get("seasonStats", {}).get("pitching", {})
            note = p.get("note", "")

            wins   = p.get("wins", 0)
            losses = p.get("losses", 0)
            saves  = p.get("saves", 0)
            holds  = p.get("holds", 0)

            decision = ""
            if wins > 0:
                decision = f"W, {sp.get('wins',0)}-{sp.get('losses',0)}"
            elif losses > 0:
                decision = f"L, {sp.get('wins',0)}-{sp.get('losses',0)}"
            elif saves > 0:
                decision = f"S, {sp.get('saves',0)}-{sp.get('saveOpportunities',0)}"
            elif holds > 0:
                decision = f"H, {sp.get('holds',0)}"

            display = f"{last_name} {decision}".strip() if decision else last_name
            pitchers.append({
                "name": display,
                "ip":   fmt_ip(p.get("inningsPitched", "0.0")),
                "h":    p.get("hits", 0),
                "r":    p.get("runs", 0),
                "er":   p.get("earnedRuns", 0),
                "bb":   p.get("baseOnBalls", 0),
                "so":   p.get("strikeOuts", 0),
                "np":   p.get("pitchesThrown", 0),
                "era":  era,
                "note": note,
            })

        return {
            "name":     team_city,
            "abbr":     team_data.get("team", {}).get("abbreviation", ""),
            "batters":  batters,
            "totals":   tot,
            "pitchers": pitchers,
        }

    away = parse_team(away_raw, away_city)
    home = parse_team(home_raw, home_city)

    away_runs   = away_raw.get("teamStats", {}).get("batting", {}).get("runs", 0)
    home_runs   = home_raw.get("teamStats", {}).get("batting", {}).get("runs", 0)
    away_hits   = away_raw.get("teamStats", {}).get("batting", {}).get("hits", 0)
    home_hits   = home_raw.get("teamStats", {}).get("batting", {}).get("hits", 0)
    away_errors = away_raw.get("teamStats", {}).get("fielding", {}).get("errors", 0)
    home_errors = home_raw.get("teamStats", {}).get("fielding", {}).get("errors", 0)

    away_lob = sum(inn.get("away", {}).get("leftOnBase", 0) for inn in (linescore or {}).get("innings", []))
    home_lob = sum(inn.get("home", {}).get("leftOnBase", 0) for inn in (linescore or {}).get("innings", []))

    innings      = (linescore or {}).get("innings", [])
    away_innings = []
    home_innings = []
    for inn in innings:
        away_innings.append(str(inn.get("away", {}).get("runs", 0)))
        h_runs = inn.get("home", {}).get("runs")
        home_innings.append("x" if h_runs is None else str(h_runs))

    def group_innings(lst):
        groups = []
        for i in range(0, len(lst), 3):
            groups.append("".join(lst[i:i+3]))
        return " ".join(groups)

    away_line = group_innings(away_innings)
    home_line = group_innings(home_innings)

    # ── Batting notes ─────────────────────────────────────────────────────────
    # data["info"] is a FLAT list (Umpires, T, Att, WP, Balk, HBP, etc.)
    # Each team's away_raw["info"]/home_raw["info"] is GROUPED by title
    # (BATTING/BASERUNNING/FIELDING), each with a nested fieldList. HR
    # and DP both come from the per-team grouped info, not the flat one.
    info = data.get("info", [])

    def build_bat_notes(away_raw, home_raw, away_city, home_city, away_lob=0, home_lob=0, last_name_counts=None):
        notes = {}

        def process_team(team_data, team_city, game_lob):
            players       = team_data.get("players", {})
            batting_order = team_data.get("battingOrder", [])
            doubles, triples = [], []
            sb, cs, sf, sac, gidp, ibb, errors = [], [], [], [], [], [], []

            for pid in batting_order:
                player = players.get(f"ID{pid}")
                if not player:
                    continue
                last = format_player_name(player["person"], last_name_counts)
                bat  = player["stats"].get("batting", {})
                sbat = player.get("seasonStats", {}).get("batting", {})
                if not bat:
                    continue
                if bat.get("doubles", 0):             doubles.append(f"{last} ({sbat.get('doubles', bat['doubles'])})")
                if bat.get("triples", 0):             triples.append(f"{last} ({sbat.get('triples', bat['triples'])})")
                if bat.get("stolenBases", 0):         sb.append(f"{last} ({sbat.get('stolenBases', bat['stolenBases'])})")
                if bat.get("caughtStealing", 0):      cs.append(f"{last} ({sbat.get('caughtStealing', bat['caughtStealing'])})")
                if bat.get("sacFlies", 0):            sf.append(last)
                if bat.get("sacBunts", 0):            sac.append(last)
                if bat.get("groundIntoDoublePlay", 0):gidp.append(last)
                if bat.get("intentionalWalks", 0):    ibb.append(last)

            for key, player in players.items():
                field  = player["stats"].get("fielding", {})
                sfield = player.get("seasonStats", {}).get("fielding", {})
                if field.get("errors", 0):
                    last = format_player_name(player["person"], last_name_counts)
                    errors.append(f"{last} ({sfield.get('errors', field['errors'])})")

            if errors:   notes.setdefault("E",    []).extend(errors)
            if doubles:  notes.setdefault("2B",   []).extend(doubles)
            if triples:  notes.setdefault("3B",   []).extend(triples)
            if sb:       notes.setdefault("SB",   []).extend(sb)
            if cs:       notes.setdefault("CS",   []).extend(cs)
            if sf:       notes.setdefault("SF",   []).extend(sf)
            if sac:      notes.setdefault("SAC",  []).extend(sac)
            if gidp:     notes.setdefault("GIDP", []).extend(gidp)
            if ibb:      notes.setdefault("IBB",  []).extend(ibb)
            notes.setdefault("_lob", []).append(f"{team_city} {game_lob}")

        process_team(away_raw, away_city, away_lob)
        process_team(home_raw, home_city, home_lob)

        # HR — per-team lookup from each team's own grouped info block
        away_hr_raw = get_team_info_field(away_raw, "HR")
        home_hr_raw = get_team_info_field(home_raw, "HR")
        away_hr = parse_hr_detail_single_team(away_hr_raw) if away_hr_raw else ""
        home_hr = parse_hr_detail_single_team(home_hr_raw) if home_hr_raw else ""
        hr_combined = "; ".join(p for p in [away_hr, home_hr] if p)
        if hr_combined:
            notes["HR"] = [hr_combined]

        # DP — per-team lookup, count-prefixed with team city
        away_name_lookup = build_name_lookup(away_raw)
        home_name_lookup = build_name_lookup(home_raw)
        away_dp_raw = get_team_info_field(away_raw, "DP")
        home_dp_raw = get_team_info_field(home_raw, "DP")
        away_dp = parse_dp_detail_single_team(away_dp_raw, away_city, away_name_lookup, last_name_counts) if away_dp_raw else ""
        home_dp = parse_dp_detail_single_team(home_dp_raw, home_city, home_name_lookup, last_name_counts) if home_dp_raw else ""
        dp_combined = "; ".join(p for p in [away_dp, home_dp] if p)
        if dp_combined:
            notes["DP"] = [dp_combined]

        order = ["E", "LOB", "2B", "3B", "HR", "SB", "CS", "SF", "SAC", "GIDP", "DP", "IBB"]
        parts = []
        ls_note = (linescore or {}).get("note", "")
        if ls_note:
            fixed_ls_note = fix_names_in_freeform_text(ls_note, away_raw, home_raw, last_name_counts)
            parts.append(f"<span class='nt-val'>{fixed_ls_note}</span>.")
        for label in order:
            if label == "LOB":
                lob_parts = notes.get("_lob", [])
                if lob_parts:
                    val = ", ".join(lob_parts)
                    parts.append(f"<b>LOB</b>\u2014<span class='nt-val'>{val.rstrip('.')}</span>.")
            elif label in ("HR", "DP") and label in notes:
                val = notes[label][0]
                parts.append(f"<b>{label}</b>\u2014<span class='nt-val'>{val.rstrip('.')}</span>.")
            elif label in notes:
                val = "; ".join(notes[label])
                parts.append(f"<b>{label}</b>\u2014<span class='nt-val'>{val.rstrip('.')}</span>.")
        return " ".join(parts)

    bat_notes = build_bat_notes(away_raw, home_raw, away_city, home_city, away_lob, home_lob, last_name_counts)

    # Pitching notes — pitchingNotes strings first, then the FLAT data["info"]
    pitching_notes_raw = data.get("pitchingNotes", [])
    pit_notes = []
    for note in pitching_notes_raw:
        if note.strip():
            fixed_note = fix_names_in_freeform_text(note.strip(), away_raw, home_raw, last_name_counts)
            pit_notes.append(f"<span class='nt-val'>{fixed_note.rstrip('.')}</span>.")
    pit_keys  = {"Inherited runners-scored", "WP", "Balk", "PB", "HBP", "Delay"}
    info_keys = {"Umpires", "T", "Att"}
    for item in info:
        label = item.get("label", "")
        value = item.get("value", "")
        if not label or not value:
            continue
        if label == "Umpires":
            umpire_text = parse_umpires_detail(value)
            if umpire_text:
                pit_notes.append(f"<b>Umpires</b>\u2014<span class='nt-val'>{umpire_text}</span>.")
        elif label in pit_keys or label in info_keys:
            fixed_value = fix_names_in_freeform_text(value, away_raw, home_raw, last_name_counts)
            pit_notes.append(f"<b>{label}</b>\u2014<span class='nt-val'>{fixed_value.rstrip('.')}</span>.")

    extra_innings_suffix = f" ({len(away_innings)})" if len(away_innings) > 9 else ""

    if away_runs > home_runs:
        winner, winner_runs, loser, loser_runs = away_city, away_runs, home_city, home_runs
    else:
        winner, winner_runs, loser, loser_runs = home_city, home_runs, away_city, away_runs

    title = f"{winner} {winner_runs}, {loser} {loser_runs}{extra_innings_suffix}"

    if len(title) > 28:
        winner_s = TEAM_SHORT.get(winner, winner)
        loser_s  = TEAM_SHORT.get(loser, loser)
        title = f"{winner_s} {winner_runs}, {loser_s} {loser_runs}{extra_innings_suffix}"

    recap = load_recaps().get(str(game_pk), {})

    # Estimate recap height
    CELL_HEIGHT  = 500
    TITLE_BAR    = 16
    CELL_PADDING = 12
    BAT_HEADER   = 12
    BAT_ROW      = 8.75
    BAT_TOTALS   = 9
    BAT_GAP      = 2
    LINESCORE    = 20
    BAT_NOTES    = 18
    PIT_NOTES    = 18
    HR_THIN      = 4
    PIT_HEADER   = 11
    PIT_ROW      = 7.5

    stats_height = (
        (BAT_HEADER + (len(away["batters"]) * BAT_ROW) + BAT_TOTALS) +
        BAT_GAP +
        (BAT_HEADER + (len(home["batters"]) * BAT_ROW) + BAT_TOTALS) +
        LINESCORE + HR_THIN + BAT_NOTES +
        (PIT_HEADER + (len(away["pitchers"]) * PIT_ROW)) +
        BAT_GAP +
        (PIT_HEADER + (len(home["pitchers"]) * PIT_ROW)) +
        HR_THIN + PIT_NOTES + CELL_PADDING
    )
    recap_height = max(30, int(CELL_HEIGHT - TITLE_BAR - stats_height))

    return {
        "game_pk":      game_pk,
        "title":        title,
        "away":         away,
        "home":         home,
        "away_runs":    away_runs,
        "home_runs":    home_runs,
        "away_hits":    away_hits,
        "home_hits":    home_hits,
        "away_errors":  away_errors,
        "home_errors":  home_errors,
        "away_line":    away_line,
        "home_line":    home_line,
        "away_innings": away_innings,
        "home_innings": home_innings,
        "bat_notes":    bat_notes,
        "pit_notes":    " ".join(pit_notes),
        "recap":        recap.get("text", ""),
        "postponed":    False,
        "recap_height": recap_height,
        "recap_words":  max(10, int(recap_height / 11 * 7)),
        "game_number":  game_number,
    }


# ── Routes ────────────────────────────────────────────────────────────────────

@app.route("/")
def index():
    season = date.today().year

    try:
        if cache_is_fresh():
            boxscores = _cache["boxscores"]
            # Always inject latest recap text so edits show immediately
            recaps = load_recaps()
            for game in boxscores:
                pk = str(game.get("game_pk", ""))
                game["recap"] = recaps.get(pk, {}).get("text", "")
        else:
            game_list = fetch_schedule(get_cached_date())
            boxscores = []
            for g in game_list:
                if g["status"] == "Postponed":
                    recap = load_recaps().get(str(g["game_pk"]), {})
                    boxscores.append({
                        "postponed": True,
                        "title":     f"{g['away_city']}-{g['home_city']}, ppd.",
                        "game_pk":   g["game_pk"],
                        "recap":     recap.get("text", ""),
                    })
                else:
                    try:
                        raw  = fetch_boxscore(g["game_pk"])
                        ls   = fetch_linescore(g["game_pk"])
                        game = parse_boxscore(raw, g["game_pk"],
                                              away_city=g["away_city"],
                                              home_city=g["home_city"],
                                              linescore=ls,
                                              game_number=g.get("game_number", 1))
                        boxscores.append(game)
                    except Exception as e:
                        print(f"  Error parsing gamePk {g['game_pk']}: {e}")
            _cache["boxscores"]  = boxscores
            _cache["cache_date"] = get_cached_date()
            archive_boxscores(get_cached_date(), boxscores)
            save_cache_to_disk()
        # Group doubleheaders together preserving original order,
        # move postponed games to end
        # Label doubleheader games first
        from collections import Counter
        pair_counts = Counter()
        for g in boxscores:
            if not g.get("postponed"):
                away = g.get("away", {}).get("name", "")
                home = g.get("home", {}).get("name", "")
                pair_counts["".join(sorted([away, home]))] += 1

        pair_seen = {}
        for g in boxscores:
            if not g.get("postponed"):
                away = g.get("away", {}).get("name", "")
                home = g.get("home", {}).get("name", "")
                pair = "".join(sorted([away, home]))
                if pair_counts[pair] > 1 and "(Game " not in g["title"]:
                    pair_seen[pair] = pair_seen.get(pair, 0) + 1
                    g["title"] = g["title"] + f" (Game {pair_seen[pair]})"

        # Group doubleheaders together while preserving original order
        # Strategy: when we encounter a game whose pair we've seen before,
        # insert it right after the first game of that pair
        result = []
        pair_positions = {}
        for g in boxscores:
            if g.get("postponed"):
                continue
            away = g.get("away", {}).get("name", "")
            home = g.get("home", {}).get("name", "")
            pair = "".join(sorted([away, home]))
            if pair in pair_positions:
                # Insert right after the first game of this pair
                insert_at = pair_positions[pair] + 1
                result.insert(insert_at, g)
                # Update all subsequent pair positions
                for k in pair_positions:
                    if pair_positions[k] >= insert_at:
                        pair_positions[k] += 1
                pair_positions[pair] = insert_at
            else:
                pair_positions[pair] = len(result)
                result.append(g)

        # Add postponed games at the end
        result += [g for g in boxscores if g.get("postponed")]
        boxscores = result
    except Exception as e:
        print(f"  Schedule error: {e}")
        boxscores = _cache["boxscores"] or []

    try:
        today = date.today().isoformat()
        if _cache.get("standings_date") != today or _cache["standings"] is None:
            _cache["standings"] = fetch_standings(season)
            _cache["standings_date"] = today
            save_cache_to_disk()
        standings = _cache["standings"]
    except Exception as e:
        print(f"  Standings error: {e}")
        standings = _cache["standings"] or {"NL": {}, "AL": {}}

    try:
        schedule = fetch_schedule_two_days()
    except Exception as e:
        print(f"  Schedule error: {e}")
        schedule = {"today":    {"label": "Today's Games",    "games": []},
                    "tomorrow": {"label": "Tomorrow's Games", "games": []}}

    try:
        leaders = fetch_leaders()
    except Exception as e:
        print(f"  Leaders error: {e}")
        leaders = {"NL": {}, "AL": {}}

    botd = load_botd()
    if botd.get("story"):
        botd["story_html"] = "<p>" + botd["story"].replace("\n\n", "</p><p>").replace("\n", " ") + "</p>"

    div_order    = {"NL": [203, 205, 204], "AL": [200, 202, 201]}
    date_str     = date.today().strftime("%A, %B %-d, %Y")
    otd_date_str = date.today().strftime("%B %-d")
    completed    = [g for g in boxscores if not g.get("postponed")]
    game_count   = len(completed)
    scheduled_count = len(boxscores)  # includes postponed games
    show_leaders = game_count < 16
    
    show_transactions = scheduled_count <= 14
    show_otd          = scheduled_count <= 13

     # ── Sidebar logic (transactions / on-this-date) ──────────────────────────
    # 12 or fewer games -> transactions + space to write (otd)
    # 13 games          -> transactions + on-this-date
    # 14 games          -> transactions only
    # 15+ games         -> nothing

    
    transactions = {"NL": [], "AL": []}
    if show_transactions:
        try:
            transactions = fetch_transactions(get_cached_date())
        except Exception as e:
            import traceback
            print(f"  Transactions error: {e}")
            traceback.print_exc()
 
    otd = load_otd() if show_otd else {}

    return render_template(
        "index.html",
        boxscores    = boxscores,
        standings    = standings,
        schedule     = schedule,
        leaders      = leaders,
        botd         = botd,
        div_order         = div_order,
        date_str          = date_str,
        otd_date_str = otd_date_str,
        season            = season,
        show_leaders      = show_leaders,
        show_transactions = show_transactions,
        show_otd          = show_otd,
        transactions      = transactions,
        otd               = otd,
        scheduled_count   = scheduled_count,
    )


@app.route("/admin")
def admin():
    yesterday = date.today() - timedelta(days=1)
    try:
        game_list = fetch_schedule(yesterday)
        games = []
        for g in game_list:
            if g["status"] == "Postponed":
                games.append({
                    "game_pk":   g["game_pk"],
                    "title":     f"{g['away_city']}-{g['home_city']}, ppd.",
                    "postponed": True,
                })
            else:
                try:
                    raw  = fetch_boxscore(g["game_pk"])
                    ls   = fetch_linescore(g["game_pk"])
                    game = parse_boxscore(raw, g["game_pk"],
                                         away_city=g["away_city"],
                                         home_city=g["home_city"],
                                         linescore=ls,
                                         game_number=g.get("game_number", 1))
                    games.append(game)
                except Exception:
                    pass
    except Exception:
        games = []

    recaps = load_recaps()
    botd   = load_botd()
    otd    = load_otd()
    notes_data = load_notes()
    return render_template("admin.html", games=games, recaps=recaps, botd=botd, otd=otd, notes_data=notes_data)


@app.route("/save_botd", methods=["POST"])
def save_botd():
    botd = load_botd()
    botd["headline"]     = request.form.get("botd_headline", "")
    botd["dateline"]     = request.form.get("botd_dateline", "")
    botd["story"]        = request.form.get("botd_story", "").replace("\r\n", "\n").replace("\r", "\n")
    botd["photo_credit"] = request.form.get("photo_credit", "")

    if "photo" in request.files:
        file = request.files["photo"]
        if file and file.filename and allowed_file(file.filename):
            filename = secure_filename(f"botd_{file.filename}")
            filepath = os.path.join(app.config["UPLOAD_FOLDER"], filename)
            file.save(filepath)
            botd["photo"] = f"/static/uploads/{filename}"

    save_botd_data(botd)
    return redirect(url_for("admin"))

@app.route("/save_otd", methods=["POST"])
def save_otd():
    otd = load_otd()
    raw_text = request.form.get("otd_text", "").replace("\r\n", "\n").replace("\r", "\n")
    otd["raw_text"] = raw_text
 
    events = []
    for line in raw_text.split("\n"):
        line = line.strip()
        if not line:
            continue
        # Split on em dash or hyphen-dash separating year from text
        m = re.match(r'^(\d{4})\s*[\u2014\-]\s*(.+)$', line)
        if m:
            events.append({"year": m.group(1), "text": m.group(2).strip()})
    otd["events"] = events
 
    save_otd_data(otd)
    return redirect(url_for("admin"))

@app.route("/save_recap", methods=["POST"])
def save_recap():
    game_pk = request.form.get("game_pk")
    text    = request.form.get("text", "")

    recaps = load_recaps()
    if game_pk not in recaps:
        recaps[game_pk] = {}
    recaps[game_pk]["game_pk"] = game_pk
    recaps[game_pk]["text"]    = text
    save_recaps(recaps)

    # Auto-save requests send this header; respond with JSON instead of
    # redirecting so the page doesn't reload.
    if request.headers.get("X-Auto-Save") == "1":
        return jsonify({"status": "saved"})

    return redirect(url_for("admin"))


@app.route("/api/standings")
def api_standings():
    return jsonify(fetch_standings(date.today().year))


@app.route("/api/schedule")
def api_schedule():
    return jsonify(fetch_schedule_two_days())


@app.route("/api/leaders")
def api_leaders():
    return jsonify(fetch_leaders())


@app.route("/api/recaps")
def api_recaps():
    return jsonify(load_recaps())


if __name__ == "__main__":
    os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)
    app.run(debug=True, port=5001)