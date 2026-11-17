"""
NHL box score in Chronicle form:

    Devils 7, Blackhawks 5
    New Jersey ..........2 4 1 — 7
    Chicago .............4 1 0 — 5
    FIRST PERIOD — 1, Chicago, Anisimov 6 (Rutta, Kane), 0:41. 2, New
    Jersey, Wood 4 (Hall, Stafford), 3:40 (pp). ...
    Shots on goal — New Jersey 12-13-13—38. Chicago 17-16-11—44.
    Power-play opportunities — New Jersey 2 of 3; Chicago 2 of 3.
    Goalies — New Jersey, Kinkaid (44 shots-39 saves). Chicago, ...
    Att.: 21,487 (19,717).
"""

import re

from .common import NameBook, stat_index, pick, team_by_id, to_int, ascii_text
from .game import game_header

PERIOD_NAMES = {1: "FIRST PERIOD", 2: "SECOND PERIOD", 3: "THIRD PERIOD",
                4: "OVERTIME"}


def _secs(clock):
    m = re.match(r"(\d+):(\d+)", clock or "")
    return int(m.group(1)) * 60 + int(m.group(2)) if m else None


def _mmss(s):
    return f"{s // 60}:{s % 60:02d}"


def _clock_counts_down(plays):
    """Detect whether ESPN's play clock is time remaining or elapsed by
    looking at consecutive plays within a period."""
    by_period = {}
    for p in plays:
        s = _secs((p.get("clock") or {}).get("displayValue"))
        per = (p.get("period") or {}).get("number")
        if s is not None and per:
            by_period.setdefault(per, []).append(s)
    up = down = 0
    for seq in by_period.values():
        for a, b in zip(seq, seq[1:]):
            if b > a:
                up += 1
            elif b < a:
                down += 1
    return down > up


def _strength(play):
    txt = " ".join([
        str((play.get("strength") or {}).get("text", "")),
        str((play.get("strength") or {}).get("abbreviation", "")),
        str((play.get("type") or {}).get("text", "")),
        str(play.get("text", "")),
    ]).lower()
    if "power play" in txt or "ppg" in txt:
        return " (pp)"
    if "short" in txt or "shg" in txt:
        return " (sh)"
    if "empty net" in txt or "eng" in txt.split():
        return " (en)"
    return ""


def _goal_text(play, book):
    """'Anisimov 6 (Rutta, Kane)'."""
    text = ascii_text(play.get("text", ""))
    parts = play.get("participants") or []
    names = []
    for p in parts:
        ath = p.get("athlete") or {}
        nm = book.short_id(ath.get("id"), ath.get("displayName", "")) \
            if (ath.get("id") or ath.get("displayName")) else ""
        if nm:
            names.append(nm)

    m = re.search(r"\((\d+)\)", text)
    tally = m.group(1) if m else ""

    if not names:                              # parse freeform text
        scorer = re.split(r"\s*\(|\s+Goal|\s+(?:Wrist|Snap|Slap|Backhand|"
                          r"Tip-In|Deflected|Wrap-around|Poke|Between)", text)[0]
        names = [book.short(scorer.strip())]
        am = re.search(r"[Aa]ssists?:?\s*(.+)$", text)
        if am:
            for a in re.split(r",\s*(?![^()]*\))", am.group(1)):
                a = re.sub(r"\s*\(\d+\)", "", a).strip(" .")
                if a and a.lower() != "none":
                    names.append(book.short(a))

    scorer, assists = names[0], names[1:3]
    out = f"{scorer} {tally}".strip()
    out += f" ({', '.join(assists)})" if assists else " (unassisted)"
    return out


def parse(summary, league, event=None, featured=None):
    head = game_header(summary, league, event, featured, title_style="comma")
    shootout = head["suffix"] == "SO"
    if shootout:                               # 0 0 1 0 — 2 (SO column dropped)
        head["away"]["line"] = head["away"]["line"][:4]
        head["home"]["line"] = head["home"]["line"][:4]

    box = summary.get("boxscore") or {}
    book = NameBook(sep=".")
    goalies = {}
    for tp in box.get("players", []):
        tid = str((tp.get("team") or {}).get("id"))
        for grp in tp.get("statistics", []):
            labels = [str(x).upper() for x in (grp.get("labels") or [])]
            gname = (grp.get("name") or grp.get("type") or "").lower()
            is_goalie = "goal" in gname or ("SV" in labels and "SA" in labels)
            for a in grp.get("athletes", []):
                book.add_athlete(a.get("athlete"))
                if is_goalie and a.get("stats"):
                    d = dict(zip(labels, a["stats"]))
                    sa = to_int(d.get("SA"))
                    sv = to_int(d.get("SV"), sa - to_int(d.get("GA")))
                    if sa or a.get("starter"):
                        goalies.setdefault(tid, []).append(
                            ((a.get("athlete") or {}).get("displayName", ""), sa, sv))

    plays = summary.get("plays") or []
    scoring = summary.get("scoringPlays") or [p for p in plays if p.get("scoringPlay")]
    countdown = _clock_counts_down(plays or scoring)
    reg_season = True
    try:
        reg_season = int(((summary.get("header") or {}).get("season") or {}).get("type", 2)) != 3
    except Exception:
        pass

    teams = {str(head["away"]["team"].get("id")): head["away"]["city"],
             str(head["home"]["team"].get("id")): head["home"]["city"]}

    n_per = max(3, len(head["away"]["line"]))
    by_period = {p: [] for p in range(1, n_per + 1)}
    so_tally = {}
    goal_no = 0
    for p in scoring:
        per = (p.get("period") or {}).get("number") or 0
        tid = str((p.get("team") or {}).get("id"))
        if shootout and per >= 5:
            so_tally[tid] = so_tally.get(tid, 0) + 1
            continue
        goal_no += 1
        clock = (p.get("clock") or {}).get("displayValue", "")
        s = _secs(clock)
        if countdown and s is not None:
            length = 20 * 60 if (per <= 3 or not reg_season) else 5 * 60
            clock = _mmss(max(0, length - s))
        by_period.setdefault(per, []).append(
            f"{goal_no}, {teams.get(tid, '')}, {_goal_text(p, book)}, "
            f"{clock}{_strength(p)}")

    periods = []
    for per in sorted(by_period):
        if per > 3 and not by_period[per] and per > len(head["away"]["line"]):
            continue
        name = PERIOD_NAMES.get(per, f"{per - 3}{'ND' if per == 5 else 'TH'} OVERTIME")
        periods.append({"name": name,
                        "goals": ". ".join(by_period[per]) + "." if by_period[per] else "None."})

    # Shots on goal: per period from plays if they add up, else totals
    away_id = str(head["away"]["team"].get("id"))
    home_id = str(head["home"]["team"].get("id"))
    sog_lines, pp_lines = [], []
    for tid, city in ((away_id, head["away"]["city"]), (home_id, head["home"]["city"])):
        ts = stat_index(team_by_id(summary, tid).get("statistics"))
        total = to_int(pick(ts, "shotsTotal", "shots", "sog", "shotsOnGoal"), 0)
        per = {}
        for p in plays:
            ttxt = ((p.get("type") or {}).get("text") or "").lower()
            if str((p.get("team") or {}).get("id")) == tid and ttxt in ("shot", "goal", "shot on goal"):
                pn = (p.get("period") or {}).get("number")
                if pn and not (shootout and pn >= 5):
                    per[pn] = per.get(pn, 0) + 1
        if per and (not total or sum(per.values()) == total):
            seq = "-".join(str(per.get(i, 0)) for i in range(1, max(per) + 1))
            sog_lines.append(f"{city} {seq}—{sum(per.values())}")
        elif total:
            sog_lines.append(f"{city} {total}")
        ppg = pick(ts, "powerPlayGoals", "ppg")
        ppo = pick(ts, "powerPlayOpportunities", "ppo", "powerPlays")
        if ppo != "":
            pp_lines.append(f"{city} {to_int(ppg)} of {to_int(ppo)}")

    goalie_parts = []
    first = True
    for tid, city in ((away_id, head["away"]["city"]), (home_id, head["home"]["city"])):
        gl = []
        for nm, sa, sv in goalies.get(tid, []):
            gl.append(f"{book.short(nm)} ({sa} shots-{sv} saves)" if first
                      else f"{book.short(nm)} ({sa}-{sv})")
            first = False
        if gl:
            goalie_parts.append(f"{city}, " + ", ".join(gl))

    so_note = ""
    if shootout:
        winner = head["home"] if head["home"]["score"] > head["away"]["score"] else head["away"]
        wid = str(winner["team"].get("id"))
        lid = home_id if wid == away_id else away_id
        tally = f" {so_tally.get(wid, 0)}-{so_tally.get(lid, 0)}" if so_tally else ""
        so_note = f"{winner['city']} won shootout{tally}."

    head.update(kind="hockey", periods=periods, so_note=so_note,
                sog=". ".join(sog_lines) + ("." if sog_lines else ""),
                pp="; ".join(pp_lines) + ("." if pp_lines else ""),
                goalies=". ".join(goalie_parts) + ("." if goalie_parts else ""))
    return head
