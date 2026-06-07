#!/usr/bin/env bash
# 証明 (shomei) — run the whole test suite with one command.
# Tests are standalone (no pytest); each prints its own count and exits non-zero on failure.
set -uo pipefail
cd "$(dirname "$0")"

fail=0
for s in \
  "methods/test_factors.py" \
  "methods/test_claims.py" \
  "methods/test_verify.py" \
  "methods/test_aggregate.py" \
  "methods/test_revoke.py" \
  "methods/test_lexicons.py" \
  "methods/test_charter_invariants.py" \
  "methods/test_analyze.py" \
  "cells/test_cell_scaffolds.py" ; do
  dir="$(dirname "$s")"; file="$(basename "$s")"
  if ( cd "$dir" && python3 "$file" ); then :; else
    echo "FAILED: $s"; fail=1
  fi
done

if [ "$fail" -eq 0 ]; then
  echo "── shomei: ALL suites green ──"
else
  echo "── shomei: FAILURES above ──"; exit 1
fi
