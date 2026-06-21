#!/usr/bin/env bash
# watari — bb/clj test suite (ADR-2606160842 py→clj port wave; Python pruned).
set -euo pipefail
cd "$(dirname "$0")/../.."
exec bb -e '(require (quote clojure.test) (quote watari.methods.test-ingest) (quote watari.methods.test-analyze) (quote watari.methods.test-autorun) (quote watari.methods.test-charter-gates) )(let [r (clojure.test/run-tests (quote watari.methods.test-ingest) (quote watari.methods.test-analyze) (quote watari.methods.test-autorun) (quote watari.methods.test-charter-gates) )](System/exit (if (zero? (+ (:fail r) (:error r))) 0 1)))'
