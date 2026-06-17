#!/usr/bin/env bash
# 朱 (ake) — run the whole test suite with one command.
# Tests are standalone-runnable (the repo pytest plugin env is broken); each prints its own
# count and exits non-zero on failure. This aggregates them and reports a grand total.
set -uo pipefail
cd "$(dirname "$0")"

SUITES=(
  "methods/test__edn.py"
  "methods/test_triage.py"
  "methods/test_revision.py"
  "methods/test_editwar.py"
  "methods/test_contributor.py"
  "methods/test_ingest.py"
  "methods/test_charter_invariants.py"
  "methods/test_analyze.py"
  "methods/test_lexicons.py"
  "methods/test_consistency.py"
  "cells/test_state_machines.py"
  "cells/test_membrane_flow.py"
)

fail=0
for s in "${SUITES[@]}"; do
  dir="$(dirname "$s")"; file="$(basename "$s")"
  if ( cd "$dir" && python3 "$file" ); then :; else
    echo "FAILED: $s"; fail=1
  fi
done

# Canonical Clojure (.cljc) suite — the .py files above mirror these; this EXECUTES the
# canonical path (proven green, not merely asserted to match Python). Skips if `bb` absent.
if ./run_tests_cljc.sh; then :; else
  echo "FAILED: canonical .cljc suite"; fail=1
fi

if [ "$fail" -eq 0 ]; then
  echo "── ake: ALL suites green (py mirror + canonical cljc) ──"
else
  echo "── ake: FAILURES above ──"; exit 1
fi
