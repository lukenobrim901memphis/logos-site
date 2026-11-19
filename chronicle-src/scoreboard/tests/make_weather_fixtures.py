"""Synthetic weather.gov / NOAA / Open-Meteo responses for testing the
weather page offline:  python3 tests/make_weather_fixtures.py 2026-11-18
Writes tests/fixtures/weather/<slug>.(json|txt|png|jpg)."""
import json, math, os, random, re, sys
from datetime import date, datetime, timedelta, timezone

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from weather import http, sources as S, build as B

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fixtures", "weather")
os.makedirs(OUT, exist_ok=True)
DAY = date.fromisoformat(sys.argv[1] if len(sys.argv) > 1 else "2026-11-18")
rnd = random.Random(7)
SKIES = ["Rain Likely", "Mostly Sunny", "Partly Cloudy", "Mostly Cloudy", "Chance Rain Showers", "Sunny", "Patchy Fog then Sunny"]

CLI = """CDUS46 KMTR 190130
CLIMTR

CLIMATE REPORT
NATIONAL WEATHER SERVICE SAN FRANCISCO CA
530 PM PST TUE NOV 17 2026

...................................

...THE SAN FRANCISCO INTL AIRPORT CLIMATE SUMMARY FOR NOVEMBER 17 2026...

CLIMATE NORMAL PERIOD 1991 TO 2020
CLIMATE RECORD PERIOD 1927 TO 2026

WEATHER ITEM   OBSERVED TIME   RECORD YEAR NORMAL DEPARTURE LAST
                VALUE   (LST)  VALUE       VALUE  FROM      YEAR
                                                  NORMAL
...................................................................
TEMPERATURE (F)
 YESTERDAY
  MAXIMUM         {hi}   1:58 PM  73    1989  64     -3       62
  MINIMUM         {lo}   6:44 AM  38    1958  49      2       50
  AVERAGE         56                        57     -1       56

PRECIPITATION (IN)
  YESTERDAY        {p:.2f}          1.27 1932   0.07  -0.04     0.00
  MONTH TO DATE    0.53                      1.10  -0.57     0.30
  SINCE JUL 1      {s:.2f}                      2.51  -1.48     1.20
  SINCE JAN 1     14.20                     18.40  -4.20    20.10
"""

AFD = """FXUS66 KMTR 181130
AFDMTR

Area Forecast Discussion
National Weather Service San Francisco CA
330 AM PST Wed Nov 18 2026

.SYNOPSIS...
Issued at 300 AM PST Wed Nov 18 2026

Many locations will see steady rain in the morning as an associated
cold front drifts slowly south. Steady rain is expected to yield to
scattered showers in the afternoon. Dry weather returns Friday.

&&

.SHORT TERM...
Lots of details here.

&&

.LONG TERM...
(Thursday through Tuesday)
Issued at 300 AM PST Wed Nov 18 2026

Dry weather returns Friday and Saturday with chilly nights in the valleys.
Another system may arrive early next week.

&&
"""

PMD = """FOUS10 KWBC 180800
PMDSPD

Short Range Forecast Discussion
NWS Weather Prediction Center College Park MD
300 AM EST Wed Nov 18 2026

...A storm will bring a chance of rain and mountain snow over the Pacific Northwest...

...Showers and storms are possible over parts of the southern Plains and Florida...

The upper-level pattern features a deep trough over the West ...
"""

CWF = """FZUS56 KMTR 181000
CWFMTR

Coastal Waters Forecast
National Weather Service San Francisco CA

PZZ530-182300-
San Pablo Bay, Suisun Bay, the West Delta and the San Francisco Bay
north of the Bay Bridge-
200 AM PST Wed Nov 18 2026

.TODAY...SW winds 10 to 20 kt. Rain in the morning, then a chance of showers in the afternoon.
.TONIGHT...W winds 5 to 10 kt.

$$

PZZ535-182300-
Monterey Bay-
200 AM PST Wed Nov 18 2026

.TODAY...SW winds 15 to 20 kt. Seas 3 to 5 ft. Wave Detail: W 4 ft at 11 seconds.
.TONIGHT...NW winds 10 kt.

$$

PZZ540-182300-
Coastal Waters from Point Arena to Point Reyes California out to 10 nm-
.TODAY...NW winds 6 to 17 kt. Seas 3 to 5 ft.

$$

PZZ545-182300-
Coastal Waters from Point Reyes to Pigeon Point California out to 10 nm-
200 AM PST Wed Nov 18 2026

.TODAY...SW winds 10 to 20 kt. Seas 2 to 4 ft. Wave Detail: NW 5 ft at 12 seconds.
.TONIGHT...W winds 10 kt.

$$

PZZ560-182300-
Coastal Waters from Pigeon Point to Point Pinos California out to 10 nm-
.TODAY...W winds 17 to 29 kt. Seas 5 to 7 ft.

$$
"""


def forecast(lat, lon):
    inland = max(0.0, min(1.0, (lon + 122.6) / 1.2)) if -125 < lon < -114 else 0.5
    base = 58 + 8 * inland - 1.1 * (lat - 37.8) * (1 if lat < 45 else 2)
    periods, t0 = [], datetime(DAY.year, DAY.month, DAY.day, 6, tzinfo=S.PT)
    for i in range(14):
        st = t0 + timedelta(hours=12 * i)
        day = i % 2 == 0
        sky = SKIES[(i // 2 + int(lat * 3)) % len(SKIES)] if day else "Mostly Cloudy"
        temp = round(base + rnd.uniform(-3, 3) + (0 if day else -14 - 4 * inland))
        periods.append({"number": i + 1, "name": "Today" if i == 0 else st.strftime("%A") + ("" if day else " Night"),
                        "startTime": st.isoformat(), "isDaytime": day, "temperature": temp,
                        "shortForecast": sky, "detailedForecast": sky + ".",
                        "probabilityOfPrecipitation": {"value": 60 if "Rain" in sky else 10}})
    return {"properties": {"periods": periods}}


def observations(u):
    q = dict(re.findall(r"(start|end)=([^&]+)", u))
    from urllib.parse import unquote
    start, end = S.parse_time(unquote(q["start"])), S.parse_time(unquote(q["end"]))
    feats, t = [], start.replace(minute=56)
    base = rnd.uniform(8, 18)
    while t < end:
        h = t.astimezone(S.PT).hour + t.minute / 60
        temp = base + 5 * math.sin((h - 9) / 24 * 2 * math.pi)
        feats.append({"properties": {"timestamp": t.isoformat(),
                                     "temperature": {"value": round(temp, 1)},
                                     "precipitationLastHour": {"value": 1.2 if h < 4 and rnd.random() < .5 else 0}}})
        t += timedelta(hours=1)
    return {"features": list(reversed(feats))}


def tides(u):
    hilo = "interval=hilo" in u
    t0 = datetime(DAY.year, DAY.month, DAY.day)
    out = []
    if hilo:
        for i, (h, typ, v) in enumerate([(0.6, "L", 2.1), (6.9, "H", 5.9), (13.4, "L", -0.2), (19.9, "H", 4.8),
                                          (25.0, "L", 2.4), (31.2, "H", 5.7), (37.8, "L", 0.1), (44.2, "H", 4.6)]):
            out.append({"t": (t0 + timedelta(hours=h)).strftime("%Y-%m-%d %H:%M"), "v": f"{v:.3f}", "type": typ})
    else:
        for k in range(96):
            h = k / 2
            v = 2.8 + 2.0 * math.cos((h - 6.9) / 12.42 * 2 * math.pi) + 0.8 * math.cos((h - 6.9) / 24.8 * 2 * math.pi)
            out.append({"t": (t0 + timedelta(hours=h)).strftime("%Y-%m-%d %H:%M"), "v": f"{v:.3f}"})
    return {"predictions": out}


def openmeteo(u):
    from urllib.parse import unquote
    lats = unquote(re.search(r"latitude=([^&]+)", u).group(1)).split(",")
    res = []
    for la in lats:
        la = float(la)
        hi = 88 - abs(la) * 0.9 + rnd.uniform(-4, 4)
        res.append({"daily": {"temperature_2m_max": [hi, hi], "temperature_2m_min": [hi - 14, hi - 13],
                              "weather_code": [rnd.choice([0, 2, 3, 61, 80, 45]), 0]}})
    return res


def image(path, label, size):
    from PIL import Image, ImageDraw
    im = Image.new("RGB", size, (200, 215, 225))
    d = ImageDraw.Draw(im)
    d.text((10, 10), label, fill=(40, 40, 40))
    im.save(path)


def fake(u):
    if "/points/" in u:
        la, lo = map(float, u.rsplit("/", 1)[1].split(","))
        return {"properties": {"forecast": f"https://api.weather.gov/gridpoints/FAKE/{la:.3f}_{lo:.3f}/forecast"}}
    if "/gridpoints/" in u:
        la, lo = map(float, u.split("/gridpoints/FAKE/")[1].split("/")[0].split("_"))
        return forecast(la, lo)
    if "/observations" in u:
        return observations(u)
    m = re.search(r"/products/types/(\w+)/locations/(\w+)", u)
    if m:
        return {"@graph": [{"id": f"{m.group(1)}-{m.group(2)}"}]}
    m = re.search(r"/products/(\w+)-(\w+)$", u)
    if m:
        kind, loc = m.groups()
        if kind == "CLI":
            txt = CLI.format(hi=61 + rnd.randint(-5, 5), lo=48 + rnd.randint(-5, 3),
                             p=rnd.choice([0, 0.12, 0.39]), s=rnd.uniform(0.4, 4))
            txt = txt.replace("SAN FRANCISCO INTL AIRPORT", loc)
        else:
            txt = {"AFD": AFD, "PMD": PMD, "CWF": CWF}.get(kind, "")
        return {"productText": txt}
    if "interval=" in u and "tidesandcurrents" in u:
        return tides(u)
    if "water_temperature" in u:
        return {"data": [{"v": "57.4"}]}
    if "open-meteo" in u:
        return openmeteo(u)
    return {}


def write(u, ext):
    name = os.path.join(OUT, http.slug(u) + ext)
    if ext == ".json":
        json.dump(fake(u), open(name, "w"))
    elif ext == ".txt":
        open(name, "w").write("#YY  MM DD hh mm WDIR WSPD GST  WVHT   DPD   APD MWD   PRES  ATMP  WTMP  DEWP  VIS PTDY  TIDE\n"
                              "#yr  mo dy hr mn degT m/s  m/s     m   sec   sec degT   hPa  degC  degC  degC  nmi  hPa    ft\n"
                              f"2026 11 18 12 50 300  5.0  7.0   1.8    11   7.5 290 1016.5  13.0  {rnd.uniform(12,15):.1f}  10.0   MM   MM    MM\n")
    else:
        image(name, "National forecast map (sample)" if "wpc" in u else "Satellite (sample)",
              (720, 480) if "wpc" in u else (600, 600))


# record every URL the builder asks for, answering with fakes
real = http._cached
def recorder(u, ttl, ext, loader, saver, binary=False):
    write(u, ext)
    with open(os.path.join(OUT, http.slug(u) + ext), "rb" if binary else "r") as f:
        return loader(f)
http._cached = recorder
http.FIXTURE_DIR = None
B.IMG_DIR = os.path.join(OUT, "_img_test")
B.build(DAY)
print("wrote", len(os.listdir(OUT)), "fixtures to", OUT)
