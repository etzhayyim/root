#!/usr/bin/env bash
# kotodama — clj/bb test suite (py→cljc port wave).
# Tests:
#   - 13 cell R0 scaffold stubs (6 tadori + 7 tsukuroi) each raise ex-info on .solve
#   - kotoba.datom Datom-log engine smoke (already-ported, determinism check)
set -euo pipefail
cd "$(dirname "$0")/../.."
exec bb --classpath "20-actors:20-actors/kotodama/src:20-actors/kotodama/tests" \
  -e '(require (quote clojure.test) (quote kotodama.tests.test-cells) (quote kotodama.tests.test-datom))
      (let [r (clojure.test/run-tests (quote kotodama.tests.test-cells) (quote kotodama.tests.test-datom))]
        (System/exit (if (zero? (+ (:fail r) (:error r))) 0 1)))'
