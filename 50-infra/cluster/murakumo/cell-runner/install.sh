#!/usr/bin/env bash
# install.sh — install kotodama-cell-runner as a launchd LaunchAgent on a
#             Murakumo Mac mini.
#
# Per ADR-2605192415 §7.1 (Religious-Corp Daemon Architecture — Tier 1
# launchd 常駐), each Mac mini in the etzhayyim Murakumo fleet runs the
# kotodama-cell-runner CLI which reads 50-infra/murakumo/fleet.toml to
# decide which cells to host. The runner is a thin supervisor — actual
# cell.py code lives under 40-engine/kotoba/crates/kotoba-kotodama/cells/<cell_name>/.
#
# Run ONCE per Mac mini, then the runner stays alive across reboots via
# launchd's RunAtLoad + KeepAlive.
#
# Prereqs:
#   - macOS 14+
#   - homebrew or system `uv` installed (`brew install uv` if not yet)
#   - kotodama venv ready (`uv sync` in 40-engine/kotoba/crates/kotoba-kotodama/py)
#   - 12-tribe SSH access set up (this script runs locally on the mac mini)
#
# Usage:
#   ./install.sh --node <NODE_NAME>
#
#   Example:
#     ./install.sh --node naphtali
#     ./install.sh --node simeon --repo-path /Users/simeon/etzhayyim-root
#
# Status / logs / stop (after install):
#   launchctl list | grep kotodama-cell-runner
#   tail -f ~/.etzhayyim/log/kotodama-cell-runner.{stdout,stderr}.log
#   ./uninstall.sh

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PLIST_SRC="$SCRIPT_DIR/com.etzhayyim.kotodama-cell-runner.plist"

NODE_NAME=""
REPO_PATH=""

while [[ $# -gt 0 ]]; do
  case "$1" in
    --node)
      NODE_NAME="$2"
      shift 2
      ;;
    --repo-path)
      REPO_PATH="$2"
      shift 2
      ;;
    -h|--help)
      sed -n '2,28p' "$0"
      exit 0
      ;;
    *)
      echo "Unknown flag: $1" >&2
      exit 2
      ;;
  esac
done

# --- Resolve parameters -----------------------------------------------------

if [[ -z "$NODE_NAME" ]]; then
  echo "ERROR: --node <NODE_NAME> is required" >&2
  echo "       expected one of: naphtali simeon judah zebulun levi joseph issachar dan benjamin asher" >&2
  exit 2
fi

# Validate tribe name against fleet.toml
case "$NODE_NAME" in
  naphtali|simeon|judah|zebulun|levi|joseph|issachar|dan|benjamin|asher)
    ;;
  *)
    echo "ERROR: $NODE_NAME is not a known Murakumo tribe" >&2
    echo "       expected one of: naphtali simeon judah zebulun levi joseph issachar dan benjamin asher" >&2
    exit 2
    ;;
esac

if [[ -z "$REPO_PATH" ]]; then
  # Default: 4 levels up from this script (50-infra/cluster/murakumo/cell-runner/ -> repo root)
  REPO_PATH="$(cd "$SCRIPT_DIR/../../../.." && pwd)"
fi

UV_PATH="$(command -v uv 2>/dev/null || true)"
if [[ -z "$UV_PATH" ]]; then
  echo "ERROR: 'uv' binary not found in PATH" >&2
  echo "       install with:  brew install uv" >&2
  exit 2
fi

USERNAME="$(id -un)"
LAUNCHAGENT_DIR="$HOME/Library/LaunchAgents"
INSTALLED_PLIST="$LAUNCHAGENT_DIR/com.etzhayyim.kotodama-cell-runner.plist"
LOG_DIR="$HOME/.etzhayyim/log"
SERVICE_LABEL="com.etzhayyim.kotodama-cell-runner"

# --- Pre-flight health check ------------------------------------------------

step() { printf "\033[34m==>\033[0m %s\n" "$*"; }
ok()   { printf "\033[32m✓\033[0m  %s\n" "$*"; }

step "pre-flight check"
echo "  node:       $NODE_NAME"
echo "  repo path:  $REPO_PATH"
echo "  uv:         $UV_PATH"
echo "  user:       $USERNAME"
echo "  plist src:  $PLIST_SRC"
echo "  installed:  $INSTALLED_PLIST"
echo "  log dir:    $LOG_DIR"

step "syncing kotoba submodule"
(cd "$REPO_PATH" && git submodule update --init --recursive 40-engine/kotoba)
ok "kotoba submodule synced"

if [[ ! -f "$REPO_PATH/40-engine/kotoba/crates/kotoba-kotodama/py/pyproject.toml" ]]; then
  echo "ERROR: kotodama project not found at $REPO_PATH/40-engine/kotoba/crates/kotoba-kotodama/py" >&2
  echo "       pass --repo-path <PATH> if your checkout is elsewhere" >&2
  exit 2
fi

step "ensuring kotodama venv is synced (uv sync)"
(cd "$REPO_PATH/40-engine/kotoba/crates/kotoba-kotodama/py" && "$UV_PATH" sync --quiet)
ok "kotodama venv ready"

step "running --health for $NODE_NAME (config readback)"
(cd "$REPO_PATH/40-engine/kotoba/crates/kotoba-kotodama/py" && "$UV_PATH" run kotoba-kotodama-cell-runner --node "$NODE_NAME" --health)
ok "health probe ok"

# --- Materialise plist -----------------------------------------------------

step "preparing log directory"
mkdir -p "$LOG_DIR"
ok "log dir ready: $LOG_DIR"

step "preparing LaunchAgents directory"
mkdir -p "$LAUNCHAGENT_DIR"

step "materialising plist with placeholders substituted"
# Use bash parameter expansion for safe substitution (no shell escape issues).
TMP_PLIST="$(mktemp -t etzhayyim-cell-runner.XXXXXX.plist)"
trap 'rm -f "$TMP_PLIST"' EXIT
{
  while IFS= read -r line; do
    line="${line//@@NODE_NAME@@/$NODE_NAME}"
    line="${line//@@USERNAME@@/$USERNAME}"
    line="${line//@@REPO_PATH@@/$REPO_PATH}"
    line="${line//@@UV_PATH@@/$UV_PATH}"
    line="${line//@@LOG_DIR@@/$LOG_DIR}"
    line="${line//@@PYTHONPATH@@/}"
    printf '%s\n' "$line"
  done
} < "$PLIST_SRC" > "$TMP_PLIST"

# Sanity: ensure no @@…@@ markers remain (catches typos / unset placeholders).
if grep -q "@@" "$TMP_PLIST"; then
  echo "ERROR: unsubstituted placeholders remain in plist:" >&2
  grep -n "@@" "$TMP_PLIST" >&2
  exit 3
fi

# --- Install + load --------------------------------------------------------

step "installing plist to $INSTALLED_PLIST"
# Unload first if already loaded — idempotent re-install.
if launchctl list "$SERVICE_LABEL" >/dev/null 2>&1; then
  launchctl unload "$INSTALLED_PLIST" 2>/dev/null || true
fi

install -m 0644 "$TMP_PLIST" "$INSTALLED_PLIST"
ok "plist installed"

step "loading LaunchAgent"
launchctl load "$INSTALLED_PLIST"
ok "loaded"

# --- Verify -----------------------------------------------------------------

sleep 2
step "verifying service is running"
if launchctl list "$SERVICE_LABEL" | grep -q PID; then
  ok "$SERVICE_LABEL is running"
else
  echo "WARN: service not yet showing PID — check logs:" >&2
  echo "  tail -f $LOG_DIR/kotodama-cell-runner.stderr.log" >&2
fi

echo ""
echo "Install complete."
echo ""
echo "Useful commands:"
echo "  status:    launchctl list | grep kotodama-cell-runner"
echo "  stdout:    tail -f $LOG_DIR/kotodama-cell-runner.stdout.log"
echo "  stderr:    tail -f $LOG_DIR/kotodama-cell-runner.stderr.log"
echo "  reload:    launchctl unload $INSTALLED_PLIST && launchctl load $INSTALLED_PLIST"
echo "  uninstall: $SCRIPT_DIR/uninstall.sh"
