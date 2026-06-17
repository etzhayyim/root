#!/usr/bin/env bash
# tsukuru 作 — bb/clj test suite (ADR-2606160842 py->clj port wave; py agent pruned).
set -euo pipefail
cd "$(dirname "$0")/../.."
exec bb -e '(require (quote clojure.test) (quote tsukuru.py.test-agent))(let [r (clojure.test/run-tests (quote tsukuru.py.test-agent))](System/exit (if (zero? (+ (:fail r) (:error r))) 0 1)))'
