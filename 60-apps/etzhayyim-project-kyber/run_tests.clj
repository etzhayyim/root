#!/usr/bin/env bb
;; lg-kyber — bb-native test runner (Clojure / babashka; NOT shell, per repo rule
;; "New actors ship run_tests.clj, not run_tests.sh"). Run from the app dir so the
;; scoped bb.edn (langgraph-clj/langchain-clj deps + classpath root) is picked up:
;;
;;   cd 60-apps/etzhayyim-project-kyber && bb run_tests.clj
;;   # or: bb test
;;
;; Classpath root = this file's dir (the app dir), so a co-located .cljc at
;;   lg/lg_kyber/graphs/<x>.cljc  ⇒  ns  lg.lg-kyber.graphs.<x>.
(require '[babashka.classpath :as cp]
         '[babashka.fs :as fs]
         '[clojure.test :as t])

(cp/add-classpath (str (fs/parent (fs/absolutize *file*))))

(def suites '[lg.lg-kyber.tests.test-graphs])

(apply require suites)

(let [{:keys [fail error]} (apply t/run-tests suites)]
  (if (zero? (+ fail error))
    (println "── lg-kyber: ALL suites green ──")
    (do (println "── lg-kyber: FAILURES above ──")
        (System/exit 1))))
