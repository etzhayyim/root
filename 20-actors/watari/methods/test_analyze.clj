#!/usr/bin/env bb
;; Working Clojure port of methods/test_analyze.py.
(ns watari.methods.test-analyze
  "Tests for the watari 渡り moving-craft situational analyzer (methods/analyze.clj).

  Covers the aggregate roll-ups (chokepoint transit, lane load, freshness tail) AND the
  load-bearing charter invariant: situational-awareness, NEVER person-surveillance — a craft is
  a craft, not a person (G4).

  Run:  bb --classpath 20-actors 20-actors/watari/methods/test_analyze.clj"
  (:require [watari.methods.analyze :as wa]
            [clojure.java.io :as io]
            [clojure.string :as str]
            [clojure.set :as set]
            [clojure.test :refer [deftest is run-tests]]))

(def ^:private this-file *file*)
(defn- seed []
  (-> this-file io/file .getAbsoluteFile .getParentFile .getParentFile
      (io/file "data" "seed-craft-graph.kotoba.edn")))
(defn- g [] (wa/classify (wa/load-edn (seed))))
(defn- a [] (wa/analyze (g)))

(deftest classify-buckets-the-seed
  (let [{:keys [craft fixes lanes]} (g)]
    (is (= (count craft) 13))      ; 8 vessels + 5 aircraft
    (is (= (count fixes) 26))
    (is (= (count lanes) 9))))

(deftest kind-split-vessels-and-aircraft
  (let [res (a)]
    (is (= (get-in res [:kind-count :vessel]) 8))
    (is (= (get-in res [:kind-count :aircraft]) 5))))

(deftest latest-fix-is-max-observed-at-per-craft
  (let [{:keys [fixes]} (g)
        res (a)
        by-craft (reduce (fn [m fx] (update m (:craft.fix/craft fx) (fnil conj [])
                                            (or (:craft.fix/observed-at fx) ""))) {} fixes)]
    (doseq [[c fx] (:latest res)]
      (is (= (or (:craft.fix/observed-at fx) "") (last (sort (by-craft c))))))))

(deftest chokepoint-transit-rollup
  (let [res (a)]
    (is (= (get-in res [:choke-transit :malacca]) 3))
    (is (= (get-in res [:choke-transit :suez-red-sea]) 1))
    (is (= (get-in res [:choke-transit :hormuz]) 1))))

(deftest freshness-tail-flags-stale-craft
  (let [res (a)]
    (is (= (count (:stale res)) 2))
    (is (every? #(neg? (compare (or (:craft.fix/observed-at (get-in res [:latest %])) "")
                                (:dataset-latest res)))
                (:stale res)))))

(deftest chokepoint-output-is-bridge-compatible-with-mitooshi
  (let [res (a)
        known #{:malacca :luzon-strait :suez-red-sea :hormuz :gibraltar
                :south-china-sea :bab-el-mandeb}]
    (is (set/subset? (set (keys (:choke-transit res))) known))))

(deftest g4-no-person-tracking-invariant
  ;; STRUCTURAL: a craft is a craft, not a person — no person-level key in the seed
  (doseq [r (filter map? (wa/load-edn (seed)))
          k (keys r)]
    (let [n (name k)]
      (is (not (str/includes? (str k) ":person")) (str "person-level key " k " (G4)"))
      (is (not (str/includes? n "operator-name"))))))

(deftest report-is-aggregate-first-and-non-targeting
  (let [md (wa/render-report (g) (a))]
    (is (str/includes? md "person-surveillance"))
    (is (str/includes? (str/lower-case md) "never"))
    (is (str/includes? md "target-list"))))

(when (= *file* (System/getProperty "babashka.file"))
  (let [{:keys [fail error]} (run-tests 'watari.methods.test-analyze)]
    (System/exit (if (zero? (+ fail error)) 0 1))))
