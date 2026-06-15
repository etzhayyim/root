#!/usr/bin/env bb
;; Working Clojure port of methods/test_synthesize.py.
(ns mitooshi.methods.test-synthesize
  "Tests for the cross-actor chokepoint resilience composite (methods/synthesize.clj).

  Run:  bb --classpath 20-actors 20-actors/mitooshi/methods/test_synthesize.clj"
  (:require [mitooshi.methods.synthesize :as ms]
            [clojure.java.io :as io]
            [clojure.string :as str]
            [clojure.test :refer [deftest is run-tests]]))

(def ^:private this-file *file*)

(defn- data-dir []
  (-> this-file io/file .getAbsoluteFile .getParentFile .getParentFile
      (io/file "data" "persisted")))

(def ^:private trail-path (io/file (data-dir) "chokepoint-trail.kotoba.edn"))
(def ^:private forecast-path (io/file (data-dir) "chokepoint-forecast.kotoba.edn"))

(defn- comp-data [] (ms/synthesize (ms/load-edn trail-path) (ms/load-edn forecast-path)))

(deftest chokepoint-extraction-strips-suffixes
  (is (= ":malacca" (ms/chokepoint-of "s-malacca-cable")))
  (is (= ":luzon-strait" (ms/chokepoint-of "s-luzon-strait-transit"))))

(deftest latest-by-series-takes-max-observed-at
  (let [rows [{:obs/series "s-x" :obs/observed-at 1 :obs/value 10.0}
              {:obs/series "s-x" :obs/observed-at 3 :obs/value 30.0}
              {:obs/series "s-x" :obs/observed-at 2 :obs/value 20.0}]
        latest (ms/latest-by-series rows)]
    (is (= 30.0 (second (get latest "s-x"))))))

(deftest composite-ranks-malacca-top
  (let [comp (comp-data)]
    (is (= ":malacca" (:chokepoint (first comp))))))

(deftest attention-is-bounded-and-sorted-desc
  (let [comp (comp-data)
        atts (mapv :attention comp)]
    (is (every? #(and (<= 0.0 %) (<= % 1.0)) atts))
    (is (= atts (sort > atts)))))

(deftest attention-formula-blend
  (let [comp (comp-data)
        cables (keep :cable_load comp)
        transits (keep :transit comp)
        mc (apply max cables)
        mt (apply max transits)]
    (doseq [d comp]
      (let [nc (if (:cable_load d) (/ (:cable_load d) mc) 0.0)
            nt (if (:transit d) (/ (:transit d) mt) 0.0)
            expected (-> (+ (* 0.7 nc) (* 0.3 nt))
                         (* 10000.0)
                         Math/round
                         (/ 10000.0))]
        (is (< (Math/abs (- (:attention d) expected)) 1e-9))))))

(deftest composite-joins-forecast
  (let [comp (comp-data)]
    (is (some #(some? (:forecast_cable_mean %)) comp))))

(deftest transit-only-chokepoint-has-low-attention
  (let [comp (comp-data)
        hormuz (first (filter #(= ":hormuz" (:chokepoint %)) comp))]
    (when hormuz
      (is (nil? (:cable_load hormuz)))
      (is (< (:attention hormuz) 0.5)))))

(deftest render-edn-is-resilience-not-target-list
  (let [edn (ms/render-edn (comp-data))]
    (is (str/includes? edn "RESILIENCE"))
    (is (str/includes? (str/lower-case edn) "never a target-list"))
    (is (str/includes? edn ":choke/attention"))
    (is (str/includes? edn "G10-gated"))))

(when (= *file* (System/getProperty "babashka.file"))
  (let [{:keys [fail error]} (run-tests 'mitooshi.methods.test-synthesize)]
    (System/exit (if (zero? (+ fail error)) 0 1))))
