#!/usr/bin/env python3
"""
MLB Transactions
Fetches transactions for a given date for both AL and NL, grouped by
parent MLB team, formatted Chronicle-style.
"""

import json
import re
import unicodedata
import urllib.request
from collections import defaultdict
from datetime import date

from minor_league_map import MINOR_LEAGUE_MAP

ROOKIE_LEAGUE_NAMES = {
    "ACL Angels", "ACL Athletics", "ACL Brewers", "ACL Cubs", "ACL D-backs",
    "ACL Dodgers", "ACL Giants", "ACL Guardians", "ACL Mariners",
    "ACL Padres", "ACL Rangers", "ACL Reds", "ACL Rockies", "ACL Royals",
    "ACL White Sox",
    "DSL Angels", "DSL Astros", "DSL Athletics", "DSL Blue Jays",
    "DSL Braves", "DSL Brewers Blue", "DSL Brewers Gold",
    "DSL Cardinals Blue", "DSL Cardinals Red", "DSL Cubs Blue",
    "DSL Cubs Red", "DSL Diamondbacks 1", "DSL Diamondbacks 2",
    "DSL Dodgers Bautista", "DSL Dodgers Shoemaker", "DSL Giants 1",
    "DSL Giants 2", "DSL Guardians 1", "DSL Guardians 2", "DSL Mariners",
    "DSL Marlins", "DSL Mets 1", "DSL Mets 2", "DSL Nationals",
    "DSL Orioles 1", "DSL Orioles 2", "DSL Padres", "DSL Phillies Red",
    "DSL Phillies White", "DSL Pirates 1", "DSL Pirates 2",
    "DSL Rangers 1", "DSL Rangers 2", "DSL Rays 1", "DSL Rays 2",
    "DSL Red Sox Blue", "DSL Red Sox Red", "DSL Reds", "DSL Rockies",
    "DSL Royals 1", "DSL Royals 2", "DSL Tigers 1", "DSL Tigers 2",
    "DSL Twins", "DSL White Sox", "DSL Yankees",
    "FCL Astros", "FCL Blue Jays", "FCL Braves", "FCL Cardinals",
    "FCL Marlins", "FCL Mets", "FCL Nationals", "FCL Orioles",
    "FCL Phillies", "FCL Pirates", "FCL Rays", "FCL Red Sox",
    "FCL Tigers", "FCL Twins", "FCL Yankees",
}

MINOR_LEAGUE_NAMES = set(MINOR_LEAGUE_MAP.keys()) | ROOKIE_LEAGUE_NAMES

INDEPENDENT_LEAGUES = {
    "atlantic league", "american association", "pioneer league",
    "frontier league", "pacific association", "pecos league",
    "empire league", "alpb", "constellation energy league",
}

NL_TEAMS = {
    "Arizona Diamondbacks", "Atlanta Braves", "Chicago Cubs",
    "Cincinnati Reds", "Colorado Rockies", "Los Angeles Dodgers",
    "Miami Marlins", "Milwaukee Brewers", "New York Mets",
    "Philadelphia Phillies", "Pittsburgh Pirates", "San Diego Padres",
    "San Francisco Giants", "St. Louis Cardinals", "Washington Nationals",
}
AL_TEAMS = {
    "Baltimore Orioles", "Boston Red Sox", "Chicago White Sox",
    "Cleveland Guardians", "Detroit Tigers", "Houston Astros",
    "Kansas City Royals", "Los Angeles Angels", "Minnesota Twins",
    "New York Yankees", "Oakland Athletics", "Athletics",
    "Seattle Mariners", "Tampa Bay Rays", "Texas Rangers",
    "Toronto Blue Jays",
}


def fetch_json(url: str) -> dict:
    with urllib.request.urlopen(url, timeout=10) as resp:
        return json.loads(resp.read().decode())


def replace_minor_league_names(text: str) -> str:
    for full_name, short_name in MINOR_LEAGUE_MAP.items():
        if full_name in text:
            text = text.replace(full_name, short_name)
    return text


def clean_description(desc: str, team_name: str) -> str:
    text = desc.strip()

    if team_name and text.startswith(team_name):
        text = text[len(team_name):].lstrip()
        text = re.sub(r'^[\u2014\-:]\s*', '', text)

    if text:
        text = text[0].upper() + text[1:]

    text = re.sub(
        r'\b(\d{1,3}-day )?injured list\b',
        lambda m: (m.group(1) or "") + "IL",
        text,
        flags=re.IGNORECASE,
    )

    # Strip injury diagnosis labels after IL placements, including
    # cases with retroactive dates before the diagnosis sentence.
    text = re.sub(
        r'(on the \d+-day IL\b[^.]*\.)\s+[A-Z][^.]+\.',
        r'\1',
        text,
    )

    text = replace_minor_league_names(text)

    text = text.rstrip(".")
    text += "."

    # Strip accented characters
    text = "".join(
        c for c in unicodedata.normalize("NFD", text)
        if unicodedata.category(c) != "Mn"
    )

    return text


def should_skip(text: str) -> bool:
    """Return True for transaction types we never want to show."""
    lowered = text.lower()
    if "roster status changed" in lowered:
        return True
    if lowered.startswith("traded"):
        return True
    if lowered.startswith("signed"):
        return True
    if "minor league contract" in lowered:
        return True
    if any(league in lowered for league in INDEPENDENT_LEAGUES):
        return True
    return False


def transaction_priority(text: str) -> int:
    """
    Tier 0: Recalled, Selected the contract, Activated, Reinstated,
            Acquired, Claimed
    Tier 1: Optioned, Designated for assignment, Placed
    Tier 2: Transferred, Outrighted, Suspended
    Tier 3: Released, Rehab assignment
    """
    lowered = text.lower()
    tier0 = ["recalled", "selected the contract", "activated", "reinstated",
             "acquired", "claimed"]
    tier1 = ["optioned", "designated for assignment", "placed"]
    tier2 = ["transferred", "outright", "suspended"]
    tier3 = ["released", "rehab"]
    for kw in tier0:
        if lowered.startswith(kw):
            return 0
    for kw in tier1:
        if lowered.startswith(kw):
            return 1
    for kw in tier2:
        if lowered.startswith(kw):
            return 2
    for kw in tier3:
        if lowered.startswith(kw):
            return 3
    return 4


def extract_player_key(text: str):
    """
    Extract (position, normalized_name) from a transaction sentence so
    we can detect when the same player appears in multiple transactions.
    """
    m = re.match(
        r'^[A-Za-z ,]+\s+([A-Z]{1,4})\s+([A-Za-z.\'\- ]+?)\s+'
        r'(?:to|from|on|off|for)\b',
        text
    )
    if m:
        return (m.group(1), m.group(2).strip().lower())
    return None


def make_secondary_clause(text: str) -> str:
    """
    Convert a full transaction sentence into a lowercase secondary clause.
    """
    text = text.rstrip(".")
    m = re.match(
        r'^([A-Za-z]+(?:\s+the\s+contract\s+of)?)\s+'
        r'[A-Z]{1,4}\s+'
        r'[A-Za-z.\'\- ]+?\s+'
        r'(to|from|on)\s+(.+)$',
        text,
        re.IGNORECASE
    )
    if m:
        verb = m.group(1).lower()
        connector = m.group(2).lower()
        tail = m.group(3)
        return f"{verb} him {connector} {tail}"
    if re.match(r'^designated', text, re.IGNORECASE):
        return "designated him for assignment"
    return None


def combine_player_transactions(txns: list) -> list:
    """
    When the same player appears in 2+ transactions on the same day,
    combine them into one sentence with the tier-0 action leading.
    """
    player_groups = defaultdict(list)

    for t in txns:
        key = extract_player_key(t)
        if key:
            player_groups[key].append(t)

    result = []
    seen_keys = set()

    for t in txns:
        key = extract_player_key(t)
        if key is None:
            result.append(t)
            continue
        if key in seen_keys:
            continue
        seen_keys.add(key)

        group = player_groups[key]
        if len(group) == 1:
            result.append(group[0])
            continue

        group_sorted = sorted(group, key=transaction_priority)
        lead = group_sorted[0].rstrip(".")
        rest = group_sorted[1:]

        clauses = [lead]
        for secondary in rest:
            clause = make_secondary_clause(secondary)
            if clause:
                clauses.append(clause)
            else:
                result.append(secondary)

        result.append(" and ".join(clauses) + ".")

    return result


def merge_similar_transactions(cleaned_list: list) -> list:
    """
    Merge transactions sharing the same action verb and destination
    into one sentence.
    """
    pattern = re.compile(
        r'^([A-Za-z]+(?:\s+the\s+contract\s+of)?)\s+'
        r'([A-Z0-9]{1,4})\s+'
        r'([A-Za-zÀ-ÿ.\'\-]+(?:\s+[A-Za-zÀ-ÿ.\'\-]+)*?)\s+'
        r'(to|from|for|on)\s+(.+?)\.?$'
    )

    groups = {}
    order = []
    unmatched = []

    for text in cleaned_list:
        m = pattern.match(text.strip())
        if not m:
            unmatched.append(text)
            continue
        verb, pos, name, connector, tail = m.groups()
        key = (verb.strip().lower(), connector.strip().lower(),
               tail.strip().rstrip(".").lower())
        entry = f"{pos} {name.strip()}"
        if key not in groups:
            groups[key] = {"verb": verb.strip(), "connector": connector.strip(),
                           "tail": tail.strip().rstrip("."), "entries": []}
            order.append(key)
        groups[key]["entries"].append(entry)

    def join_entries(entries):
        if len(entries) == 1:
            return entries[0]
        if len(entries) == 2:
            return f"{entries[0]} and {entries[1]}"
        return ", ".join(entries[:-1]) + f" and {entries[-1]}"

    merged = []
    for key in order:
        g = groups[key]
        merged.append(
            f"{g['verb']} {join_entries(g['entries'])} {g['connector']} {g['tail']}."
        )

    return merged + unmatched


def fetch_all_transactions(target_date: date) -> dict:
    """
    Fetch all transactions for both leagues in a single pass, assigning
    each transaction to the correct league based on the RECEIVING team.
    This prevents cross-league transactions (e.g. NL team claims AL
    player) from appearing in the wrong league column.
    """
    date_str = target_date.strftime("%Y-%m-%d")
    grouped = {"NL": {}, "AL": {}}
    seen_per_team = {}

    for league_id, league_key in [(104, "NL"), (103, "AL")]:
        url = (
            f"https://statsapi.mlb.com/api/v1/transactions"
            f"?leagueId={league_id}&startDate={date_str}&endDate={date_str}"
        )
        try:
            data = fetch_json(url)
        except Exception:
            continue

        for t in data.get("transactions", []):
            to_team   = t.get("toTeam") or {}
            from_team = t.get("fromTeam") or {}
            team_obj  = to_team if to_team.get("name") else from_team
            team_name = team_obj.get("name", "")
            description = t.get("description", "")
            if not team_name or not description:
                continue

            # Resolve minor league affiliates to their parent MLB club
            if team_name in MINOR_LEAGUE_NAMES:
                team_name = from_team.get("name", team_name)
                if team_name in MINOR_LEAGUE_NAMES:
                    continue

            # Assign to correct league by team name, not by which
            # API feed this transaction came from
            if team_name in NL_TEAMS:
                correct_league = "NL"
            elif team_name in AL_TEAMS:
                correct_league = "AL"
            else:
                correct_league = league_key

            cleaned = clean_description(description, team_name)

            if should_skip(cleaned):
                continue

            norm = re.sub(r'\s+', ' ', cleaned.strip().lower())
            seen = seen_per_team.setdefault(team_name, set())
            if norm in seen:
                continue
            seen.add(norm)

            grouped[correct_league].setdefault(team_name, []).append(cleaned)

    results = {"NL": [], "AL": []}
    for league in ("NL", "AL"):
        for team_name in sorted(grouped[league].keys()):
            combined = combine_player_transactions(grouped[league][team_name])
            merged   = merge_similar_transactions(combined)
            ordered  = sorted(merged, key=transaction_priority)
            results[league].append({"team": team_name, "text": " ".join(ordered)})

    return results


def fetch_transactions(target_date: date) -> dict:
    return fetch_all_transactions(target_date)


if __name__ == "__main__":
    from datetime import timedelta
    yesterday = date.today() - timedelta(days=1)
    txns = fetch_transactions(yesterday)
    for league in ["AL", "NL"]:
        print(f"\n{league}")
        for t in txns[league]:
            print(f"  {t['team'].upper()} — {t['text']}")