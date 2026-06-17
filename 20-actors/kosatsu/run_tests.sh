#!/usr/bin/env bash
# kosatsu 高札 — bb/clj test suite (ADR-2606160842 py→clj port wave; Python pruned).
set -euo pipefail
cd "$(dirname "$0")/../.."
exec bb -e '(require (quote clojure.test) (quote kosatsu.cells.social-post.test-state-machine) (quote kosatsu.methods.test-analyze) (quote kosatsu.methods.test-autorun) (quote kosatsu.methods.test-charter-invariants) (quote kosatsu.methods.test-consistency) (quote kosatsu.methods.test-lexicons) (quote kosatsu.methods.test-weave))(let [r (clojure.test/run-tests (quote kosatsu.cells.social-post.test-state-machine) (quote kosatsu.methods.test-analyze) (quote kosatsu.methods.test-autorun) (quote kosatsu.methods.test-charter-invariants) (quote kosatsu.methods.test-consistency) (quote kosatsu.methods.test-lexicons) (quote kosatsu.methods.test-weave))](System/exit (if (zero? (+ (:fail r) (:error r))) 0 1)))'
