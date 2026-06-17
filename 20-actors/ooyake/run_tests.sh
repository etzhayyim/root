#!/usr/bin/env bash
# ooyake — charter-gate suite (bb/clj) + remaining standalone cell py suites (pending port), ADR-2606160842.
# (Additional audits live under 70-tools/scripts/audit/test_ooyake_*.py — run via the repo audit pass.)
set -euo pipefail
cd "$(dirname "$0")/../.."
exec bb -e '(require (quote clojure.test) (quote [babashka.process :as p]) (quote ooyake.methods.test-charter-gates))
(let [r (clojure.test/run-tests (quote ooyake.methods.test-charter-gates))
      cells [["cells/reconcile" "test_reconcile_cell.py"]
             ["cells/reconcile" "test_seed_integrity.py"]
             ["cells/world_model" "test_world_model_cell.py"]
             ["cells/world_model" "test_consistency.py"]]
      pys (mapv (fn [[d f]] (:exit (p/shell {:dir (str "20-actors/ooyake/" d) :continue true} "python3" f))) cells)]
  (println "== ooyake cell py exits:" pys "==")
  (System/exit (if (and (zero? (+ (:fail r) (:error r))) (every? zero? pys)) 0 1)))'
