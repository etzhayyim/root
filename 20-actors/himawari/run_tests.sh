#!/usr/bin/env bash
# himawari — clj/bb test suite (ADR-2606021200 py→clj port wave); wired into the fleet
# green-check. Runs all cljc test namespaces via babashka from the repo root (for the
# :paths config in bb.edn). Covers 3 ported cells:
# - cell_process (cell process line + flash IV test, G3 high-GWP abatement gate)
# - ingot_wafer (ingot growth + wafer slicing, G4 renewable-only + G5 kerf recovery)
# - panel_loading (積込 robot cycle, G7 labor-liberation + G12 internal-only gates)
#
# 4 cells deferred to next port wave (see BLOCKER.md files):
# - module_assembly (cryptographic + kotoba query integration)
# - polysilicon_refine (JSON canonicalization + EAVT datom complexity)
# - outbound_logistics (file I/O + BPMN + kami-autodrive composition)
# - supply_procurement (okaimono + giemon SBOM bridge + abaki policy)
set -euo pipefail
cd "$(dirname "$0")/../.."
exec bb -e '(def nss (quote [himawari.cells.cell-process.test-state-machine
                             himawari.cells.ingot-wafer.test-state-machine
                             himawari.cells.panel-loading.test-state-machine]))
              (apply require (quote clojure.test) nss)
              (let [r (apply clojure.test/run-tests nss)]
                (System/exit (if (zero? (+ (:fail r) (:error r))) 0 1)))'
