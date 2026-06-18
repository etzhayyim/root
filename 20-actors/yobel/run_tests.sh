#!/usr/bin/env bash
# yobel — clj/bb test suite (ADR-2606160842 py->clj port wave). Auto-wired into the fleet
# green-check; runs all cljc test namespaces via babashka from the repo root.
set -euo pipefail
cd "$(dirname "$0")/../.."
exec bb -e '(require (quote clojure.test) (quote yobel.cells.audit-witness.tests.test-cell) (quote yobel.cells.creditor-enrollment.tests.test-cell) (quote yobel.cells.debtor-enrollment.tests.test-cell) (quote yobel.cells.release-settlement.tests.test-cell) (quote yobel.cells.rite-declaration.tests.test-cell) (quote yobel.tests.test-orchestrator))(let [r (apply clojure.test/run-tests (quote [yobel.cells.audit-witness.tests.test-cell yobel.cells.creditor-enrollment.tests.test-cell yobel.cells.debtor-enrollment.tests.test-cell yobel.cells.release-settlement.tests.test-cell yobel.cells.rite-declaration.tests.test-cell yobel.tests.test-orchestrator]))](System/exit (if (zero? (+ (:fail r) (:error r))) 0 1)))'
