#!/usr/bin/env bash
# kasa 嵩 — run the whole test suite with one command.
# Tests are standalone-runnable (the repo pytest plugin env is broken); each prints its own
# count and exits non-zero on failure. This aggregates them and reports a grand total.
set -uo pipefail
cd "$(dirname "$0")"

SUITES=(
  "tests/test_kasa.py"
  "tests/test_invariants.py"
)

fail=0
for s in "${SUITES[@]}"; do
  if python3 "$s"; then :; else
    echo "FAILED: $s"; fail=1
  fi
done

if [ "$fail" -eq 0 ]; then
  echo "── kasa: ALL suites green ──"
else
  echo "── kasa: FAILURES above ──"; exit 1
fi
