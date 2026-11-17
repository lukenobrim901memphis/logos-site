#!/bin/bash
# Mac option: publish every night at 12:05 a.m. with launchd.
# The Mac must be on (if it's asleep, the job runs when it wakes).
#
#   bash deploy/install_mac_schedule.sh          # install
#   bash deploy/install_mac_schedule.sh remove   # uninstall
#
# Log: ~/Library/Logs/chronicle-publish.log

LABEL="com.logos-site.chronicle-publish"
PLIST="$HOME/Library/LaunchAgents/$LABEL.plist"

if [ "$1" = "remove" ]; then
  launchctl unload "$PLIST" 2>/dev/null; rm -f "$PLIST"; echo "Removed."; exit 0
fi

DIR="$(cd "$(dirname "$0")/.." && pwd)"
PY="$(command -v python3)"
if [ -z "$PY" ]; then echo "python3 not found"; exit 1; fi

mkdir -p "$HOME/Library/LaunchAgents"
cat > "$PLIST" <<PL
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0"><dict>
  <key>Label</key><string>$LABEL</string>
  <key>ProgramArguments</key>
  <array><string>$PY</string><string>$DIR/tools/publish.py</string><string>--push</string></array>
  <key>WorkingDirectory</key><string>$DIR</string>
  <key>StartCalendarInterval</key><dict><key>Hour</key><integer>0</integer><key>Minute</key><integer>5</integer></dict>
  <key>StandardOutPath</key><string>$HOME/Library/Logs/chronicle-publish.log</string>
  <key>StandardErrorPath</key><string>$HOME/Library/Logs/chronicle-publish.log</string>
  <key>EnvironmentVariables</key><dict><key>PATH</key><string>/usr/local/bin:/opt/homebrew/bin:/usr/bin:/bin</string></dict>
</dict></plist>
PL
launchctl unload "$PLIST" 2>/dev/null
launchctl load "$PLIST"
echo "Installed: publishes nightly at 12:05 a.m. using $PY"
echo "Test it now with:  launchctl start $LABEL   (then check ~/Library/Logs/chronicle-publish.log)"
