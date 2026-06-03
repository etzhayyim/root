#!/usr/bin/env bash
# Build the reference plc-control WASM Component (ADR-2606031600 §D2/§D3) and
# verify its world. Deliberately avoids cargo-component (blocked here by a
# malformed global ~/.config/wasm-pkg/config.toml): plain cargo + wit-bindgen
# macro -> wasm32 core module, then `wasm-tools component new` -> component.
#
# The cargo/rustc step is pinned to the rustup toolchain's own bin dir because a
# Homebrew rust shadows rustup in PATH and lacks the wasm32 std. wasm-tools runs
# under the normal PATH.
set -euo pipefail
cd "$(dirname "$0")"

TC="$(rustup show active-toolchain | awk '{print $1}')"
BIN="$HOME/.rustup/toolchains/$TC/bin"
CORE="target/wasm32-unknown-unknown/release/plc_control_guest.wasm"
OUT="plc-control.component.wasm"

# 1. core wasm module (forced toolchain bin; wit-bindgen embeds component-type).
( env -u RUSTC -u RUSTFLAGS PATH="$BIN:/usr/bin:/bin" \
    "$BIN/cargo" build --target wasm32-unknown-unknown --release )

# 2. core module -> Component Model component.
wasm-tools component new "$CORE" -o "$OUT"

# 3. validate + show the world it actually exposes.
wasm-tools validate --features component-model "$OUT"
echo "=== component world ==="
wasm-tools component wit "$OUT"

# 4. the component is a content-addressed actor — print its digest.
echo "=== component digest (sha256; the CID is over this byte stream) ==="
shasum -a 256 "$OUT"
echo "OK: $(wc -c < "$OUT") bytes"
