#!/usr/bin/env bash
# attach-langserver.sh — open a stdio↔TCP/Unix bridge to a fleet langserver.
#
# Designed to be invoked AS IF IT WERE THE LSP BINARY by any editor that
# supports a custom LSP command. Editor sends/receives JSON-RPC over our
# stdio; we relay to the fleet LSP via socat over either:
#   - the host's mesh-IP TCP port (fleet-wide, default)
#   - the same-host Unix socket (faster if editor runs on the LSP's mini)
#
# Usage:
#   attach-langserver.sh <lang>
#   attach-langserver.sh <lang> --transport tcp|unix
#   attach-langserver.sh <lang> --host <tribe>  # override fleet placement
#
# Looks up the target endpoint from lsp-fleet.json (run
# scripts/generate-fleet-registry.sh first to refresh).

set -euo pipefail
cd "$(dirname "$0")/.."

REGISTRY="scripts/lsp-fleet.json"
if [ ! -f "$REGISTRY" ]; then
  echo "FATAL: $REGISTRY not found — run scripts/generate-fleet-registry.sh first" >&2
  exit 1
fi

LANG_ID="${1:-}"
if [ -z "$LANG_ID" ]; then
  echo "Usage: $0 <lang> [--transport tcp|unix] [--host <tribe>]" >&2
  exit 64
fi
shift

TRANSPORT="tcp"
HOST_OVERRIDE=""
while [ $# -gt 0 ]; do
  case "$1" in
    --transport) shift; TRANSPORT="$1" ;;
    --transport=*) TRANSPORT="${1#--transport=}" ;;
    --host) shift; HOST_OVERRIDE="$1" ;;
    --host=*) HOST_OVERRIDE="${1#--host=}" ;;
    *) echo "ignoring unknown arg: $1" >&2 ;;
  esac
  shift
done

# Resolve endpoint from registry
read -r MESH_IP PORT SOCKET_PATH HOST_NAME < <(python3 -c "
import json, sys
reg = json.load(open('$REGISTRY'))
target_host = '$HOST_OVERRIDE'
matched = None
for e in reg['entries']:
    if e['lang'] != '$LANG_ID':
        continue
    if target_host and e['host'] != target_host:
        continue
    matched = e
    break
if not matched:
    sys.stderr.write(f\"no fleet entry for lang=$LANG_ID host='$HOST_OVERRIDE'\n\")
    sys.exit(1)
print(matched['mesh_ip'], matched['port'], matched['socket_path'], matched['host'])
") || exit 2

SOCAT="${SOCAT_BIN:-/opt/homebrew/bin/socat}"
if [ ! -x "$SOCAT" ]; then
  if command -v socat >/dev/null 2>&1; then
    SOCAT=$(command -v socat)
  else
    echo "FATAL: socat not found (brew install socat)" >&2
    exit 70
  fi
fi

case "$TRANSPORT" in
  tcp)
    # stdio (editor) ↔ TCP (fleet LSP). Editor reads/writes JSON-RPC on stdin/stdout.
    # echo to stderr so the editor doesn't ingest our diagnostic noise.
    echo "[attach-langserver/$LANG_ID] stdio ↔ tcp://${MESH_IP}:${PORT} (host=${HOST_NAME})" >&2
    exec "$SOCAT" - "TCP:${MESH_IP}:${PORT}"
    ;;
  unix)
    if [ ! -S "$SOCKET_PATH" ]; then
      echo "FATAL: Unix socket not present at $SOCKET_PATH (LSP not running on this host, or host=${HOST_NAME} is remote)" >&2
      exit 71
    fi
    echo "[attach-langserver/$LANG_ID] stdio ↔ unix:${SOCKET_PATH}" >&2
    exec "$SOCAT" - "UNIX-CONNECT:${SOCKET_PATH}"
    ;;
  *)
    echo "FATAL: unknown transport '$TRANSPORT' (want tcp | unix)" >&2
    exit 72
    ;;
esac
