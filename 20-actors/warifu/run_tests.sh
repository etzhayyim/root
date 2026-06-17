#!/usr/bin/env bash
# warifu — clj/bb test suite (ADR-2606160842 py->clj port wave). Auto-wired into the fleet
# green-check; runs all cljc test namespaces via babashka from the repo root.
set -euo pipefail
cd "$(dirname "$0")/../.."
exec bb -e '(require (quote clojure.test) (quote warifu.cells.test-refund))(let [r (apply clojure.test/run-tests (quote [warifu.cells.test-refund]))](System/exit (if (zero? (+ (:fail r) (:error r))) 0 1)))'
