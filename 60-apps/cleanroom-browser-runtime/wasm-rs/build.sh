#!/usr/bin/env bash
# Build the compact RAW single-block WASM actor (browser-local tier).
# Uses the rustup toolchain (has wasm32-unknown-unknown std); the Homebrew
# cargo on PATH does not. Output is a few KB → single IPFS block → raw bafkrei CID.
set -euo pipefail
TC="$HOME/.rustup/toolchains/stable-aarch64-apple-darwin/bin"
[ -x "$TC/cargo" ] || { echo "rustup stable toolchain not found"; exit 1; }
rustup target add wasm32-unknown-unknown >/dev/null 2>&1 || true
env RUSTC="$TC/rustc" PATH="$TC:$PATH" "$TC/cargo" build --release --target wasm32-unknown-unknown
W="target/wasm32-unknown-unknown/release/cleanroom_actor_raw.wasm"
wasm-tools validate "$W" && echo "validate: OK ($(wc -c < "$W") bytes)"
