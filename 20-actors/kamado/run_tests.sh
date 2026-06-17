#!/usr/bin/env bash
# kamado — clj/bb test suite (ADR-2606160842 py->clj port wave). Auto-wired into the fleet
# green-check; runs all cljc test namespaces via babashka from the repo root.
set -euo pipefail
cd "$(dirname "$0")/../.."
exec bb -e '(require (quote clojure.test) (quote kamado.methods.test-ingest) (quote kamado.methods.test-kamado))(let [r (apply clojure.test/run-tests (quote [kamado.methods.test-ingest kamado.methods.test-kamado]))](System/exit (if (zero? (+ (:fail r) (:error r))) 0 1)))'
