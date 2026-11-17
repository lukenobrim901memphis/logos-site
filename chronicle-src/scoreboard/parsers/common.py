"""
Shared helpers: names, team labels, dates/times, status, stat lookups.
Everything is written defensively — ESPN's undocumented JSON moves around,
so every lookup tolerates a missing key.
"""

import re
import unicodedata
from datetime import datetime, date, timezone

try:
    from zoneinfo import ZoneInfo
    PT = ZoneInfo("America/Los_Angeles")
except Exception:                          # pragma: no cover
    PT = timezone.utc

DAY_NAMES = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday",
             "Saturday", "Sunday"]

# ── Names ─────────────────────────────────────────────────────────────────────

_TRANSLIT = str.maketrans({"ø": "o", "Ø": "O", "ł": "l", "Ł": "L", "đ": "d",
                           "Đ": "D", "ß": "ss", "æ": "ae", "Æ": "AE",
                           "ı": "i", "œ": "oe"})


def ascii_text(s):
    """Strip accents (José -> Jose) — same idea as normalize_name()."""
    if not s:
        return ""
    s = str(s).translate(_TRANSLIT)
    return "".join(c for c in unicodedata.normalize("NFD", s)
                   if unicodedata.category(c) != "Mn")


SUFFIXES = {"jr.", "jr", "sr.", "sr", "ii", "iii", "iv", "v"}
PARTICLES = {"de", "la", "del", "della", "van", "von", "da", "di", "le",
             "st.", "der", "den", "dos", "du", "mac"}


def split_name(full):
    """'Amon-Ra St. Brown' -> ('Amon-Ra', 'St. Brown');
       'Jaren Jackson Jr.' -> ('Jaren', 'Jackson Jr.')"""
    toks = ascii_text(full).split()
    if not toks:
        return "", ""
    suffix = ""
    if len(toks) > 2 and toks[-1].lower().rstrip(",") in SUFFIXES:
        suffix = " " + toks.pop()
    if len(toks) == 1:
        return "", toks[0] + suffix
    i = len(toks) - 1
    while i > 1 and toks[i - 1].lower() in PARTICLES:
        i -= 1
    return " ".join(toks[:i]), " ".join(toks[i:]) + suffix


class NameBook:
    """Last names only, unless two players in the same game share one —
    then 'T.Young' / 'J.Young' (Chronicle agate style)."""

    def __init__(self, sep="."):
        self.sep = sep
        self.people = {}          # full ascii name -> (first, last)
        self.by_id = {}           # athlete id -> full ascii name
        self.counts = {}

    def add(self, full, athlete_id=None):
        full = ascii_text(full).strip()
        if not full:
            return
        if athlete_id is not None:
            self.by_id[str(athlete_id)] = full
        if full in self.people:
            return
        first, last = split_name(full)
        self.people[full] = (first, last)
        self.counts[last] = self.counts.get(last, 0) + 1

    def add_athlete(self, ath):
        if not ath:
            return
        self.add(ath.get("displayName") or ath.get("fullName") or "",
                 ath.get("id"))

    def short(self, full):
        full = ascii_text(full).strip()
        if full not in self.people:
            self.add(full)
        first, last = self.people.get(full, ("", full))
        if self.counts.get(last, 0) > 1 and first:
            return f"{first[0]}{self.sep}{last}"
        return last

    def short_id(self, athlete_id, fallback=""):
        full = self.by_id.get(str(athlete_id))
        return self.short(full) if full else self.short(fallback)

    def replace_in(self, text):
        """Swap any full name in freeform text for its short form."""
        text = ascii_text(text)
        for full in sorted(self.people, key=len, reverse=True):
            if full in text:
                text = text.replace(full, self.short(full))
        return text


# ── Teams ─────────────────────────────────────────────────────────────────────

# Chronicle style: Bay Area clubs by nickname, shared cities disambiguated.
TEAM_OVERRIDES = {
    "San Francisco 49ers": "49ers", "Golden State Warriors": "Warriors",
    "San Jose Sharks": "Sharks", "San Francisco Giants": "Giants",
    "Athletics": "Athletics", "Oakland Athletics": "Athletics",
    "Golden State Valkyries": "Valkyries", "San Jose Earthquakes": "Earthquakes",
    "Bay FC": "Bay FC",
    "LA Clippers": "L.A. Clippers", "Los Angeles Clippers": "L.A. Clippers",
    "Los Angeles Lakers": "L.A. Lakers",
    "Los Angeles Rams": "L.A. Rams", "Los Angeles Chargers": "L.A. Chargers",
    "Los Angeles Dodgers": "L.A. Dodgers", "Los Angeles Angels": "L.A. Angels",
    "New York Rangers": "N.Y. Rangers", "New York Islanders": "N.Y. Islanders",
    "New York Giants": "N.Y. Giants", "New York Jets": "N.Y. Jets",
    "New York Yankees": "N.Y. Yankees", "New York Mets": "N.Y. Mets",
    "Chicago Cubs": "Chicago Cubs", "Chicago White Sox": "Chicago White Sox",
    "Oklahoma City Thunder": "Okla. City",
    "LA Galaxy": "Galaxy", "Los Angeles FC": "LAFC",
    "New York Red Bulls": "N.Y. Red Bulls", "New York City FC": "NYCFC",
    "California Golden Bears": "Cal", "Saint Mary's Gaels": "St. Mary's",
    "San Francisco Dons": "USF", "San Jose State Spartans": "San Jose St.",
}


def team_city(team, league=None):
    """Standings / results / schedule label."""
    if not team:
        return ""
    dn = ascii_text(team.get("displayName", ""))
    if dn in TEAM_OVERRIDES:
        return TEAM_OVERRIDES[dn]
    kind = (league or {}).get("kind")
    if kind == "soccer":
        return ascii_text(team.get("shortDisplayName") or dn)
    loc = team.get("location") or team.get("shortDisplayName") or dn
    return ascii_text(loc)


def team_nick(team, league=None):
    """Box-score headline label: 'Thunder 112, Mavericks 99'."""
    if not team:
        return ""
    dn = ascii_text(team.get("displayName", ""))
    if (league or {}).get("college") or (league or {}).get("kind") == "soccer":
        return team_city(team, league)
    if dn in ("Athletics", "Oakland Athletics"):
        return "Athletics"
    return ascii_text(team.get("name") or team.get("shortDisplayName") or dn)


def is_featured(team, featured):
    if not team or not featured:
        return False
    dn = ascii_text(team.get("displayName", "")).lower()
    return dn in featured


def abbr_style(abbr):
    """'CLE' -> 'Cle', keep 2-letter and a few NY/LA forms as-is."""
    a = (abbr or "").upper()
    keep = {"NYJ", "NYG", "LAR", "LAC", "LV", "KC", "GB", "NE", "NO", "SF",
            "TB", "LA", "SD", "SJ", "NJ", "TBL", "LAK", "VGK"}
    special = {"WSH": "Was", "JAX": "Jac"}
    if a in special:
        return special[a]
    if a in keep or len(a) <= 2:
        return a
    return a.title()


# ── Dates / times ─────────────────────────────────────────────────────────────

def parse_dt(s):
    if not s:
        return None
    s = s.strip().replace("Z", "+00:00")
    for fmt in (None, "%Y-%m-%dT%H:%M%z", "%Y-%m-%dT%H:%M:%S%z"):
        try:
            if fmt is None:
                return datetime.fromisoformat(s)
            return datetime.strptime(s, fmt)
        except Exception:
            continue
    return None


def to_pt(s):
    dt = parse_dt(s)
    if dt is None:
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(PT)


def fmt_time(s):
    """UTC ISO -> '4 p.m.' / '4:30 p.m.' Pacific."""
    dt = to_pt(s)
    if not dt:
        return "TBA"
    h = dt.hour % 12 or 12
    ampm = "a.m." if dt.hour < 12 else "p.m."
    return f"{h} {ampm}" if dt.minute == 0 else f"{h}:{dt.minute:02d} {ampm}"


def day_name(d):
    return DAY_NAMES[d.weekday()]


def today_pt():
    return datetime.now(PT).date()


# ── Numbers ───────────────────────────────────────────────────────────────────

def to_int(v, default=0):
    if isinstance(v, dict):
        v = v.get("value", v.get("displayValue"))
    try:
        return int(float(str(v).replace(",", "")))
    except Exception:
        return default


def to_float(v, default=None):
    if isinstance(v, dict):
        v = v.get("value", v.get("displayValue"))
    try:
        return float(str(v).replace(",", ""))
    except Exception:
        return default


def halves(x):
    """6.5 -> '6½', 0.5 -> '½', 3.0 -> '3'."""
    if x is None:
        return ""
    neg = x < 0
    x = abs(x)
    whole = int(x)
    frac = round(x - whole, 2)
    s = str(whole) if whole or frac == 0 else ""
    if abs(frac - 0.5) < 0.01:
        s += "½"
    elif frac:
        s = f"{x:g}"
    return ("-" if neg else "") + s


def pct3(made, att):
    if not att:
        return ".000"
    p = made / att
    return "1.000" if p >= 1 else f".{round(p * 1000):03d}"


def made_att(s):
    """'6-11' or '6/11' -> (6, 11)."""
    m = re.match(r"\s*(\d+)\s*[-/]\s*(\d+)", str(s or ""))
    return (int(m.group(1)), int(m.group(2))) if m else (0, 0)


def commas(n):
    try:
        return f"{int(n):,}"
    except Exception:
        return str(n or "")


def ordinal(n):
    n = int(n)
    if 10 <= n % 100 <= 20:
        suf = "th"
    else:
        suf = {1: "st", 2: "nd", 3: "rd"}.get(n % 10, "th")
    return f"{n}{suf}"


# ── Event helpers ─────────────────────────────────────────────────────────────

def comp0(ev):
    comps = (ev or {}).get("competitions") or [{}]
    return comps[0] or {}


def status_of(ev_or_comp):
    st = (ev_or_comp or {}).get("status") or comp0(ev_or_comp).get("status") or {}
    t = st.get("type") or {}
    return {
        "state": t.get("state", ""),                      # pre / in / post
        "completed": bool(t.get("completed")),
        "detail": t.get("detail") or t.get("shortDetail") or t.get("description", ""),
        "short": t.get("shortDetail") or t.get("detail") or "",
        "name": t.get("name", ""),                        # STATUS_FINAL, STATUS_POSTPONED
        "period": st.get("period", 0),
    }


def final_suffix(detail):
    """'Final/OT' -> 'OT', 'Final/2OT' -> '2OT', 'Final/SO' -> 'SO',
       'Final/10' -> '10' (baseball innings)."""
    m = re.search(r"Final\s*/\s*([A-Za-z0-9]+)", detail or "")
    return m.group(1).upper() if m else ""


def sides(comp):
    """(away, home) competitor dicts."""
    away = home = None
    for c in comp.get("competitors", []):
        if c.get("homeAway") == "home":
            home = c
        elif c.get("homeAway") == "away":
            away = c
    cs = comp.get("competitors", [])
    if (away is None or home is None) and len(cs) == 2:
        away, home = cs[0], cs[1]
    return away or {}, home or {}


def rank_of(competitor):
    r = (competitor.get("curatedRank") or {}).get("current")
    try:
        r = int(r)
    except Exception:
        return None
    return r if 1 <= r <= 25 else None


def linescore_vals(competitor):
    out = []
    for ls in competitor.get("linescores") or []:
        v = ls.get("displayValue", ls.get("value"))
        if isinstance(v, float) and v.is_integer():
            v = int(v)
        out.append(str(v if v is not None else ""))
    return out


def stat_index(items):
    """Flatten ESPN stat lists into {lowercased name/label/abbr: displayValue}.
    Handles both [{name, displayValue}] and [{name: group, stats: [...]}]."""
    out = {}

    def put(it):
        val = it.get("displayValue", it.get("summary", it.get("value")))
        for k in ("name", "label", "abbreviation", "type", "shortDisplayName",
                  "displayName"):
            key = it.get(k)
            if key and key.lower() not in out:
                out[key.lower()] = val

    for it in items or []:
        if isinstance(it.get("stats"), list):
            for sub in it["stats"]:
                put(sub)
        else:
            put(it)
    return out


def pick(idx, *keys, default=""):
    for k in keys:
        v = idx.get(k.lower())
        if v not in (None, ""):
            return v
    return default


def column_map(group, key_aliases, label_aliases):
    """Map each stat column of an ESPN boxscore player group to our name."""
    keys = group.get("keys") or []
    labels = group.get("labels") or group.get("names") or []
    cols = []
    for i in range(max(len(keys), len(labels))):
        k = key_aliases.get(keys[i]) if i < len(keys) else None
        if not k and i < len(labels):
            k = label_aliases.get(str(labels[i]).upper())
        cols.append(k)
    return cols


def team_by_id(summary, team_id):
    for t in (summary.get("boxscore") or {}).get("teams", []):
        if str((t.get("team") or {}).get("id")) == str(team_id):
            return t
    return {}


# ── Shortening names to fit narrow columns (Chronicle style) ──────────────────

_ABBR = [("State", "St."), ("Saint", "St."), ("Mount", "Mt."), ("Fort", "Ft."),
         ("University", "U."), ("College", "Coll."), ("International", "Int'l"),
         ("Northern", "N."), ("Southern", "S."), ("Eastern", "E."), ("Western", "W."),
         ("Central", "C."), ("North", "N."), ("South", "S."), ("East", "E."),
         ("West", "W."), ("Christian", "Chr."), ("Carolina", "Car."),
         ("Tennessee", "Tenn."), ("Mississippi", "Miss."), ("Louisiana", "La."),
         ("Washington", "Wash."), ("Chicago", "Chi."), ("Arkansas", "Ark."),
         ("Methodist", "Meth."), ("Technology", "Tech")]
_SUFFIX = {"jr.", "sr.", "ii", "iii", "iv", "v"}
_PARTICLE = {"de", "la", "van", "von", "da", "di", "le", "mac", "del", "st."}


def _swap(word, short):
    return short.upper() if word.isupper() and len(word) > 1 else short


def shorten(name, max_len=12):
    """Shorten a team or player name until it fits max_len characters:
    'Long Beach State' -> 'Long Beach St.' -> 'L. Beach St.';
    'Gilgeous-Alexander' -> 'G-Alexander'; 'WASHINGTON' -> 'WASHINGTN'."""
    s = (name or "").strip()
    if len(s) <= max_len:
        return s

    # 1. standard abbreviations (multi-word names only: 'Washington St.' yes,
    #    'WASHINGTON' the city no — that one drops vowels instead)
    for long_w, short_w in (_ABBR if " " in s else []):
        if len(s) <= max_len:
            return s
        s = re.sub(rf"\b{long_w}\b", lambda m: _swap(m.group(0), short_w), s, flags=re.I)
    if len(s) <= max_len:
        return s

    words = s.split(" ")
    # suffixes go first for players: 'Carter Jr.' -> 'Carter'
    if len(words) > 1 and words[-1].lower() in _SUFFIX:
        words = words[:-1]
        s = " ".join(words)
        if len(s) <= max_len:
            return s

    # 2. first word (or first half of a hyphenated name) to an initial
    if len(words) > 1 and not words[0].endswith(".") and words[0].lower() not in _PARTICLE \
            and words[0][:1].isalpha():
        words[0] = words[0][0] + "."
        s = " ".join(words)
    elif len(words) == 1 and "-" in s:
        first, rest = s.split("-", 1)
        s = f"{first[0]}-{rest}"
    if len(s) <= max_len:
        return s

    # 3. drop vowels from the end of the longest word (never its first letter)
    words = s.split(" ")
    i = max(range(len(words)), key=lambda k: len(words[k]))
    w = list(words[i])
    for j in range(len(w) - 2, 0, -1):
        if len(" ".join(words[:i] + ["".join(w)] + words[i + 1:])) <= max_len:
            break
        if w[j].lower() in "aeiou":
            del w[j]
    words[i] = "".join(w)
    s = " ".join(words)
    # 4. last resort: trim
    return s if len(s) <= max_len else s[:max_len].rstrip(" .-")



def shorten_steps(name, floor=5):
    """Every progressively shorter version of a name, longest first:
    ['Long Beach State', 'Long Beach St.', 'L. Beach St.', 'L. Bech St.', ...].
    The page uses the first one that fits its column (see scoreboard.html)."""
    s = (name or "").strip()
    out = [s]

    def push(x):
        x = x.strip()
        if x and x != out[-1]:
            out.append(x)

    if " " in s:                                   # 1. standard abbreviations
        for long_w, short_w in _ABBR:
            t = re.sub(rf"\b{long_w}\b", lambda m: _swap(m.group(0), short_w), s, flags=re.I)
            if t != s:
                s = t
                push(s)
    words = s.split(" ")
    if len(words) > 1 and words[-1].lower() in _SUFFIX:   # 'Carter Jr.' -> 'Carter'
        words = words[:-1]
        s = " ".join(words)
        push(s)
    if len(words) > 1 and not words[0].endswith(".") and words[0].lower() not in _PARTICLE \
            and words[0][:1].isalpha():                # 2. 'L. Beach St.'
        words[0] = words[0][0] + "."
        s = " ".join(words)
        push(s)
    elif len(words) == 1 and "-" in s:                # 'G-Alexander'
        first, rest = s.split("-", 1)
        s = f"{first[0]}-{rest}"
        push(s)
    while True:                                        # 3. drop vowels, one at a time
        words = s.split(" ")
        i = max(range(len(words)), key=lambda k: len(words[k]))
        w = words[i]
        idx = [j for j in range(len(w) - 2, 0, -1)
               if w[j].lower() in "aeiou" and w[j - 1] not in "-'."]
        if not idx:
            break
        words[i] = w[:idx[0]] + w[idx[0] + 1:]
        s = " ".join(words)
        push(s)
    while len(s) > floor:                              # 4. trim (never below `floor`)
        t = s[:-1].rstrip(" .-")
        if len(t) < floor:
            break
        s = t
        push(s)
    return out
