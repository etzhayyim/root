#!/usr/bin/env bash
# hoshimori — clj/bb test suite (ADR-2606160842 py->clj port wave). Auto-wired into the fleet
# green-check; runs all cljc test namespaces via babashka from the repo root.
set -euo pipefail
cd "$(dirname "$0")/../.."
exec bb -e '(require (quote clojure.test) (quote hoshimori.methods.test-datom-emit) (quote hoshimori.tests.test-analyze) (quote hoshimori.tests.test-coverage))(let [r (apply clojure.test/run-tests (quote [hoshimori.methods.test-datom-emit hoshimori.tests.test-analyze hoshimori.tests.test-coverage]))](System/exit (if (zero? (+ (:fail r) (:error r))) 0 1)))'
