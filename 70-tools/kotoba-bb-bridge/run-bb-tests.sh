#!/usr/bin/env bash
# kotoba-bb-bridge — run the food/logistics actor bb (babashka) test sweep as a
# kotoba-code test-gate. kotoba-code's gate (gate.cljc `green?`) decides PASS only if the
# output matches /0 failures,\s*0 errors/ — so this script AGGREGATES per-suite results and
# emits that exact phrase ONLY when EVERY suite is green. On any failure it prints the failing
# suites WITHOUT that phrase (green sub-suite lines are suppressed) so the gate cannot false-green.
#
# Run from the project root (kotoba-code invokes it with :dir = project root):
#   KC_TEST_GLOB="orgs/etzhayyim/com-etzhayyim-mitooshi/methods/test_*.clj" bash 70-tools/kotoba-bb-bridge/run-bb-tests.sh
# Default glob = every actor test suite under 20-actors/**/{methods,tests}/test_*.clj.
set -uo pipefail

ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
cd "$ROOT" || exit 2

GLOB="${KC_TEST_GLOB:-}"
if [ -n "$GLOB" ]; then
  # shellcheck disable=SC2206
  FILES=( $GLOB )
else
  FILES=()
  while IFS= read -r f; do FILES+=("$f"); done < <(
    find 20-actors -name 'test_*.clj' \( -path '*/methods/*' -o -path '*/tests/*' -o -path '*/py/*' \) | sort)
fi

n=0; failed=0; failed_names=()
tmp="$(mktemp)"
for t in "${FILES[@]}"; do
  [ -f "$t" ] || continue
  n=$((n+1))
  if ! bb --classpath 20-actors "$t" >"$tmp" 2>&1; then
    failed=$((failed+1)); failed_names+=("$t")
    echo "✗ FAILED: $t"
    # show failing detail, but strip any green sub-suite phrase so the gate regex can't match it
    grep -vE "0 failures,[[:space:]]*0 errors" "$tmp" | tail -8
  fi
done
rm -f "$tmp"

echo "── kotoba-bb-bridge summary ──"
if [ "$n" -eq 0 ]; then
  echo "no test suites matched (gate: NOT green — expected test file missing)"
  exit 1
elif [ "$failed" -eq 0 ]; then
  echo "$n suites green: 0 failures, 0 errors"
  exit 0
else
  echo "$failed of $n suites RED (gate: NOT green) — ${failed_names[*]}"
  exit 1
fi
