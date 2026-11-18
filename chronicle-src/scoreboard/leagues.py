"""
leagues.py — every league the Scoreboard page knows about.

kind        which box-score parser / layout to use
path        ESPN {sport}/{league}
standings   standings column style (None = no standings)
box         default box-score policy: "all" | "featured" | "none"
            (admin can override per league and per game)
weekly      football: "today's games" = rest of ESPN's current week
college     results split into Top 25 / featured / other
"""

LEAGUES = [
    # ── Pro team sports ──────────────────────────────────────────────────────
    dict(key="nfl",  label="NFL", path="football/nfl", kind="football",
         standings="nfl", standings_params={"level": 3}, box="all",
         odds=True, weekly=True, transactions=True,
         nfl_weeks=True),            # last week's scores + next week until the new week starts
    dict(key="nba",  label="NBA", path="basketball/nba", kind="basketball",
         standings="wl", standings_params={"level": 3}, box="all",
         odds=True, transactions=True,
         periods=4, period_min=12, ot_min=5),
    dict(key="nhl",  label="NHL", path="hockey/nhl", kind="hockey",
         standings="nhl", standings_params={"level": 3}, box="all",
         odds=True, transactions=True),
    dict(key="mlbst", label="MLB", sublabel="Spring Training", path="baseball/mlb",
         kind="spring"),                          # only while MLB is in spring training
    dict(key="wnba", label="WNBA", path="basketball/wnba", kind="basketball",
         standings="wl", box="all", odds=True, transactions=True,
         periods=4, period_min=10, ot_min=5),
    dict(key="mls",  label="MLS", path="soccer/usa.1", kind="soccer",
         standings="soccer", box="featured", odds=False, transactions=True),
    dict(key="nwsl", label="NWSL", path="soccer/usa.nwsl", kind="soccer",
         standings="soccer", box="featured", odds=False),
    dict(key="epl",  label="Premier League", path="soccer/eng.1",
         kind="soccer", standings="soccer", box="none", odds=False),

    # ── College ──────────────────────────────────────────────────────────────
    dict(key="cfb",  label="College Football", path="football/college-football",
         kind="football", box="featured", odds=True, weekly=True, college=True,
         scoreboard_params={"groups": 80, "limit": 300},      # FBS
         extra_groups=[("FCS", {"groups": 81, "limit": 300})],  # + FCS = all Division I
         all_scores=True,                                     # every D-I score, Bay Area boxes only
         rankings_weekdays=[0, 1]),                           # Mon, Tue papers
    dict(key="mcbb", label="College Basketball", sublabel="Men",
         path="basketball/mens-college-basketball", kind="basketball",
         box="featured", odds=True, college=True,
         scoreboard_params={"groups": 50, "limit": 500},      # all D-I
         rankings_weekdays=[1, 2],
         periods=2, period_min=20, ot_min=5),
    dict(key="wcbb", label="College Basketball", sublabel="Women",
         path="basketball/womens-college-basketball", kind="basketball",
         box="featured", odds=False, college=True,
         scoreboard_params={"groups": 50, "limit": 500},
         rankings_weekdays=[1, 2],
         periods=4, period_min=10, ot_min=5),

    # ── Individual sports ────────────────────────────────────────────────────
    dict(key="pga",    label="Golf", sublabel="PGA Tour", path="golf/pga", kind="golf"),
    dict(key="lpga",   label="Golf", sublabel="LPGA",     path="golf/lpga", kind="golf"),
    dict(key="nascar", label="Motor Sports", sublabel="NASCAR Cup",
         path="racing/nascar-premier", kind="racing"),
    dict(key="f1",     label="Motor Sports", sublabel="Formula 1",
         path="racing/f1", kind="racing"),
    dict(key="atp",    label="Tennis", sublabel="ATP", path="tennis/atp", kind="tennis"),
    dict(key="wta",    label="Tennis", sublabel="WTA", path="tennis/wta", kind="tennis"),
]

BY_KEY = {lg["key"]: lg for lg in LEAGUES}

# Teams that always get a box score in "featured" mode and are set in bold.
# Matched against ESPN's team displayName (accents ignored). Editable in /admin.
DEFAULT_FEATURED = [
    "San Francisco 49ers", "Golden State Warriors",
    "San Jose Sharks", "San Francisco Giants", "Athletics",
    "Golden State Valkyries", "San Jose Earthquakes", "Bay FC",
    "California Golden Bears", "Stanford Cardinal", "San Jose State Spartans",
    "Saint Mary's Gaels", "San Francisco Dons", "Santa Clara Broncos",
]
