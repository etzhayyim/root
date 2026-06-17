#!/usr/bin/env bash
# kawaraban 瓦版 — test runner, bb/clj (ADR-2606160842 py→clj port wave; clj + datomic first tier).
# The methods suite (route/analyze/ingest/charter-gates) is cljc — run via babashka from the
# repo root (registered in bb.edn test:pywasm). The Python sources + tests were pruned once the
# cljc ports verified green. The only remaining Python is cells/test_state_machines.py (the
# Pregel state-machine guards, not yet ported); it is shelled out so no coverage is lost.
set -euo pipefail
cd "$(dirname "$0")/../.."
exec bb -e '
(require (quote clojure.test) (quote [babashka.process :as p])
         (quote kawaraban.methods.test-route) (quote kawaraban.methods.test-analyze)
         (quote kawaraban.methods.test-ingest) (quote kawaraban.methods.test-charter-gates))
(let [r (clojure.test/run-tests (quote kawaraban.methods.test-route)
                                (quote kawaraban.methods.test-analyze)
                                (quote kawaraban.methods.test-ingest)
                                (quote kawaraban.methods.test-charter-gates))
      cells (p/shell {:dir "20-actors/kawaraban/cells" :continue true} "python3" "test_state_machines.py")]
  (println "cells/test_state_machines.py (py, pending cljc port) exit:" (:exit cells))
  (System/exit (if (and (zero? (+ (:fail r) (:error r))) (zero? (:exit cells))) 0 1)))'
