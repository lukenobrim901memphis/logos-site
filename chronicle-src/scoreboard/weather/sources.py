"""
weather/sources.py — fetch + parse each data source for the weather page.
Every function returns plain dicts/lists, or None/[] when a source is down,
so one missing piece never stops the page.
"""

import math
import re
from datetime import datetime, timedelta, timezone

from . import http

try:
    from zoneinfo import ZoneInfo
    PT = ZoneInfo("America/Los_Angeles")
except Exception:                                   # pragma: no cover
    PT = timezone(timedelta(hours=-8))

NWS = "https://api.weather.gov"


# ── Small helpers ────────────────────────────────────────────────────────────

def c_to_f(c):
    return None if c is None else c * 9 / 5 + 32


def rnd(x):
    return None if x is None else int(math.floor(x + 0.5))


def parse_time(s):
    try:
        return datetime.fromisoformat(str(s).replace("Z", "+00:00"))
    except (TypeError, ValueError):
        return None


def clock(dt):
    """6:52 a.m. (AP style)"""
    if dt is None:
        return ""
    h = dt.hour % 12 or 12
    return f"{h}:{dt.minute:02d} {'a.m.' if dt.hour < 12 else 'p.m.'}"


def pt_midnight(d):
    return datetime(d.year, d.month, d.day, tzinfo=PT)


def sentences(text, n):
    parts = re.split(r"(?<=[.!?])\s+(?=[A-Z])", text.strip())
    return " ".join(parts[:n]).strip()


def tidy_caps(text):
    """NWS products are sometimes ALL CAPS; make them readable."""
    text = re.sub(r"\s+", " ", text or "").strip()
    if text and sum(c.isupper() for c in text) > 0.6 * sum(c.isalpha() for c in text):
        text = text.lower()
        text = re.sub(r"(^|[.!?]\s+)([a-z])", lambda m: m.group(1) + m.group(2).upper(), text)
        for w in ("Bay Area", "Pacific", "California", "Sierra", "Sacramento", "Monterey",
                  "San Francisco", "North Bay", "East Bay", "South Bay", "Central Coast",
                  "Santa Cruz", "Marin", "Napa", "Sonoma", "Golden Gate", "Point Reyes",
                  "Pigeon Point", "Point Arena", "Point Sur", "Delta", "Valley",
                  "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"):
            text = re.sub(r"\b" + re.escape(w.lower()) + r"\b", w, text)
    return text


# ── Sky words → codes and pictures ───────────────────────────────────────────

def sky_code(short):
    """NWS shortForecast → the Chronicle's two-letter sky codes."""
    t = (short or "").lower()
    if not t:
        return ""
    slight = "slight chance" in t
    if "thunder" in t and not slight:
        return "TS"
    if ("snow" in t or "blizzard" in t) and not slight:
        return "SN"
    if ("sleet" in t or "freezing" in t or "ice" in t) and not slight:
        return "IC"
    if "drizzle" in t and not slight:
        return "DZ"
    if "showers" in t and not slight:
        return "SH"
    if "rain" in t and not slight:
        return "RN"
    if "fog" in t or "haze" in t or "smoke" in t:
        return "FG"
    if "wind" in t or "breezy" in t or "blustery" in t:
        return "WN"
    if "partly" in t:
        return "PC"
    if "cloudy" in t or "overcast" in t:
        return "CY"
    if "sunny" in t or "clear" in t or "fair" in t:
        return "CL"
    return "PC"


ICON_OF = {"CL": "sun", "PC": "partly", "CY": "cloud", "RN": "rain", "SH": "showers",
           "DZ": "rain", "TS": "storm", "SN": "snow", "IC": "snow", "FG": "fog", "WN": "wind"}


def wmo_sky(code):
    """Open-Meteo WMO weather code → sky code."""
    c = int(code) if code is not None else -1
    if c in (0, 1):
        return "CL"
    if c == 2:
        return "PC"
    if c == 3:
        return "CY"
    if c in (45, 48):
        return "FG"
    if c in (51, 53, 55, 56, 57):
        return "DZ"
    if c in (61, 63, 65, 66, 67):
        return "RN"
    if c in (71, 73, 75, 77, 85, 86):
        return "SN"
    if c in (80, 81, 82):
        return "SH"
    if c in (95, 96, 99):
        return "TS"
    return ""


# ── Forecasts (api.weather.gov points → gridpoint forecast) ──────────────────

def point_forecast_url(lat, lon):
    d = http.get_json(f"{NWS}/points/{lat:.4f},{lon:.4f}", http.TTL_POINT) or {}
    return (d.get("properties") or {}).get("forecast")


def forecast_periods(lat, lon):
    u = point_forecast_url(lat, lon)
    if not u:
        return []
    d = http.get_json(u, http.TTL_FORECAST) or {}
    return (d.get("properties") or {}).get("periods") or []


def by_day(periods):
    """{date: {hi, lo, short, sky, name, detail, pop}} — a day's low is the
    night that follows it ('Today… highs 65; tonight… lows 48')."""
    days = {}
    for p in periods:
        st = parse_time(p.get("startTime"))
        if st is None:
            continue
        st = st.astimezone(PT)
        d = st.date()
        if not p.get("isDaytime") and st.hour < 6:       # 'Overnight' = the previous night
            d = d - timedelta(days=1)
        e = days.setdefault(d, {})
        if p.get("isDaytime"):
            e.update(hi=p.get("temperature"), short=p.get("shortForecast", ""),
                     detail=p.get("detailedForecast", ""), name=p.get("name", ""),
                     pop=(p.get("probabilityOfPrecipitation") or {}).get("value"))
        else:
            e["lo"] = p.get("temperature")
            e.setdefault("night_short", p.get("shortForecast", ""))
    for e in days.values():
        e["sky"] = sky_code(e.get("short") or e.get("night_short"))
        e["icon"] = ICON_OF.get(e["sky"], "partly")
    return days


# ── Observations (yesterday's high, low, rain) ───────────────────────────────

def observations(station, start, end):
    if not station:
        return []
    u = http.url(NWS, f"/stations/{station}/observations",
                 {"start": start.isoformat(), "end": end.isoformat()})
    d = http.get_json(u, http.TTL_OBS) or {}
    return [f.get("properties") or {} for f in d.get("features") or []]


def day_summary(obs, day):
    """High/low/rain for one Pacific day from a list of METAR observations.
    Uses the official midnight 24-hour max/min when the station sends it,
    otherwise the highest/lowest hourly reading."""
    lo_t, hi_t = pt_midnight(day), pt_midnight(day + timedelta(days=1))
    temps, rain, official = [], {}, None
    for o in obs:
        t = parse_time(o.get("timestamp"))
        if t is None:
            continue
        v = (o.get("temperature") or {}).get("value")
        if lo_t <= t < hi_t and v is not None:
            temps.append(v)
        mx = (o.get("maxTemperatureLast24Hours") or {}).get("value")
        mn = (o.get("minTemperatureLast24Hours") or {}).get("value")
        if mx is not None and mn is not None and abs((t - hi_t).total_seconds()) <= 90 * 60:
            official = (mx, mn)
        p = (o.get("precipitationLastHour") or {}).get("value")
        if lo_t < t <= hi_t and p is not None:
            tl = t.astimezone(PT)
            hour = (tl.date(), tl.hour if tl.minute >= 45 else tl.hour - 1)
            if tl.minute >= 45:                               # routine hourly report
                rain[hour] = p
    if not temps and not official:
        return None
    hi, lo = official if official else (max(temps), min(temps))
    if temps and official:                    # guard against a bad 24-hour group
        hi, lo = max(hi, max(temps)), min(lo, min(temps))
    pcp = sum(rain.values()) / 25.4 if rain else None
    return {"hi": rnd(c_to_f(hi)), "lo": rnd(c_to_f(lo)),
            "pcp": None if pcp is None else round(pcp, 2)}


# ── NWS text products ────────────────────────────────────────────────────────

def latest_product(kind, loc):
    lst = http.get_json(f"{NWS}/products/types/{kind}/locations/{loc}", http.TTL_PRODUCT) or {}
    items = lst.get("@graph") or []
    if not items:
        return None
    d = http.get_json(f"{NWS}/products/{items[0]['id']}", 30 * 24 * 3600) or {}
    return d.get("productText")


def _section(text, name):
    m = re.search(r"^\." + name + r"[^\n]*?\.\.\.(.*?)(?:^&&|^\.[A-Z][A-Z /]+\.\.\.|\Z)",
                  text, re.S | re.M)
    if not m:
        return ""
    body = m.group(1)
    body = re.sub(r"^\s*\(?Issued at [^\n]*\)?\s*$", "", body, flags=re.M | re.I)
    return body.strip()


def area_discussion(office="MTR"):
    """Short summary + outlook from the Bay Area office's forecast discussion."""
    t = latest_product("AFD", office)
    if not t:
        return {}
    syn = _section(t, "SYNOPSIS")
    if not syn:
        km = _section(t, "KEY MESSAGES")
        syn = " ".join(re.sub(r"^\s*[-*]\s*", "", ln) for ln in km.splitlines() if ln.strip())
    longterm = _section(t, "LONG TERM")
    longterm = re.sub(r"^\(?[A-Z][a-z]+ (?:through|and|night)[^)\n]*\)?\s*$", "", longterm, flags=re.M)
    return {"summary": sentences(tidy_caps(syn), 3),
            "outlook": sentences(tidy_caps(longterm), 1)}


def national_discussion():
    """Headlines from the Weather Prediction Center's short-range discussion."""
    t = latest_product("PMD", "SPD")
    if not t:
        return ""
    heads = re.findall(r"^\.\.\.(.+?)\.\.\.\s*$", t, re.M)
    heads = [tidy_caps(h).rstrip(".") + "." for h in heads if len(h) > 15][:3]
    if heads:
        return " ".join(h[0].upper() + h[1:] for h in heads)
    paras = [p for p in re.split(r"\n\s*\n", t) if len(p) > 200]
    return sentences(tidy_caps(paras[0]), 3) if paras else ""


DIRS = {"N": "North", "NE": "Northeast", "E": "East", "SE": "Southeast", "S": "South",
        "SW": "Southwest", "W": "West", "NW": "Northwest", "NNE": "North-northeast",
        "ENE": "East-northeast", "ESE": "East-southeast", "SSE": "South-southeast",
        "SSW": "South-southwest", "WSW": "West-southwest", "WNW": "West-northwest",
        "NNW": "North-northwest"}


def plain_marine(s):
    s = tidy_caps(s)
    s = re.sub(r"\bkt\b", "knots", s, flags=re.I)
    s = re.sub(r"\bft\b", "feet", s, flags=re.I)
    s = re.sub(r"\b(N|NE|E|SE|S|SW|W|NW|NNE|ENE|ESE|SSE|SSW|WSW|WNW|NNW)\b",
               lambda m: DIRS[m.group(1)], s)
    s = re.sub(r"(^|[.]\s+)([a-z])", lambda m: m.group(1) + m.group(2).upper(), s)
    s = re.sub(r"\.?\s*Wave Detail:.*?(?=\.\s+[A-Z]|$)", "", s, flags=re.I).strip()
    return s if not s or s.endswith(".") else s + "."


def coastal_waters(office="MTR"):
    """{zone: {'text': first period in plain words, 'wind': 'NW 10-20 kt', 'seas': '5-7 ft'}}"""
    t = latest_product("CWF", office)
    out = {}
    if not t:
        return out
    for block in re.split(r"^\$\$\s*$", t, flags=re.M):
        zm = re.search(r"^((?:PZZ\d{3}[->]?)+)", block, re.M)
        if not zm:
            continue
        zones = set(re.findall(r"PZZ\d{3}", zm.group(1)))
        if ">" in zm.group(1):                      # PZZ530>535 style ranges
            for a, b in re.findall(r"PZZ(\d{3})>(\d{3})", zm.group(1)):
                zones |= {f"PZZ{n:03d}" for n in range(int(a), int(b) + 1)}
        per = re.search(r"^\.([A-Z][A-Z ]+?)\.\.\.(.*?)(?=^\.[A-Z][A-Z ]+?\.\.\.|\Z)", block, re.S | re.M)
        if not per:
            continue
        raw = re.sub(r"\s+", " ", per.group(2)).strip()
        wind = re.search(r"\b([NESW]{1,3})\s+winds?\s+(\d+)\s+to\s+(\d+)\s*kt", raw, re.I)
        seas = re.search(r"\bseas\s+(\d+)\s+to\s+(\d+)\s*ft", raw, re.I) or \
            re.search(r"\bseas\s+(?:around\s+)?(\d+)\s*ft", raw, re.I)
        info = {"text": plain_marine(raw),
                "wind": f"{wind.group(1).upper()} {wind.group(2)}-{wind.group(3)} kt" if wind else "",
                "seas": ("-".join(g for g in seas.groups() if g) + " ft") if seas else ""}
        for z in zones:
            out.setdefault(z, info)
    return out


def _num(tok):
    if tok in (None, "MM", "M"):
        return None
    if tok == "T":
        return "T"
    tok = tok.rstrip("R")
    try:
        return float(tok) if "." in tok else int(tok)
    except ValueError:
        return None


def climate_report(code):
    """Parse an NWS daily climate report (CLI) for one site."""
    t = latest_product("CLI", code)
    if not t:
        return None
    out = {"code": code, "preliminary": bool(re.search(r"VALID (?:TODAY )?AS OF", t))}
    m = re.search(r"CLIMATE SUMMARY FOR ([A-Z]+ \d{1,2} \d{4})", t)
    if m:
        try:
            out["date"] = datetime.strptime(m.group(1).title(), "%B %d %Y").date()
        except ValueError:
            pass
    def row(label):
        mm = re.search(r"^\s*" + label + r"\s+(.*)$", t, re.M)
        if not mm:
            return None
        toks = mm.group(1).split()
        toks = [x for i, x in enumerate(toks)
                if not re.match(r"^\d{1,2}:\d\d$", x) and x not in ("AM", "PM")]
        return [_num(x) if not re.match(r"^(19|20)\d\d$", x) else int(x) for x in toks]
    temp = t.split("PRECIPITATION")[0]
    for key, label in (("max", "MAXIMUM"), ("min", "MINIMUM")):
        mm = re.search(r"^\s*" + label + r"\s+(.*)$", temp, re.M)
        if not mm:
            continue
        toks = [x for x in mm.group(1).split() if not re.match(r"^\d{1,2}:\d\d$", x) and x not in ("AM", "PM")]
        vals = toks + [None] * 6
        if len(toks) >= 6:       # obs, record, year, normal, departure, last year
            out[key] = {"obs": _num(vals[0]), "record": _num(vals[1]), "year": vals[2],
                        "normal": _num(vals[3])}
        else:                    # no record columns
            out[key] = {"obs": _num(vals[0]), "record": None, "year": None,
                        "normal": _num(vals[1]) if len(toks) > 1 else None}
    precip = t.split("PRECIPITATION", 1)[1] if "PRECIPITATION" in t else ""
    precip = precip.split("SNOWFALL")[0]
    def prow(label):
        mm = re.search(r"^\s*" + label + r"\s+(.*)$", precip, re.M)
        return mm.group(1).split() if mm else None
    day = prow("(?:YESTERDAY|TODAY)")
    if day:
        out["pcp"] = _num(day[0])
        if len(day) >= 6:
            out["pcp_record"], out["pcp_record_year"], out["pcp_normal"] = _num(day[1]), day[2], _num(day[3])
    mtd = prow("MONTH TO DATE")
    if mtd:
        out["month"] = _num(mtd[0])
        out["month_normal"] = _num(mtd[1]) if len(mtd) > 1 else None
    mm = re.search(r"^\s*SINCE ([A-Z]{3}) 1\s+(.*)$", precip, re.M)
    seasons = re.findall(r"^\s*SINCE ([A-Z]{3}) 1\s+(.*)$", precip, re.M)
    pick = next((s for s in seasons if s[0] == "JUL"), None) or next((s for s in seasons if s[0] == "OCT"), None) \
        or (seasons[0] if seasons else None)
    if pick:
        toks = pick[1].split()
        out["season_from"] = pick[0].title()
        out["season"] = _num(toks[0])
        out["season_normal"] = _num(toks[1]) if len(toks) > 1 else None
        out["season_last"] = _num(toks[3]) if len(toks) > 3 else None
    return out


# ── Tides and water temperature (NOAA CO-OPS, NDBC) ──────────────────────────

COOPS = "https://api.tidesandcurrents.noaa.gov/api/prod/datagetter"


def tides(station, day):
    base = {"station": station, "begin_date": day.strftime("%Y%m%d"), "range": 48,
            "product": "predictions", "datum": "MLLW", "time_zone": "lst_ldt",
            "units": "english", "format": "json", "application": "chronicle_agate"}
    hilo = http.get_json(http.url(COOPS, "", dict(base, interval="hilo")), 24 * 3600) or {}
    curve = http.get_json(http.url(COOPS, "", dict(base, interval="30")), 24 * 3600) or {}
    def rows(d):
        out = []
        for p in d.get("predictions") or []:
            try:
                t = datetime.strptime(p["t"], "%Y-%m-%d %H:%M")
                out.append({"t": t, "v": float(p["v"]), "type": p.get("type")})
            except (KeyError, ValueError):
                pass
        return out
    return {"events": rows(hilo), "curve": rows(curve)}


def bay_water_temp(station):
    d = http.get_json(http.url(COOPS, "", {"station": station, "product": "water_temperature",
                                           "date": "latest", "units": "english", "time_zone": "lst_ldt",
                                           "format": "json", "application": "chronicle_agate"}), 3 * 3600) or {}
    try:
        return rnd(float(d["data"][0]["v"]))
    except (KeyError, IndexError, ValueError, TypeError):
        return None


def buoy_water_temp(buoy):
    t = http.get_text(f"https://www.ndbc.noaa.gov/data/realtime2/{buoy}.txt", 3 * 3600)
    if not t:
        return None
    lines = t.splitlines()
    if not lines:
        return None
    head = lines[0].lstrip("#").split()
    if "WTMP" not in head:
        return None
    i = head.index("WTMP")
    for ln in lines[2:30]:
        parts = ln.split()
        if len(parts) > i and parts[i] != "MM":
            try:
                return rnd(c_to_f(float(parts[i])))
            except ValueError:
                pass
    return None


# ── International (Open-Meteo: weather.gov covers only the U.S.) ─────────────

def international(groups):
    flat = [(g, n, la, lo) for g, cities in groups for n, la, lo in cities]
    u = http.url("https://api.open-meteo.com/v1/forecast", "", {
        "latitude": ",".join(f"{c[2]:.2f}" for c in flat),
        "longitude": ",".join(f"{c[3]:.2f}" for c in flat),
        "daily": "temperature_2m_max,temperature_2m_min,weather_code",
        "temperature_unit": "fahrenheit", "timezone": "auto",
        "past_days": 1, "forecast_days": 1})
    d = http.get_json(u, 3 * 3600)
    if isinstance(d, dict):
        d = [d]
    out = {}
    for (g, n, _, _), loc in zip(flat, d or []):
        daily = (loc or {}).get("daily") or {}
        try:
            out[n] = {"hi": rnd(daily["temperature_2m_max"][0]), "lo": rnd(daily["temperature_2m_min"][0]),
                      "sky": wmo_sky(daily["weather_code"][0])}
        except (KeyError, IndexError, TypeError):
            pass
    return out


# ── Sun, moon and planets (computed, no network) ─────────────────────────────

def almanac(day, lat=37.775, lon=-122.419):
    try:
        import ephem
    except ImportError:
        return None
    obs = ephem.Observer()
    obs.lat, obs.lon, obs.elevation = str(lat), str(lon), 16
    obs.pressure = 0
    obs.horizon = "-0:34"

    def local(e):
        return ephem.Date(e).datetime().replace(tzinfo=timezone.utc).astimezone(PT)

    def rise_set(body, d):
        obs.date = pt_midnight(d).astimezone(timezone.utc).replace(tzinfo=None)
        try:
            r = local(obs.next_rising(body))
            s = local(obs.next_setting(body))
        except (ephem.AlwaysUpError, ephem.NeverUpError):
            return None, None
        return (r if r.date() == d else None), (s if s.date() == d else None)

    rows = []
    for label, d in (("Today", day), ((day + timedelta(days=1)).strftime("%A"), day + timedelta(days=1))):
        sr, ss = rise_set(ephem.Sun(), d)
        mr, ms = rise_set(ephem.Moon(), d)
        rows.append({"label": label, "sun": (clock(sr), clock(ss)), "moon": (clock(mr), clock(ms))})

    phases = []
    start = ephem.Date(pt_midnight(day).astimezone(timezone.utc).replace(tzinfo=None))
    for name, fn in (("New", ephem.next_new_moon), ("First", ephem.next_first_quarter_moon),
                     ("Full", ephem.next_full_moon), ("Last", ephem.next_last_quarter_moon)):
        phases.append((local(fn(start)), name))
    phases.sort()
    phase_rows = [{"name": n, "dt": t.date(), "kind": n.lower()} for t, n in phases]

    # planets: say when each bright planet is up tonight
    sun_set = rise_set(ephem.Sun(), day)[1]
    notes = []
    for nm, body in (("Venus", ephem.Venus()), ("Mars", ephem.Mars()),
                     ("Jupiter", ephem.Jupiter()), ("Saturn", ephem.Saturn())):
        obs.date = (sun_set or pt_midnight(day)).astimezone(timezone.utc).replace(tzinfo=None)
        try:
            nr, ns = local(obs.next_rising(body)), local(obs.next_setting(body))
        except (ephem.AlwaysUpError, ephem.NeverUpError):
            continue
        if ns < nr:                       # already up at sunset
            notes.append(f"{nm} sets at {clock(ns)}")
        else:
            notes.append(f"{nm} rises at {clock(nr)}")
    obs.date = pt_midnight(day).astimezone(timezone.utc).replace(tzinfo=None)
    m = ephem.Moon(obs)
    return {"rows": rows, "phases": phase_rows, "planets": notes,
            "moon_pct": round(m.moon_phase * 100)}
