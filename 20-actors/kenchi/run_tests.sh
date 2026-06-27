#!/usr/bin/env bash
# kenchi 検地 — run the whole test suite with one command.
# Standalone-runnable tests (no repo pytest plugin needed); each exits non-zero on failure.
set -uo pipefail
cd "$(dirname "$0")"

SUITES=(
  "methods/test_charter_gates.py"
)

fail=0
for s in "${SUITES[@]}"; do
  dir="$(dirname "$s")"; file="$(basename "$s")"
  if ( cd "$dir" && python3 "$file" ); then :; else
    echo "FAILED: $s"; fail=1
  fi
done

if [ "$fail" -eq 0 ]; then
  echo "── kenchi: ALL suites green ──"
else
  echo "── kenchi: FAILURES above ──"; exit 1
fi
