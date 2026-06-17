#!/usr/bin/env bash
# hikari — clj/bb test suite (ADR-2606160842 py->clj port wave); ALL test namespaces, fleet green-check.
set -euo pipefail
cd "$(dirname "$0")/../.."
exec bb -e '(require (quote clojure.test) (quote hikari.methods.test-charter-gates) (quote hikari.methods.test-microgrid) (quote hikari.methods.test-panel-install))(let [r (apply clojure.test/run-tests (quote [hikari.methods.test-charter-gates hikari.methods.test-microgrid hikari.methods.test-panel-install]))](System/exit (if (zero? (+ (:fail r) (:error r))) 0 1)))'
