#!/usr/bin/env bash
# Build the browser kotoba node (kotoba-wasm) bundles from the kotoba submodule and
# assemble a self-contained serve/ dir for the Playwright browser proof.
#
# TOOLCHAIN LESSON (verified 2026-06-06): use the RUSTUP toolchain, not Homebrew rust —
# Homebrew's rustc lacks the wasm32-unknown-unknown std (core/std E0463). Pin stable.
set -euo pipefail
cd "$(dirname "$0")"
POC="$PWD"
KW="$(cd ../../../40-engine/kotoba/crates/kotoba-wasm && pwd)"
export RUSTUP_TOOLCHAIN=stable
export PATH="$HOME/.cargo/bin:$PATH"

echo "── 1. node bundle (wasm-bindgen --target nodejs, release) ──"
( cd "$KW/../.." && cargo build --release --target wasm32-unknown-unknown -p kotoba-wasm )
WASM="$KW/../../target/wasm32-unknown-unknown/release/kotoba_wasm.wasm"
rm -rf "$POC/node-pkg"; mkdir -p "$POC/node-pkg"
wasm-bindgen "$WASM" --out-dir "$POC/node-pkg" --target nodejs
# wasm-bindgen --target nodejs emits CommonJS (exports.*). This package.json has
# "type":"module", so mark node-pkg/ as CommonJS per-directory, else Node parses the
# .js as ESM and throws `exports is not defined` (ESM `await import()` interops fine).
printf '{"type":"commonjs"}\n' > "$POC/node-pkg/package.json"

echo "── 2. web bundle (wasm-pack --target web --release, wasm-opt) ──"
( cd "$KW" && wasm-pack build --target web --out-dir web/pkg --release >/dev/null 2>&1 )

echo "── 3. assemble self-contained serve/ (submodule web/ harness + real-actor seed) ──"
mkdir -p "$POC/serve/pkg"
cp "$KW"/web/demo.html "$KW"/web/kotoba-*.js "$POC/serve/"
cp "$KW"/web/pkg/kotoba_wasm.js "$KW"/web/pkg/kotoba_wasm_bg.wasm "$POC/serve/pkg/"
node "$POC/gen-actor-datoms.mjs"   # (re)writes serve/seed-datoms.json from the REAL SSoT — keep last

echo "── done ──"
ls -la "$POC/serve" "$POC/node-pkg" | grep -E "\.wasm|\.js|\.json|\.html" | sed "s#$POC/##"
echo "web wasm gzip bytes: $(gzip -c "$POC/serve/pkg/kotoba_wasm_bg.wasm" | wc -c)"
