#!/usr/bin/env bash
# Build the reference Modbus control component (ADR-2606031600 §D3) and show its
# world. Same toolchain approach as the other guests (wit-bindgen + plain cargo +
# wasm-tools component new; rustup bin pinned because Homebrew rust shadows the
# rustup wasm32 std).
set -euo pipefail
cd "$(dirname "$0")"

TC="$(rustup show active-toolchain | awk '{print $1}')"
BIN="$HOME/.rustup/toolchains/$TC/bin"
CORE="target/wasm32-unknown-unknown/release/modbus_control_guest.wasm"
OUT="modbus-control.component.wasm"

( env -u RUSTC -u RUSTFLAGS PATH="$BIN:/usr/bin:/bin" \
    "$BIN/cargo" build --target wasm32-unknown-unknown --release )

wasm-tools component new "$CORE" -o "$OUT"
wasm-tools validate --features component-model "$OUT"
echo "=== component world ==="
wasm-tools component wit "$OUT"
echo "OK: $(wc -c < "$OUT") bytes"
