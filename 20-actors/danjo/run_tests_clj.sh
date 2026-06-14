#!/usr/bin/env bash
# danjo 弾正 — Clojure test suites (revenue ledger). Runs under bb (fast) or clojure (JVM).
# Each suite prints its own count and exits non-zero on failure; this aggregates.
set -uo pipefail
cd "$(dirname "$0")/methods"

RUNNER="${CLJ_RUNNER:-bb}"   # CLJ_RUNNER=clojure ./run_tests_clj.sh  to use the JVM
command -v "$RUNNER" >/dev/null 2>&1 || { echo "runner '$RUNNER' not found"; exit 127; }

SUITES=( "revenue-ledger-suite/test_revenue_ledger.clj" "revenue-ledger-suite/test_ingest.clj" "revenue-ledger-suite/test_discrepancy.clj" "revenue-ledger-suite/test_taxes.clj" "revenue-ledger-suite/test_transfers.clj" "revenue-ledger-suite/test_org_actor.clj" "revenue-ledger-suite/test_coverage.clj" "revenue-ledger-suite/test_lexicon.clj" "revenue-ledger-suite/test_maturity.clj" "revenue-ledger-suite/test_cofog_xcheck.clj" "revenue-ledger-suite/test_autorun.clj" "revenue-ledger-suite/test_freshness.clj" "revenue-ledger-suite/test_honesty_adversarial.clj" "revenue-ledger-suite/test_kotoba_bridge.clj" )

fail=0
for s in "${SUITES[@]}"; do
  if [ "$RUNNER" = "clojure" ]; then RUN=( clojure -M "$s" ); else RUN=( "$RUNNER" "$s" ); fi
  if "${RUN[@]}"; then :; else echo "FAILED: $s"; fail=1; fi
done

if [ "$fail" -eq 0 ]; then echo "── danjo clj: ALL suites green ──"; else echo "── danjo clj: FAILURES above ──"; exit 1; fi
