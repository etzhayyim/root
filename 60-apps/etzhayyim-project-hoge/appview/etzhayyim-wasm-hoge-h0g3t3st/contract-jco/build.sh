#!/bin/bash
# Pattern C build: Rust WIT Component Model → jco → ESM JS for CF Workers
#
# Pipeline:
#   1. cargo build (wasm32-unknown-unknown, no WASI)
#   2. wasm-tools component new → P2 component (no WASI imports)
#   3. jco transpile --instantiation async → ESM JS + core.wasm
#   4. Copy output to appview/src/jco-component/
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
APPVIEW="$SCRIPT_DIR/../../../appview/src/jco-component"
CARGO_TARGET="${CARGO_TARGET_DIR:-$HOME/.cargo-target/etzhayyim-root}"

# 1. Build core module (no WASI)
cd "$SCRIPT_DIR"
cargo build --target wasm32-unknown-unknown --release

CORE="$CARGO_TARGET/wasm32-unknown-unknown/release/hoge_shannon_jco.wasm"

# 2. Wrap into WIT Component (no adapter — wasm32-unknown-unknown has no WASI imports)
mkdir -p build
wasm-tools component new "$CORE" -o build/shannon-jco-component.wasm
echo "Component: $(wasm-tools component wit build/shannon-jco-component.wasm | head -5)"

# 3. jco transpile → ESM JS + core.wasm (no WASI shim, no Node.js compat)
mkdir -p /tmp/jco-out
npx --yes @bytecodealliance/jco transpile build/shannon-jco-component.wasm \
  --no-nodejs-compat \
  --no-wasi-shim \
  --instantiation async \
  --name shannon-jco \
  -o /tmp/jco-out/

# 4. Copy to appview
mkdir -p "$APPVIEW/interfaces"
cp /tmp/jco-out/shannon-jco.core.wasm \
   /tmp/jco-out/shannon-jco.js \
   /tmp/jco-out/shannon-jco.d.ts \
   "$APPVIEW/"
cp /tmp/jco-out/interfaces/etzhayyim-hoge-compute-compute.d.ts \
   "$APPVIEW/interfaces/"

echo "Done. Output:"
ls -lh "$APPVIEW/"
