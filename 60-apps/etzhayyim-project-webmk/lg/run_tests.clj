#!/usr/bin/env bb
;; lg-webmk — bb-native test runner (Clojure / babashka; NOT shell, per the
;; repo-wide rule "Operational code = clj/bb", ADR-2606072802 + 2606280030).
;;
;;   bb --config 60-apps/etzhayyim-project-webmk/lg/bb.edn test
;;   # or directly (resolves langgraph-clj via the same bb.edn):
;;   bb --config 60-apps/etzhayyim-project-webmk/lg/bb.edn run_tests.clj
;;
;; Audit emit is disabled here so no background HTTP fires during tests.
(require '[clojure.test :as t])

(when-not (= "1" (System/getenv "LG_AUDIT_DISABLED"))
  (println "note: set LG_AUDIT_DISABLED=1 to silence background audit posts"))

(require 'lg-webmk.test-smoke)

(let [{:keys [fail error]} (t/run-tests 'lg-webmk.test-smoke)]
  (if (zero? (+ fail error))
    (println "── lg-webmk: ALL suites green ──")
    (do (println "── lg-webmk: FAILURES above ──")
        (System/exit 1))))
