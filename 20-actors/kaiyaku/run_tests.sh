#!/usr/bin/env bash
# kaiyaku — clj/bb test suite (ADR-2606160842 py->clj port wave). Auto-wired into the fleet
# green-check; runs all cljc test namespaces via babashka from the repo root.
set -euo pipefail
cd "$(dirname "$0")/../.."
exec bb -e '(require (quote clojure.test) (quote kaiyaku.methods.test-datom-emit) (quote kaiyaku.tests.test-analyze) (quote kaiyaku.tests.test-handoff) (quote kaiyaku.tests.test-kotoba) (quote kaiyaku.tests.test-plan) (quote kaiyaku.tests.test-driver) (quote kaiyaku.tests.test-catalog))(let [r (apply clojure.test/run-tests (quote [kaiyaku.methods.test-datom-emit kaiyaku.tests.test-analyze kaiyaku.tests.test-handoff kaiyaku.tests.test-kotoba kaiyaku.tests.test-plan kaiyaku.tests.test-driver kaiyaku.tests.test-catalog]))](System/exit (if (zero? (+ (:fail r) (:error r))) 0 1)))'
