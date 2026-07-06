#!/usr/bin/env bash
set -uo pipefail
cd "$(dirname "$0")/../.."   # → repo root (classpath base = 20-actors)

SUITES=(
  "20-actors/hirameki/methods/test_hirameki_edn.cljc"
  "20-actors/hirameki/methods/test_analyze.cljc"
  "20-actors/hirameki/methods/test_cid.cljc"
  "20-actors/hirameki/methods/test_dataset.cljc"
  "20-actors/hirameki/methods/test_ingest.cljc"
  "20-actors/hirameki/methods/test_kotoba.cljc"
  "20-actors/hirameki/methods/test_autorun.cljc"
)

fail=0
for s in "${SUITES[@]}"; do
  echo "== $s =="
  # No explicit --classpath: bb.edn's own :paths/:deps must resolve (test_cid.cljc needs the
  # multiformats-clj git dep declared there; an explicit --classpath override bypasses bb.edn
  # entirely and drops it, breaking that suite even though 20-actors is already in :paths).
  if bb "$s"; then :; else echo "FAILED: $s"; fail=1; fi
done
exit $fail
