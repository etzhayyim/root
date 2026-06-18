#!/usr/bin/env bash
# ainori — clj/bb test suite (ADR-2606160842 py->clj port wave). Auto-wired into the fleet
# green-check; runs all cljc test namespaces via babashka from the repo root.
set -euo pipefail
cd "$(dirname "$0")/../.."
exec bb -e '(require (quote clojure.test) (quote ainori.methods.test-pooled-route))(let [r (apply clojure.test/run-tests (quote [ainori.methods.test-pooled-route]))](System/exit (if (zero? (+ (:fail r) (:error r))) 0 1)))'
