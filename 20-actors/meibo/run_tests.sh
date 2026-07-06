#!/usr/bin/env bash
# meibo — clj/bb test suite (ADR-2607062200). Runs all cljc test namespaces via
# babashka from the repo root.
set -euo pipefail
cd "$(dirname "$0")/../.."
exec bb -e '(require (quote clojure.test) (quote meibo.tests.test-directory) (quote meibo.tests.test-coverage))(let [r (apply clojure.test/run-tests (quote [meibo.tests.test-directory meibo.tests.test-coverage]))](System/exit (if (zero? (+ (:fail r) (:error r))) 0 1)))'
