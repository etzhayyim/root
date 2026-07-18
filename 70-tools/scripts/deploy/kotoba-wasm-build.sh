#!/usr/bin/env bash
# kotoba-wasm-build.sh — build a kotoba/actor WASM component and content-address it.
#
# Produces, with NO secrets and NO network, three artifacts under <crate>/dist/:
#   <name>.wasm   stripped + validated wasm32-unknown-unknown component
#   <name>.cid    CIDv1 (raw, sha2-256) — identical to `ipfs add --cid-version=1`
#   <name>.car    CARv1 bundle of that block — what CI pins to IPFS
#
# This is the "build + content-address" half of the kotoba-wasm→IPFS deploy.
# The actual pin (which needs a pinning-service credential) happens in GitHub
# Actions (.github/workflows/kotoba-wasm-ipfs-deploy.yml), never in this
# container — consistent with the no-server-key / no-secrets-in-cloud posture.
#
# Usage:
#   70-tools/scripts/deploy/kotoba-wasm-build.sh <crate-dir> [artifact-name]
#
# Examples:
#   70-tools/scripts/deploy/kotoba-wasm-build.sh orgs/etzhayyim/com-etzhayyim-tsumugi/wasm/tsumugi-core
#   70-tools/scripts/deploy/kotoba-wasm-build.sh orgs/etzhayyim/com-etzhayyim-kanae/wasm/kanae-core kanae-core
set -euo pipefail

CRATE_DIR="${1:?usage: kotoba-wasm-build.sh <crate-dir> [artifact-name]}"
CRATE_DIR="$(cd "$CRATE_DIR" && pwd)"

# Derive a hyphenated artifact name from the crate name unless one is given.
crate_name="$(grep -m1 '^name *=' "$CRATE_DIR/Cargo.toml" | sed -E 's/.*"([^"]+)".*/\1/')"
NAME="${2:-${crate_name//_/-}}"
WASM_UNDERSCORE="${crate_name//-/_}"

echo "==> kotoba-wasm-build: crate=$crate_name  artifact=$NAME"
cd "$CRATE_DIR"

# 1. Build (rustup toolchain so wasm std is present).
rustup target add wasm32-unknown-unknown >/dev/null 2>&1 || true
cargo build --release --target wasm32-unknown-unknown

SRC="target/wasm32-unknown-unknown/release/${WASM_UNDERSCORE}.wasm"
[ -f "$SRC" ] || { echo "!! expected artifact missing: $SRC" >&2; exit 1; }

mkdir -p dist

# 2. Strip + validate.
if command -v wasm-tools >/dev/null 2>&1; then
  wasm-tools strip "$SRC" -o "dist/${NAME}.wasm"
  wasm-tools validate "dist/${NAME}.wasm"
else
  echo "   (wasm-tools absent — copying unstripped)"
  cp "$SRC" "dist/${NAME}.wasm"
fi

# 3. Content-address (offline). CIDv1, matches the per-actor build.sh convention.
if command -v ipfs >/dev/null 2>&1; then
  export IPFS_PATH="${IPFS_PATH:-$HOME/.ipfs}"
  [ -f "$IPFS_PATH/config" ] || ipfs init --profile=lowpower >/dev/null 2>&1 || true
  CID="$(ipfs add -Q --cid-version=1 "dist/${NAME}.wasm")"
  echo "$CID" > "dist/${NAME}.cid"
  # CARv1 bundle of the just-added block(s) — the unit CI pins.
  ipfs dag export "$CID" > "dist/${NAME}.car" 2>/dev/null
  echo "==> ${NAME}.wasm  $(wc -c < "dist/${NAME}.wasm") bytes  CID=$CID"
  echo "    dist/${NAME}.cid  dist/${NAME}.car ($(wc -c < "dist/${NAME}.car") bytes)"
else
  echo "!! ipfs absent — built dist/${NAME}.wasm but could not content-address" >&2
  echo "   install kubo (see .claude/hooks/session-start.sh) to emit .cid/.car" >&2
  exit 1
fi
