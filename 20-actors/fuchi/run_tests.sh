#!/usr/bin/env bash
# 扶持 (fuchi) — run the whole test suite with one command.
# Tests are standalone-runnable (the repo pytest plugin env is broken); each prints its own
# count and exits non-zero on failure. This aggregates them and reports a grand total.
set -uo pipefail
cd "$(dirname "$0")"

SUITES=(
  "methods/test_allocate.py"
  "methods/test_route.py"
  "methods/test_provision.py"
  "methods/test_vote.py"
  "methods/test_book.py"
  "methods/test_couple.py"
  "methods/test_analyze.py"
  "methods/test_charter_invariants.py"
  "methods/test_lexicons.py"
  "methods/test_consistency.py"
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
  echo "── fuchi: ALL suites green ──"
else
  echo "── fuchi: FAILURES above ──"; exit 1
fi
