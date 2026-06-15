#!/usr/bin/env bb
;; Working Clojure port of methods/test_autorun.py.
(ns kabuto.methods.test-autorun
  "test_autorun.clj — kabuto autonomous supply-chain heartbeat + kotoba Datom-log invariants.
  ADR-2606022000. Guards autonomy + persistence + resilience-not-target-list + canonical-order
  determinism.

  Run:  bb --classpath 20-actors 20-actors/kabuto/methods/test_autorun.clj"
  (:require [kabuto.methods.autorun :as autorun]
            [kabuto.methods.kotoba :as kotoba]
            [clojure.java.io :as io]
            [clojure.string :as str]
            [clojure.test :refer [deftest is run-tests]]))

(def ^:private this-file *file*)
(defn- tmp-log []
  (let [f (java.io.File/createTempFile "kabuto" ".datoms.kotoba.edn")] (.delete f) f))

(deftest heartbeat-persists
  (let [log (tmp-log)]
    (try
      (let [res (autorun/run-autonomous :cycles 3 :log-path log)]
        (is (= (:log-length res) 3))
        (is (every? #(> (:datoms %) 0) (:beats res)))
        (is (:ok (:chain res)))
        (is (str/starts-with? (:head-cid res) "b")))
      (finally (.delete log)))))

(deftest deterministic-resume-safe
  (let [a (tmp-log) b (tmp-log)]
    (try
      (let [ra (autorun/run-autonomous :cycles 3 :log-path a)
            rb (autorun/run-autonomous :cycles 3 :log-path b)]
        (is (= (map :cid (:beats ra)) (map :cid (:beats rb)))))
      (finally (.delete a) (.delete b)))))

(deftest canonical-order-is-deterministic
  (let [log (tmp-log)]
    (try
      (autorun/run-cycle 1 :log-path log)
      (let [datoms (:tx/datoms (nth (kotoba/read-log log) 0))
            keyed (map pr-str datoms)]
        (is (= keyed (sort keyed)) "persisted datoms are in canonical sorted order")
        (is (= (kotoba/canonical-order datoms) (kotoba/canonical-order (kotoba/canonical-order datoms)))
            "canonical-order is idempotent"))
      (finally (.delete log)))))

(deftest append-only-and-tamper
  (let [log (tmp-log)]
    (try
      (autorun/run-cycle 1 :log-path log)
      (let [first* (kotoba/read-log log)]
        (autorun/run-cycle 2 :log-path log)
        (let [second* (kotoba/read-log log)]
          (is (= (count second*) (inc (count first*))))
          (is (= (:tx/prev (nth second* 1)) (:tx/cid (nth first* 0))))
          (let [lines (str/split-lines (slurp log))
                done (atom false)
                tampered (mapv (fn [ln]
                                 (if (and (not @done) (not (str/starts-with? (str/trim ln) ";"))
                                          (str/includes? ln ":supply/derived true"))
                                   (do (reset! done true)
                                       (str/replace-first ln ":supply/derived true" ":supply/derived false"))
                                   ln)) lines)]
            (is @done "earliest tx located + tampered")
            (spit log (str (str/join "\n" tampered) "\n"))
            (let [v (kotoba/verify-chain log)]
              (is (and (not (:ok v)) (= (:broken-at v) 0)))))))
      (finally (.delete log)))))

(deftest g2-resilience-not-target-list
  (let [log (tmp-log)]
    (try
      (autorun/run-cycle 1 :log-path log)
      (let [attrs (set (map #(str (nth % 2)) (:tx/datoms (nth (kotoba/read-log log) 0))))]
        (is (some #(str/starts-with? % ":supply/") attrs))
        (doseq [forbidden [":supply/target" ":supply/raid" ":supply/takeover-target"
                           ":target" ":supply/who-to-hit" ":supply/attack"]]
          (is (not (contains? attrs forbidden)) (str "no target-list attr " forbidden " (G2)"))))
      (finally (.delete log)))))

(deftest derived-flagged-and-append-only-op
  (let [log (tmp-log)]
    (try
      (autorun/run-cycle 1 :log-path log)
      (let [tx (nth (kotoba/read-log log) 0)
            derived (filter #(= (nth % 2) :supply/derived) (:tx/datoms tx))
            ops (set (map first (:tx/datoms tx)))]
        (is (pos? (count derived)))
        (is (every? #(true? (nth % 3)) derived))
        (is (= ops #{:db/add})))
      (finally (.delete log)))))

(deftest no-external-io
  (let [dir (-> this-file io/file .getAbsoluteFile .getParentFile)
        src (str (slurp (io/file dir "autorun.clj")) (slurp (io/file dir "kotoba.clj")))]
    (doseq [banned ["urllib" "http.client" "babashka.http" "java.net.Socket" "shell" "ProcessBuilder"]]
      (is (not (str/includes? src banned))))))

(when (= *file* (System/getProperty "babashka.file"))
  (let [{:keys [fail error]} (run-tests 'kabuto.methods.test-autorun)]
    (System/exit (if (zero? (+ fail error)) 0 1))))
