#!/usr/bin/env bash
# mitooshi 見通し — run the whole test suite with one command.
# Tests are standalone-runnable (the repo pytest plugin env is broken); each prints its own
# count and exits non-zero on failure. This aggregates them and reports a grand total.
set -uo pipefail
cd "$(dirname "$0")"

SUITES=(
  "methods/test_score.py"
  "methods/test_analyze.py"
  "methods/test_ingest.py"
  "methods/test_bridge.py"
  "methods/test_persist.py"
  "methods/test_horizon.py"
  "cells/test_state_machines.py"
  "test_learning_loop.py"
  "test_continual_learning.py"
)

fail=0
for s in "${SUITES[@]}"; do
  dir="$(dirname "$s")"; file="$(basename "$s")"
  if ( cd "$dir" && python3 "$file" ); then :; else
    echo "FAILED: $s"; fail=1
  fi
done

if [ "$fail" -eq 0 ]; then
  echo "── mitooshi: ALL suites green ──"
else
  echo "── mitooshi: FAILURES above ──"; exit 1
fi
