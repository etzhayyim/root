#!/usr/bin/env bash
set -euo pipefail

KOTOBA_DIR="/Users/junkawasaki/github/etzhayyim-root/40-engine/kotoba"
WIT_DIR="${KOTOBA_DIR}/crates/kotoba-runtime/wit"
BINDINGS_DIR="$(pwd)/bindings"
PY_PKG_DIR="${KOTOBA_DIR}/py"
AGENT_DIR="$(pwd)"
AGENT_MODULE="agent"
OUTPUT="agent.wasm"

SITE_PKG="$(python3 -c "import site; print(site.getsitepackages()[0])" 2>/dev/null || true)"
if [[ -z "$SITE_PKG" ]]; then
    SITE_PKG="$(python3 -m site --user-site 2>/dev/null || true)"
fi

echo "Generating bindings in $BINDINGS_DIR..."
mkdir -p "$BINDINGS_DIR"
componentize-py -d "$WIT_DIR" -w kotoba-node bindings "$BINDINGS_DIR"

echo "Building component $OUTPUT..."
componentize-py \
    -d "$WIT_DIR" \
    -w kotoba-node \
    componentize "$AGENT_MODULE" \
    -p "$AGENT_DIR" \
    -p "$BINDINGS_DIR" \
    -p "$PY_PKG_DIR" \
    ${SITE_PKG:+-p "$SITE_PKG"} \
    -o "$OUTPUT"

echo "Build successful: $OUTPUT"
