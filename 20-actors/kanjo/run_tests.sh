#!/usr/bin/env bash
# kanjo — clj/bb test suite (ADR-2606160842 py->clj port wave; Python pruned).
set -euo pipefail
cd "$(dirname "$0")/../.."
exec bb -e '(require (quote clojure.test) (quote kanjo.methods.test-autorun) (quote kanjo.tests.test-invariants) (quote kanjo.tests.test-kanjo))(let [r (apply clojure.test/run-tests (quote [kanjo.methods.test-autorun kanjo.tests.test-invariants kanjo.tests.test-kanjo]))](System/exit (if (zero? (+ (:fail r) (:error r))) 0 1)))'
