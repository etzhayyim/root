#!/usr/bin/env bash
# hotaru — clj/bb test suite (ADR-2606160842 py->clj port wave). Auto-wired into the fleet
# green-check; runs all cljc test namespaces via babashka from the repo root.
set -euo pipefail
cd "$(dirname "$0")/../.."
exec bb -e '(require (quote clojure.test) (quote hotaru.cells.commons-readiness.test-state-machine) (quote hotaru.cells.test-state-machine) (quote hotaru.methods.test-analyze))(let [r (apply clojure.test/run-tests (quote [hotaru.cells.commons-readiness.test-state-machine hotaru.cells.test-state-machine hotaru.methods.test-analyze]))](System/exit (if (zero? (+ (:fail r) (:error r))) 0 1)))'
