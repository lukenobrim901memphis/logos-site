"""
AP Top 25 from .../rankings — 'rankings': [{name, type, ranks: [...], others: [...]}]
"""

from .common import team_city, is_featured, to_int


def parse(data, league, featured=None, poll="ap"):
    polls = (data or {}).get("rankings") or []
    if not polls:
        return None
    chosen = next((p for p in polls if (p.get("type") or "").lower() == poll), None)
    chosen = chosen or next((p for p in polls if "ap" in (p.get("name") or "").lower()), polls[0])

    rows = []
    for r in chosen.get("ranks", []):
        team = r.get("team") or {}
        fpv = to_int(r.get("firstPlaceVotes"))
        rows.append({
            "rank": r.get("current"),
            "name": team_city(team, league) or team.get("nickname", ""),
            "fpv": f" ({fpv})" if fpv else "",
            "record": r.get("recordSummary", ""),
            "pts": to_int(r.get("points")) or "",
            "prev": r.get("previous") if r.get("previous") else "—",
            "featured": is_featured(team, featured),
        })
    others = []
    for o in chosen.get("others") or []:
        team = o.get("team") or {}
        pts = to_int(o.get("points"))
        if pts:
            others.append(f"{team_city(team, league)} {pts}")
    return {"title": chosen.get("name") or "AP Top 25", "rows": rows,
            "others": ", ".join(others)}
