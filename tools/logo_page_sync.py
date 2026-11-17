#!/usr/bin/env python3
"""
Logo Page Sync
--------------
Keeps each team page on your logos site in step with that team's image
folder, so you never have to copy file names into the page by hand.

Every run (launchd runs it every 30 seconds; you can also run it yourself):
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
import time
from datetime import datetime

SITE_DIR = "/Users/luke/logos-site"
TOOL_DIR = os.path.dirname(os.path.abspath(__file__))   # e.g. /Users/luke/logos-site/tools
BACKUP_DIR = os.path.join(TOOL_DIR, "backups")
LOG_FILE = os.path.join(TOOL_DIR, "logo-sync.log")

IMAGE_EXTENSIONS = {".png"}          # add ".jpg", ".svg" etc. if you ever use them
SETTLE_SECONDS = 10                   # leave files alone until they've stopped changing (still copying)
NOTIFY = True                         # macOS notification when a page is updated

# Team codes stripped from the start of a file name. Covers "MiLB ABQ ",
# "MLB COL ", "MiLB SWB-" etc. (2-5 letters, then a space, dash or underscore).
PREFIX_PATTERNS = [
    re.compile(r"^\s*(?:MiLB|MLB|LMB|NFL|NBA|WBC|LIDOM)[\s_-]+[A-Za-z]{2,5}[\s_-]+"),
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


def main():
    dry_run = "--dry-run" in sys.argv
    if not os.path.isdir(SITE_DIR):
        log(f"! Site folder not found: {SITE_DIR}")
        return 1
    for folder, pages in sorted(find_pages().items()):
        if not os.path.isdir(folder):
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
