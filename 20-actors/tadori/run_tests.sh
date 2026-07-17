#!/usr/bin/env bash
# tadori 辿 — run the whole test suite with one command.
# Fully migrated to cljc (ADR-2606160842): the self-audit loop + threat-intel ingest gates
# all live in methods/*.cljc and tests/*.cljc. Was run via the root bb.edn `test:tadori`
# task; bb.edn was deleted (ADR-2607173000), so this now inlines that task's exact body
# directly (same pattern as credits/karakuri's own self-contained run_tests.sh).
set -uo pipefail
cd "$(dirname "$0")"

if ! command -v bb >/dev/null 2>&1; then
  echo "!! bb (babashka) not found — install it to run the tadori cljc suite" >&2
  exit 1
fi

if (cd "$(git rev-parse --show-toplevel)" && bb -e '(require (quote clojure.test) (quote tadori.tests.test-autorun) (quote tadori.tests.test-ingest) (quote tadori.tests.test-trace) (quote tadori.tests.test-risk) (quote tadori.tests.test-malak) (quote tadori.tests.test-ofac) (quote tadori.tests.test-malak-contract))(let [r (clojure.test/run-tests (quote tadori.tests.test-autorun) (quote tadori.tests.test-ingest) (quote tadori.tests.test-trace) (quote tadori.tests.test-risk) (quote tadori.tests.test-malak) (quote tadori.tests.test-ofac) (quote tadori.tests.test-malak-contract))](System/exit (if (zero? (+ (:fail r) (:error r))) 0 1)))'); then
  echo "── tadori: ALL suites green ──"
else
  echo "── tadori: FAILURES above ──"; exit 1
fi
