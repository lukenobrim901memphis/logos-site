"""
Game header shared by every box score: teams, scores, linescore, title,
attendance. Reads summary['header'] and falls back to the scoreboard event.
"""

from .common import (comp0, sides, status_of, final_suffix, team_city,
                     team_nick, linescore_vals, to_int, commas, is_featured)


def game_header(summary, league, event=None, featured=None,
                title_style="paren", max_periods=None):
    comp = comp0(summary.get("header") or {})
    if not comp.get("competitors") and event:
        comp = comp0(event)
    away, home = sides(comp)
    if event:                                   # scoreboard has linescores too
        ea, eh = sides(comp0(event))
        if not away.get("linescores"):
            away = {**ea, **away, "linescores": ea.get("linescores")}
        if not home.get("linescores"):
            home = {**eh, **home, "linescores": eh.get("linescores")}

    st = status_of(comp if comp.get("status") else (event or {}))
    suffix = final_suffix(st["detail"])

    a_team, h_team = away.get("team") or {}, home.get("team") or {}
    a_score, h_score = to_int(away.get("score")), to_int(home.get("score"))
    a_ls, h_ls = linescore_vals(away), linescore_vals(home)
    if max_periods:
        a_ls, h_ls = a_ls[:max_periods], h_ls[:max_periods]

    if h_score > a_score:
        w, ws, l, ls = h_team, h_score, a_team, a_score
    else:
        w, ws, l, ls = a_team, a_score, h_team, h_score
    title = f"{team_nick(w, league)} {ws}, {team_nick(l, league)} {ls}"
    if suffix:
        if title_style == "comma":
            title += f", {suffix}"
        elif suffix.isdigit():
            title += f" ({suffix})"
        else:
            title += f" ({suffix})"

    info = summary.get("gameInfo") or {}
    att = info.get("attendance") or comp.get("attendance") or 0
    cap = (info.get("venue") or {}).get("capacity")
    att_str = ""
    if att:
        att_str = commas(att) + (f" ({commas(cap)})" if cap else "")

    return {
        "title": title,
        "suffix": suffix,
        "away": {"team": a_team, "city": team_city(a_team, league),
                 "score": a_score, "line": a_ls,
                 "featured": is_featured(a_team, featured)},
        "home": {"team": h_team, "city": team_city(h_team, league),
                 "score": h_score, "line": h_ls,
                 "featured": is_featured(h_team, featured)},
        "attendance": att_str,
        "officials": [o.get("displayName") or o.get("fullName", "")
                      for o in info.get("officials", [])],
        "status": st,
    }
