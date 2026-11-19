"""
weather/http.py — cached fetching for the weather page.

Sources (all free, no key):
  api.weather.gov                 forecasts, observations, NWS text products
  api.tidesandcurrents.noaa.gov   Golden Gate tides, bay water temperature
  www.ndbc.noaa.gov               offshore buoy water temperatures
  api.open-meteo.com              international cities (weather.gov is U.S. only)
  www.wpc.ncep.noaa.gov           national forecast map (image)
  cdn.star.nesdis.noaa.gov        GOES-West satellite picture

Everything is cached under cache/weather/ with a per-call TTL, and a stale
copy is used if a source is down. AGATE_FIXTURES works here too.
"""

import hashlib
import json
import os
import re
import time
import urllib.parse
import urllib.request
from concurrent.futures import ThreadPoolExecutor

CACHE_DIR = os.path.join(os.environ.get("AGATE_CACHE", "cache"), "weather")
FIXTURE_DIR = os.environ.get("AGATE_FIXTURES")
# weather.gov asks every app to identify itself
USER_AGENT = "chronicle-agate-weather (personal page; github pages)"

HOUR = 3600
TTL_FORECAST = 1 * HOUR
TTL_OBS = 1 * HOUR
TTL_PRODUCT = 1 * HOUR
TTL_POINT = 90 * 24 * HOUR      # a lat/lon's forecast office + grid never changes
TTL_IMAGE = 3 * HOUR


def slug(url):
    s = re.sub(r"^https?://", "", url)
    s = re.sub(r"[^A-Za-z0-9]+", "_", s).strip("_")
    if len(s) > 150:
        s = s[:110] + "_" + hashlib.sha1(s.encode()).hexdigest()[:10]
    return s


def _cached(url, ttl, ext, loader, saver, binary=False):
    name = slug(url) + ext
    if FIXTURE_DIR:
        p = os.path.join(FIXTURE_DIR, "weather", name)
        if os.path.exists(p):
            with open(p, "rb" if binary else "r") as f:
                return loader(f)
        return None
    os.makedirs(CACHE_DIR, exist_ok=True)
    path = os.path.join(CACHE_DIR, name)
    if os.path.exists(path) and time.time() - os.path.getmtime(path) < ttl:
        try:
            with open(path, "rb" if binary else "r") as f:
                return loader(f)
        except Exception:
            pass
    try:
        req = urllib.request.Request(url, headers={
            "User-Agent": USER_AGENT,
            "Accept": "application/geo+json, application/json;q=0.9, */*;q=0.5"})
        with urllib.request.urlopen(req, timeout=20) as r:
            raw = r.read()
        data = saver(raw)
        with open(path, "wb") as f:
            f.write(raw)
        return data
    except Exception as e:
        print(f"  weather fetch failed ({e}): {url}")
        if os.path.exists(path):
            with open(path, "rb" if binary else "r") as f:
                return loader(f)
        return None


def get_json(url, ttl=TTL_FORECAST):
    return _cached(url, ttl, ".json", json.load, lambda raw: json.loads(raw.decode()))


def get_text(url, ttl=TTL_PRODUCT):
    return _cached(url, ttl, ".txt", lambda f: f.read(), lambda raw: raw.decode("utf-8", "replace"))


def get_file(url, ttl=TTL_IMAGE):
    """Download (or reuse) a picture; returns the cached file's path or None."""
    ext = os.path.splitext(urllib.parse.urlparse(url).path)[1] or ".bin"
    got = _cached(url, ttl, ext, lambda f: True, lambda raw: True, binary=True)
    if not got:
        return None
    base = os.path.join(FIXTURE_DIR, "weather") if FIXTURE_DIR else CACHE_DIR
    return os.path.join(base, slug(url) + ext)


def url(base, path="", params=None):
    q = ("?" + urllib.parse.urlencode(params)) if params else ""
    return f"{base}{path}{q}"


def run_parallel(jobs, workers=6):
    """weather.gov is happiest with only a few requests at once."""
    def wrap(fn):
        try:
            return fn()
        except Exception as e:
            print(f"  weather job error: {e}")
            return None
    with ThreadPoolExecutor(max_workers=workers) as pool:
        futs = {k: pool.submit(wrap, fn) for k, fn in jobs.items()}
        return {k: f.result() for k, f in futs.items()}
