#!/usr/bin/env python3
"""
Logo Page Sync
--------------
Keeps each team page on your logos site in step with that team's image
folder, so you never have to copy file names into the page by hand.

Every run (launchd runs it every 30 seconds; you can also run it yourself):
  0. Copies your logos from iCloud Drive (Sports/Logos/MLB, MiLB, ...) into the
     site's image folders as compressed PNGs, using logo-teams.txt to decide
     which team folder each file goes in. iCloud is only ever READ: nothing
     there is written, renamed, moved or deleted. Each site team folder that
     has logos in iCloud becomes an exact copy of them (a logo you delete or
     rename in iCloud is removed from the site); a team with nothing in iCloud
     yet keeps its current site images. Before the very first copy, the seven
     site image folders are backed up outside the site.
  1. Finds every .html page in the site that has a line like
       const path = "../../images/triple-a-teams/albuquerque-isotopes/";
     and works out which image folder that page shows.
  2. In each of those folders, renames new images:
       "MiLB ABQ Red hat logo 2015-present.png" -> "Red hat logo 2015-present.png"
       "red hat logo 2015-present.png"          -> "Red hat logo 2015-present.png"
  3. Rewrites the page's  const allFiles = [ ... ];  list so it contains
     exactly the images in the folder (added, renamed and deleted ones).
     Nothing else in the page is touched, and the page is only rewritten
     when the list actually changed. The previous version is saved in
     backups/ first.

Usage:
  python3 logo_page_sync.py            # do it
  python3 logo_page_sync.py --dry-run  # only show what it would change
"""

import os
import re
import shutil
import subprocess
import sys
import errno
import fcntl
import json
import tempfile
import time
from datetime import datetime

SITE_DIR = "/Users/luke/logos-site"
TOOL_DIR = os.path.dirname(os.path.abspath(__file__))   # e.g. /Users/luke/logos-site/tools
BACKUP_DIR = os.path.join(TOOL_DIR, "backups")
LOG_FILE = os.path.join(TOOL_DIR, "logo-sync.log")

IMAGE_EXTENSIONS = {".png"}          # add ".jpg", ".svg" etc. if you ever use them

# ---- iCloud -> site (step 0) ----
ICLOUD_LOGOS = "/Users/luke/Library/Mobile Documents/com~apple~CloudDocs/Sports/Logos"
LEAGUE_FOLDERS = {      # first word of the iCloud file name -> folder in images/
    "MLB": "mlb-teams", "MiLB": "triple-a-teams", "LMB": "lmb-teams", "LIDOM": "lidom-teams",
    "NBA": "nba-teams", "NFL": "nfl-teams", "WBC": "wbc-teams",
}
ICLOUD_SUBFOLDERS = ["MLB", "MiLB", "LMB", "LIDOM", "NBA", "NFL", "WBC"]   # under ICLOUD_LOGOS
SKIP_SOURCE_FOLDERS = {"not on site"}  # folders (any depth, any capitalization) never copied
TEAM_LIST = os.path.join(TOOL_DIR, "logo-teams.txt")
SCALE = 0.70             # each logo on the site is 70% of its original width and height
                         # (scaled down 30%), proportions kept, then compressed. Needs Pillow:
                         #   python3 -m pip install pillow
MAX_SIDE = 3000          # ...but never wider or taller than this (very large originals are scaled
                         # down further to fit). None = no limit
USE_PNGQUANT = True      # extra (slightly lossy) compression, if pngquant is installed
MAX_SOURCE_MEGAPIXELS = 1000   # Pillow refuses images over ~179 megapixels by default (a safety check for
                               # files from the internet); your own logos can be bigger than that
IMAGES_BACKUP_DIR = "/Users/luke/logos-site-images-backup"   # outside the site; made once
MANIFEST = os.path.join(TOOL_DIR, "icloud-import.json")
SETTLE_SECONDS = 10                   # leave files alone until they've stopped changing (still copying)
NOTIFY = True                         # macOS notification when a page is updated

# Team codes stripped from the start of a file name. Covers "MiLB ABQ ",
# "MLB COL ", "MiLB SWB-" etc. (2-5 letters, then a space, dash or underscore).
PREFIX_PATTERNS = [
    re.compile(r"^\s*(?:MiLB|MLB)[\s_-]+[A-Za-z]{2,5}[\s_-]+"),
]

PATH_LINE = re.compile(r"""const\s+path\s*=\s*["']([^"']+)["']""")
ALL_FILES = re.compile(r"(const\s+allFiles\s*=\s*\[)(.*?)(\];)", re.DOTALL)
SKIP_DIRS = {".git", "node_modules", ".venv", "venv"}


def log(msg):
    line = f"[{datetime.now():%Y-%m-%d %H:%M:%S}] {msg}"
    print(line)
    try:
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(line + "\n")
    except OSError:
        pass


def notify(title, text):
    if not NOTIFY or sys.platform != "darwin":
        return
    safe = lambda s: s.replace("\\", "\\\\").replace('"', '\\"')
    subprocess.run(["osascript", "-e", f'display notification "{safe(text)}" with title "{safe(title)}"'],
                   capture_output=True)


def find_pages():
    """{image folder (absolute): [html pages that show it]}"""
    pages = {}
    for root, dirs, files in os.walk(SITE_DIR):
        # Never look inside this script's own folder (its backups are copies of pages)
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS and not d.startswith(".")
                   and os.path.abspath(os.path.join(root, d)) not in (TOOL_DIR, BACKUP_DIR)]
        for name in files:
            if not name.lower().endswith(".html"):
                continue
            page = os.path.join(root, name)
            try:
                text = open(page, encoding="utf-8").read()
            except (OSError, UnicodeDecodeError):
                continue
            m = PATH_LINE.search(text)
            if not m or not ALL_FILES.search(text):
                continue
            folder = os.path.normpath(os.path.join(root, m.group(1)))
            pages.setdefault(folder, []).append(page)
    return pages


def clean_name(name):
    stem, ext = os.path.splitext(name)
    for pattern in PREFIX_PATTERNS:
        stem = pattern.sub("", stem, count=1)
    stem = stem.strip()
    if stem and stem[0].isalpha() and stem[0].islower():
        stem = stem[0].upper() + stem[1:]
    return stem + ext.lower()


def is_settled(path):
    try:
        return time.time() - os.path.getmtime(path) >= SETTLE_SECONDS
    except OSError:
        return False


def images_in(folder):
    if not os.path.isdir(folder):
        return []
    return [n for n in os.listdir(folder)
            if not n.startswith(".") and os.path.splitext(n)[1].lower() in IMAGE_EXTENSIONS
            and os.path.isfile(os.path.join(folder, n))]


def rename_images(folder, dry_run):
    """Renames new files in place. Returns (renamed list, still-copying count)."""
    renamed, waiting = [], 0
    for name in images_in(folder):
        new = clean_name(name)
        if new == name:
            continue
        src, dst = os.path.join(folder, name), os.path.join(folder, new)
        if not is_settled(src):
            waiting += 1
            continue
        case_only = new.lower() == name.lower()
        if os.path.exists(dst) and not case_only:
            log(f"  ! {folder}: not renaming '{name}' — '{new}' already exists")
            continue
        if not dry_run:
            if case_only:   # macOS ignores case in names, so go through a temporary name
                tmp = dst + ".renaming"
                os.rename(src, tmp)
                os.rename(tmp, dst)
            else:
                os.rename(src, dst)
        renamed.append((name, new))
    return renamed, waiting


def js_string(name):
    return '"' + name.replace("\\", "\\\\").replace('"', '\\"') + '"'


def update_page(page, folder, dry_run):
    """Rewrites the allFiles list. Returns (added, removed) or None if unchanged."""
    text = open(page, encoding="utf-8").read()
    m = ALL_FILES.search(text)
    current = re.findall(r'"((?:[^"\\]|\\.)*)"', m.group(2))
    current = [c.replace('\\"', '"').replace("\\\\", "\\") for c in current]
    wanted = sorted(images_in(folder), key=lambda n: n.lower())
    if current == wanted:
        return None
    added = [n for n in wanted if n not in current]
    removed = [n for n in current if n not in wanted]
    if not added and not removed:
        return None   # same files, different order — the page sorts them itself
    body = "\n" + "".join(f"{js_string(n)},\n" for n in wanted)
    new_text = text[:m.start(2)] + body + text[m.end(2):]
    if not dry_run:
        os.makedirs(BACKUP_DIR, exist_ok=True)
        rel = os.path.relpath(page, SITE_DIR).replace(os.sep, "__")
        shutil.copy2(page, os.path.join(BACKUP_DIR, f"{datetime.now():%Y%m%d-%H%M%S}__{rel}"))
        tmp = page + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            f.write(new_text)
        os.replace(tmp, page)
    return added, removed


# ---------------------------------------------------------------------------
# Step 0: iCloud -> site images (reads iCloud only)
# ---------------------------------------------------------------------------

YEARS_FIELD = re.compile(r"^(\d{4})?(-)?(\d{4})?$")


def load_team_list():
    """{(league, code): [(folder, first_year, last_year)]}  ('-' folder = skip)."""
    teams = {}
    with open(TEAM_LIST, encoding="utf-8") as f:
        for line_no, line in enumerate(f, 1):
            line = line.split("#", 1)[0].strip()
            if not line:
                continue
            parts = line.split()
            if len(parts) < 3:
                log(f"  ! logo-teams.txt line {line_no}: needs LEAGUE CODE folder — skipped")
                continue
            league, code, folder = parts[:3]
            lo = hi = None
            if len(parts) > 3:
                m = YEARS_FIELD.match(parts[3])
                if not m or not (m.group(1) or m.group(3)):
                    log(f"  ! logo-teams.txt line {line_no}: can't read years '{parts[3]}' — skipped")
                    continue
                lo, dash, hi = (int(m.group(1)) if m.group(1) else None), m.group(2), \
                               (int(m.group(3)) if m.group(3) else None)
                if not dash:          # a single year: just that year
                    hi = lo
            teams.setdefault((league, code), []).append((folder, lo, hi))
    return teams


def last_year_in(name):
    """The LAST year in a file name; 'present' counts as this year."""
    tokens = re.findall(r"(?<!\d)\d{4}(?!\d)|present", name, re.IGNORECASE)
    if not tokens:
        return None
    t = tokens[-1]
    if t.lower() != "present":
        return int(t)
    # "2027-present" before 2027 still means 2027 on
    before = [int(x) for x in tokens[:-1] if x.lower() != "present"]
    return max([datetime.now().year] + before[-1:])


def pick_folder(lines, year):
    if year is None:
        open_end = [l for l in lines if l[2] is None]
        return (open_end or (lines if len(lines) == 1 else [None]))[0]
    for folder, lo, hi in lines:
        if (lo is None or lo <= year) and (hi is None or year <= hi):
            return (folder, lo, hi)
    return None


def find_tool(name):
    return shutil.which(name) or next((p for p in (f"/opt/homebrew/bin/{name}", f"/usr/local/bin/{name}")
                                       if os.path.exists(p)), None)


def compress_copy(src, dest):
    """Writes a copy of src (read only) to dest at SCALE of its size, compressed."""
    from PIL import Image
    Image.MAX_IMAGE_PIXELS = MAX_SOURCE_MEGAPIXELS * 1_000_000
    os.makedirs(os.path.dirname(dest), exist_ok=True)
    # Work in the system temp folder, so nothing half-finished ever sits in the site
    # folder (where autopush could publish it)
    fd, tmp = tempfile.mkstemp(suffix=".png", prefix="logo-sync-")
    os.close(fd)
    with Image.open(src) as im:
        if im.mode not in ("RGBA", "RGB", "LA", "L", "P"):
            im = im.convert("RGBA")
        if im.mode == "P":
            im = im.convert("RGBA")
        factor = SCALE
        if MAX_SIDE and max(im.size) * factor > MAX_SIDE:
            factor = MAX_SIDE / max(im.size)
        size = (max(1, round(im.width * factor)), max(1, round(im.height * factor)))
        # For a big reduction, shrink by a whole number first (fast, little memory),
        # then finish with the high-quality resize
        step = int(1 / factor)
        if step >= 2:
            im = im.reduce(step)
        small = im.resize(size, Image.LANCZOS)
        small.save(tmp, "PNG", optimize=True)
        # Scaling smooths edges, which can make flat-color logos take more space.
        # If the copy came out bigger than the original, try a 256-color version.
        if os.path.getsize(tmp) > os.path.getsize(src) and not find_tool("pngquant"):
            q = tmp + ".256.png"
            small.convert("RGBA").quantize(256, method=Image.Quantize.FASTOCTREE).save(q, "PNG", optimize=True)
            if os.path.getsize(q) < os.path.getsize(tmp):
                os.replace(q, tmp)
            else:
                os.remove(q)
    pngquant = find_tool("pngquant") if USE_PNGQUANT else None
    if pngquant:
        smaller = tmp + ".q.png"
        r = subprocess.run([pngquant, "--quality=70-95", "--skip-if-larger", "--strip",
                            "--force", "--output", smaller, tmp], capture_output=True)
        if r.returncode == 0 and os.path.exists(smaller):
            os.replace(smaller, tmp)
        elif os.path.exists(smaller):
            os.remove(smaller)
    shutil.move(tmp, dest)


def have_pillow():
    try:
        import PIL  # noqa: F401
        return True
    except ImportError:
        return False


def plan_icloud_import():
    """Works out where every iCloud logo belongs. Reads only."""
    teams = load_team_list()
    desired, problems = {}, []      # dest path -> src path
    unmatched, not_downloaded, unsettled = {}, 0, set()
    keep = set()                    # site copies of logos that are only placeholders in iCloud right now
    for sub in ICLOUD_SUBFOLDERS:
        top = os.path.join(ICLOUD_LOGOS, sub)
        if not os.path.isdir(top):
            problems.append(f"iCloud folder not found: {top}")
            continue
        for root, dirs, files in os.walk(top):
            dirs[:] = [d for d in dirs if d.strip().lower() not in SKIP_SOURCE_FOLDERS and not d.startswith(".")]
            for name in files:
                placeholder = name.startswith(".") and name.endswith(".icloud")
                if placeholder:
                    # Only a placeholder on this Mac (".MLB CHC Hat logo.png.icloud"): it can't be
                    # copied, but its site copy must be kept, not removed
                    not_downloaded += 1
                    name = name[1:-len(".icloud")]
                stem, ext = os.path.splitext(name)
                if (name.startswith(".") and not placeholder) or ext.lower() not in IMAGE_EXTENSIONS:
                    continue
                src = os.path.join(root, name)
                parts = stem.split(None, 2)
                if len(parts) < 3:
                    problems.append(f"no 'LEAGUE CODE name' in: {os.path.relpath(src, ICLOUD_LOGOS)}")
                    continue
                league, code, rest = parts
                if league not in LEAGUE_FOLDERS:
                    problems.append(f"unknown league '{league}': {os.path.relpath(src, ICLOUD_LOGOS)}")
                    continue
                lines = teams.get((league, code))
                if not lines and teams.get((league, "*")):
                    # A league-wide logo (no team code): only the league word comes off,
                    # so "MLB Father's Day hat texture" keeps "Father's"
                    lines = teams[(league, "*")]
                    rest = f"{code} {rest}"
                if not lines:
                    unmatched.setdefault(f"{league} {code}", []).append(name)
                    continue
                chosen = pick_folder(lines, last_year_in(rest))
                if chosen is None:
                    problems.append(f"no {league} {code} line in logo-teams.txt covers the year of: {name}")
                    continue
                if chosen[0] == "-":
                    continue
                dest = os.path.join(SITE_DIR, "images", LEAGUE_FOLDERS[league], chosen[0], clean_name(rest + ext))
                key = dest.lower()       # macOS treats names that differ only in capitals as the same file
                if placeholder:
                    keep.add(key)
                    continue
                if key in desired:
                    problems.append(f"two iCloud files would both become {os.path.relpath(dest, SITE_DIR)}: "
                                    f"'{os.path.basename(desired[key][1])}' and '{name}' — keeping the first")
                    continue
                desired[key] = (dest, src)
                if not is_settled(src):
                    unsettled.add(key)
    return desired, problems, unmatched, not_downloaded, unsettled, keep


def backup_site_images_once(dry_run):
    marker = os.path.join(IMAGES_BACKUP_DIR, ".done")
    if dry_run or os.path.exists(marker):
        return
    for folder in sorted(set(LEAGUE_FOLDERS.values())):
        src = os.path.join(SITE_DIR, "images", folder)
        if os.path.isdir(src):
            shutil.copytree(src, os.path.join(IMAGES_BACKUP_DIR, folder), dirs_exist_ok=True)
    open(marker, "w").close()
    log(f"Backed up the site's current images to {IMAGES_BACKUP_DIR} (one time only)")


def icloud_import(dry_run):
    """Returns a set of site folders that changed."""
    if not os.path.exists(TEAM_LIST):
        log(f"! {TEAM_LIST} not found — skipping the iCloud copy")
        return set()
    if not os.path.isdir(ICLOUD_LOGOS):
        log(f"! Can't read {ICLOUD_LOGOS} — skipping the iCloud copy (see the permissions note)")
        return set()
    if not have_pillow():
        log("! Pillow isn't installed, so logos can't be scaled — skipping the iCloud copy. "
            "Install it with:  python3 -m pip install pillow")
        return set()
    desired, problems, unmatched, not_downloaded, unsettled, keep = plan_icloud_import()
    try:
        manifest = json.load(open(MANIFEST, encoding="utf-8"))
    except (OSError, ValueError):
        manifest = {}
    # Changing any of these redoes every logo on the next run
    settings = f"scale{SCALE}|max{MAX_SIDE}|{USE_PNGQUANT and bool(find_tool('pngquant'))}"

    to_copy, upgraded = [], False
    for key, (dest, src) in desired.items():
        if key in unsettled:
            continue
        st = os.stat(src)
        sig = [src, st.st_mtime, st.st_size, settings]
        recorded = manifest.get(dest) or []
        if len(recorded) == 4 and recorded == sig and os.path.exists(dest):
            # Copied by an older version of this script: remember the copy as it is now
            dst = os.stat(dest)
            recorded = manifest[dest] = sig + [dst.st_size, int(dst.st_mtime)]
            upgraded = True
        # Redo it if the iCloud logo or the settings changed, the copy is missing,
        # or something else has since replaced the copy (e.g. an older file put back)
        replaced = False
        if os.path.exists(dest) and len(recorded) == 6:
            dst = os.stat(dest)
            replaced = [dst.st_size, int(dst.st_mtime)] != recorded[4:6]
        if recorded[:4] == sig and recorded[-2:] == ["failed", "image"]:
            continue   # the image itself couldn't be read, and the file hasn't changed since — don't retry every run
        if recorded[:4] != sig or not os.path.exists(dest) or replaced:
            to_copy.append((dest, src, sig))

    # Folders that have at least one iCloud logo are kept as exact copies;
    # folders with none are left alone (team not done yet).
    managed = {os.path.dirname(dest) for dest, _ in desired.values()}
    wanted = {dest.lower() for dest, _ in desired.values()} | keep
    to_remove = []
    for folder in managed:
        if os.path.isdir(folder):
            for n in images_in(folder):
                path = os.path.join(folder, n)
                if path.lower() not in wanted:
                    to_remove.append(path)

    prefix = "(dry run) " if dry_run else ""
    if to_copy or to_remove:
        backup_site_images_once(dry_run)
    changed, failed_any = set(), False
    for i, (dest, src, sig) in enumerate(sorted(to_copy), 1):
        if not dry_run:
            try:
                compress_copy(src, dest)
            except Exception as e:
                if isinstance(e, OSError) and e.errno in (errno.EDEADLK, errno.EAGAIN, errno.EBUSY,
                                                          errno.ETIMEDOUT, errno.EINTR, errno.EPERM):
                    # iCloud hasn't finished bringing the file back (e.g. right after a rename):
                    # ask it to download, and try again on the next run
                    if find_tool("brctl"):
                        subprocess.run([find_tool("brctl"), "download", src], capture_output=True)
                    log(f"  {os.path.basename(src)} is still downloading from iCloud — will copy it on the next run")
                    manifest.pop(dest, None)
                else:
                    log(f"  ! couldn't copy {os.path.basename(src)}: {e} — will try again when the file changes")
                    manifest[dest] = sig + ["failed", "image"]
                failed_any = True
                continue
            dst = os.stat(dest)
            manifest[dest] = sig + [dst.st_size, int(dst.st_mtime)]
        changed.add(os.path.dirname(dest))
        if len(to_copy) <= 40:
            log(f"{prefix}iCloud -> {os.path.relpath(dest, SITE_DIR)}")
    for path in sorted(to_remove):
        if not dry_run:
            os.remove(path)
            manifest.pop(path, None)
        changed.add(os.path.dirname(path))
        log(f"{prefix}Removed (not in iCloud): {os.path.relpath(path, SITE_DIR)}")
    if len(to_copy) > 40:   # a big first run: one line per folder instead of per logo
        per = {}
        for dest, _, _ in to_copy:
            per[os.path.relpath(os.path.dirname(dest), SITE_DIR)] = per.get(os.path.relpath(os.path.dirname(dest), SITE_DIR), 0) + 1
        for folder, n in sorted(per.items()):
            log(f"{prefix}iCloud -> {folder}: {n} logo(s)")
    if not dry_run and (to_copy or to_remove or upgraded or failed_any):
        live = {d for d, _ in desired.values()}
        manifest = {k: v for k, v in manifest.items() if k in live or k.lower() in keep}
        tmp = MANIFEST + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(manifest, f, indent=0)
        os.replace(tmp, MANIFEST)

    # Things to look at (logged only when something changed, or on a dry run, to keep the log short)
    if dry_run or changed:
        for code, names in sorted(unmatched.items()):
            log(f"  ! no line for '{code}' in logo-teams.txt ({len(names)} file(s), e.g. '{names[0]}') — not copied")
        for p in problems:
            log(f"  ! {p}")
        if not_downloaded:
            log(f"  {not_downloaded} iCloud logo(s) aren't downloaded to this Mac right now — their site copies "
                f"are left as they are, and they're copied again once you open or download them.")
        if dry_run:
            known = {os.path.join(SITE_DIR, "images", LEAGUE_FOLDERS[l], f)
                     for (l, c), lines in load_team_list().items() if l in LEAGUE_FOLDERS
                     for f, _, _ in lines if f != "-"}
            waiting = sorted(os.path.relpath(f, SITE_DIR) for f in known - managed)
            if waiting:
                log(f"  Left as they are (no iCloud logos for them yet): {len(waiting)} folder(s), e.g. "
                    + ", ".join(waiting[:5]))
            log(f"(dry run) {len(to_copy)} logo(s) would be copied, {len(to_remove)} removed.")
    if changed and not dry_run:
        notify("Logos copied from iCloud", f"{len(to_copy)} copied, {len(to_remove)} removed")
    return changed


def main():
    dry_run = "--dry-run" in sys.argv
    # Only one copy runs at a time (the 30-second schedule vs. a run you started yourself)
    lock = open(os.path.join(TOOL_DIR, ".logo-sync.lock"), "w")
    try:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except OSError:
        print("Another logo sync run is still going — leaving it to finish.")
        return 0
    if not os.path.isdir(SITE_DIR):
        log(f"! Site folder not found: {SITE_DIR}")
        return 1
    icloud_import(dry_run)
    for folder, pages in sorted(find_pages().items()):
        if not os.path.isdir(folder):
            # A cleared/removed team folder: its page should list no logos
            for page in pages:
                result = update_page(page, folder, dry_run)
                if result:
                    log(f"{'(dry run) ' if dry_run else ''}Updated {os.path.relpath(page, SITE_DIR)}: "
                        f"folder is empty or missing — {len(result[1])} logo(s) taken off the page")
            continue
        renamed, waiting = rename_images(folder, dry_run)
        for old, new in renamed:
            log(f"{'(dry run) ' if dry_run else ''}Renamed in {os.path.basename(folder)}: '{old}' -> '{new}'")
        if waiting and dry_run:
            log(f"  {os.path.basename(folder)}: {waiting} file(s) still copying — will rename next run")
        if waiting:
            continue   # update the page once everything has its final name
        for page in pages:
            result = update_page(page, folder, dry_run)
            if not result:
                continue
            added, removed = result
            team = os.path.splitext(os.path.basename(page))[0]
            summary = ", ".join(filter(None, [f"{len(added)} added" if added else "",
                                              f"{len(removed)} removed" if removed else ""]))
            log(f"{'(dry run) ' if dry_run else ''}Updated {os.path.relpath(page, SITE_DIR)}: {summary}")
            for n in added:
                log(f"    + {n}")
                if "'" in n:
                    log("      ! this name has an apostrophe, which breaks the click-to-enlarge on the page")
            for n in removed:
                log(f"    - {n}")
            if not dry_run:
                notify("Logo page updated", f"{team}: {summary}")


if __name__ == "__main__":
    sys.exit(main())
