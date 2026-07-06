#!/usr/bin/env bash
# saisei — clj/bb test suite (ADR-2607061800). Runs all cljc test namespaces via babashka
# from the repo root.
set -euo pipefail
cd "$(dirname "$0")/../.."
exec bb -e '(require (quote clojure.test) (quote saisei.tests.test-filing-plan) (quote saisei.tests.test-coverage))(let [r (apply clojure.test/run-tests (quote [saisei.tests.test-filing-plan saisei.tests.test-coverage]))](System/exit (if (zero? (+ (:fail r) (:error r))) 0 1)))'
