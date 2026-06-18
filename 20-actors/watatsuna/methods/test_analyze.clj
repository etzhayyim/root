#!/usr/bin/env bb
;; Working Clojure port of methods/test_analyze.py.
(ns watatsuna.methods.test-analyze
  "Tests for the watatsuna 綿津綱 submarine-cable resilience analyzer (methods/analyze.clj).

  Covers chokepoint/station/diversity roll-ups, the render_datoms bridge-input shape that
  mitooshi consumes, and the load-bearing charter invariant: a RESILIENCE map, NEVER a
  target-list (G2); no sabotage-intent adjudication (G4).

  Run:  bb --classpath 20-actors 20-actors/watatsuna/methods/test_analyze.clj"
  (:require [watatsuna.methods.analyze :as wa]
            [clojure.java.io :as io]
            [clojure.string :as str]
            [clojure.test :refer [deftest is run-tests]]))

(def ^:private this-file *file*)
(defn- seed []
  (-> this-file io/file .getAbsoluteFile .getParentFile .getParentFile
      (io/file "data" "seed-cable-graph.kotoba.edn")))
(defn- g [] (wa/classify (wa/load-edn (seed))))
(defn- a [] (wa/analyze (g)))

(deftest classify-buckets-the-seed
  (let [{:keys [cables stations links segs faults]} (g)]
    (is (= (count cables) 14))
    (is (= (count stations) 22))
    (is (= (count links) 43))
    (is (= (count segs) 11))
    (is (= (count faults) 2))))

(deftest chokepoint-load-ranking
  (let [res (a)
        top (take 3 (sort-by (comp - val) (:choke-load res)))]
    (is (= (ffirst top) :malacca))
    (is (< (Math/abs (- (get-in res [:choke-load :malacca]) 490.16)) 1e-6))
    (is (< (Math/abs (- (get-in res [:choke-load :luzon-strait]) 454.56)) 1e-6))
    (is (< (Math/abs (- (get-in res [:choke-load :gibraltar]) 324.0)) 1e-6))))

(deftest chokepoint-count-matches-load-keys
  (let [res (a)]
    (is (= (set (keys (:choke-count res))) (set (keys (:choke-load res)))))
    (is (every? #(>= (val %) 1) (:choke-count res)))))

(deftest redundancy-gap-is-single-cable-stations
  (let [res (a)]
    (is (every? #(<= (get-in res [:station-degree %]) 1) (:redundancy-gap res)))))

(deftest render-datoms-emit-bridge-input-shape
  (let [edn (wa/render-datoms (g) (a))]
    (is (str/includes? edn ":resilience/chokepoint "))
    (is (str/includes? edn ":resilience/chokepoint-load "))
    (is (str/includes? edn ":resilience/derived true"))))

(deftest chokepoint-keys-are-mitooshi-bridge-compatible
  (let [res (a)
        known #{:malacca :luzon-strait :suez-red-sea :hormuz :gibraltar
                :south-china-sea :bab-el-mandeb}]
    (is (clojure.set/subset? (set (keys (:choke-load res))) known))))

(deftest g2-resilience-not-targeting-invariant
  (let [md (wa/render-report (g) (a))]
    (is (str/includes? md "RESILIENCE"))
    (is (str/includes? md "target-list"))
    (is (str/includes? md "NOT a target-list"))))

(deftest g4-faults-do-not-adjudicate-intent
  ;; fault records mirror public bulletins; no field claims culprit/attribution/intent
  (doseq [r (filter map? (wa/load-edn (seed)))
          :when (:cable.fault/id r)]
    (is (not-any? (fn [k] (let [n (name k)]
                            (or (str/includes? n "culprit")
                                (str/includes? n "attribution")
                                (str/includes? n "intent"))))
                  (keys r)))))

(when (= *file* (System/getProperty "babashka.file"))
  (let [{:keys [fail error]} (run-tests 'watatsuna.methods.test-analyze)]
    (System/exit (if (zero? (+ fail error)) 0 1))))
