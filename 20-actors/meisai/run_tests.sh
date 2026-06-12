#!/usr/bin/env bash
# meisai 明細 — run the whole test suite with one command.
# Tests are standalone-runnable; each prints its own count and exits non-zero on failure.
set -uo pipefail
cd "$(dirname "$0")"

SUITES=(
  "methods/test_ingest.py"
  "methods/test_autorun.py"
)

fail=0
for s in "${SUITES[@]}"; do
  dir="$(dirname "$s")"; file="$(basename "$s")"
  if ( cd "$dir" && python3 "$file" ); then :; else
    echo "FAILED: $s"; fail=1
  fi
done

if [ "$fail" -eq 0 ]; then
  echo "── meisai: ALL suites green ──"
else
  echo "── meisai: FAILURES above ──"; exit 1
fi
