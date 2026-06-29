#!/usr/bin/env bb
;; kanmon 関門 — bb-native test runner (Clojure / babashka; no shell). ADR-2606291500.
;;
;; Per the repo-wide rule (root CLAUDE.md §"Operational code = clj/bb"): first-party
;; tooling is clj/bb, NOT shell (new actors ship run_tests.clj, not run_tests.sh).
;;
;;   bb 20-actors/kanmon/run_tests.clj      ; run from anywhere
;;
;; Classpath root (the absolute 20-actors/ dir) is derived from THIS file's location,
;; so the `kanmon.methods.*` namespaces and the *file*-relative seed lookups resolve
;; without a --classpath flag.
(require '[babashka.classpath :as cp]
         '[babashka.fs :as fs]
         '[clojure.test :as t])

;; this file is 20-actors/kanmon/run_tests.clj → classpath root is its grandparent (20-actors/)
(cp/add-classpath (str (fs/parent (fs/parent (fs/absolutize *file*)))))

(def suites
  '[kanmon.methods.test-kanmon-edn
    kanmon.methods.test-analyze
    kanmon.methods.test-kotoba
    kanmon.methods.test-autorun])

(apply require suites)

(let [{:keys [fail error]} (apply t/run-tests suites)]
  (if (zero? (+ fail error))
    (println "── kanmon: ALL suites green ──")
    (do (println "── kanmon: FAILURES above ──")
        (System/exit 1))))
