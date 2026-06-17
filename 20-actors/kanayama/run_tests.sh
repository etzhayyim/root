#!/usr/bin/env bash
# kanayama — charter-gate suite, bb/clj (ADR-2606160842; py pruned).
set -euo pipefail
cd "$(dirname "$0")/../.."
exec bb -e '(require (quote clojure.test) (quote kanayama.methods.test-charter-gates) (quote kanayama.py.test-agent) (quote kanayama.cells.intake-qa.test-state-machine) (quote kanayama.cells.decoating-separation.test-state-machine))(let [r (clojure.test/run-tests (quote kanayama.methods.test-charter-gates) (quote kanayama.py.test-agent) (quote kanayama.cells.intake-qa.test-state-machine) (quote kanayama.cells.decoating-separation.test-state-machine))](System/exit (if (zero? (+ (:fail r) (:error r))) 0 1)))'
