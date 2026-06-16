#!/usr/bin/env bash
# utsushie 写し絵 — run the whole test suite with one command.
# Tests are standalone-runnable (the repo pytest plugin env is broken); each prints its own
# count and exits non-zero on failure.
set -uo pipefail
cd "$(dirname "$0")"

SUITES=(
  "methods/test_render_plan.py"
)

fail=0
for s in "${SUITES[@]}"; do
  dir="$(dirname "$s")"; file="$(basename "$s")"
  if ( cd "$dir" && python3 "$file" ); then :; else
    echo "FAILED: $s"; fail=1
  fi
done

if [ "$fail" -eq 0 ]; then
  echo "── utsushie: ALL suites green ──"
else
  echo "── utsushie: FAILURES above ──"; exit 1
fi
