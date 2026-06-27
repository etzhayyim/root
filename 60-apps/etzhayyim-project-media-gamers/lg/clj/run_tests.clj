#!/usr/bin/env bb
;; media-gamers LangGraph clj-port test runner (repo rule: run_tests.clj, NOT .sh).
;; Usage (from this dir):  bb run_tests.clj   |   bb test
(require '[clojure.test :as t]
         'tests.test-smoke)

(let [{:keys [fail error]} (t/run-tests 'tests.test-smoke)]
  (System/exit (if (zero? (+ (or fail 0) (or error 0))) 0 1)))
