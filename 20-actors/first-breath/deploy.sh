#!/usr/bin/env bash
# deploy.sh — install first-breath cell on a mini via SSH (cron @60s heartbeat).
#
# Idempotent: re-running updates the script + crontab; existing state.json is preserved.
#
# Usage:
#   ./deploy.sh <ssh-host> <ssh-user> [<rpc-url>] [<anchor-addr>]
#   ./deploy.sh judahnomac-mini.local judah http://192.168.1.9:8545 0x5fbdb...

set -euo pipefail

HOST="${1:?usage: deploy.sh <ssh-host> <ssh-user> [<rpc-url>] [<anchor-addr>]}"
USER="${2:?usage: deploy.sh <ssh-host> <ssh-user> [<rpc-url>] [<anchor-addr>]}"
RPC="${3:-http://192.168.1.9:8545}"
ANCHOR="${4:-0x5fbdb2315678afecb367f032d93f642f64180aa3}"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "[deploy] target: $USER@$HOST"
echo "[deploy] rpc:    $RPC"
echo "[deploy] anchor: $ANCHOR"

# 1) ensure uv + create cell dir
ssh -o StrictHostKeyChecking=accept-new "$USER@$HOST" bash -s <<'REMOTE_BOOTSTRAP'
set -e
if ! command -v uv >/dev/null 2>&1 && [ ! -x "$HOME/.local/bin/uv" ]; then
  curl -LsSf https://astral.sh/uv/install.sh | sh > /dev/null 2>&1
fi
mkdir -p ~/etzhayyim/first-breath
REMOTE_BOOTSTRAP

# 2) scp the cell source
scp -o StrictHostKeyChecking=accept-new \
  "$SCRIPT_DIR/README.md" \
  "$SCRIPT_DIR/pyproject.toml" \
  "$SCRIPT_DIR/breath.py" \
  "$SCRIPT_DIR/.gitignore" \
  "$USER@$HOST:~/etzhayyim/first-breath/" > /dev/null

# 3) uv sync + first breath smoke + install cron @60s
ssh "$USER@$HOST" bash -s -- "$USER" "$RPC" "$ANCHOR" <<'REMOTE_INSTALL'
set -e
USER_=$1; RPC=$2; ANCHOR=$3
export PATH=$HOME/.local/bin:$PATH
cd ~/etzhayyim/first-breath
[ -d .venv ] || uv sync --quiet
ETZ_RPC="$RPC" ETZ_ANCHOR="$ANCHOR" .venv/bin/python breath.py | tail -3

# Install crontab
crontab -l 2>/dev/null | grep -v 'first-breath/breath.py' | grep -v '^ETZ_' > /tmp/cron.bak || true
cat /tmp/cron.bak > /tmp/cron.new
cat >> /tmp/cron.new <<CRON
ETZ_RPC=$RPC
ETZ_ANCHOR=$ANCHOR
* * * * * /Users/$USER_/etzhayyim/first-breath/.venv/bin/python /Users/$USER_/etzhayyim/first-breath/breath.py >> /Users/$USER_/etzhayyim/first-breath/breath.log 2>&1
CRON
crontab /tmp/cron.new
echo "[deploy] cron installed on $USER_@$(hostname -s)"
REMOTE_INSTALL

echo "[deploy] $USER@$HOST DONE — first breath above, cron @60s active"
