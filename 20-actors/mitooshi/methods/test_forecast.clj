#!/usr/bin/env bb
;; Tests for mitooshi baseline forecasting over the persisted trail (methods/forecast.clj).
;; 1:1 port of test_forecast.py.
;;
;; Run:
;;   bb --classpath 20-actors 20-actors/mitooshi/methods/test_forecast.clj
;;
;; Proves observe→bridge→persist→forecast closes leak-free: forecasts are distributions
;; (G1, point-asserted false), use only pre-target history (G5), and score against the
;; realizing obs with proper rules + skill vs climatology (G12). One test runs over the
;; REAL persisted trail; the rest use a synthetic varying history for non-trivial skill.
(ns mitooshi.methods.test-forecast
  (:require [clojure.test :refer [deftest is run-tests]]
            [clojure.java.io :as io]
            [clojure.edn :as edn]
            [clojure.string :as str]
            [mitooshi.methods.forecast :as forecast]
            [mitooshi.methods.score :as score]))

(def ^:private this-file *file*)

(def ^:private trail-path
  (-> this-file io/file .getAbsoluteFile .getParentFile .getParentFile
      (io/file "data" "persisted" "chokepoint-trail.kotoba.edn")))

(defn- synthetic
  "One series with a clear upward trend, through the target t=7 (so the forecast at
  target=7 — built from history t<7 — has a realizing obs to score against).
  Mirrors _synthetic() in test_forecast.py: string-keyed maps with string obs values."
  []
  (mapv (fn [t] {":obs/series"      "s-x"
                 ":obs/observed-at" t
                 ":obs/value"       (double (+ 10 (* 2 t)))})
        (range 1 8)))

;; ── ported test cases ────────────────────────────────────────────────────────

(deftest test-series-histories-are-sorted
  (let [h (forecast/series-histories (synthetic))]
    (is (contains? h "s-x"))
    (let [ts (mapv first (get h "s-x"))]
      (is (= ts (vec (sort ts)))))))

(deftest test-forecast-is-distribution-not-point
  (let [fc (forecast/forecast-next "s-x" (get (forecast/series-histories (synthetic)) "s-x") 7)]
    (is (some? fc))
    (is (false? (:point-asserted fc)))         ; G1 — never a deterministic point
    (is (= "gaussian" (:dist-kind fc)))
    (is (= ":resilience" (:use fc)))))

(deftest test-forecast-is-leak-free-info-as-of-before-target
  (let [fc (forecast/forecast-next "s-x" (get (forecast/series-histories (synthetic)) "s-x") 7)]
    (is (< (:info-as-of fc) 7))                ; G5 — only saw history strictly before target
    ;; scoring against the realized obs at 7 does NOT raise (obs strictly after info)
    (let [s (score/score-pair fc (score/->observation "o" :observed-at 7 :value 24.0))]
      (is (contains? s "crps")))))

(deftest test-forecast-next-returns-none-without-prior-history
  ;; target at/before the first observation → no leak-free history → no forecast
  (is (nil? (forecast/forecast-next
             "s-x"
             (get (forecast/series-histories (synthetic)) "s-x")
             1))))

(deftest test-persistence-beats-climatology-on-a-trend
  (let [rows (synthetic)
        pers  (forecast/forecast-trail rows 7 "persistence")
        clim  (forecast/forecast-trail rows 7 "climatology")
        pj    (first (filter #(= (get % "series") "s-x") pers))
        cj    (first (filter #(= (get % "series") "s-x") clim))]
    ;; on a clean linear trend, persistence (last value) tracks far better than the mean
    (is (< (get pj "crps") (get cj "crps")))
    (is (> (get pj "skill") 0))))              ; G12 — persistence is skilled vs climatology

(deftest test-emit-forecast-edn-marks-g1-and-g5
  (let [rows (synthetic)
        edn-str (forecast/emit-forecast-edn
                 (forecast/forecast-trail rows 7 "climatology")
                 7 "climatology")]
    (is (str/includes? edn-str ":forecast/point-asserted false"))  ; G1
    (is (str/includes? edn-str "leak-free"))                        ; G5
    (is (str/includes? edn-str "G10-gated"))))                      ; G10

(deftest test-runs-over-real-persisted-trail-leak-free
  ;; the real append-only trail must be forecastable end-to-end without a leak
  (if-not (.exists trail-path)
    ;; trail not generated in this checkout — skip (matches Python behaviour)
    (is true "trail not present — skipped")
    (let [rows (forecast/load-trail-edn (.getAbsolutePath trail-path))
          h    (forecast/series-histories rows)]
      (is (seq h) "expected series in the persisted trail")
      (let [target (reduce max (mapcat (fn [[_ pairs]] (map first pairs)) h))
            fcs (forecast/forecast-trail rows target "climatology")]
        (is (seq fcs) "expected at least one forecast over the real trail")
        (doseq [r fcs]
          (is (< (:info-as-of (get r "forecast")) target)
              "leak-free by construction"))))))

;; ── entry point ──────────────────────────────────────────────────────────────

(when (= *file* (System/getProperty "babashka.file"))
  (let [{:keys [fail error]} (clojure.test/run-tests 'mitooshi.methods.test-forecast)]
    (System/exit (if (zero? (+ fail error)) 0 1))))
