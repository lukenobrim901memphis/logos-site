"""
weather/build.py — gather everything for one weather page.

build(page_date) -> dict used by templates/weather.html. Only today's page
can be built (forecasts are live); the published archive keeps past days.
"""

import json
import math
import os
import shutil
from datetime import timedelta

from . import cities as C
from . import http
from . import sources as S

HERE = os.path.dirname(os.path.abspath(__file__))
GEO = json.load(open(os.path.join(HERE, "geo.json")))

AP_MONTH = {1: "Jan.", 2: "Feb.", 3: "March", 4: "April", 5: "May", 6: "June", 7: "July",
            8: "Aug.", 9: "Sept.", 10: "Oct.", 11: "Nov.", 12: "Dec."}

# where the downloaded pictures are kept for each day (inside cache/, which the
# auto-publisher ignores) — publish.py copies them next to the page
IMG_DIR = os.path.join(os.environ.get("AGATE_CACHE", "cache"), "weather-img")


def ap_date(d):
    return f"{AP_MONTH[d.month]} {d.day}"


def project(geo, lat, lon):
    lon0, lat0, lon1, lat1 = geo["bounds"]
    k = math.cos(math.radians((lat0 + lat1) / 2))
    s = geo["width"] / ((lon1 - lon0) * k)
    return round((lon - lon0) * k * s, 1), round((lat1 - lat) * s, 1)


def hl(d):
    if not d or d.get("hi") is None or d.get("lo") is None:
        return ""
    return f"{d['hi']}/{d['lo']}"


def pcp(v):
    if v is None or v == 0:
        return ""
    if v == "T":
        return "T"
    return f"{v:.2f}".lstrip("0") if v < 1 else f"{v:.2f}"


def trend_chart(trend, normal, W=222, H=92, L=18, T=6, B=14):
    vals = [v for d in trend for v in (d["hi"], d["lo"]) if v is not None] + [v for v in normal if v is not None]
    if not vals:
        return None
    top, bot = math.ceil(max(vals) / 10) * 10, math.floor(min(vals) / 10) * 10
    span = (top - bot) or 10
    Y = lambda v: round(T + (top - v) / span * (H - T - B), 1)
    step = (W - L) / len(trend)
    bars, days = [], []
    for i, d in enumerate(trend):
        x = L + step * i
        if d["hi"] is not None and d["lo"] is not None:
            bars.append({"x": round(x + step * .2, 1), "w": round(step * .6, 1), "y": Y(d["hi"]),
                         "h": max(1, round(Y(d["lo"]) - Y(d["hi"]), 1)), "cls": d["kind"]})
        days.append({"x": round(x + step / 2, 1), "t": d["d"].strftime("%a")[0]})
    return {"W": W, "H": H, "L": L, "bars": bars, "days": days, "ylab": H - 3,
            "grid": [{"y": Y(t), "t": t} for t in range(bot, top + 1, 10)],
            "normal": [Y(v) for v in normal if v is not None],
            "split": round(L + step * 7, 1), "split_top": T, "split_bot": H - B}


def tide_chart(curve, labels, W=222, H=62, L=14, B=14):
    if len(curve) < 2:
        return None
    vs = [p["v"] for p in curve]
    hi, lo = max(vs), min(vs)
    n = len(curve)
    pts = " ".join(f"{L + i / (n - 1) * (W - L - 2):.1f},{4 + (hi - p['v']) / ((hi - lo) or 1) * (H - B - 4):.1f}"
                   for i, p in enumerate(curve))
    mid = L + (W - L - 2) / 2
    return {"W": W, "H": H, "L": L, "base": H - B, "poly": f"{L},{H - B} {pts} {W - 2},{H - B}",
            "mid": round(mid, 1), "hi": f"{hi:.0f}", "lo": f"{lo:.0f}",
            "labels": [{"x": round(L + (W - L) / 4), "t": labels[0]}, {"x": round(mid + (W - L) / 4), "t": labels[1]}]}


def yest_line(y):
    """Yesterday at a map city: 51/48 0.39″"""
    if not y:
        return ""
    r = y.get("pcp")
    return f"{y['hi']}/{y['lo']} {'0.00' if not r else f'{r:.2f}'}\u2033"


def save_picture(url, name, page_date):
    """Keep a dated copy so an archived page still shows that day's map."""
    os.makedirs(IMG_DIR, exist_ok=True)
    ext = os.path.splitext(url)[1]
    dest = os.path.join(IMG_DIR, f"{page_date}-{name}{ext}")
    if not os.path.exists(dest):
        src = http.get_file(url)
        if src and os.path.exists(src):
            shutil.copy(src, dest)
    return os.path.basename(dest) if os.path.exists(dest) else None


def prune(folder, days):
    """Drop cached files older than `days` (observations are fetched per day)."""
    import time
    if not os.path.isdir(folder):
        return
    cutoff = time.time() - days * 86400
    for fn in os.listdir(folder):
        p = os.path.join(folder, fn)
        try:
            if os.path.isfile(p) and os.path.getmtime(p) < cutoff:
                os.remove(p)
        except OSError:
            pass


def build(page_date):
    if not http.FIXTURE_DIR:
        prune(http.CACHE_DIR, 10)
        prune(IMG_DIR, 21)
    yday, tmrw = page_date - timedelta(days=1), page_date + timedelta(days=1)
    week_ago = page_date - timedelta(days=7)

    # ── everything that needs the network, in parallel ──
    places = {}                                           # name -> (lat, lon, station)
    for n, la, lo, st, _ in C.BAY_AREA:
        places[("bay", n)] = (la, lo, st)
    for n, la, lo, st in C.OFF_MAP:
        places[("bay", n)] = (la, lo, st)
    for n, la, lo, st, _ in C.CALIFORNIA:
        places[("ca", n)] = (la, lo, st)
    for n, la, lo, st in C.NATIONAL:
        places[("us", n)] = (la, lo, st)

    jobs = {("fc",) + k: (lambda la=v[0], lo=v[1]: S.forecast_periods(la, lo)) for k, v in places.items()}
    stations = {v[2] for v in places.values() if v[2]}
    start, end = S.pt_midnight(yday), S.pt_midnight(page_date) + timedelta(hours=2)
    for st in stations:
        if st == "KSFO":
            continue
        jobs[("obs", st)] = lambda st=st: S.observations(st, start, end)
    jobs[("obs", "KSFO")] = lambda: S.observations("KSFO", S.pt_midnight(week_ago), end)
    for _, code in C.CLI_SITES:
        jobs[("cli", code)] = lambda code=code: S.climate_report(code)
    jobs[("afd",)] = S.area_discussion
    jobs[("pmd",)] = S.national_discussion
    jobs[("cwf",)] = S.coastal_waters
    jobs[("tides",)] = lambda: S.tides(C.TIDE_STATION, page_date)
    jobs[("baytemp",)] = lambda: S.bay_water_temp(C.TIDE_STATION)
    for b, _, _ in C.BUOYS:
        jobs[("buoy", b)] = lambda b=b: S.buoy_water_temp(b)
    jobs[("intl",)] = lambda: S.international(C.INTERNATIONAL)
    jobs[("img", "national")] = lambda: save_picture(C.NATIONAL_MAP, "national", page_date)
    jobs[("img", "satellite")] = lambda: save_picture(C.SATELLITE, "satellite", page_date)
    got = http.run_parallel(jobs)

    fc = {k[1:]: S.by_day(v or []) for k, v in got.items() if k[0] == "fc"}
    obs_y = {}
    for st in stations:
        obs_y[st] = S.day_summary(got.get(("obs", st)) or [], yday)

    def yesterday(st):
        return obs_y.get(st) if st else None

    # ── 5-day strip (San Francisco's forecast) + Bay Area ranges ──
    sf_days = fc.get(("bay", "San Francisco"), {})
    strip = []
    for i in range(5):
        d = page_date + timedelta(days=i)
        f = sf_days.get(d)
        if not f:
            continue
        his = [fc[("bay", n)][d]["hi"] for n, *_ in C.BAY_AREA
               if d in fc.get(("bay", n), {}) and fc[("bay", n)][d].get("hi") is not None]
        los = [fc[("bay", n)][d]["lo"] for n, *_ in C.BAY_AREA
               if d in fc.get(("bay", n), {}) and fc[("bay", n)][d].get("lo") is not None]
        short = (f.get("short") or f.get("night_short") or "").strip()
        short = short[:1].upper() + short[1:].lower() + ("." if short and not short.endswith(".") else "")
        strip.append({"name": "Today" if i == 0 else d.strftime("%A"), "short": short,
                      "icon": f.get("icon", "partly"),
                      "highs": f"{min(his)}-{max(his)}" if his else "",
                      "lows": f"{min(los)}-{max(los)}" if los else ""})

    # ── Bay Area map ──
    geo = GEO["bayarea"]
    marks = []
    for n, la, lo, st, side in C.BAY_AREA:
        x, y = project(geo, la, lo)
        today = fc.get(("bay", n), {}).get(page_date) or {}
        y_ = yesterday(st)
        marks.append({"name": n, "x": x, "y": y, "side": side,
                      "fc": f"{today['hi']}°/{today['lo']}°" if today.get("hi") is not None and today.get("lo") is not None else "",
                      "yest": yest_line(y_)})
    off = []
    for n, la, lo, st in C.OFF_MAP:
        today = fc.get(("bay", n), {}).get(page_date) or {}
        y_ = yesterday(st)
        off.append({"name": n, "fc": f"{today.get('hi')}°/{today.get('lo')}°" if today.get("hi") is not None else "",
                    "yest": yest_line(y_)})
    icons = []
    for city, x, y in C.MAP_ICONS:
        f = fc.get(("bay", city), {}).get(page_date)
        if f:
            icons.append({"icon": f["icon"], "x": x - 23, "y": y - 23})
    geo = dict(geo, counties=[dict(c, **({"x": C.COUNTY_POS[c["name"]][0], "y": C.COUNTY_POS[c["name"]][1]}
                                         if c["name"] in C.COUNTY_POS else {}))
                              for c in geo.get("counties", [])])
    cwf = got.get(("cwf",)) or {}
    boxes = []
    for label, zone, la, lo in C.MARINE_BOXES:
        z = cwf.get(zone) or {}
        if z.get("wind") or z.get("seas"):
            x, y = project(geo, la, lo)
            boxes.append({"x": x, "y": y, "wind": z.get("wind"), "seas": z.get("seas")})
    water = []
    for b, la, lo in C.BUOYS:
        v = got.get(("buoy", b))
        if v is not None:
            x, y = project(geo, la, lo)
            water.append({"x": max(14, x), "y": y, "t": v})
    bay_t = got.get(("baytemp",))
    if bay_t is not None:
        x, y = project(geo, 37.81, -122.47)
        water.append({"x": x, "y": y, "t": bay_t})

    # ── San Francisco report + 14-day trend ──
    cli = {code: got.get(("cli", code)) for _, code in C.CLI_SITES}
    sf_cli = cli.get(C.SF_CLI) or {}
    sf_obs = got.get(("obs", "KSFO")) or []
    trend = []
    for i in range(7, 0, -1):
        d = page_date - timedelta(days=i)
        s = S.day_summary(sf_obs, d)
        trend.append({"d": d, "kind": "past", "hi": s and s["hi"], "lo": s and s["lo"]})
    for i in range(7):
        d = page_date + timedelta(days=i)
        f = sf_days.get(d) or {}
        trend.append({"d": d, "kind": "fc", "hi": f.get("hi"), "lo": f.get("lo")})
    normal = ((sf_cli.get("max") or {}).get("normal"), (sf_cli.get("min") or {}).get("normal"))

    # ── tides ──
    td = got.get(("tides",)) or {}
    tide_rows = []
    for i, d in enumerate((page_date, tmrw)):
        ev = [e for e in td.get("events", []) if e["t"].date() == d]
        tide_rows.append({"label": "Today" if i == 0 else d.strftime("%A"),
                          "high": [f"{S.clock(e['t'])}/{e['v']:.1f}'" for e in ev if e["type"] == "H"],
                          "low": [f"{S.clock(e['t'])}/{e['v']:.1f}'" for e in ev if e["type"] == "L"]})

    # ── California, national, international tables ──
    def table(group, rows):
        out = []
        for n, la, lo, st, *_ in rows:
            f = fc.get((group, n), {})
            y_ = yesterday(st)
            out.append({"name": n,
                        "y": hl(y_), "yp": pcp(y_.get("pcp")) if y_ else "",
                        "t": hl(f.get(page_date)), "ts": (f.get(page_date) or {}).get("sky", ""),
                        "m": hl(f.get(tmrw)), "ms": (f.get(tmrw) or {}).get("sky", ""),
                        "yhi": y_ and y_["hi"], "ylo": y_ and y_["lo"]})
        return out
    ca_rows = table("ca", C.CALIFORNIA)
    us_rows = table("us", C.NATIONAL)

    def extreme(rows, hi=True):
        vals = [(r["yhi"] if hi else r["ylo"], r["name"]) for r in rows
                if (r["yhi"] if hi else r["ylo"]) is not None]
        return (max(vals) if hi else min(vals)) if vals else None

    cageo = GEO["california"]
    ca_marks = []
    for n, la, lo, st, side in C.CALIFORNIA:
        if not side:
            continue
        x, y = project(cageo, la, lo)
        f = fc.get(("ca", n), {}).get(page_date) or {}
        ca_marks.append({"name": n, "x": x, "y": y, "side": side,
                         "fc": f"{f['hi']}/{f['lo']}" if f.get("hi") is not None and f.get("lo") is not None else ""})

    intl = got.get(("intl",)) or {}
    intl_groups = [{"name": g, "rows": [{"name": n, **intl[n]} for n, *_ in cities if n in intl]}
                   for g, cities in C.INTERNATIONAL]
    intl_groups = [g for g in intl_groups if g["rows"]]

    rain = []
    for name, code in C.CLI_SITES:
        r = cli.get(code)
        if r and r.get("season") is not None:
            rain.append({"name": name, "day": pcp(r.get("pcp")) or "0.00",
                         "season": pcp(r.get("season")) or "0.00",
                         "last": pcp(r.get("season_last")) if r.get("season_last") is not None else "",
                         "normal": pcp(r.get("season_normal")) if r.get("season_normal") is not None else "",
                         "from": r.get("season_from", "Jul")})
    rain_from = rain[0]["from"] if rain else "Jul"

    alm = S.almanac(page_date)
    if alm:
        for p in alm["phases"]:
            p["date"] = ap_date(p.pop("dt"))

    afd = got.get(("afd",)) or {}
    return {
        "page_date": page_date, "yday": yday, "tmrw": tmrw,
        "yday_name": yday.strftime("%A"), "tmrw_name": tmrw.strftime("%A"),
        "strip": strip, "summary": afd.get("summary", ""), "outlook": afd.get("outlook", ""),
        "sf": sf_cli, "sf_yest": obs_y.get("KSFO"),
        "trend": trend_chart(trend, normal),
        "tides": tide_rows,
        "tide_chart": tide_chart(td.get("curve", []), [t["label"] for t in tide_rows]),
        "marine": [{"label": lbl, "text": (cwf.get(z) or {}).get("text", "")} for lbl, z in C.MARINE
                   if (cwf.get(z) or {}).get("text")],
        "map": {"geo": geo, "marks": marks, "off": off, "icons": icons, "boxes": boxes, "water": water},
        "ca": {"geo": cageo, "marks": ca_marks, "rows": ca_rows,
               "hot": extreme(ca_rows, True), "cold": extreme(ca_rows, False)},
        "us": {"rows": us_rows, "text": got.get(("pmd",)) or "",
               "hot": extreme(us_rows, True), "cold": extreme(us_rows, False)},
        "intl": intl_groups, "rain": rain, "rain_from": rain_from,
        "almanac": alm,
        "img": {"national": got.get(("img", "national")), "satellite": got.get(("img", "satellite"))},
    }
