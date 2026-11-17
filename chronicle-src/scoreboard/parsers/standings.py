"""
Standings from https://site.api.espn.com/apis/v2/sports/{sport}/{league}/standings

The response nests groups: root -> conferences -> (divisions). Any node
with standings.entries is a table. We recompute Pct and GB ourselves and
sort, because ESPN's entry order isn't guaranteed.
"""

from .common import stat_index, to_float, to_int, team_city, is_featured, halves

STYLES = {
    #        columns shown                                    sort
    "wl":     (["W", "L", "Pct", "GB"],                        "pct"),
    "nhl":    (["W", "L", "OT", "Pts", "GF", "GA"],            "pts"),
    "nfl":    (["W", "L", "T", "Pct", "PF", "PA"],              "pct"),
    "soccer": (["W", "D", "L", "GF", "GA", "Pts"],             "pts"),
}

KEYS = {
    "W": ("wins", "w"), "L": ("losses", "l"), "T": ("ties", "t"),
    "D": ("ties", "draws", "d"), "OT": ("otlosses", "overtimelosses", "otl", "ot"),
    "Pts": ("points", "pts"), "GP": ("gamesplayed", "gp"),
    "GF": ("pointsfor", "goalsfor", "gf"), "GA": ("pointsagainst", "goalsagainst", "ga"),
    "PF": ("pointsfor", "pf"), "PA": ("pointsagainst", "pa"),
    "Home": ("home", "homerecord"), "Away": ("road", "away", "awayrecord"),
    "Div": ("vs. div.", "vsdiv", "divisionrecord", "division", "div"),
    "L10": ("lasttengames", "l10", "last ten games"), "Strk": ("streak", "strk"),
}


def _get(idx, col):
    for k in KEYS.get(col, (col.lower(),)):
        if k in idx and idx[k] not in (None, ""):
            return idx[k]
    return ""


def _walk(node, parents, out):
    name = node.get("name") or node.get("abbreviation") or ""
    entries = (node.get("standings") or {}).get("entries")
    if entries:
        out.append({"conference": parents[-1] if parents else "",
                    "name": name, "entries": entries})
    for ch in node.get("children") or []:
        _walk(ch, parents + ([name] if name else []), out)


def parse(data, league, featured=None):
    style = league.get("standings") or "wl"
    cols, sort_by = STYLES.get(style, STYLES["wl"])
    raw_groups = []
    _walk(data or {}, [], raw_groups)

    groups, last_conf = [], None
    for g in raw_groups:
        rows = []
        for e in g["entries"]:
            idx = stat_index(e.get("stats"))
            team = e.get("team") or {}
            w, l, t = (to_int(_get(idx, "W")), to_int(_get(idx, "L")),
                       to_int(_get(idx, "T")) if style == "nfl" else 0)
            gp = w + l + t
            pct = (w + 0.5 * t) / gp if gp else 0.0
            row = {"name": team_city(team, league),
                   "featured": is_featured(team, featured),
                   "_w": w, "_l": l, "_pct": pct,
                   "_pts": to_float(_get(idx, "Pts"), 0) or 0,
                   "_gp": to_int(_get(idx, "GP")) or gp,
                   "_seed": to_float(idx.get("playoffseed"), 99) or 99}
            for c in cols:
                if c == "Pct":
                    row[c] = "1.000" if pct >= 1 else f".{round(pct * 1000):03d}"
                elif c in ("W", "L", "T"):
                    row[c] = {"W": w, "L": l, "T": t}[c]
                else:
                    row[c] = _get(idx, c)
            rows.append(row)

        if sort_by == "pts":
            rows.sort(key=lambda r: (-r["_pts"], r["_gp"], r["_seed"]))
        else:
            rows.sort(key=lambda r: (-r["_pct"], r["_seed"], -r["_w"]))

        if "GB" in cols and rows:
            lw, ll = rows[0]["_w"], rows[0]["_l"]
            for r in rows:
                gb = ((lw - r["_w"]) + (r["_l"] - ll)) / 2
                r["GB"] = "—" if gb <= 0 else halves(gb)

        conf = g["conference"] if g["conference"] != g["name"] else ""
        groups.append({"conference": conf if conf != last_conf else "",
                       "name": g["name"], "rows": rows})
        last_conf = conf
    return {"columns": cols, "groups": groups,
            "note": ("Two points for a win, one point for overtime loss."
                     if style == "nhl" else "")}
