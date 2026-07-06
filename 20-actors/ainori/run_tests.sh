#!/usr/bin/env bash
# ainori — test suite (ADR-2606160842 py->clj port wave). Auto-wired into the fleet green-check.
# Runs BOTH the cljc route suite AND the py agent suite (matching + cost-share + settlement
# gates G5/G10 — the no-auto-execute / member-signed-capability guards, FINDING 260617).
set -uo pipefail
here="$(dirname "$0")"
fail=0

# cljc route suite (todoke route-core parity) — bb from the repo root (uses bb.edn paths)
( cd "$here/../.." && bb -e '(require (quote clojure.test) (quote ainori.methods.test-pooled-route))(let [r (apply clojure.test/run-tests (quote [ainori.methods.test-pooled-route]))](System/exit (if (zero? (+ (:fail r) (:error r))) 0 1)))' ) || fail=1

# cljc agent suite (methods/agent.cljc port: safety-envelope + cost-share + match-pool + settlement)
( cd "$here/../.." && bb -e '(require (quote clojure.test) (quote ainori.methods.test-agent))(let [r (apply clojure.test/run-tests (quote [ainori.methods.test-agent]))](System/exit (if (zero? (+ (:fail r) (:error r))) 0 1)))' ) || fail=1

# py.agent LIVE parity suite (py/test_agent_parity.clj — python3 subprocess vs the clj port)
( cd "$here/../.." && bb -e '(require (quote clojure.test) (quote ainori.py.test-agent-parity))(let [r (apply clojure.test/run-tests (quote [ainori.py.test-agent-parity]))](System/exit (if (zero? (+ (:fail r) (:error r))) 0 1)))' ) || fail=1

[ "$fail" -eq 0 ] && echo "── ainori: ALL suites green ──" || { echo "── ainori: FAILURES above ──"; exit 1; }
