#!/usr/bin/env bb
;; lg-karma — bb-native test runner (Clojure / babashka; NOT shell, per the
;; repo-wide rule "Operational code = clj/bb", ADR-2606072802 + 2606280030).
;;
;;   bb --config 60-apps/etzhayyim-project-karma/lg-clj/bb.edn test
;;   # or directly (resolves langgraph-clj via the same bb.edn):
;;   bb --config 60-apps/etzhayyim-project-karma/lg-clj/bb.edn run_tests.clj
;;
;; Exits non-zero if any test fails or errors.
(require '[clojure.test :as t]
         'lg-karma.smoke-test)

(let [{:keys [fail error]} (t/run-tests 'lg-karma.smoke-test)]
  (if (zero? (+ (or fail 0) (or error 0)))
    (println "── lg-karma: ALL suites green ──")
    (do (println "── lg-karma: FAILURES above ──")
        (System/exit 1))))
