#!/usr/bin/env bash
# tatekata 建方 — run the whole test suite with one command.
set -uo pipefail
ROOT="$(cd "$(dirname "$0")" && pwd)"
REPO_ROOT="$(cd "$ROOT/../.." && pwd)"
cd "$ROOT"
SUITES=( "methods/test_charter_gates.py" "py/test_agent.py" )
fail=0
for s in "${SUITES[@]}"; do
  [ -f "$s" ] || continue
  dir="$(dirname "$s")"; file="$(basename "$s")"
  if ( cd "$dir" && python3 "$file" ); then :; else echo "FAILED: $s"; fail=1; fi
done

# cljc (babashka) tests — py→cljc port
BB_CP="20-actors"
run_cljc() {
  local ns="$1"
  echo "==> tatekata [cljc] $ns"
  ( cd "$REPO_ROOT" && bb -cp "$BB_CP" -e "(require (quote clojure.test) (quote $ns))(let [r (clojure.test/run-tests (quote $ns))](System/exit (if (zero? (+ (:fail r) (:error r))) 0 1)))" ) || fail=1
}

run_cljc "tatekata.methods.test-charter-gates"
run_cljc "tatekata.methods.test-agent"

[ "$fail" -eq 0 ] && echo "── tatekata: ALL suites green ──" || { echo "── tatekata: FAILURES ──"; exit 1; }
