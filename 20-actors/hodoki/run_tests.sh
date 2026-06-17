#!/usr/bin/env bash
# hodoki — charter-gate suite, bb/clj (ADR-2606160842; py pruned).
set -euo pipefail
cd "$(dirname "$0")/../.."
exec bb -e '(require (quote clojure.test) (quote hodoki.methods.test-charter-gates) (quote hodoki.py.test-agent))(let [r (clojure.test/run-tests (quote hodoki.methods.test-charter-gates) (quote hodoki.py.test-agent))](System/exit (if (zero? (+ (:fail r) (:error r))) 0 1)))'
