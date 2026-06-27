#!/usr/bin/env bb
;; etzhayyim-project-common-crawl — bb-native test runner (Clojure, no shell; repo
;; CLAUDE.md §"Operational code = clj/bb", ADR-2606072802 / ADR-2606280030).
;;
;;   bb 60-apps/etzhayyim-project-common-crawl/run_tests.clj
;;
;; Classpath root = the app's clj/ dir (derived from THIS file's location), so the
;; common-crawl.* namespaces + their *_test twins resolve without a --classpath flag.
(require '[babashka.classpath :as cp]
         '[babashka.fs :as fs]
         '[clojure.test :as t])

;; this file is <app>/run_tests.clj → classpath root is <app>/clj
(cp/add-classpath (str (fs/file (fs/parent (fs/absolutize *file*)) "clj")))

(def suites
  '[common-crawl.did-test
    common-crawl.intel-test
    common-crawl.cypher-test
    common-crawl.inject-test])

(apply require suites)

(let [{:keys [fail error]} (apply t/run-tests suites)]
  (if (zero? (+ fail error))
    (println "── common-crawl: ALL suites green ──")
    (do (println "── common-crawl: FAILURES above ──")
        (System/exit 1))))
