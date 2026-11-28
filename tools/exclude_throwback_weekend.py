#!/usr/bin/env python3
"""
Keep "Throwback weekend" logos out of the Throwback section on every MLB and
Triple-A page. They go where they did before (Hat Logos, Jersey Logos, ...).

Safe to run more than once. Every page it changes is backed up to
tools/backups/ first.

Usage:
  python3 exclude_throwback_weekend.py --dry-run
  python3 exclude_throwback_weekend.py
"""

import os
import re
import shutil
import sys
from datetime import datetime

SITE_DIR = "/Users/luke/logos-site"
TOOL_DIR = os.path.dirname(os.path.abspath(__file__))
BACKUP_DIR = os.path.join(TOOL_DIR, "backups")
EXCLUDE = "throwback weekend"

RULE = re.compile(r'lowerName\.includes\("throwback"\)(?!\s*&&)')


def main():
    dry_run = "--dry-run" in sys.argv
    done = 0
    for root, dirs, files in os.walk(SITE_DIR):
        dirs[:] = [d for d in dirs if not d.startswith(".") and os.path.join(root, d) != TOOL_DIR]
        for name in sorted(files):
            if not name.endswith(".html"):
                continue
            page = os.path.join(root, name)
            text = open(page, encoding="utf-8").read()
            new, n = RULE.subn(f'(lowerName.includes("throwback") && !lowerName.includes("{EXCLUDE}"))', text)
            if not n:
                continue
            done += 1
            rel = os.path.relpath(page, SITE_DIR)
            print(f"{'(dry run) ' if dry_run else ''}{rel}: throwback weekend left out of Throwback")
            if not dry_run:
                os.makedirs(BACKUP_DIR, exist_ok=True)
                shutil.copy2(page, os.path.join(BACKUP_DIR, f"{datetime.now():%Y%m%d-%H%M%S}__{rel.replace(os.sep, '__')}"))
                with open(page, "w", encoding="utf-8") as f:
                    f.write(new)
    print(f"\n{'Would change' if dry_run else 'Changed'} {done} page(s).")


if __name__ == "__main__":
    main()
