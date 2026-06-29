#!/usr/bin/env bb
;; shinan 指南 — bb-native test runner (Clojure / babashka; no shell). ADR-2606291501.
;;
;; Per the repo-wide rule (root CLAUDE.md §"Operational code = clj/bb"): first-party
;; tooling is clj/bb, NOT shell (new actors ship run_tests.clj, not run_tests.sh).
;;
;;   bb 20-actors/shinan/run_tests.clj      ; run from anywhere
;;
;; Classpath root (the absolute 20-actors/ dir) is derived from THIS file's location.
(require '[babashka.classpath :as cp]
         '[babashka.fs :as fs]
         '[clojure.test :as t])

;; this file is 20-actors/shinan/run_tests.clj → classpath root is its grandparent (20-actors/)
(cp/add-classpath (str (fs/parent (fs/parent (fs/absolutize *file*)))))

(def suites
  '[shinan.methods.test-shinan-edn
    shinan.methods.test-analyze
    shinan.methods.test-kotoba
    shinan.methods.test-autorun])

(apply require suites)

(let [{:keys [fail error]} (apply t/run-tests suites)]
  (if (zero? (+ fail error))
    (println "── shinan: ALL suites green ──")
    (do (println "── shinan: FAILURES above ──")
        (System/exit 1))))
