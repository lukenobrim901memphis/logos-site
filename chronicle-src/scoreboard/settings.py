"""Admin-editable settings, stored in settings.json."""

import json
import os
import copy

from leagues import LEAGUES, DEFAULT_FEATURED

SETTINGS_FILE = os.environ.get("AGATE_SETTINGS", "settings.json")

DEFAULTS = {
    "page_label": "B10",
    "nfl_page_label": "B9",
    "nfl_monday_page": True,
    "weather_page_label": "C6",
    "columns": 6,
    "column_width": 120,           # px per column; page width is fixed from this
    "min_height": 0,               # px; 0 = as short as the content allows
    "layout_version": 5,
    "featured": DEFAULT_FEATURED,
    # per league: mode auto|on|off, box all|featured|none|"" (""=league default)
    "leagues": {lg["key"]: {"mode": "auto", "box": ""} for lg in LEAGUES},
    "order": [lg["key"] for lg in LEAGUES],
    "box_overrides": {},           # event id -> true/false
    "college_results": "top25",    # top25 | all
    "show_odds": True,
    "show_transactions": True,
    "copy_fonts": False,           # publish the Ford Antenna/Farnham/Archer font files
    "golf_limit": 30,
    "custom_sections": [],         # [{"title": "CCCAA", "body": "..."}]
}


def load():
    s = copy.deepcopy(DEFAULTS)
    saved_version = 5                      # brand-new installs are already current
    if os.path.exists(SETTINGS_FILE):
        try:
            with open(SETTINGS_FILE) as f:
                saved = json.load(f)
            saved_version = saved.get("layout_version", 1)
            for k, v in saved.items():
                if k == "leagues":
                    for lk, lv in v.items():
                        s["leagues"].setdefault(lk, {}).update(lv)
                else:
                    s[k] = v
        except Exception as e:
            print(f"  settings load error: {e}")
    # v2 layout: narrower columns, every NFL box score, no baseball
    if saved_version < 2:
        s["leagues"].get("nfl", {})["box"] = ""
    if saved_version < 3:                  # v3: six fixed-width columns
        s["columns"] = DEFAULTS["columns"]
        s["column_width"] = DEFAULTS["column_width"]
    if saved_version < 4 and s.get("column_width") == 190:   # v4: narrower default
        s["column_width"] = DEFAULTS["column_width"]
    if saved_version < 5 and s.get("column_width") in (160, 190):  # v5: 120px columns
        s["column_width"] = DEFAULTS["column_width"]
    s["layout_version"] = 5
    s["order"] = [k for k in s["order"] if k != "mlb"]
    # new leagues added to leagues.py show up at the end of a saved order
    keys = [lg["key"] for lg in LEAGUES]
    for i, k in enumerate(keys):              # a newly added league slots in after
        if k not in s["order"]:               # its neighbor from leagues.py
            prev = next((p for p in reversed(keys[:i]) if p in s["order"]), None)
            s["order"].insert(s["order"].index(prev) + 1 if prev else 0, k)
    return s


def save(s):
    with open(SETTINGS_FILE, "w") as f:
        json.dump(s, f, indent=2)
