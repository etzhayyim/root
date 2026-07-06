#!/usr/bin/env bash
# niyaku — clj/bb test suite (ADR-2606160842 py->clj port wave). Auto-wired into the fleet
# green-check; runs all cljc test namespaces via babashka from the repo root.
set -euo pipefail
cd "$(dirname "$0")/../.."
exec bb -e '(require (quote clojure.test) (quote niyaku.cells.test-state-machine) (quote niyaku.methods.test-agv-transfer) (quote niyaku.methods.test-crane-dynamics) (quote niyaku.methods.test-isaac-sway-sim) (quote niyaku.methods.test-stow-plan) (quote niyaku.methods.test-terminal-cycle) (quote niyaku.methods.test-agv-transfer-parity) (quote niyaku.methods.test-crane-dynamics-parity) (quote niyaku.methods.test-stow-plan-parity) (quote niyaku.methods.test-terminal-cycle-parity))(let [r (apply clojure.test/run-tests (quote [niyaku.cells.test-state-machine niyaku.methods.test-agv-transfer niyaku.methods.test-crane-dynamics niyaku.methods.test-isaac-sway-sim niyaku.methods.test-stow-plan niyaku.methods.test-terminal-cycle niyaku.methods.test-agv-transfer-parity niyaku.methods.test-crane-dynamics-parity niyaku.methods.test-stow-plan-parity niyaku.methods.test-terminal-cycle-parity]))](System/exit (if (zero? (+ (:fail r) (:error r))) 0 1)))'
