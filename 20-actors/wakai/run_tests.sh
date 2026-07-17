#!/usr/bin/env bash
# wakai 和会 — run the whole test suite with one command.
# The suites themselves ported py -> cljc (repo-wide convention). Was shelling out to
# the root bb.edn `test:wakai` task; bb.edn was deleted (ADR-2607173000), so this now
# inlines that task's exact body directly (same pattern as credits/karakuri's own
# self-contained run_tests.sh).
set -uo pipefail
cd "$(dirname "$0")/../.."

if bb -e '(require (quote clojure.test) (quote wakai.methods.test-pool) (quote wakai.methods.test-charter-gates))(let [r (clojure.test/run-tests (quote wakai.methods.test-pool) (quote wakai.methods.test-charter-gates))](System/exit (if (zero? (+ (:fail r) (:error r))) 0 1)))'; then
  echo "── wakai: ALL suites green ──"
else
  echo "── wakai: FAILURES above ──"; exit 1
fi
