#!/usr/bin/env bb
;; shinogi 鎬 — bb-native test runner (Clojure / babashka; no shell). ADR-2606291200.
;;
;; Per the repo-wide rule (root CLAUDE.md §"Operational code = clj/bb"): first-party
;; tooling is clj/bb, NOT shell. New actors ship run_tests.clj.
;;
;;   bb 20-actors/shinogi/run_tests.clj      ; run from the repo root
;;
;; Classpath root (the absolute 20-actors/ dir) is derived from THIS file's location,
;; so the shinogi.methods.* suites resolve. The *file*-relative seed lookups in the
;; suites are repo-root-relative ("20-actors/shinogi/kotoba/…"), so run from the root.
(require '[babashka.classpath :as cp]
         '[babashka.fs :as fs]
         '[clojure.test :as t])

;; this file is 20-actors/shinogi/run_tests.clj → classpath root is its grandparent (20-actors/)
(cp/add-classpath (str (fs/parent (fs/parent (fs/absolutize *file*)))))

(def suites
  '[shinogi.methods.test-shinogi-edn
    shinogi.methods.test-analyze
    shinogi.methods.test-kotoba
    shinogi.methods.test-autorun
    shinogi.methods.test-charter-gates])

(apply require suites)

(let [{:keys [fail error]} (apply t/run-tests suites)]
  (if (zero? (+ fail error))
    (println "── shinogi: ALL suites green ──")
    (do (println "── shinogi: FAILURES above ──")
        (System/exit 1))))
