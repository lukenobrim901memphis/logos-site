"""
espn.py — thin client for ESPN's public (unofficial) JSON API.

  Site API     https://site.api.espn.com/apis/site/v2/sports/{sport}/{league}/...
               scoreboard, summary, rankings, transactions
  Standings    https://site.api.espn.com/apis/v2/sports/{sport}/{league}/standings
               (the site/v2 standings path only returns a stub)

Every response is cached on disk under cache/ with a per-call TTL, so a
Flask restart or a page reload doesn't hammer ESPN, and a stale copy is
served if ESPN is down.

Offline / test mode: set AGATE_FIXTURES=/path/to/dir and every call is
answered from <dir>/<slug>.json instead of the network (see slug()).
"""

import hashlib
import json
import os
import re
import time
import urllib.parse
import urllib.request
from concurrent.futures import ThreadPoolExecutor

SITE = "https://site.api.espn.com/apis/site/v2/sports"
SITE_V2 = "https://site.api.espn.com/apis/v2/sports"

CACHE_DIR = os.environ.get("AGATE_CACHE", "cache")
FIXTURE_DIR = os.environ.get("AGATE_FIXTURES")
USER_AGENT = "Mozilla/5.0 (agate-page; personal use)"

# TTLs in seconds
TTL_LIVE = 5 * 60           # today's / upcoming scoreboards
TTL_PAST = 60 * 60          # yesterday's scoreboard (stat corrections)
TTL_FINAL = 7 * 24 * 3600   # a completed game's summary
TTL_STANDINGS = 30 * 60
TTL_SLOW = 6 * 3600         # rankings, transactions


def slug(url):
    """Readable, filesystem-safe name for a URL (used for cache + fixtures)."""
    tail = url.split("/sports/", 1)[-1]
    s = re.sub(r"[^A-Za-z0-9]+", "_", tail).strip("_")
    if len(s) > 150:
        s = s[:110] + "_" + hashlib.sha1(s.encode()).hexdigest()[:10]
    return s


def get_json(url, ttl=TTL_LIVE):
    name = slug(url) + ".json"

    if FIXTURE_DIR:
        path = os.path.join(FIXTURE_DIR, name)
        if os.path.exists(path):
            with open(path) as f:
                return json.load(f)
        return {}

    os.makedirs(CACHE_DIR, exist_ok=True)
    path = os.path.join(CACHE_DIR, name)
    if os.path.exists(path) and time.time() - os.path.getmtime(path) < ttl:
        try:
            with open(path) as f:
                return json.load(f)
        except Exception:
            pass

    try:
        req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read().decode())
        with open(path, "w") as f:
            json.dump(data, f)
        return data
    except Exception as e:
        print(f"  ESPN fetch failed ({e}): {url}")
        if os.path.exists(path):          # serve stale copy
            with open(path) as f:
                return json.load(f)
        return {}


def _url(base, path, endpoint, params=None):
    q = ("?" + urllib.parse.urlencode(params)) if params else ""
    return f"{base}/{path}/{endpoint}{q}"


# ── Endpoints ─────────────────────────────────────────────────────────────────

def scoreboard(path, day=None, extra=None, ttl=None):
    """day: datetime.date or None (None = ESPN's 'current' slate/week)."""
    params = dict(extra or {})
    if day is not None:
        params["dates"] = day.strftime("%Y%m%d")
    return get_json(_url(SITE, path, "scoreboard", params), ttl or TTL_LIVE)


def summary(path, event_id, final=True):
    return get_json(_url(SITE, path, "summary", {"event": event_id}),
                    TTL_FINAL if final else TTL_LIVE)


def standings(path, extra=None):
    return get_json(_url(SITE_V2, path, "standings", extra), TTL_STANDINGS)


def rankings(path):
    return get_json(_url(SITE, path, "rankings"), TTL_SLOW)


def transactions(path):
    return get_json(_url(SITE, path, "transactions"), TTL_SLOW)


def run_parallel(jobs, workers=12):
    """jobs: dict name -> zero-arg callable. Returns dict name -> result
    (exceptions are caught and returned as None so one bad call can't
    take down the page)."""
    out = {}

    def wrap(fn):
        try:
            return fn()
        except Exception as e:
            print(f"  job error: {e}")
            return None

    with ThreadPoolExecutor(max_workers=workers) as pool:
        futs = {k: pool.submit(wrap, fn) for k, fn in jobs.items()}
        for k, fut in futs.items():
            out[k] = fut.result()
    return out
