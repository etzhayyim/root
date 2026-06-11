#!/usr/bin/env bash
# run-langserver.sh — wrapper invoked by com.etzhayyim.langserver.@@LANG@@ launchd job.
#
# Responsibilities:
#   L2 (initial): exec LSP binary in stdio
#   L4 (this revision): bind LSP stdio to a Unix domain socket and/or TCP
#                       listener via socat (fork mode, one LSP per connection)
#
# Transport selection (precedence):
#   1. $ETZHAYYIM_LISTEN_ADDR if explicitly set:
#        - "stdio"                            → raw stdio (no socat) — debugging only
#        - "unix:<path>"                      → Unix socket at <path>
#        - "tcp:<bind>:<port>"                → TCP listener on explicit bind addr
#        - "mesh-tcp:<port>"                  → TCP on mesh-IP (resolved at start, L5)
#        - "both:<sock>|<bind>:<port>"        → both, in two socat processes
#        - "mesh-both:<sock>|<port>"          → Unix socket + mesh-IP TCP (L5)
#   2. Else: resolve from transports.toml using $ETZHAYYIM_LANG.
#      Default mode = mesh-both (Unix socket + mesh-IP TCP).
#
# Mesh-IP is read from $HOME/.etzhayyim/mesh/identity.json or, if the
# cutover hasn't landed, from $HOME/.etzhayyim/mesh/identity.json.

set -euo pipefail

LANG_ID="${1:-${ETZHAYYIM_LANG:-}}"
if [ -z "$LANG_ID" ]; then
  echo "FATAL: language identifier missing (arg \$1 or \$ETZHAYYIM_LANG)" >&2
  exit 64
fi

BIN="${ETZHAYYIM_LSP_BIN_PATH:-}"
if [ -z "$BIN" ]; then
  echo "FATAL: ETZHAYYIM_LSP_BIN_PATH not set" >&2
  exit 65
fi
# Resolve ~ in BIN
BIN="${BIN/#\~/$HOME}"
if [ ! -x "$BIN" ]; then
  echo "FATAL: LSP binary not executable: $BIN" >&2
  exit 66
fi

WORKSPACE="${ETZHAYYIM_LANGSERVER_WORKSPACE:-${ETZHAYYIM_REPO:-$PWD}}"
if [ ! -d "$WORKSPACE" ]; then
  echo "FATAL: workspace not a directory: $WORKSPACE" >&2
  exit 67
fi

# shellcheck disable=SC2206
ARGS=(${ETZHAYYIM_LSP_ARGS:-})

# ── Resolve transport ───────────────────────────────────────────────────

LISTEN="${ETZHAYYIM_LISTEN_ADDR:-}"
if [ -z "$LISTEN" ]; then
  # Default: both Unix socket + TCP loopback. Resolve port from transports.toml.
  TRANSPORTS_TOML="${ETZHAYYIM_REPO:-$(cd "$(dirname "$0")/../../.." && pwd)}/50-infra/etzhayyim-langserver/transports.toml"
  if [ ! -f "$TRANSPORTS_TOML" ]; then
    echo "FATAL: transports.toml not found at $TRANSPORTS_TOML" >&2
    exit 68
  fi

  PORT_TCP=$(python3 -c "
import tomllib, sys
d = tomllib.loads(open('$TRANSPORTS_TOML').read())
for t in d.get('transport', []):
    if t['lang'] == '$LANG_ID':
        print(t['port_tcp'])
        sys.exit(0)
sys.exit(1)
") || { echo "FATAL: no transport entry for lang=$LANG_ID in $TRANSPORTS_TOML" >&2; exit 69; }

  SOCK_BASE=$(python3 -c "
import tomllib, sys
d = tomllib.loads(open('$TRANSPORTS_TOML').read())
for t in d.get('transport', []):
    if t['lang'] == '$LANG_ID':
        print(t['socket_basename'])
        sys.exit(0)
sys.exit(1)
") || exit 69

  SOCK_DIR="/tmp/etzhayyim-langserver-$USER"
  install -d -m 0700 "$SOCK_DIR"
  SOCK_PATH="$SOCK_DIR/$SOCK_BASE"
  LISTEN="mesh-both:${SOCK_PATH}|${PORT_TCP}"

  # L6: resolve healthz port (lsp_port + 100 per transports.toml convention)
  PORT_HEALTHZ=$(python3 -c "
import tomllib, sys
d = tomllib.loads(open('$TRANSPORTS_TOML').read())
for t in d.get('transport', []):
    if t['lang'] == '$LANG_ID':
        print(t.get('port_healthz', t['port_tcp'] + 100))
        sys.exit(0)
sys.exit(1)
") || PORT_HEALTHZ=$((PORT_TCP + 100))
fi

# ── L6: healthz sidecar spawn ───────────────────────────────────────────

spawn_healthz_sidecar() {
  local bind="$1"
  local lsp_port="$2"
  local healthz_port="${PORT_HEALTHZ:-$((lsp_port + 100))}"
  local sidecar="${ETZHAYYIM_REPO:-$(cd "$(dirname "$0")/../../.." && pwd)}/50-infra/etzhayyim-langserver/healthz/healthz-sidecar.py"
  if [ ! -x "$sidecar" ]; then
    echo "WARN: healthz sidecar not found at $sidecar — skipping L6 probe" >&2
    return 0
  fi
  python3 "$sidecar" \
    --lang "$LANG_ID" \
    --lsp-port "$lsp_port" \
    --healthz-port "$healthz_port" \
    --bind "$bind" \
    >&2 &
  HEALTHZ_PID=$!
  echo "[$(date -u +%Y-%m-%dT%H:%M:%SZ)] healthz sidecar pid=$HEALTHZ_PID lang=$LANG_ID listening on $bind:$healthz_port" >&2
}

# ── Mesh-IP resolution (L5) ─────────────────────────────────────────────

resolve_mesh_ip() {
  local id
  for id in "$HOME/.etzhayyim/mesh/identity.json" "$HOME/.etzhayyim/mesh/identity.json"; do
    if [ -r "$id" ]; then
      # jq is a L3 prereq; fall back to python3 if missing
      if command -v jq >/dev/null 2>&1; then
        jq -r '.mesh_ip' "$id"
      else
        python3 -c "import json; print(json.load(open('$id'))['mesh_ip'])"
      fi
      return 0
    fi
  done
  return 1
}

# ── socat invocation helpers ────────────────────────────────────────────

SOCAT="${SOCAT_BIN:-/opt/homebrew/bin/socat}"
LSP_EXEC="$BIN ${ARGS[*]:-}"

socat_unix_listener() {
  local sock="$1"
  exec "$SOCAT" \
    "UNIX-LISTEN:${sock},reuseaddr,fork,unlink-early,mode=0600" \
    "EXEC:${LSP_EXEC}"
}

socat_tcp_listener() {
  local bind="$1"
  local port="$2"
  exec "$SOCAT" \
    "TCP-LISTEN:${port},bind=${bind},reuseaddr,fork" \
    "EXEC:${LSP_EXEC}"
}

# ── Dispatch ────────────────────────────────────────────────────────────

echo "[$(date -u +%Y-%m-%dT%H:%M:%SZ)] starting langserver" \
  "lang=$LANG_ID bin=$BIN args=${ARGS[*]:-} ws=$WORKSPACE listen=$LISTEN" >&2

case "$LISTEN" in
  stdio)
    cd "$WORKSPACE"
    exec "$BIN" "${ARGS[@]}"
    ;;
  unix:*)
    SOCK_PATH="${LISTEN#unix:}"
    cd "$WORKSPACE"
    socat_unix_listener "$SOCK_PATH"
    ;;
  tcp:*)
    REST="${LISTEN#tcp:}"
    BIND="${REST%:*}"
    PORT="${REST##*:}"
    cd "$WORKSPACE"
    spawn_healthz_sidecar "$BIND" "$PORT"
    socat_tcp_listener "$BIND" "$PORT"
    ;;
  mesh-tcp:*)
    PORT="${LISTEN#mesh-tcp:}"
    BIND="$(resolve_mesh_ip)" || { echo "FATAL: mesh identity not found (looked in ~/.etzhayyim/mesh/, ~/.etzhayyim/mesh/)" >&2; exit 72; }
    cd "$WORKSPACE"
    spawn_healthz_sidecar "$BIND" "$PORT"
    socat_tcp_listener "$BIND" "$PORT"
    ;;
  mesh-both:*)
    REST="${LISTEN#mesh-both:}"
    SOCK_PATH="${REST%%|*}"
    PORT="${REST#*|}"
    BIND="$(resolve_mesh_ip)" || { echo "FATAL: mesh identity not found" >&2; exit 72; }
    cd "$WORKSPACE"
    if [ ! -x "$SOCAT" ]; then
      echo "FATAL: socat not found at $SOCAT (install via L3 prereq)" >&2
      exit 70
    fi
    "$SOCAT" "UNIX-LISTEN:${SOCK_PATH},reuseaddr,fork,unlink-early,mode=0600" \
             "EXEC:${LSP_EXEC}" &
    UNIX_PID=$!
    spawn_healthz_sidecar "$BIND" "$PORT"
    trap "kill -TERM $UNIX_PID ${HEALTHZ_PID:-} 2>/dev/null || true" EXIT TERM INT
    exec "$SOCAT" \
      "TCP-LISTEN:${PORT},bind=${BIND},reuseaddr,fork" \
      "EXEC:${LSP_EXEC}"
    ;;
  both:*)
    REST="${LISTEN#both:}"
    SOCK_PATH="${REST%%|*}"
    TCP_PART="${REST#*|}"
    BIND="${TCP_PART%:*}"
    PORT="${TCP_PART##*:}"
    cd "$WORKSPACE"
    # Run TCP listener in foreground; Unix listener in background (same process group).
    # If either socat exits, kill the parent shell so launchd restarts everything.
    if [ ! -x "$SOCAT" ]; then
      echo "FATAL: socat not found at $SOCAT (install via L3 prereq)" >&2
      exit 70
    fi
    "$SOCAT" "UNIX-LISTEN:${SOCK_PATH},reuseaddr,fork,unlink-early,mode=0600" \
             "EXEC:${LSP_EXEC}" &
    UNIX_PID=$!
    spawn_healthz_sidecar "$BIND" "$PORT"
    trap "kill -TERM $UNIX_PID ${HEALTHZ_PID:-} 2>/dev/null || true" EXIT TERM INT
    exec "$SOCAT" \
      "TCP-LISTEN:${PORT},bind=${BIND},reuseaddr,fork" \
      "EXEC:${LSP_EXEC}"
    ;;
  *)
    echo "FATAL: unrecognized ETZHAYYIM_LISTEN_ADDR='$LISTEN' (want stdio | unix:<path> | tcp:<bind>:<port> | mesh-tcp:<port> | both:<sock>|<bind>:<port> | mesh-both:<sock>|<port>)" >&2
    exit 71
    ;;
esac
