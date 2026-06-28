#!/usr/bin/env bb
;; run_tests.clj — repo rule: ship a .clj runner, not a .sh. Equivalent to `bb test`.
;; Loads every organism-viz cljc twin + its tests and exits non-zero on any failure.
(require '[clojure.test :as t]
         '[etzhayyim-organism-viz.pruning-test]
         '[etzhayyim-organism-viz.aliveness-test]
         '[etzhayyim-organism-viz.ideal-state-test])

(let [{:keys [fail error]}
      (t/run-tests 'etzhayyim-organism-viz.pruning-test
                   'etzhayyim-organism-viz.aliveness-test
                   'etzhayyim-organism-viz.ideal-state-test)]
  (System/exit (if (pos? (+ fail error)) 1 0)))
