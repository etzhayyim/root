#!/usr/bin/env bash
# ossekai — clj/bb test suite (ADR-2606160842). charter-gates + the ported agent suite (cljc) are
# the AUTHORITATIVE gate; the legacy py/test_agent.py is superseded by ossekai.py.test-agent.
set -euo pipefail
cd "$(dirname "$0")/../.."
exec bb -e '(require (quote clojure.test) (quote ossekai.methods.test-charter-gates) (quote ossekai.py.test-agent))(let [r (apply clojure.test/run-tests (quote [ossekai.methods.test-charter-gates ossekai.py.test-agent]))](System/exit (if (zero? (+ (:fail r) (:error r))) 0 1)))'
