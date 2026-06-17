#!/usr/bin/env bash
# kasa 嵩 — bb/clj test suite (ADR-2606160842 py→clj port wave; Python pruned). ADR-2606072000.
set -euo pipefail
cd "$(dirname "$0")/../.."
exec bb -e '(require (quote clojure.test) (quote kasa.tests.test-invariants) (quote kasa.tests.test-kasa))(let [r (clojure.test/run-tests (quote kasa.tests.test-invariants) (quote kasa.tests.test-kasa))](System/exit (if (zero? (+ (:fail r) (:error r))) 0 1)))'
