#!/bin/bash
# SessionStart hook — etzhayyim/root
#
# Bootstraps the dev→build→verify→artifact toolchain so a Claude Code on the web
# session can take etzhayyim from development through to GitHub-driven deploy
# WITHOUT any secrets ever touching the cloud container.
#
# What it installs (all idempotent, all from public sources — no credentials):
#   - rustup wasm32-unknown-unknown target   (kotoba/actor WASM builds)
#   - wasm-tools                              (strip / validate the .wasm)
#   - kubo (ipfs)                             (deterministic CIDv1 + offline CAR)
#   - lefthook                                (the constitutional pre-commit gate)
#   - an OFFLINE ipfs repo                    (CID + CAR need no daemon, no network)
#
# What it deliberately does NOT do (operating-entity / no-server-key boundary):
#   - no Cloudflare / IPFS-pin / fleet credentials (those live in GitHub Actions
#     secrets; deploy is GitHub-driven — see .claude/REMOTE-DEPLOY.md)
#   - no DID signing key (macOS Keychain only)
#   - no live deploy to the LAN Mac-mini fleet (physically unreachable from cloud)
#
# Runs only in the remote (web) environment. Local Macs already have the toolchain.
set -euo pipefail

# Local dev machines keep their own toolchain — only bootstrap the cloud container.
if [ "${CLAUDE_CODE_REMOTE:-}" != "true" ]; then
  echo "session-start: not a remote session — skipping toolchain bootstrap"
  exit 0
fi

PROJECT_DIR="${CLAUDE_PROJECT_DIR:-$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)}"
BIN_DIR="/usr/local/bin"
WASM_TOOLS_VER="1.225.0"
KUBO_VER="v0.34.1"
ARCH="$(uname -m)"   # expected: x86_64

log() { echo "session-start: $*"; }

# ── 1. Rust wasm32 target ────────────────────────────────────────────────────
if command -v rustup >/dev/null 2>&1; then
  if ! rustup target list --installed 2>/dev/null | grep -q '^wasm32-unknown-unknown$'; then
    log "adding rust target wasm32-unknown-unknown"
    rustup target add wasm32-unknown-unknown
  else
    log "wasm32-unknown-unknown target already present"
  fi
else
  log "WARN: rustup not found — WASM builds will be unavailable"
fi

# ── 2. wasm-tools (strip / validate) ─────────────────────────────────────────
if ! command -v wasm-tools >/dev/null 2>&1; then
  log "installing wasm-tools ${WASM_TOOLS_VER}"
  tmp="$(mktemp -d)"
  url="https://github.com/bytecodealliance/wasm-tools/releases/download/v${WASM_TOOLS_VER}/wasm-tools-${WASM_TOOLS_VER}-${ARCH}-linux.tar.gz"
  if curl -sSL -o "$tmp/wt.tar.gz" "$url" && tar xzf "$tmp/wt.tar.gz" -C "$tmp"; then
    cp "$tmp/wasm-tools-${WASM_TOOLS_VER}-${ARCH}-linux/wasm-tools" "$BIN_DIR/" && log "wasm-tools installed: $(wasm-tools --version)"
  else
    log "WARN: wasm-tools download failed — falling back to 'cargo install wasm-tools' (slow)"
    cargo install wasm-tools --locked >/dev/null 2>&1 || log "WARN: wasm-tools unavailable"
  fi
  rm -rf "$tmp"
else
  log "wasm-tools already present: $(wasm-tools --version)"
fi

# ── 3. kubo / ipfs (deterministic CID + offline CAR export) ──────────────────
if ! command -v ipfs >/dev/null 2>&1; then
  log "installing kubo ${KUBO_VER}"
  tmp="$(mktemp -d)"
  url="https://dist.ipfs.tech/kubo/${KUBO_VER}/kubo_${KUBO_VER}_linux-amd64.tar.gz"
  if curl -sSL -o "$tmp/kubo.tar.gz" "$url" && tar xzf "$tmp/kubo.tar.gz" -C "$tmp"; then
    cp "$tmp/kubo/ipfs" "$BIN_DIR/" && log "kubo installed: $(ipfs --version)"
  else
    log "WARN: kubo download failed — CID/CAR steps will be unavailable"
  fi
  rm -rf "$tmp"
else
  log "kubo already present: $(ipfs --version)"
fi

# ── 4. Offline IPFS repo (no daemon, no network, no peers) ───────────────────
# --only-hash and 'dag export' both require an initialized repo, but never a
# running daemon or any outbound connection.
export IPFS_PATH="${IPFS_PATH:-$HOME/.ipfs}"
if command -v ipfs >/dev/null 2>&1 && [ ! -f "$IPFS_PATH/config" ]; then
  log "initializing offline ipfs repo at $IPFS_PATH"
  ipfs init --profile=lowpower >/dev/null 2>&1 || log "WARN: ipfs init failed"
fi
# Persist IPFS_PATH for the rest of the session.
if [ -n "${CLAUDE_ENV_FILE:-}" ]; then
  echo "export IPFS_PATH=\"$IPFS_PATH\"" >> "$CLAUDE_ENV_FILE"
fi

# ── 5. lefthook (the constitutional pre-commit gate, mirrors CI ci.yml) ───────
if ! command -v lefthook >/dev/null 2>&1; then
  log "installing lefthook (constitutional gate)"
  npm install -g @evilmartians/lefthook >/dev/null 2>&1 && log "lefthook installed: $(lefthook version)" \
    || log "WARN: lefthook install failed"
else
  log "lefthook already present: $(lefthook version)"
fi

# ── 6. xxd (the lefthook end-of-file gate calls `tail -c1 | xxd -p`) ──────────
# Some cloud images ship without xxd; without it the constitutional gate's
# end-of-file check false-positives on every file. Prefer the real tool, else
# drop an od-backed shim so the gate runs honestly.
if ! command -v xxd >/dev/null 2>&1; then
  if command -v apt-get >/dev/null 2>&1 && (sudo apt-get install -y xxd >/dev/null 2>&1 || sudo apt-get install -y vim-common >/dev/null 2>&1) && command -v xxd >/dev/null 2>&1; then
    log "xxd installed via apt"
  else
    log "xxd unavailable — installing od-backed shim for the lefthook gate"
    cat > "$BIN_DIR/xxd" <<'SHIM'
#!/bin/sh
# Minimal xxd shim (od-backed) covering `xxd -p` plain hex dump, used by the
# lefthook end-of-file gate. Reads stdin when no file argument is given.
case "${1:-}" in
  -p|-ps|-plain) shift ;;
  -r|-revert) shift; cat "$@"; exit 0 ;;
esac
if [ "$#" -eq 0 ]; then od -An -v -tx1 | tr -d ' \n'; echo
else od -An -v -tx1 "$@" | tr -d ' \n'; echo; fi
SHIM
    chmod +x "$BIN_DIR/xxd"
  fi
else
  log "xxd already present"
fi

log "toolchain ready — dev/build/verify + kotoba-wasm→CID/CAR enabled (deploy is GitHub-driven)"
