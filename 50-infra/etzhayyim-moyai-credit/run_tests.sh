#!/usr/bin/env bash
# moyai 舫い — run the whole test suite with one command.
# Each suite is standalone-runnable (stdlib only, no pytest), prints its own count, and
# exits non-zero on failure. This aggregates them and reports a grand total.
set -uo pipefail
cd "$(dirname "$0")/methods"

SUITES=(
  "test_ledger.py"
  "test_proof_of_contribution.py"
  "test_fair_share.py"
  "test_lexicons.py"
  "test_charter_invariants.py"
  "test_analyze.py"
)

fail=0
for s in "${SUITES[@]}"; do
  if ! python3 "$s"; then
    fail=1
  fi
done

echo "---"
if [ "$fail" -eq 0 ]; then
  echo "moyai: ALL SUITES GREEN"
else
  echo "moyai: FAILURES ABOVE"
fi
exit "$fail"
