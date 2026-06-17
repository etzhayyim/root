#!/usr/bin/env bash
# todoke — clj/bb test suite (ADR-2606160842 py->clj port wave). Auto-wired into the fleet
# green-check; runs all cljc test namespaces via babashka from the repo root.
set -euo pipefail
cd "$(dirname "$0")/../.."
exec bb -e '(require (quote clojure.test) (quote todoke.cells.handoff-proof.test-state-machine) (quote todoke.cells.route-sequencing.test-state-machine) (quote todoke.methods.test-last-mile))(let [r (apply clojure.test/run-tests (quote [todoke.cells.handoff-proof.test-state-machine todoke.cells.route-sequencing.test-state-machine todoke.methods.test-last-mile]))](System/exit (if (zero? (+ (:fail r) (:error r))) 0 1)))'
