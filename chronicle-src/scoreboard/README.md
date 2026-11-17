# Chronicle Scoreboard — all-sports agate page (ESPN API)

The B10 "Scoreboard" page, built from ESPN's public JSON. It's the same Flask setup, masthead and fonts as your MLB page.

## Run it

```bash
pip install flask tzdata
cp -r ../your-mlb-app/static/fonts static/      # reuse your font files
python app.py                                    # http://localhost:5002
```

- `/` — today's paper (Pacific time). Results are from yesterday; schedules and odds are for today and tomorrow.
- `/?date=2026-11-16` — any paper date, past or future.
- `/admin` — sections, box-score picks, featured teams, local results.
- `/api/page?date=…` — the assembled page as JSON, for debugging.

**First thing to do:** run `python tools/check_live.py`. It checks that the parsers line up with ESPN's live JSON (see "Notes" below).

## What's on the page

| Sport | Source | Shown |
|---|---|---|
| NFL, college football | `football/nfl`, `football/college-football` | standings, results, week schedule, odds, box (scoring summary, team stats, individual stats), AP Top 25 on Mon/Tue |
| NBA, WNBA, men's & women's college basketball | `basketball/...` | standings, results, today/tomorrow, odds, Chronicle box (Min, FG M-A, FT M-A, Reb O-T, A, PF, Pts plus Percentages, 3-Point Goals, Blocked shots…), AP Top 25 on Tue/Wed |
| NHL | `hockey/nhl` | standings (W L OT Pts GF GA), results, schedule, odds, box (goals by period with assists and pp/sh/en, SOG, power plays, goalies, shootout) |
| MLB | `baseball/mlb` | standings, results, compact box |
| MLS, NWSL, Premier League | `soccer/...` | table, results, box (goals, cautions, ejections, lineups) |
| Golf (PGA, LPGA), F1, NASCAR, ATP/WTA | scoreboards | leaderboard, race order, match results |
| Transactions | `.../transactions` | NBA, NHL, NFL, MLB, WNBA, MLS |

**When leagues appear.** A league shows up when ESPN says it's in season (or it has games). You can force it on or off in `/admin`.

**Which games get box scores.** Each league is set to `all`, `featured` (Bay Area teams only) or `none`. You can override individual games on the admin page; everything else prints as a result line.

**Local results.** Anything ESPN doesn't carry (high school, CCCAA, horse racing) goes in a free-text box on the admin page. An ALL-CAPS line becomes a subhead.

## Files

```
app.py            Flask routes
builder.py        fetches everything in parallel and assembles the page
espn.py           API client, on-disk cache (cache/), offline fixture mode
leagues.py        league registry — add a league here
settings.py       admin settings -> settings.json
parsers/          one module per sport + standings, rankings, slate (results/schedule/odds)
templates/        scoreboard.html, _macros.html (all agate blocks), admin.html
static/agate.css  multi-column newspaper layout
tools/check_live.py   verify against live ESPN
tests/make_fixtures.py  synthetic data:  AGATE_FIXTURES=tests/fixtures python app.py
```

## Notes

- **The parsers were written against ESPN's documented response shapes.** My build environment couldn't reach ESPN, so none of this has been run against live data yet. The code tolerates missing fields: a section just drops out instead of crashing. Still, run `tools/check_live.py` (add a league key, e.g. `nhl`, for verbose output). Any line marked `MISSING` shows where ESPN's shape differs from what the code expects.
- **NHL goal times.** ESPN's play clock may count down rather than up. The parser detects which and converts to elapsed time, newspaper style.
- **MLB.** Your existing MLB Stats API code makes a richer box (season HR totals, DP, umpires) than ESPN gives. In season, you could keep that as the baseball box. To do that, move `parse_boxscore` into its own module and register it in `parsers/__init__.py` for `kind="baseball"`.
- **Time zone.** Times use the `America/Los_Angeles` zone, so PST/PDT is handled. Your MLB app hard-codes UTC−7, which runs an hour off from November to March.

## Publishing to logos-site (a static website)

Your host serves only files, so both Flask apps run on your Mac and
`tools/publish.py` saves their output as plain HTML:

```
logos-site/
  chronicle-src/scoreboard/   <- this app
  chronicle-src/mlb/          <- your MLB app (moved from the Desktop)
  chronicle/                  <- generated: hub page + both agate pages + archive
```

Daily: run both apps locally, write recaps in /admin, then
`python3 tools/publish.py` (add `--push` if logos-site is a git repo) and upload as usual.
The MLB page is always built for today; `--date` only applies to the Scoreboard.

## Nightly automatic publishing

- **GitHub (recommended, Mac can be off):** copy `deploy/chronicle-publish.yml` to
  `logos-site/.github/workflows/`, commit and push. Runs 12:05 a.m. Pacific daily;
  run it by hand from the repo's Actions tab.
- **Mac only:** `bash deploy/install_mac_schedule.sh` (runs `publish.py --push` at 12:05 a.m.).

## Date navigation
Previous / Next / Today buttons and a date list sit beside the banner. Locally any
date works; on the website they cover every date that has been published
(`chronicle/scoreboard/archive.json`).
