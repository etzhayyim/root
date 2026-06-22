#!/usr/bin/env bash
# kuni-umi — clj/bb test suite (ADR-2606160842 py->clj port wave). Auto-wired into the fleet
# green-check; runs all cljc test namespaces via babashka from the repo root.
set -euo pipefail
cd "$(dirname "$0")/../.."
exec bb -e '(def nss (quote [kuni-umi.cells.site-survey.test-cell
                             kuni-umi.cells.deployment-planning.test-cell
                             kuni-umi.cells.construction-orchestration.test-cell
                             kuni-umi.cells.decommission.test-cell
                             kuni-umi.cells.audit-witness.test-cell
                             kuni-umi.robotics.test-robotics
                             kuni-umi.robotics.test-kinematics]))
            (apply require (quote clojure.test) nss)
            (let [r (apply clojure.test/run-tests nss)]
              (System/exit (if (zero? (+ (:fail r) (:error r))) 0 1)))'
