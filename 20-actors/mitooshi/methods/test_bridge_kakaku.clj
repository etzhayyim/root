#!/usr/bin/env bb
;; Working Clojure port of methods/test_bridge_kakaku.py.
(ns mitooshi.methods.test-bridge-kakaku
  "Tests for the mitooshi kakaku price/supply-demand bridge (methods/bridge_kakaku.clj).

  Run:  bb --classpath 20-actors 20-actors/mitooshi/methods/test_bridge_kakaku.clj"
  (:require [mitooshi.methods.bridge-kakaku :as mbk]
            [mitooshi.methods.analyze :as analyze]
            [clojure.java.io :as io]
            [clojure.test :refer [deftest is run-tests]]))

(def ^:private this-file *file*)

(defn- bridge-data-dir []
  (-> this-file io/file .getAbsoluteFile .getParentFile .getParentFile
      (io/file "data" "bridge")))

(defn- records []
  (analyze/load-edn (io/file (bridge-data-dir) "kakaku-sample.edn")))

;; ── tests (1:1 with test_bridge_kakaku.py) ───────────────────────────────────

(deftest maps-price-and-supply-demand-series
  ;; each product yields a price-level series AND a supply-demand-index series
  (let [b   (mbk/bridge-kakaku (records) 1)
        ids (set (keys (get b "series")))]
    (is (contains? ids "s-jan-4901777300443-price"))
    (is (contains? ids "s-jan-4901777300443-supply-demand"))
    (is (contains? ids "s-gtin-04901234567894-price"))
    (is (contains? ids "s-gtin-04901234567894-supply-demand"))))

(deftest ignores-non-price-sd-records
  ;; sample has 1 spread + 1 offer + 1 merchant → 3 skipped; 4 forecastable series
  (let [b (mbk/bridge-kakaku (records) 1)]
    (is (= 3 (get b "skipped")))
    (is (= 4 (count (get b "series"))))))

(deftest carries-value-and-source-actor
  (let [b     (mbk/bridge-kakaku (records) 5)
        price (first (filter #(= "s-jan-4901777300443-price" (get % ":obs/series"))
                             (get b "obs")))
        sd    (first (filter #(= "s-jan-4901777300443-supply-demand" (get % ":obs/series"))
                             (get b "obs")))]
    (is (= 3200.0 (get price ":obs/value")))
    (is (= "kakaku" (get price ":obs/source-actor")))
    (is (= 5 (get price ":obs/observed-at")))
    (is (= 0.42 (get sd ":obs/value")))))

(deftest source-class-is-public-broadcast-g4
  (let [b (mbk/bridge-kakaku (records) 1)
        s (get-in b ["series" "s-jan-4901777300443-supply-demand"])]
    (is (= ":public-broadcast" (get s ":series/source-class")))   ;; G4
    (is (= ":representative"   (get s ":series/sourcing")))        ;; G11
    (is (= ":supply-demand-index" (get s ":series/kind")))))

(deftest obs-chain-into-a-forecast-trail
  ;; two snapshots build the append-only as-of trail mitooshi forecasts (非終末論)
  (let [b1    (mbk/bridge-kakaku (records) 1)
        b2    (mbk/bridge-kakaku (records) 2)
        trail (filter #(= "s-jan-4901777300443-supply-demand" (get % ":obs/series"))
                      (concat (get b1 "obs") (get b2 "obs")))
        ats   (sort (map #(get % ":obs/observed-at") trail))]
    (is (= [1 2] ats))))

;; ── runner ────────────────────────────────────────────────────────────────────

(when (= *file* (System/getProperty "babashka.file"))
  (let [{:keys [fail error]} (run-tests 'mitooshi.methods.test-bridge-kakaku)]
    (System/exit (if (zero? (+ fail error)) 0 1))))
