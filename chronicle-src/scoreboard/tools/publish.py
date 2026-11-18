#!/usr/bin/env python3
"""
publish.py — turn the Scoreboard app and the MLB Chronicle app into plain
HTML inside your static website (logos-site), plus a hub page linking both.

    python3 tools/publish.py                  # build today's pages
    python3 tools/publish.py --date 2026-11-16     # rebuild one past day
    python3 tools/publish.py --date 2026-11-10..2026-11-16   # or a range
    python3 tools/publish.py --push           # also git commit + push logos-site

Result in logos-site:

    chronicle/index.html                   hub page (latest + archive)
    chronicle/scoreboard/index.html        today's all-sports page
    chronicle/scoreboard/2026-11-16.html   archived copy
    chronicle/scoreboard/static/           its CSS
    chronicle/mlb/index.html               today's MLB page
    chronicle/mlb/2026-11-16.html
    chronicle/mlb/static/                  its CSS + uploaded photos

Nothing here needs a server: the Flask apps run only on your Mac, inside
this script, and the HTML they produce is saved as files.
"""

import argparse
import html
import json
import urllib.request
import os
import re
import shutil
import subprocess
import sys
from datetime import date, datetime, timedelta

HERE = os.path.dirname(os.path.abspath(__file__))

# ── Paths: edit these if your folders live somewhere else ────────────────────
SITE_DIR       = os.environ.get("AGATE_SITE_DIR", os.path.expanduser("~/logos-site"))
SCOREBOARD_DIR = os.path.join(SITE_DIR, "chronicle-src", "scoreboard")   # this app
MLB_DIR        = os.path.join(SITE_DIR, "chronicle-src", "mlb")          # your MLB app
OUT_DIR        = os.path.join(SITE_DIR, "chronicle")

# The Chronicle fonts (Ford Antenna, Farnham, Archer) are licensed typefaces.
# Putting the font files on a public website usually breaks that license, so
# by default they are NOT copied; the pages fall back to similar free fonts.
COPY_FONTS = True


# ── Freezing one page (runs in its own process so the two app.py files
#    don't collide) ───────────────────────────────────────────────────────────

ADMIN_LINK = re.compile(r'<a[^>]*href="/admin[^"]*"[^>]*>.*?</a>', re.S)


def freeze_one(app_dir, url, out_file):
    os.chdir(app_dir)                      # apps read settings/recaps/cache from cwd
    sys.path.insert(0, app_dir)
    import app as flask_app                # the app.py in app_dir
    client = flask_app.app.test_client()
    resp = client.get(url)
    if resp.status_code != 200:
        sys.exit(f"{app_dir}{url} returned {resp.status_code}")
    page = resp.get_data(as_text=True)
    page = ADMIN_LINK.sub("", page)
    page = page.replace('<html lang="en">', '<html lang="en" data-static="1">', 1)
    page = page.replace('"/static/', '"static/').replace("'/static/", "'static/")
    page = add_back_button(page)
    page = add_favicon(page)
    os.makedirs(os.path.dirname(out_file), exist_ok=True)
    with open(out_file, "w", encoding="utf-8") as f:
        f.write(page)


# ── "← Back to Agate" button, copied from .back-btn in logos-site/style.css ──
# (the agate pages don't load style.css, so the button carries its own style)
BACK_STYLE = """<style>
.site-back-btn{display:inline-block;text-decoration:none;font-family:'Gill Sans','Gill Sans MT',Calibri,'Trebuchet MS',sans-serif;
  font-weight:bold;font-size:0.9rem;line-height:normal;letter-spacing:normal;text-transform:none;
  color:#FDFBF7;background-color:#1C2D24;padding:8px 16px;margin:5px 0 12px 0;
  border:1px solid #2D5A27;border-radius:4px;transition:all 0.2s ease-in-out}
.site-back-btn:hover{background-color:#2D5A27;color:#FDFBF7;border-color:#2D5A27;transform:translateY(-1px)}
@media print{.site-back-btn{display:none}}
</style>"""
BACK_LINK = '<a href="../../agate.html" class="site-back-btn">← Back to Agate</a>'


def add_back_button(page):
    page = page.replace("</head>", BACK_STYLE + "\n</head>", 1)
    if re.search(r'<div class="page">', page):
        return re.sub(r'(<div class="page">)', r"\1" + BACK_LINK, page, count=1)
    return re.sub(r"(<body[^>]*>)", r"\1" + BACK_LINK, page, count=1)


# logos-site/images/navigation/favicon.png, seen from chronicle/<page>/x.html
FAVICON = '<link rel="icon" type="image/png" href="../../images/navigation/favicon.png">'


def add_favicon(page):
    page = re.sub(r'<link[^>]*rel="(?:shortcut )?icon"[^>]*>\s*', "", page)   # drop any local one
    return page.replace("</head>", FAVICON + "\n</head>", 1)


def copy_static(app_dir, dest):
    src = os.path.join(app_dir, "static")
    if not os.path.isdir(src):
        return
    ignore = None if COPY_FONTS else shutil.ignore_patterns("fonts")
    if os.path.isdir(dest):
        shutil.rmtree(dest)
    shutil.copytree(src, dest, ignore=ignore)
    # CSS sits inside static/, so '/static/fonts/x' becomes 'fonts/x'
    for root, _, files in os.walk(dest):
        for fn in files:
            if fn.endswith(".css"):
                p = os.path.join(root, fn)
                with open(p, encoding="utf-8") as f:
                    css = f.read()
                css = (css.replace("('/static/", "('").replace('("/static/', '("')
                          .replace("(/static/", "("))
                with open(p, "w", encoding="utf-8") as f:
                    f.write(css)


def run_freeze(app_dir, url, out_file):
    r = subprocess.run([sys.executable, os.path.abspath(__file__), "--freeze-one",
                        app_dir, url, out_file])
    return r.returncode == 0


# ── MLB season window (the MLB page is dormant outside it) ──────────────────

def mlb_season(year):
    """(regular season start, postseason end) from the MLB Stats API."""
    url = f"https://statsapi.mlb.com/api/v1/seasons/{year}?sportId=1"
    try:
        with urllib.request.urlopen(url, timeout=10) as r:
            s = (json.loads(r.read().decode()).get("seasons") or [{}])[0]
        start = s.get("regularSeasonStartDate")
        end = s.get("postSeasonEndDate") or s.get("seasonEndDate")
        if start and end:
            return date.fromisoformat(start), date.fromisoformat(end)
    except Exception as e:
        print(f"  (couldn't read MLB season dates for {year}: {e})")
    return None


def mlb_status(today):
    """Returns (in_season, note). The paper the morning after Opening Day
    through the morning after the last World Series game is 'in season'."""
    cur = mlb_season(today.year)
    if cur is None:                                   # fallback: April 1 – Nov 5
        return (date(today.year, 4, 1) <= today <= date(today.year, 11, 5),
                "Back next spring.")
    start, end = cur
    if start + timedelta(days=1) <= today <= end + timedelta(days=1):
        return True, ""
    nxt = cur if today <= start else mlb_season(today.year + 1)
    if nxt:
        back = nxt[0] + timedelta(days=1)
        return False, f"Back {back.strftime('%B %-d, %Y')}, the morning after Opening Day."
    return False, "Back next spring."


def write_archive_json(folder):
    """List of built dates; the page's Previous/Next buttons read this."""
    with open(os.path.join(folder, "archive.json"), "w") as f:
        json.dump(sorted(archive_dates(folder)), f)


# ── Hub page ─────────────────────────────────────────────────────────────────

def archive_dates(folder):
    out = []
    for fn in os.listdir(folder) if os.path.isdir(folder) else []:
        m = re.match(r"(\d{4}-\d{2}-\d{2})\.html$", fn)
        if m:
            out.append(m.group(1))
    return sorted(out, reverse=True)


def hub_page(mlb_active=True, mlb_note=""):
    def links(sub):
        rows = []
        for d in archive_dates(os.path.join(OUT_DIR, sub))[:60]:
            label = datetime.strptime(d, "%Y-%m-%d").strftime("%a, %b %-d, %Y")
            rows.append(f'<li><a href="{sub}/{d}.html">{html.escape(label)}</a></li>')
        return "\n".join(rows) or "<li><i>No pages yet</i></li>"

    if mlb_active:
        mlb_button = '<a class="latest" href="mlb/index.html">Latest page →</a>'
    else:
        last = os.path.exists(os.path.join(OUT_DIR, "mlb", "index.html"))
        mlb_button = (f'<p class="off"><b>Off-season.</b> {html.escape(mlb_note)}</p>'
                      + ('<a class="latest dim" href="mlb/index.html">Last page of the season →</a>'
                         if last else ""))
    return f"""<!DOCTYPE html>
<html lang="en"><head><meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Chronicle Agate</title>
<style>
body{{background:#f5f0e8;color:#111;font-family:Georgia,serif;margin:0}}
.wrap{{max-width:900px;margin:0 auto;padding:24px 20px 60px}}
.top{{border-bottom:2px solid #111;padding-bottom:4px;font-weight:700;font-size:13px}}
.banner{{display:inline-block;background:#8caa6a;color:#fff;font-size:30px;font-weight:700;
        text-transform:uppercase;padding:4px 18px 6px;margin:10px 0 18px}}
.grid{{display:grid;grid-template-columns:1fr 1fr;gap:20px}}
.card{{border-top:3px solid #111;padding-top:8px}}
.card h2{{font-family:Arial,sans-serif;font-size:20px;margin:0 0 4px}}
.card p{{font-size:13px;margin:0 0 10px}}
.latest{{display:inline-block;background:#111;color:#f5f0e8;padding:6px 14px;text-decoration:none;
        font-family:Arial,sans-serif;font-weight:700;font-size:12px;text-transform:uppercase}}
ul{{list-style:none;padding:0;margin:12px 0 0;font-size:13px;columns:2}}
li{{padding:1px 0}} a{{color:#111}}
.off{{font-size:13px;border-top:.75px solid #111;border-bottom:.75px solid #111;padding:4px 0;margin:0 0 10px}}
.latest.dim{{background:#777}}
@media(max-width:640px){{.grid{{grid-template-columns:1fr}}}}
</style></head><body><div class="wrap">
<div class="top">Agate pages in the style of the San Francisco Chronicle</div>
<div class="banner">Chronicle Agate</div>
<div class="grid">
  <div class="card"><h2>Scoreboard</h2>
    <p>Every sport: standings, results, box scores, odds, transactions.</p>
    <a class="latest" href="scoreboard/index.html">Latest page →</a>
    <ul>{links("scoreboard")}</ul></div>
  <div class="card"><h2>Baseball</h2>
    <p>The MLB agate page: box scores with recaps, standings, leaders.</p>
    {mlb_button}
    <ul>{links("mlb")}</ul></div>
</div>
<p style="font-size:11px;color:#666;margin-top:30px">Updated {datetime.now().strftime("%B %-d, %Y, %-I:%M %p")}.
Data: ESPN, MLB Stats API.</p>
</div></body></html>"""


# ── Main ─────────────────────────────────────────────────────────────────────

def main():
    if len(sys.argv) == 5 and sys.argv[1] == "--freeze-one":
        freeze_one(sys.argv[2], sys.argv[3], sys.argv[4])
        return

    ap = argparse.ArgumentParser()
    ap.add_argument("--date", help="paper date YYYY-MM-DD, or a range YYYY-MM-DD..YYYY-MM-DD "
                                   "(default: today)")
    ap.add_argument("--skip-mlb", action="store_true")
    ap.add_argument("--skip-scoreboard", action="store_true")
    ap.add_argument("--force-mlb", action="store_true", help="build the MLB page even in the off-season")
    ap.add_argument("--push", action="store_true", help="git commit + push logos-site")
    a = ap.parse_args()

    try:                                    # today in Pacific time, even on a UTC server
        from zoneinfo import ZoneInfo
        today = datetime.now(ZoneInfo("America/Los_Angeles")).date()
    except Exception:
        today = date.today()

    if a.date and ".." in a.date:
        first, last = (date.fromisoformat(x) for x in a.date.split(".."))
        dates = [first + timedelta(days=i) for i in range((last - first).days + 1)]
    elif a.date:
        dates = [date.fromisoformat(a.date)]
    else:
        dates = [today]
    d = dates[-1]
    ok = True

    if not a.skip_scoreboard:
        out = os.path.join(OUT_DIR, "scoreboard")
        for day in dates:
            print(f"Scoreboard {day} ...")
            if run_freeze(SCOREBOARD_DIR, f"/?date={day.isoformat()}", os.path.join(out, f"{day}.html")):
                print(f"  -> {out}/{day}.html")
            else:
                ok = False
        copy_static(SCOREBOARD_DIR, os.path.join(out, "static"))
        write_archive_json(out)
        # index.html is always the newest page, so rebuilding an old day never replaces it
        newest = max(archive_dates(out), default=None)
        if newest:
            shutil.copy(os.path.join(out, f"{newest}.html"), os.path.join(out, "index.html"))
            print(f"  latest page (index.html): {newest}")

    mlb_active, mlb_note = mlb_status(today)
    if a.force_mlb:
        mlb_active = True
    if not mlb_active:
        print(f"MLB Chronicle: off-season, not built. {mlb_note}")
    elif not a.skip_mlb and dates != [today]:
        print("MLB Chronicle: skipped (the MLB app can only build today's page).")
    elif not a.skip_mlb:
        out = os.path.join(OUT_DIR, "mlb")
        print("MLB Chronicle ...")
        if not os.path.isdir(MLB_DIR):
            print(f"  MLB app not found at {MLB_DIR} — edit MLB_DIR at the top of this file")
            ok = False
        elif run_freeze(MLB_DIR, "/", os.path.join(out, f"{today}.html")):
            shutil.copy(os.path.join(out, f"{today}.html"), os.path.join(out, "index.html"))
            copy_static(MLB_DIR, os.path.join(out, "static"))
            write_archive_json(out)
            print(f"  -> {out}/index.html")
        else:
            ok = False

    os.makedirs(OUT_DIR, exist_ok=True)
    # agate.html (in the site root) reads this to show the MLB off-season note
    with open(os.path.join(OUT_DIR, "status.json"), "w") as f:
        json.dump({"updated": datetime.now().isoformat(timespec="minutes"),
                   "page_date": max(archive_dates(os.path.join(OUT_DIR, "scoreboard")),
                                    default=d.isoformat()),
                   "mlb_active": mlb_active, "mlb_note": mlb_note}, f)
    # chronicle/ itself just forwards to the site's Agate page
    with open(os.path.join(OUT_DIR, "index.html"), "w", encoding="utf-8") as f:
        f.write('<!DOCTYPE html><meta charset="utf-8"><meta http-equiv="refresh" '
                'content="0; url=../agate.html"><a href="../agate.html">Agate pages</a>')
    print(f"Status -> {OUT_DIR}/status.json")

    if a.push:
        subprocess.run(["git", "-C", SITE_DIR, "add", "chronicle"], check=False)
        subprocess.run(["git", "-C", SITE_DIR, "commit", "-m", f"Chronicle pages for {d}"], check=False)
        subprocess.run(["git", "-C", SITE_DIR, "push"], check=False)

    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
