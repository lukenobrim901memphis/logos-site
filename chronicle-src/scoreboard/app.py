#!/usr/bin/env python3
"""
Chronicle Scoreboard — all-sports agate page from the ESPN public API.

    python app.py                  -> http://localhost:5002/
    /?date=2026-11-16              -> any paper date (results = day before)
    /admin                         -> sections, box-score picks, local results
    /api/page?date=...             -> the assembled page data as JSON (debugging)
"""

import json
from datetime import date

from flask import Flask, render_template, request, redirect, url_for, jsonify, Response
from markupsafe import Markup, escape

import builder
import settings as settings_mod
from leagues import LEAGUES
from parsers.common import today_pt, shorten, shorten_steps

app = Flask(__name__)
app.config["SEND_FILE_MAX_AGE_DEFAULT"] = 0


def page_date_from_request():
    raw = request.args.get("date", "")
    try:
        return date.fromisoformat(raw)
    except ValueError:
        return today_pt()


@app.template_filter("short")
def short_filter(name, max_len=12):
    """{{ name|short(9) }} — shorten a team/player name to fit a narrow column."""
    return shorten(str(name or ""), max_len)


@app.template_filter("fit")
def fit_filter(name):
    """{{ name|fit }} — full name, plus shorter versions the page swaps in
    only if the name doesn't fit its column."""
    steps = shorten_steps(str(name or ""))
    if len(steps) == 1:
        return escape(steps[0])
    return Markup('<span class="fit" data-alt="{}">{}</span>').format(json.dumps(steps), steps[0])


@app.template_filter("agate_text")
def agate_text(body):
    """Custom-section text: an ALL-CAPS line becomes a centered subhead,
    every other line is an agate line. Blank lines add a little space."""
    out = []
    for line in (body or "").replace("\r\n", "\n").split("\n"):
        s = line.strip()
        if not s:
            out.append('<div class="gap"></div>')
        elif s.upper() == s and any(c.isalpha() for c in s):
            out.append(f'<div class="subhd">{escape(s)}</div>')
        else:
            out.append(f'<div class="ln">{escape(s)}</div>')
    return Markup("".join(out))


@app.route("/")
def index():
    s = settings_mod.load()
    page = builder.build(page_date_from_request(), s)
    return render_template("scoreboard.html", page=page, s=s, today=today_pt())


@app.route("/api/page")
def api_page():
    s = settings_mod.load()
    page = builder.build(page_date_from_request(), s)
    return Response(json.dumps(page, default=str, indent=1), mimetype="application/json")


@app.route("/admin")
def admin():
    s = settings_mod.load()
    pd = page_date_from_request()
    games = builder.admin_games(pd, s)
    return render_template("admin.html", s=s, leagues=LEAGUES, games=games,
                           page_date=pd.isoformat())


@app.route("/admin/save", methods=["POST"])
def admin_save():
    s = settings_mod.load()
    f = request.form
    s["page_label"] = f.get("page_label", s["page_label"]).strip()
    try:
        s["columns"] = max(3, min(12, int(f.get("columns", s["columns"]))))
        s["golf_limit"] = max(5, int(f.get("golf_limit", s["golf_limit"])))
        s["column_width"] = max(100, min(400, int(f.get("column_width", s.get("column_width", 120)) or 120)))
        s["min_height"] = max(0, int(f.get("min_height", s.get("min_height", 0)) or 0))
    except ValueError:
        pass
    s["featured"] = [x.strip() for x in f.get("featured", "").splitlines() if x.strip()]
    s["college_results"] = f.get("college_results", "top25")
    s["show_odds"] = bool(f.get("show_odds"))
    s["show_transactions"] = bool(f.get("show_transactions"))

    for lg in LEAGUES:
        k = lg["key"]
        s["leagues"].setdefault(k, {})
        s["leagues"][k]["mode"] = f.get(f"mode_{k}", "auto")
        s["leagues"][k]["box"] = f.get(f"box_{k}", "")
    order = [x.strip() for x in f.get("order", "").split(",") if x.strip()]
    if order:
        s["order"] = order + [lg["key"] for lg in LEAGUES if lg["key"] not in order]

    # box-score picks: only store the games shown on the form, and only
    # where they differ from the league rule
    for gid in f.getlist("game_ids"):
        want = f.get(f"game_{gid}") == "on"
        default = f.get(f"default_{gid}") == "1"
        if want == default:
            s["box_overrides"].pop(gid, None)
        else:
            s["box_overrides"][gid] = want

    customs = []
    for i in range(int(f.get("custom_count", 0))):
        t, b = f.get(f"custom_title_{i}", "").strip(), f.get(f"custom_body_{i}", "")
        if t or b.strip():
            customs.append({"title": t, "body": b})
    s["custom_sections"] = customs

    settings_mod.save(s)
    return redirect(url_for("admin", date=f.get("page_date", "")))


@app.route("/admin/reset_overrides", methods=["POST"])
def reset_overrides():
    s = settings_mod.load()
    s["box_overrides"] = {}
    settings_mod.save(s)
    return redirect(url_for("admin"))


if __name__ == "__main__":
    app.run(debug=True, port=5002)
