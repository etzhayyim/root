#!/usr/bin/env bash
# Build the real WASM component for a clean-room actor via componentize-py.
# Reproducible: same app.py + wit → byte-identical component.
#   python3 -m venv .venv && .venv/bin/pip install componentize-py
#   ./build.sh app stripe-compat
set -euo pipefail
MOD="${1:-app}"
NAME="${2:-stripe-compat}"
CZPY="${CZPY:-componentize-py}"
"$CZPY" -d wit -w actor componentize "$MOD" -o "$NAME.actor.wasm"
echo "built $NAME.actor.wasm"
wasm-tools validate "$NAME.actor.wasm" && echo "validate: OK"
