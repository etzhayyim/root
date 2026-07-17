#!/usr/bin/env bash
# kazaori — full suite (emergency engine + charter-gates), bb/clj (ADR-2606160842; py pruned).
# Self-contained: requires the namespaces directly rather than the removed bb.edn
# `test:kazaori` task (bb.edn deleted by ADR-2607173000; this inlines that task's
# exact body — same pattern as credits/karakuri/shomei/suji's own run_tests.sh).
set -euo pipefail
cd "$(dirname "$0")/../.."
exec bb -e '(require (quote clojure.test) (quote kazaori.methods.test-emergency) (quote kazaori.methods.test-charter-gates))(let [r (clojure.test/run-tests (quote kazaori.methods.test-emergency) (quote kazaori.methods.test-charter-gates))](System/exit (if (zero? (+ (:fail r) (:error r))) 0 1)))'
