#!/usr/bin/env bash
# junkan 循環 — clj/bb test suite (governance-asymmetry substrate + charter gates).
# Wired into the fleet green-check.
set -uo pipefail
cd "$(dirname "$0")/../.."   # → repo root (classpath base = 20-actors)
NSES=(
  junkan.methods.test-junkan-edn
  junkan.methods.test-analyze
  junkan.methods.test-demography
  junkan.methods.test-kotoba
  junkan.methods.test-autorun
  junkan.methods.test-query
  junkan.methods.test-validate
  junkan.methods.test-scorecard
  junkan.methods.test-history
  junkan.methods.test-charter-gates
)
joined=$(printf "(quote %s) " "${NSES[@]}")
exec bb --classpath 20-actors -e "
(apply require [${joined}])
(let [r (clojure.test/run-tests ${joined})]
  (System/exit (if (zero? (+ (:fail r) (:error r))) 0 1)))"
