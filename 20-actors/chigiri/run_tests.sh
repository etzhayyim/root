#!/usr/bin/env bash
# chigiri — charter-gate suite, bb/clj (ADR-2606160842 py→clj port wave; py pruned).
set -euo pipefail
cd "$(dirname "$0")/../.."
exec bb -e '(require (quote clojure.test) (quote chigiri.methods.test-charter-gates) (quote chigiri.methods.test-datom-kotoba))(let [r (apply clojure.test/run-tests (quote [chigiri.methods.test-charter-gates chigiri.methods.test-datom-kotoba]))](System/exit (if (zero? (+ (:fail r) (:error r))) 0 1)))'
