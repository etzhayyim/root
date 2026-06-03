#!/usr/bin/env bash
# Build the reference mesh-agent WASM Component (ADR-2606031600 §D2/§D5) and
# verify its world. Same toolchain approach as plc-control-guest (wit-bindgen +
# plain cargo + wasm-tools component new; rustup bin pinned because Homebrew rust
# shadows rustup's wasm32 std).
set -euo pipefail
cd "$(dirname "$0")"

TC="$(rustup show active-toolchain | awk '{print $1}')"
BIN="$HOME/.rustup/toolchains/$TC/bin"
CORE="target/wasm32-unknown-unknown/release/mesh_agent_guest.wasm"
OUT="mesh-agent.component.wasm"

( env -u RUSTC -u RUSTFLAGS PATH="$BIN:/usr/bin:/bin" \
    "$BIN/cargo" build --target wasm32-unknown-unknown --release )

wasm-tools component new "$CORE" -o "$OUT"
wasm-tools validate --features component-model "$OUT"
echo "=== component world ==="
wasm-tools component wit "$OUT"
echo "=== component digest (sha256) ==="
shasum -a 256 "$OUT"
echo "OK: $(wc -c < "$OUT") bytes"
