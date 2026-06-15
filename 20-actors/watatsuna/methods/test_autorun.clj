#!/usr/bin/env bb
;; Working Clojure port of methods/test_autorun.py.
(ns watatsuna.methods.test-autorun
  "test_autorun.clj — watatsuna autonomous cable-resilience heartbeat + kotoba Datom-log invariants.
  ADR-2606012600. Guards the autonomy + persistence + resilience-not-interdiction contract:

    - one content-addressed tx per heartbeat to an append-only log;
    - the log is a verifiable commit-DAG (every CID recomputes; tamper is detected);
    - deterministic / resume-safe (same cycles → same CIDs) and append-only;
    - derived :resilience/* signals flagged :resilience/derived (recomputed-on-read);
    - G2 resilience, not interdiction (chokepoint-load / redundancy-gap framing, NO cut attr);
    - NO external I/O (offline ingest, local persist — G7 stays gated).

  Run:  bb --classpath 20-actors 20-actors/watatsuna/methods/test_autorun.clj"
  (:require [watatsuna.methods.autorun :as autorun]
            [watatsuna.methods.kotoba :as kotoba]
            [clojure.java.io :as io]
            [clojure.string :as str]
            [clojure.test :refer [deftest is run-tests]]))

(def ^:private this-file *file*)

(defn- tmp-log []
  (let [f (java.io.File/createTempFile "watatsuna" ".datoms.kotoba.edn")]
    (.delete f) f))

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
        (is (= (map :cid (:beats ra)) (map :cid (:beats rb)))
            "same cycles → same CIDs (deterministic / resume-safe)"))
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
          ;; tamper the EARLIEST tx (first non-comment line) → chain breaks at 0
          (let [lines (str/split-lines (slurp log))
                tampered-once (atom false)
                tampered (mapv (fn [ln]
                                (if (and (not @tampered-once)
                                         (not (str/starts-with? (str/trim ln) ";"))
                                         (str/includes? ln ":resilience/derived true"))
                                  (do (reset! tampered-once true)
                                      (str/replace-first ln ":resilience/derived true" ":resilience/derived false"))
                                  ln))
                              lines)]
            (is @tampered-once "the earliest tx line was located + tampered")
            (spit log (str (str/join "\n" tampered) "\n"))
            (let [v (kotoba/verify-chain log)]
              (is (and (not (:ok v)) (= (:broken-at v) 0)) "tampering an earlier tx breaks the chain")))))
      (finally (.delete log)))))

(deftest g2-resilience-not-interdiction
  (let [log (tmp-log)]
    (try
      (autorun/run-cycle 1 :log-path log)
      (let [tx (nth (kotoba/read-log log) 0)
            attrs (set (map #(str (nth % 2)) (:tx/datoms tx)))]
        (is (some #(str/starts-with? % ":resilience/") attrs) "derived :resilience/* signals persisted")
        (is (or (contains? attrs ":resilience/redundancy-gap-station")
                (contains? attrs ":resilience/chokepoint"))
            "resilience framing (chokepoint / redundancy-gap) present")
        (doseq [forbidden [":target" ":resilience/target" ":cut" ":resilience/cut-point"
                           ":interdiction" ":attack-point" ":vulnerability-to-attack"]]
          (is (not (contains? attrs forbidden)) (str "no interdiction attr " forbidden " (G2)"))))
      (finally (.delete log)))))

(deftest derived-flagged-and-append-only-op
  (let [log (tmp-log)]
    (try
      (autorun/run-cycle 1 :log-path log)
      (let [tx (nth (kotoba/read-log log) 0)
            derived (filter #(= (nth % 2) :resilience/derived) (:tx/datoms tx))
            ops (set (map first (:tx/datoms tx)))]
        (is (pos? (count derived)) "derived :resilience/* signals are persisted")
        (is (every? #(true? (nth % 3)) derived) "every :resilience/derived flag is true")
        (is (= ops #{:db/add}) "every datom is append-only :db/add (no :db/retract — 非終末論)"))
      (finally (.delete log)))))

(deftest no-external-io
  (let [dir (-> this-file io/file .getAbsoluteFile .getParentFile)
        src (str (slurp (io/file dir "autorun.clj")) (slurp (io/file dir "kotoba.clj")))]
    (doseq [banned ["urllib" "http.client" "babashka.http" "java.net.Socket" "shell" "ProcessBuilder"]]
      (is (not (str/includes? src banned)) (str "autorun/kotoba does no external I/O (no " banned ")")))))

(when (= *file* (System/getProperty "babashka.file"))
  (let [{:keys [fail error]} (run-tests 'watatsuna.methods.test-autorun)]
    (System/exit (if (zero? (+ fail error)) 0 1))))
