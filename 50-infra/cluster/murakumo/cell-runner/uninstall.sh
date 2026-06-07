#!/usr/bin/env bash
# uninstall.sh — remove kotodama-cell-runner LaunchAgent from this Mac mini.
# Per ADR-2605192415.
#
# Usage:
#   ./uninstall.sh           # interactive: prints log paths before exit
#   ./uninstall.sh --quiet   # silent removal

set -euo pipefail

QUIET=false
[[ "${1:-}" == "--quiet" ]] && QUIET=true

SERVICE_LABEL="com.etzhayyim.kotodama-cell-runner"
INSTALLED_PLIST="$HOME/Library/LaunchAgents/$SERVICE_LABEL.plist"
LOG_DIR="$HOME/.etzhayyim/log"

step() { $QUIET || printf "\033[34m==>\033[0m %s\n" "$*"; }
ok()   { $QUIET || printf "\033[32m✓\033[0m  %s\n" "$*"; }

if [[ ! -f "$INSTALLED_PLIST" ]]; then
  $QUIET || echo "$SERVICE_LABEL is not installed at $INSTALLED_PLIST"
  exit 0
fi

step "unloading $SERVICE_LABEL"
launchctl unload "$INSTALLED_PLIST" 2>/dev/null || true
ok "unloaded"

step "removing plist $INSTALLED_PLIST"
rm -f "$INSTALLED_PLIST"
ok "removed"

$QUIET || {
  echo ""
  echo "Logs retained at:"
  echo "  $LOG_DIR/kotodama-cell-runner.stdout.log"
  echo "  $LOG_DIR/kotodama-cell-runner.stderr.log"
  echo ""
  echo "To wipe logs:"
  echo "  rm -rf $LOG_DIR"
}
