#!/usr/bin/env bb
;; lg-dougaka test runner (repo rule: run_tests.clj, NOT .sh; ADR-2606280030).
;; Usage: from 60-apps/etzhayyim-project-dougaka/lg/  →  bb run_tests.clj
;; Uses the scoped bb.edn (src + tests on the classpath; langgraph-clj dep).
(require '[clojure.test :as t]
         '[lg-dougaka.test-smoke])

(let [{:keys [fail error]} (t/run-tests 'lg-dougaka.test-smoke)]
  (System/exit (if (pos? (+ fail error)) 1 0)))
