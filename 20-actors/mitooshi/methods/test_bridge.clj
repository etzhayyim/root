#!/usr/bin/env bb
;; Working Clojure port of methods/test_bridge.py.
(ns mitooshi.methods.test-bridge
  "Tests for the mitooshi watari/watatsuna chokepoint bridge (methods/bridge.clj).

  Run:  bb --classpath 20-actors 20-actors/mitooshi/methods/test_bridge.clj"
  (:require [mitooshi.methods.bridge :as mb]
            [clojure.java.io :as io]
            [clojure.test :refer [deftest is run-tests]]))

(def ^:private this-file *file*)

(defn- bridge-data-dir []
  (-> this-file io/file .getAbsoluteFile .getParentFile .getParentFile
      (io/file "data" "bridge")))

(defn- by-actor []
  {"watari"    (mb/load-edn (io/file (bridge-data-dir) "watari-sample.edn"))
   "watatsuna" (mb/load-edn (io/file (bridge-data-dir) "watatsuna-sample.edn"))})

(deftest bridge-maps-chokepoints-to-series
  (let [b (mb/bridge (by-actor) 1)
        ids (set (keys (get b "series")))]
    ;; watari → transit series, watatsuna → cable series, joined on the chokepoint keyword
    (is (contains? ids "s-malacca-transit"))
    (is (contains? ids "s-malacca-cable"))
    (is (contains? ids "s-luzon-strait-transit"))
    (is (contains? ids "s-luzon-strait-cable"))))

(deftest bridge-ignores-non-chokepoint-records
  (let [b (mb/bridge (by-actor) 1)]
    ;; watari sample has 1 lane + 1 craft; watatsuna sample has 1 station → 3 skipped
    (is (= 3 (get b "skipped")))
    ;; series are chokepoints only (4 watari + 3 watatsuna = 7)
    (is (= 7 (count (get b "series"))))))

(deftest bridge-carries-value-and-source-actor
  (let [b (mb/bridge (by-actor) 5)
        malacca-t (first (filter #(= "s-malacca-transit" (get % ":obs/series")) (get b "obs")))
        malacca-c (first (filter #(= "s-malacca-cable" (get % ":obs/series")) (get b "obs")))]
    (is (= 3.0 (get malacca-t ":obs/value")))
    (is (= "watari" (get malacca-t ":obs/source-actor")))
    (is (= 5 (get malacca-t ":obs/observed-at")))
    (is (= 940.16 (get malacca-c ":obs/value")))
    (is (= "watatsuna" (get malacca-c ":obs/source-actor")))))

(deftest bridge-same-chokepoint-two-series-two-units
  ;; the shared keyword :malacca yields BOTH a vessel-transit and a cable-load series
  (let [b (mb/bridge (by-actor) 1)]
    (is (= ":transit-load" (get-in b ["series" "s-malacca-transit" ":series/kind"])))
    (is (= ":cable-load"   (get-in b ["series" "s-malacca-cable"   ":series/kind"])))
    (is (= ":public-broadcast" (get-in b ["series" "s-malacca-cable" ":series/source-class"])))))

(deftest bridge-single-actor-ok
  (let [b (mb/bridge {"watari" (mb/load-edn (io/file (bridge-data-dir) "watari-sample.edn"))} 1)]
    (is (= 4 (count (get b "series"))))
    (is (every? #(contains? % ":obs/source-actor") (get b "obs")))))

(deftest bridged-obs-chain-into-a-forecast-series
  ;; two snapshots at ts 1 and 2 build an append-only as-of trail for one chokepoint
  (let [b1 (mb/bridge (by-actor) 1)
        b2 (mb/bridge (by-actor) 2)
        trail (filter #(= "s-malacca-cable" (get % ":obs/series"))
                      (concat (get b1 "obs") (get b2 "obs")))
        ats (sort (map #(get % ":obs/observed-at") trail))]
    (is (= [1 2] ats))))

(when (= *file* (System/getProperty "babashka.file"))
  (let [{:keys [fail error]} (run-tests 'mitooshi.methods.test-bridge)]
    (System/exit (if (zero? (+ fail error)) 0 1))))
