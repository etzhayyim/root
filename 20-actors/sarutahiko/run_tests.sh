#!/usr/bin/env bash
# sarutahiko — charter-gate suite, bb/clj (ADR-2606160842; py pruned).
set -euo pipefail
cd "$(dirname "$0")/../.."
exec bb -e '(require (quote clojure.test) (quote sarutahiko.methods.test-charter-gates))(let [r (clojure.test/run-tests (quote sarutahiko.methods.test-charter-gates))](System/exit (if (zero? (+ (:fail r) (:error r))) 0 1)))'
