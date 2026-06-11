#!/usr/bin/env bash
# Build the kotoba-wasm browser-node bundle and stage it for the apex Worker's
# static-asset route (`/kotoba/*`, wrangler.toml [assets]). Run after bumping the
# kotoba submodule or changing crates/kotoba-wasm. (ADR-2606013600, kabuto G6.)
set -euo pipefail

here="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
crate="$here/../../40-engine/kotoba/crates/kotoba-wasm"
dest="$here/public/kotoba"

# wasm-pack must use the rustup toolchain (it carries wasm32-unknown-unknown);
# a Homebrew rustc has no wasm sysroot.
export PATH="$HOME/.cargo/bin:$PATH"

echo "→ wasm-pack build (web target) …"
( cd "$crate" && wasm-pack build --release --target web --out-dir pkg )

mkdir -p "$dest"
cp "$crate/pkg/kotoba_wasm.js" "$crate/pkg/kotoba_wasm_bg.wasm" "$dest/"

echo "✓ staged $(du -h "$dest/kotoba_wasm_bg.wasm" | cut -f1) wasm + js → $dest"
ls -la "$dest"
