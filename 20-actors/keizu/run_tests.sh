#!/usr/bin/env bash
# 系図 (keizu) — run the whole test suite with one command.
# The METHOD layer was MIGRATED to Clojure (ADR-2606160842): methods/*.py → *.cljc, and the
# Python source + tests were pruned once the cljc ports were verified. The method suites now run
# as Clojure via `bb test:keizu`; the cell state-machine tests remain Python. Exits non-zero on
# any failure.
set -uo pipefail
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
fail=0

echo "==> keizu method suites (Clojure / bb test:keizu)"
( cd "$ROOT" && bb test:keizu ) || fail=1

echo "==> keizu cell suites (Python)"
for s in cells/test_state_machines.py cells/test_membrane_flow.py; do
  [ -f "$(dirname "$0")/$s" ] || continue
  dir="$(dirname "$0")/$(dirname "$s")"; file="$(basename "$s")"
  if ( cd "$dir" && python3 "$file" >/dev/null 2>&1 ); then echo "  ok  $s"; else echo "  FAIL $s"; fail=1; fi
done

if [ "$fail" -eq 0 ]; then
  echo "── keizu: ALL suites green ──"
else
  echo "── keizu: FAILURES above ──"; exit 1
fi
