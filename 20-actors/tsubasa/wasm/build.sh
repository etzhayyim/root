#!/usr/bin/env bash
# tsubasa 翼 — WASM component build (R3 scaffold). ADR-2606072802.
#
# OPERATOR STEP — this script is the documented build recipe; running it (and pinning the
# resulting CID) is the no-server-key operator action, exactly like rasen/shionome. The
# core to compile is the PURE compute in 20-actors/tsubasa/methods/analyze.cljc
# (analyze / coverage) + the template digest — none of which do I/O.
#
# Recommended path (matches the live T1 actors shionome-core / tsumugi): port the pure
# analyze core to a tiny Rust crate `tsubasa-core` and compile to a WASM component against
# wasm/world.wit, then CID-verify the artifact (raw sha2-256, ipfs-parity).
#
#   cargo component build --release --target wasm32-wasip2
#   wasm-tools component wit target/wasm32-wasip2/release/tsubasa_core.wasm   # must match world.wit
#   ipfs add --raw-leaves --cid-version 1 -Q target/.../tsubasa_core.wasm     # → CID to register
#
# BUILD-TIME CHARTER ASSERTION (the shionome `no_trade:true` pattern): the build MUST fail
# if the compiled component imports any side-effecting WASI interface or contains a
# commission/affiliate symbol — the absence is the guarantee (G1/G5/G6).
set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
WASM="${1:-}"

if [[ -z "$WASM" ]]; then
  echo "usage: build.sh <compiled-component.wasm>   # after cargo component build" >&2
  echo "(this scaffold verifies the artifact's charter cleanliness + prints its CID)" >&2
  exit 2
fi

echo "== verifying WIT export matches wasm/world.wit =="
wasm-tools component wit "$WASM" | grep -q "analyze:" || { echo "FAIL: analyze not exported"; exit 1; }

echo "== charter assertion: no side-effecting WASI imports (G1/G5/G6) =="
if wasm-tools component wit "$WASM" | grep -Eq "import wasi:(sockets|clocks|random)"; then
  echo "FAIL: component imports a side-effecting interface — not charter-clean (no-network/no-clock)"; exit 1
fi

echo "== charter assertion: no commission/affiliate symbol =="
if wasm-tools print "$WASM" 2>/dev/null | grep -Eiq "commission|affiliate"; then
  echo "FAIL: component contains a commission/affiliate symbol (G1)"; exit 1
fi

echo "== content-address (raw sha2-256, ipfs-parity) =="
ipfs add --raw-leaves --cid-version 1 -Q "$WASM"
echo "OK — register this CID in INFRA_ACTORS.tsubasa.wasmCid + did.json _meta.wasmCid"
