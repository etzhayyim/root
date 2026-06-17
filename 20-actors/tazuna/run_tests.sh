#!/usr/bin/env bash
# tazuna — clj/bb test suite (ADR-2606160842 py->clj port wave). Auto-wired into the fleet
# green-check; runs all cljc test namespaces via babashka from the repo root.
set -euo pipefail
cd "$(dirname "$0")/../.."
exec bb -e '(require (quote clojure.test) (quote tazuna.cells.teleop-session.test-state-machine) (quote tazuna.methods.test-teleop-safety))(let [r (apply clojure.test/run-tests (quote [tazuna.cells.teleop-session.test-state-machine tazuna.methods.test-teleop-safety]))](System/exit (if (zero? (+ (:fail r) (:error r))) 0 1)))'
