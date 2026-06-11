#!/usr/bin/env bash
# 高札 (kosatsu) — run the whole test suite with one command.
# Tests are standalone-runnable (no pytest needed); each prints its own count and exits
# non-zero on failure. This aggregates them and reports a grand total.
set -uo pipefail
cd "$(dirname "$0")"

SUITES=(
  "methods/test_weave.py"
  "methods/test_charter_invariants.py"
  "methods/test_lexicons.py"
  "methods/test_analyze.py"
  "methods/test_consistency.py"
  "methods/test_autorun.py"
  "cells/test_state_machines.py"
)

fail=0
for s in "${SUITES[@]}"; do
  dir="$(dirname "$s")"; file="$(basename "$s")"
  if ( cd "$dir" && python3 "$file" ); then :; else
    echo "FAILED: $s"; fail=1
  fi
done

if [ "$fail" -eq 0 ]; then
  echo "── kosatsu: ALL suites green ──"
else
  echo "── kosatsu: FAILURES above ──"; exit 1
fi
