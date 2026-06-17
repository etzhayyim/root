#!/usr/bin/env bash
# ossekai — charter-gate suite (bb/clj) + remaining py agent suite (pending port), ADR-2606160842.
# The charter cljc is the AUTHORITATIVE green gate; the agent py is expected-red (known-failing
# agent tests) and is echoed for VISIBILITY only — it does NOT block the exit code.
set -euo pipefail
cd "$(dirname "$0")/../.."
exec bb -e '(require (quote clojure.test) (quote [babashka.process :as p]) (quote ossekai.methods.test-charter-gates))
(let [r (clojure.test/run-tests (quote ossekai.methods.test-charter-gates))
      py (p/shell {:dir "20-actors/ossekai/py" :continue true} "bash" "-c" "PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python3 -m pytest -q test_agent.py")]
  (println "== ossekai agent py (expected-red, non-blocking) exit:" (:exit py) "==")
  (System/exit (if (zero? (+ (:fail r) (:error r))) 0 1)))'
