#!/usr/bin/env bash
# cell-runner (bb lite-runner) — clj/bb test suite. ADR-2606221900 runtime cutover.
# Pins the byte-parity ops commit-DAG + cron + cells.edn load + native cljc fire.
set -uo pipefail
cd "$(dirname "$0")"
exec bb --classpath ".:test_fixtures" -e '(require (quote clojure.test) (quote test-lite-runner))
  (let [r (clojure.test/run-tests (quote test-lite-runner))]
    (System/exit (if (zero? (+ (:fail r) (:error r))) 0 1)))'
