#!/usr/bin/env bash
# ossekai — clj/bb test suite (ADR-2606160842).
# charter-gates (lexicon conformance) + the ported agent suite (cljc) are
# the AUTHORITATIVE gate; the legacy py/test_agent.py is superseded by
# ossekai.methods.test-agent (methods/ canonical) and ossekai.py.test-agent (py/ twin).
set -uo pipefail
ROOT="$(cd "$(dirname "$0")" && pwd)"
REPO_ROOT="$(cd "$ROOT/../.." && pwd)"

BB_CP="20-actors"
rc=0

run_cljc() {
  local ns="$1"
  echo "==> ossekai [cljc] $ns"
  ( cd "$REPO_ROOT" && bb -cp "$BB_CP" -e "(require (quote clojure.test) (quote $ns))(let [r (clojure.test/run-tests (quote $ns))](System/exit (if (zero? (+ (:fail r) (:error r))) 0 1)))" ) || rc=1
}

run_cljc "ossekai.methods.test-charter-gates"
run_cljc "ossekai.methods.test-agent"
run_cljc "ossekai.py.test-agent"

if [[ $rc -eq 0 ]]; then
  echo "==> ossekai: ALL GREEN"
else
  echo "==> ossekai: FAILURES (rc=$rc)" >&2
fi
exit $rc
