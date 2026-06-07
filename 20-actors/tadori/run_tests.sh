#!/usr/bin/env bash
# tadori 辿 — run the whole test suite with one command.
# Tests are stdlib unittest (the repo pytest plugin env is broken); each exits non-zero on
# failure. This aggregates them and reports a grand total.
set -uo pipefail
cd "$(dirname "$0")"

SUITES=(
  "kotoba/test_ingest_threat_intel.py"
  "kotoba/test_invariants.py"
)

fail=0
for s in "${SUITES[@]}"; do
  if python3 "$s"; then :; else
    echo "FAILED: $s"; fail=1
  fi
done

if [ "$fail" -eq 0 ]; then
  echo "── tadori: ALL suites green ──"
else
  echo "── tadori: FAILURES above ──"; exit 1
fi
