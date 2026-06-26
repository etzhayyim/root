#!/usr/bin/env bash
# hibiki 響 — clj/bb test suite.
# charter-gates (lexicon conformance) is the AUTHORITATIVE gate that pins the 説得力 knife-edge;
# present-plan exercises the offline builder. Both are auto-discovered by `bb run test:actors`
# (ADR-2606131500) — this script is the standalone targeted runner.
set -uo pipefail
ROOT="$(cd "$(dirname "$0")" && pwd)"
REPO_ROOT="$(cd "$ROOT/../.." && pwd)"
BB_CP="20-actors"
rc=0

run_cljc() {
  local ns="$1"
  echo "==> hibiki [cljc] $ns"
  ( cd "$REPO_ROOT" && bb -cp "$BB_CP" -e "(require (quote clojure.test) (quote $ns))(let [r (clojure.test/run-tests (quote $ns))](System/exit (if (zero? (+ (:fail r) (:error r))) 0 1)))" ) || rc=1
}

run_cljc "hibiki.methods.test-charter-gates"
run_cljc "hibiki.methods.test-present-plan"

if [[ $rc -eq 0 ]]; then
  echo "==> hibiki: ALL GREEN"
else
  echo "==> hibiki: FAILURES (rc=$rc)" >&2
fi
exit $rc
