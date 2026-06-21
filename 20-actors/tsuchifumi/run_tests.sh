#!/usr/bin/env bash
# tsuchifumi 土踏み — clj-native test runner (babashka).
set -uo pipefail
cd "$(dirname "$0")/../.."   # → repo root (classpath base = 20-actors)
SUITES=(
  "20-actors/tsuchifumi/methods/test_ontology.cljc"
  "20-actors/tsuchifumi/methods/test_analyze.cljc"
  "20-actors/tsuchifumi/methods/test_sysdyn.cljc"
  "20-actors/tsuchifumi/methods/test_risk.cljc"
  "20-actors/tsuchifumi/methods/test_coscientist.cljc"
  "20-actors/tsuchifumi/methods/test_social.cljc"
  "20-actors/tsuchifumi/methods/test_kotoba.cljc"
  "20-actors/tsuchifumi/methods/test_autorun.cljc"
  "20-actors/tsuchifumi/methods/test_viz.cljc"
)
fail=0
for s in "${SUITES[@]}"; do
  echo "== $s =="
  if bb --classpath 20-actors "$s"; then :; else echo "FAILED: $s"; fail=1; fi
done
exit $fail
