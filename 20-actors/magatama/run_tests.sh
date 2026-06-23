#!/usr/bin/env bash
# run_tests.sh — magatama test runner
# Runs both Python shionome tests and the bb/cljc cell tests.
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ACTOR_DIR="$(dirname "$SCRIPT_DIR")"

echo "=== magatama Python tests ==="
cd "$SCRIPT_DIR/cells"
python3 test_shionome_cells.py

echo ""
echo "=== magatama cljc cell tests ==="
cd "$ACTOR_DIR"
bb --classpath . -e "(require 'magatama.cells.test-cells)(magatama.cells.test-cells/-main)"
