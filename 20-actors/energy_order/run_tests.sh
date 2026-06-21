#!/usr/bin/env bash
# Energy Order Protocol — suite-level digest test runner (babashka).
set -uo pipefail
cd "$(dirname "$0")/../.."

echo "== 20-actors/energy_order/test_digest.cljc =="
bb --classpath 20-actors 20-actors/energy_order/test_digest.cljc
