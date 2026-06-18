#!/usr/bin/env bash
# organizer — clj/bb test suite (ADR-2606160842 py->clj port wave); wired into the fleet green-check.
set -euo pipefail
cd "$(dirname "$0")/../.."
exec bb -e '(require (quote clojure.test) (quote organizer.py.test-agent))(let [r (apply clojure.test/run-tests (quote [organizer.py.test-agent]))](System/exit (if (zero? (+ (:fail r) (:error r))) 0 1)))'
