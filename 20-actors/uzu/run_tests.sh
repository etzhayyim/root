#!/usr/bin/env bash
# uzu 渦 — clj-native test runner (babashka).
set -uo pipefail
cd "$(dirname "$0")/../.."   # → repo root (classpath base = 20-actors)
SUITES=(
  "20-actors/uzu/methods/test_model.cljc"
  "20-actors/uzu/methods/test_ledger.cljc"
  "20-actors/uzu/methods/test_metabolism.cljc"
  "20-actors/uzu/methods/test_measure.cljc"
  "20-actors/uzu/methods/test_validate.cljc"
  "20-actors/uzu/methods/test_lexicons.cljc"
  "20-actors/uzu/methods/test_digest.cljc"
  "20-actors/uzu/methods/test_kotoba.cljc"
  "20-actors/uzu/methods/test_autorun.cljc"
  "20-actors/uzu/methods/test_viz.cljc"
)
fail=0
for s in "${SUITES[@]}"; do
  echo "== $s =="
  if bb --classpath 20-actors "$s"; then :; else echo "FAILED: $s"; fail=1; fi
done
exit $fail
