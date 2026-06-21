#!/usr/bin/env bash
# tsubasa 翼 — clj-native test runner (babashka). ADR-2606072800.
# Covers the live query handlers (py->clj port) + the R2 maturity layer
# (analyze / kotoba commit-DAG / autorun heartbeat / seed integrity).
set -uo pipefail
cd "$(dirname "$0")/../.."   # → repo root (classpath base = 20-actors)

SUITES=(
  "20-actors/tsubasa/methods/test_analyze.cljc"
  "20-actors/tsubasa/methods/test_kotoba.cljc"
  "20-actors/tsubasa/methods/test_autorun.cljc"
  "20-actors/tsubasa/methods/test_seed_integrity.cljc"
  "20-actors/tsubasa/methods/test_ingest.cljc"
  "20-actors/tsubasa/methods/test_digest.cljc"
)

fail=0
for s in "${SUITES[@]}"; do
  echo "== $s =="
  if bb --classpath 20-actors "$s"; then :; else echo "FAILED: $s"; fail=1; fi
done

# Live query handlers (agent.cljc): the py->clj port suite (shared ns name).
echo "== 20-actors/tsubasa/py/test_agent (handlers) =="
if bb --classpath 20-actors -e '(require (quote clojure.test) (quote tsubasa.py.test-agent))(let [r (apply clojure.test/run-tests (quote [tsubasa.py.test-agent]))](System/exit (if (zero? (+ (:fail r) (:error r))) 0 1)))'; then :; else echo "FAILED: test_agent"; fail=1; fi

exit $fail
