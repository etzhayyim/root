#!/usr/bin/env bb
;; kanmon 関門 — bb-native test runner (Clojure / babashka; no shell). ADR-2606291500.
;;
;; Per the repo-wide rule (root CLAUDE.md §"Operational code = clj/bb"): first-party
;; tooling is clj/bb, NOT shell (new actors ship run_tests.clj, not run_tests.sh).
;;
;;   bb 20-actors/kanmon/run_tests.clj      ; run from anywhere
;;
;; Classpath: the absolute 20-actors/ dir (kanmon.methods.*) + 70-tools/src for the
;; SHARED etzhayyim.ie-flow.metrics order-calculus (the energy-flow suite). Both are
;; derived from THIS file's location so no --classpath flag is needed.
(require '[babashka.classpath :as cp]
         '[babashka.fs :as fs]
         '[clojure.test :as t])

;; this file is 20-actors/kanmon/run_tests.clj → 20-actors/ = grandparent, repo-root = great-grandparent
(let [actors-root (fs/parent (fs/parent (fs/absolutize *file*)))
      repo-root   (fs/parent actors-root)]
  (cp/add-classpath (str actors-root))
  (cp/add-classpath (str (fs/path repo-root "70-tools" "src"))))

(def suites
  '[kanmon.methods.test-kanmon-edn
    kanmon.methods.test-analyze
    kanmon.methods.test-dynamics
    kanmon.methods.test-ie-flow
    kanmon.methods.test-social
    kanmon.methods.test-kotoba
    kanmon.methods.test-autorun])

(apply require suites)

(let [{:keys [fail error]} (apply t/run-tests suites)]
  (if (zero? (+ fail error))
    (println "── kanmon: ALL suites green ──")
    (do (println "── kanmon: FAILURES above ──")
        (System/exit 1))))
