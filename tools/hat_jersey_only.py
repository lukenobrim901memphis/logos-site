#!/usr/bin/env python3
"""
Keep the Hat Logos and Jersey Logos sections for actual hat and jersey logos.
Any file whose name has one of NOT_LOGOS ("pattern", "texture", "gradient")
skips those two sections and lands in Other at the bottom instead:

  "Red to black hat gradient 2016-2019.png"   -> Other   (was Hat Logos)
  "City Connect jersey texture 2025.png"      -> Other   (was Jersey Logos)
  "Red jersey logo 2016-2019.png"             -> Jersey Logos, as before

Works on every team page (MLB, Triple-A, NBA, ...). Safe to run more than
once. Every page it changes is backed up to tools/backups/ first.

Usage:
  python3 hat_jersey_only.py --dry-run
  python3 hat_jersey_only.py
"""

import os
import re
import shutil
import sys
from datetime import datetime

SITE_DIR = "/Users/luke/logos-site"
TOOL_DIR = os.path.dirname(os.path.abspath(__file__))
BACKUP_DIR = os.path.join(TOOL_DIR, "backups")
NOT_LOGOS = ["pattern", "texture", "gradient"]     # add words here if you need more

RULE = re.compile(r'lowerName\.includes\("(hat|jersey)"\)(?!\s*&&)')
WORDS = "|".join(re.escape(w) for w in NOT_LOGOS)


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
            if "const allFiles" not in text:
                continue
            new, n = RULE.subn(lambda m: f'(lowerName.includes("{m.group(1)}") && !/{WORDS}/.test(lowerName))', text)
            if not n:
                continue
            done += 1
            rel = os.path.relpath(page, SITE_DIR)
            print(f"{'(dry run) ' if dry_run else ''}{rel}: hat/jersey sections now skip {', '.join(NOT_LOGOS)}")
            if not dry_run:
                os.makedirs(BACKUP_DIR, exist_ok=True)
                shutil.copy2(page, os.path.join(BACKUP_DIR, f"{datetime.now():%Y%m%d-%H%M%S}__{rel.replace(os.sep, '__')}"))
                with open(page, "w", encoding="utf-8") as f:
                    f.write(new)
    print(f"\n{'Would change' if dry_run else 'Changed'} {done} page(s).")


if __name__ == "__main__":
    main()
