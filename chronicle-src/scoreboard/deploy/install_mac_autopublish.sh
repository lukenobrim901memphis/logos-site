#!/bin/bash
# One-time setup. After this, nothing needs Terminal:
#   • Scoreboard app always running  -> http://localhost:5002/admin
#   • MLB app always running         -> http://localhost:5001/admin
#   • Auto-publish: a few seconds after any change, and nightly at 12:05 a.m.
#   • Desktop shortcuts: "Scoreboard Admin" and "MLB Admin"
# Everything starts at login and restarts itself if it ever stops.
#
#   bash deploy/install_mac_autopublish.sh          # install / reinstall
#   bash deploy/install_mac_autopublish.sh remove   # turn it all off
#
# Logs: ~/Library/Logs/chronicle-*.log

AGENTS="$HOME/Library/LaunchAgents"
LOGS="$HOME/Library/Logs"
PUB="com.logos-site.chronicle-autopublish"
SB_APP="com.logos-site.chronicle-scoreboard-app"
MLB_APP="com.logos-site.chronicle-mlb-app"
OLD="com.logos-site.chronicle-publish"            # earlier midnight-only job

unload() { launchctl unload "$AGENTS/$1.plist" 2>/dev/null; rm -f "$AGENTS/$1.plist"; }

if [ "$1" = "remove" ]; then
  for a in "$PUB" "$SB_APP" "$MLB_APP" "$OLD"; do unload "$a"; done
  rm -f "$HOME/Desktop/Scoreboard Admin.webloc" "$HOME/Desktop/MLB Admin.webloc"
  echo "Turned off: auto-publishing and both background apps."; exit 0
fi

DIR="$(cd "$(dirname "$0")/.." && pwd)"          # chronicle-src/scoreboard
SITE="$(cd "$DIR/../.." && pwd)"                 # logos-site
MLB_DIR="$SITE/chronicle-src/mlb"
PY="$(command -v python3)"
[ -z "$PY" ] && { echo "python3 not found"; exit 1; }
"$PY" -c "import flask" 2>/dev/null || { echo "Flask isn't installed for $PY. Run: $PY -m pip install flask tzdata"; exit 1; }
mkdir -p "$AGENTS" "$LOGS"

[ -f "$AGENTS/$OLD.plist" ] && { unload "$OLD"; echo "Removed the old midnight-only job."; }

# write_agent LABEL WORKDIR LOGFILE ARGS...
write_agent() {
  local label="$1" dir="$2" log="$3"; shift 3
  local args=""
  for a in "$@"; do args="$args<string>$a</string>"; done
  cat > "$AGENTS/$label.plist" <<PL
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0"><dict>
  <key>Label</key><string>$label</string>
  <key>ProgramArguments</key><array>$args</array>
  <key>WorkingDirectory</key><string>$dir</string>
  <key>RunAtLoad</key><true/>
  <key>KeepAlive</key><true/>
  <key>ThrottleInterval</key><integer>30</integer>
  <key>StandardOutPath</key><string>$log</string>
  <key>StandardErrorPath</key><string>$log</string>
  <key>EnvironmentVariables</key><dict><key>PATH</key><string>/usr/local/bin:/opt/homebrew/bin:/usr/bin:/bin</string></dict>
</dict></plist>
PL
  launchctl unload "$AGENTS/$label.plist" 2>/dev/null
  launchctl load "$AGENTS/$label.plist"
}

webloc() {   # Desktop shortcut that opens a URL in the browser
  cat > "$HOME/Desktop/$1.webloc" <<WL
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0"><dict><key>URL</key><string>$2</string></dict></plist>
WL
}

# 1. Scoreboard app (admin at :5002)
write_agent "$SB_APP" "$DIR" "$LOGS/chronicle-scoreboard-app.log" "$PY" "-u" "$DIR/app.py"
webloc "Scoreboard Admin" "http://localhost:5002/admin"
echo "Scoreboard app: always on  ->  http://localhost:5002/admin"

# 2. MLB app (admin at :5001)
if [ -f "$MLB_DIR/app.py" ]; then
  write_agent "$MLB_APP" "$MLB_DIR" "$LOGS/chronicle-mlb-app.log" "$PY" "-u" "$MLB_DIR/app.py"
  webloc "MLB Admin" "http://localhost:5001/admin"
  echo "MLB app:        always on  ->  http://localhost:5001/admin"
else
  echo "MLB app not found at $MLB_DIR — skipped (move it there and run this again)."
fi

# 3. Auto-publish (on change + nightly)
PUSH=""
if [ -d "$SITE/.git" ]; then PUSH="--push"; echo "logos-site is a git repo: each publish also commits and pushes."; fi
if [ -n "$PUSH" ]; then
  write_agent "$PUB" "$DIR" "$LOGS/chronicle-publish.log" "$PY" "-u" "$DIR/tools/watch.py" "$PUSH"
else
  write_agent "$PUB" "$DIR" "$LOGS/chronicle-publish.log" "$PY" "-u" "$DIR/tools/watch.py"
fi
echo "Auto-publish:   on (after any change, and nightly at 12:05 a.m.)"
echo
echo "Done. Double-click 'Scoreboard Admin' or 'MLB Admin' on your Desktop any time."
