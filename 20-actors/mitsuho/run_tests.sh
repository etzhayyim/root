#!/usr/bin/env bash
# mitsuho 瑞穂 — run the whole test suite with one command.
set -uo pipefail
cd "$(dirname "$0")"
SUITES=( "methods/test_charter_gates.py" "py/test_agent.py" )
fail=0
for s in "${SUITES[@]}"; do
  [ -f "$s" ] || continue
  dir="$(dirname "$s")"; file="$(basename "$s")"
  if ( cd "$dir" && python3 "$file" ); then :; else echo "FAILED: $s"; fail=1; fi
done
[ "$fail" -eq 0 ] && echo "── mitsuho: ALL suites green ──" || { echo "── mitsuho: FAILURES ──"; exit 1; }
