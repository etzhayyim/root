#!/usr/bin/env bash
# hagukumi — charter-gate suite, bb/clj (ADR-2606160842 py→clj port wave; py pruned).
set -euo pipefail
cd "$(dirname "$0")/../.."
exec bb -e '(require (quote clojure.test) (quote hagukumi.methods.test-charter-gates))(let [r (clojure.test/run-tests (quote hagukumi.methods.test-charter-gates))](System/exit (if (zero? (+ (:fail r) (:error r))) 0 1)))'
