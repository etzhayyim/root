#!/usr/bin/env bash
# kafun 花粉 — clj-native test runner (babashka).
set -uo pipefail
cd "$(dirname "$0")/../.."   # → repo root (classpath base = 20-actors)
SUITES=(
  "20-actors/kafun/methods/test_kafun_edn.cljc"
  "20-actors/kafun/methods/test_remediate.cljc"
  "20-actors/kafun/methods/test_kotoba.cljc"
  "20-actors/kafun/methods/test_autorun.cljc"
)
fail=0
for s in "${SUITES[@]}"; do
  echo "== $s =="
  if bb --classpath 20-actors "$s"; then :; else echo "FAILED: $s"; fail=1; fi
done
exit $fail
