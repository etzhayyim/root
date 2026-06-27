#!/usr/bin/env bash
# run_tests.sh — magatama test runner
# Runs the bb/cljc cell tests. The legacy Python shionome test + shionome_core.py
# were superseded by the cljc port (cells/test_cells.cljc covers shionome_core +
# every shionome/suimin cell run-chain + Council gate), per the repo py→cljc rule.
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ACTOR_DIR="$(dirname "$SCRIPT_DIR")"

echo "=== magatama cljc cell tests ==="
cd "$ACTOR_DIR"
bb --classpath . -e "(require 'magatama.cells.test-cells)(magatama.cells.test-cells/-main)"
