#!/usr/bin/env bb
;; Working Clojure port of methods/test_autorun.py.
(ns watari.methods.test-autorun
  "test_autorun.clj — watari autonomous moving-craft heartbeat + kotoba Datom-log invariants.
  ADR-2606041827. Guards the autonomy + persistence + no-person-tracking contract:

    - one content-addressed tx per heartbeat to an append-only log;
    - verifiable commit-DAG (every CID recomputes; tamper detected);
    - deterministic / resume-safe (same cycles → same CIDs) and append-only;
    - derived :movement/* signals flagged :movement/derived;
    - G4 no person-tracking (craft/lane/chokepoint aggregates, NO person/owner/passenger/crew attr);
    - NO external I/O (offline ingest, local persist — G7 stays gated).

  Run:  bb --classpath 20-actors 20-actors/watari/methods/test_autorun.clj"
  (:require [watari.methods.autorun :as autorun]
            [watari.methods.kotoba :as kotoba]
            [clojure.java.io :as io]
            [clojure.string :as str]
            [clojure.test :refer [deftest is run-tests]]))

(def ^:private this-file *file*)
(defn- tmp-log []
  (let [f (java.io.File/createTempFile "watari" ".datoms.kotoba.edn")] (.delete f) f))

(deftest heartbeat-persists
  (let [log (tmp-log)]
    (try
      (let [res (autorun/run-autonomous :cycles 3 :log-path log)]
        (is (= (:log-length res) 3) "one tx per heartbeat")
        (is (every? #(> (:datoms %) 0) (:beats res)) "every heartbeat persisted datoms")
        (is (:ok (:chain res)) "commit-DAG verifies (chain OK)")
        (is (str/starts-with? (:head-cid res) "b") "head CID is content-addressed"))
      (finally (.delete log)))))

(deftest deterministic-resume-safe
  (let [a (tmp-log) b (tmp-log)]
    (try
      (let [ra (autorun/run-autonomous :cycles 3 :log-path a)
            rb (autorun/run-autonomous :cycles 3 :log-path b)]
        (is (= (map :cid (:beats ra)) (map :cid (:beats rb))) "same cycles → same CIDs"))
      (finally (.delete a) (.delete b)))))

(deftest append-only-and-tamper
  (let [log (tmp-log)]
    (try
      (autorun/run-cycle 1 :log-path log)
      (let [first* (kotoba/read-log log)]
        (autorun/run-cycle 2 :log-path log)
        (let [second* (kotoba/read-log log)]
          (is (= (count second*) (inc (count first*))) "second heartbeat appends, does not rewrite")
          (is (= (:tx/prev (nth second* 1)) (:tx/cid (nth first* 0))) "tx 2 links tx 1's CID")
          (let [lines (str/split-lines (slurp log))
                tampered-once (atom false)
                tampered (mapv (fn [ln]
                                 (if (and (not @tampered-once)
                                          (not (str/starts-with? (str/trim ln) ";"))
                                          (str/includes? ln ":movement/derived true"))
                                   (do (reset! tampered-once true)
                                       (str/replace-first ln ":movement/derived true" ":movement/derived false"))
                                   ln))
                               lines)]
            (is @tampered-once "the earliest tx line was located + tampered")
            (spit log (str (str/join "\n" tampered) "\n"))
            (let [v (kotoba/verify-chain log)]
              (is (and (not (:ok v)) (= (:broken-at v) 0)) "tampering an earlier tx breaks the chain")))))
      (finally (.delete log)))))

(deftest g4-no-person-tracking
  (let [log (tmp-log)]
    (try
      (autorun/run-cycle 1 :log-path log)
      (let [tx (nth (kotoba/read-log log) 0)
            attrs (set (map #(str (nth % 2)) (:tx/datoms tx)))]
        (doseq [forbidden [":craft/owner-person" ":craft/passenger" ":craft/crew" ":craft/person"
                           ":person" ":craft.fix/person" ":movement/person" ":craft/owner-name"
                           ":pattern-of-life"]]
          (is (not (contains? attrs forbidden)) (str "no person-tracking attr " forbidden " (G4)")))
        (is (some #(str/starts-with? % ":movement/") attrs) "aggregate :movement/* signals persisted"))
      (finally (.delete log)))))

(deftest derived-flagged-and-append-only-op
  (let [log (tmp-log)]
    (try
      (autorun/run-cycle 1 :log-path log)
      (let [tx (nth (kotoba/read-log log) 0)
            derived (filter #(= (nth % 2) :movement/derived) (:tx/datoms tx))
            ops (set (map first (:tx/datoms tx)))]
        (is (pos? (count derived)) "derived :movement/* signals are persisted")
        (is (every? #(true? (nth % 3)) derived) "every :movement/derived flag is true")
        (is (= ops #{:db/add}) "every datom is append-only :db/add (no :db/retract — 非終末論)"))
      (finally (.delete log)))))

(deftest no-external-io
  (let [dir (-> this-file io/file .getAbsoluteFile .getParentFile)
        src (str (slurp (io/file dir "autorun.clj")) (slurp (io/file dir "kotoba.clj")))]
    (doseq [banned ["urllib" "http.client" "babashka.http" "java.net.Socket" "shell" "ProcessBuilder"]]
      (is (not (str/includes? src banned)) (str "autorun/kotoba does no external I/O (no " banned ")")))))

(when (= *file* (System/getProperty "babashka.file"))
  (let [{:keys [fail error]} (run-tests 'watari.methods.test-autorun)]
    (System/exit (if (zero? (+ fail error)) 0 1))))
