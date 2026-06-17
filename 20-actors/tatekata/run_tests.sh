#!/usr/bin/env bash
# tatekata — clj/bb test suite (ADR-2606160842 py->clj port wave); ALL test namespaces, fleet green-check.
set -euo pipefail
cd "$(dirname "$0")/../.."
exec bb -e '(require (quote clojure.test) (quote tatekata.cells.mep-installation.test-cell) (quote tatekata.methods.test-charter-gates))(let [r (apply clojure.test/run-tests (quote [tatekata.cells.mep-installation.test-cell tatekata.methods.test-charter-gates]))](System/exit (if (zero? (+ (:fail r) (:error r))) 0 1)))'
