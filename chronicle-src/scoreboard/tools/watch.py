#!/usr/bin/env python3
"""
watch.py — keeps the published Chronicle pages up to date on its own.

  • Republishes a few seconds after anything changes in the Scoreboard or
    MLB app folders (CSS, templates, /admin settings, MLB recaps, photos …).
  • Republishes every night at 12:05 a.m. Pacific (or as soon as the Mac
    wakes up, if it was asleep at midnight).
  • Refreshes the weather page at 6:15 a.m. Pacific with the morning's
    forecasts (CHRONICLE_WEATHER_AT to change it).
  • Adds the site favicon to any HTML page in logos-site that doesn't
    have one yet (new pages included), with the right path for its folder.

Run it by hand:      python3 tools/watch.py            (Ctrl+C to stop)
                     python3 tools/watch.py --push     (also git push each time)
Or install it to run in the background all the time:
                     bash deploy/install_mac_autopublish.sh
"""

import os
import re
import subprocess
import sys
import time
from datetime import datetime

try:
    from zoneinfo import ZoneInfo
    PT = ZoneInfo("America/Los_Angeles")
except Exception:                                   # pragma: no cover
    PT = None

HERE = os.path.dirname(os.path.abspath(__file__))
SCOREBOARD_DIR = os.path.dirname(HERE)
sys.path.insert(0, HERE)
import publish                                      # noqa: E402  (for its folder settings)

PUSH = "--push" in sys.argv
CHECK_EVERY = 2          # seconds between looks at the folders
QUIET_FOR = 3            # wait until nothing has changed for this long
NIGHTLY_AT = tuple(int(x) for x in os.environ.get("CHRONICLE_NIGHTLY_AT", "0:05").split(":"))

WATCH_DIRS = [SCOREBOARD_DIR, publish.MLB_DIR]
# Things the apps write by themselves while publishing — watching them
# would make the watcher republish in an endless loop.
IGNORE_DIRS = {"cache", "__pycache__", "archive", ".git", "node_modules", "tests"}
IGNORE_FILES = {"cache.json"}
EXTENSIONS = {".py", ".html", ".css", ".js", ".json", ".png", ".jpg", ".jpeg",
              ".gif", ".webp", ".svg", ".otf", ".ttf", ".woff", ".woff2"}
STAMP = os.path.join(SCOREBOARD_DIR, "cache", ".last_nightly")
WEATHER_AT = tuple(int(x) for x in os.environ.get("CHRONICLE_WEATHER_AT", "6:15").split(":"))
WEATHER_STAMP = os.path.join(SCOREBOARD_DIR, "cache", ".last_weather")


# ── Favicon on every logos-site page ─────────────────────────────────────────
SITE_DIR = publish.SITE_DIR
SKIP_SITE_DIRS = {"node_modules", ".git", "chronicle", "chronicle-src"}
ICON_RE = re.compile(r'<link[^>]+rel=["\'](?:shortcut )?icon["\']', re.I)


def favicon_file():
    for name in ("favicon.png", "favicon.ico", "favicon.svg"):
        p = os.path.join(SITE_DIR, "images", "navigation", name)
        if os.path.exists(p):
            return p
    return None


def site_pages():
    pages = {}
    for root, dirs, names in os.walk(SITE_DIR):
        dirs[:] = [d for d in dirs if d not in SKIP_SITE_DIRS and not d.startswith(".")]
        for n in names:
            if n.endswith(".html"):
                p = os.path.join(root, n)
                try:
                    pages[p] = os.path.getmtime(p)
                except OSError:
                    pass
    return pages


def ensure_favicons(paths):
    icon = favicon_file()
    if not icon:
        return
    kind = {".png": "image/png", ".ico": "image/x-icon", ".svg": "image/svg+xml"}[os.path.splitext(icon)[1]]
    for p in paths:
        try:
            with open(p, encoding="utf-8") as f:
                html = f.read()
        except (OSError, UnicodeDecodeError):
            continue
        if ICON_RE.search(html) or "</head>" not in html.lower():
            continue
        href = os.path.relpath(icon, os.path.dirname(p)).replace(os.sep, "/")
        tag = f'    <link rel="icon" type="{kind}" href="{href}">\n'
        i = html.lower().index("</head>")
        with open(p, "w", encoding="utf-8") as f:
            f.write(html[:i] + tag + html[i:])
        log(f"Added favicon to {os.path.relpath(p, SITE_DIR)}")


def log(msg):
    print(f"[{datetime.now():%Y-%m-%d %H:%M:%S}] {msg}", flush=True)


def snapshot():
    files = {}
    for root_dir in WATCH_DIRS:
        if not os.path.isdir(root_dir):
            continue
        for root, dirs, names in os.walk(root_dir):
            dirs[:] = [d for d in dirs if d not in IGNORE_DIRS and not d.startswith(".")]
            for n in names:
                if n in IGNORE_FILES or n.startswith("."):
                    continue
                if os.path.splitext(n)[1].lower() not in EXTENSIONS:
                    continue
                p = os.path.join(root, n)
                try:
                    files[p] = os.path.getmtime(p)
                except OSError:
                    pass
    return files


def changed_files(before, after):
    paths = set(before) | set(after)
    return sorted(p for p in paths if before.get(p) != after.get(p))


def publish_now(reason, extra=()):
    log(f"Publishing ({reason}) …")
    cmd = [sys.executable, os.path.join(HERE, "publish.py")] + list(extra) + (["--push"] if PUSH else [])
    r = subprocess.run(cmd, cwd=SCOREBOARD_DIR)
    log("Done." if r.returncode == 0 else f"Publish finished with errors (code {r.returncode}).")


def now_pt():
    return datetime.now(PT) if PT else datetime.now()


def last_nightly(stamp=STAMP):
    try:
        with open(stamp) as f:
            return f.read().strip()
    except OSError:
        return ""


def mark_nightly(day, stamp=STAMP):
    os.makedirs(os.path.dirname(stamp), exist_ok=True)
    with open(stamp, "w") as f:
        f.write(day)


def nightly_due(at=NIGHTLY_AT, stamp=STAMP):
    n = now_pt()
    return (n.hour, n.minute) >= at and last_nightly(stamp) != n.date().isoformat()


def main():
    log(f"Watching: {', '.join(d for d in WATCH_DIRS if os.path.isdir(d))}")
    log(f"Nightly publish at {NIGHTLY_AT[0]}:{NIGHTLY_AT[1]:02d} Pacific"
        + ("; pushing with git after each publish." if PUSH else "."))
    publish_now("starting up")
    if (now_pt().hour, now_pt().minute) >= NIGHTLY_AT:
        mark_nightly(now_pt().date().isoformat())
    if (now_pt().hour, now_pt().minute) >= WEATHER_AT:
        mark_nightly(now_pt().date().isoformat(), WEATHER_STAMP)

    pages = site_pages()
    ensure_favicons(list(pages))
    pages = site_pages()

    snap = snapshot()
    pending, last_change = [], 0.0
    while True:
        time.sleep(CHECK_EVERY)
        new_pages = site_pages()
        touched = [p for p in new_pages if pages.get(p) != new_pages[p]]
        if touched:
            ensure_favicons(touched)
            new_pages = site_pages()
        pages = new_pages
        new = snapshot()
        diff = changed_files(snap, new)
        if diff:
            pending = sorted(set(pending) | set(diff))
            last_change = time.time()
            snap = new
        if pending and time.time() - last_change >= QUIET_FOR:
            names = ", ".join(os.path.relpath(p, os.path.dirname(SCOREBOARD_DIR)) for p in pending[:4])
            more = f" and {len(pending) - 4} more" if len(pending) > 4 else ""
            publish_now(f"changed: {names}{more}")
            pending = []
            snap = snapshot()
        if nightly_due():
            publish_now("nightly")
            mark_nightly(now_pt().date().isoformat())
            snap = snapshot()
        if nightly_due(WEATHER_AT, WEATHER_STAMP):
            publish_now("morning weather", ["--weather-only"])
            mark_nightly(now_pt().date().isoformat(), WEATHER_STAMP)
            snap = snapshot()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        log("Stopped.")
