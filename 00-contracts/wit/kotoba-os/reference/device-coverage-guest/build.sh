#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
TC="$(rustup show active-toolchain | awk '{print $1}')"
BIN="$HOME/.rustup/toolchains/$TC/bin"
CORE="target/wasm32-unknown-unknown/release/device_coverage_guest.wasm"
OUT="device-coverage.component.wasm"
( env -u RUSTC -u RUSTFLAGS PATH="$BIN:/usr/bin:/bin" "$BIN/cargo" build --target wasm32-unknown-unknown --release )
wasm-tools component new "$CORE" -o "$OUT"
wasm-tools validate --features component-model "$OUT"
echo "=== component world ==="
wasm-tools component wit "$OUT"
echo "OK: $(wc -c < "$OUT") bytes"
