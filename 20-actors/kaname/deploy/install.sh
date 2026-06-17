#!/bin/bash
# kaname 要 — install/uninstall the production heartbeat LaunchAgent (ADR-2606172100; deploy 実運用).
#   install.sh install   → render the plist from the template (repo root + bb resolved), load it, kickstart once
#   install.sh uninstall → bootout + remove the plist
#   install.sh status    → print the agent state + tail the log
# macOS launchd (per-user LaunchAgent). The repo root is resolved from this script's location, so a
# post-merge re-install repoints automatically. NOTE: when run from a temporary git worktree the path
# is ephemeral — re-run install from the merged checkout once kaname lands on main.
set -uo pipefail

LABEL="com.etzhayyim.kaname.heartbeat"
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO="$(cd "$HERE/../../.." && pwd)"           # 20-actors/kaname/deploy → repo root
BB="$(command -v bb || echo /opt/homebrew/bin/bb)"
PLIST="$HOME/Library/LaunchAgents/$LABEL.plist"
UID_NUM="$(id -u)"

cmd="${1:-status}"
case "$cmd" in
  install)
    mkdir -p "$HOME/Library/LaunchAgents" "$HOME/Library/Logs"
    sed -e "s#@REPO@#$REPO#g" -e "s#@BB@#$BB#g" -e "s#@HOME@#$HOME#g" \
        "$HERE/com.etzhayyim.kaname.heartbeat.plist.template" > "$PLIST"
    chmod +x "$HERE/run-heartbeat.sh"
    launchctl bootout "gui/$UID_NUM/$LABEL" 2>/dev/null || true
    launchctl bootstrap "gui/$UID_NUM" "$PLIST"
    echo "installed + loaded: $PLIST (repo=$REPO bb=$BB)"
    echo "kickstarting one beat…"
    launchctl kickstart -k "gui/$UID_NUM/$LABEL"
    sleep 6
    tail -n 4 "$HOME/Library/Logs/kaname-heartbeat.log" 2>/dev/null || echo "(log not yet written)"
    ;;
  uninstall)
    launchctl bootout "gui/$UID_NUM/$LABEL" 2>/dev/null || true
    rm -f "$PLIST"
    echo "uninstalled: $LABEL"
    ;;
  status)
    launchctl print "gui/$UID_NUM/$LABEL" 2>/dev/null | grep -E 'state|program|last exit|runs' | head || echo "(not loaded)"
    echo "--- last log ---"
    tail -n 6 "$HOME/Library/Logs/kaname-heartbeat.log" 2>/dev/null || echo "(no log)"
    ;;
  *) echo "usage: install.sh [install|uninstall|status]"; exit 2 ;;
esac
