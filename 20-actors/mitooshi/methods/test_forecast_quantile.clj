#!/usr/bin/env bb
;; Tests for mitooshi quantile forecasting (methods/forecast_quantile.clj).
;; 1:1 port of test_forecast_quantile.py.
;;
;; Run:
;;   bb --classpath 20-actors 20-actors/mitooshi/methods/test_forecast_quantile.clj
;;
;; Verifies: distribution-only (G1), resilience use (G2), leak-free (G5), monotone quantiles,
;; pinball scoring + skill vs the documented persistence baseline (G12).
(ns mitooshi.methods.test-forecast-quantile
  (:require [clojure.test :refer [deftest is run-tests]]
            [mitooshi.methods.forecast-quantile :as fq]
            [mitooshi.methods.score :as score]))

;; ── fixture ──────────────────────────────────────────────────────────────────

(defn- rising
  "Rising series t=1..7; values = 10 + 2t. Mirrors _rising() in test_forecast_quantile.py."
  []
  (mapv (fn [t] [(long t) (double (+ 10 (* 2 t)))]) (range 1 8)))

;; ── test cases (1:1 port of test_forecast_quantile.py) ───────────────────────

(deftest test-forecast-is-quantile-distribution-g1
  (let [fc (fq/forecast-next-quantile "s-x" (rising) 7)]
    (is (some? fc))
    (is (= "quantile" (:dist-kind fc)))
    (is (false? (:point-asserted fc)))               ; G1
    (is (= ":resilience" (:use fc)))                 ; G2
    (is (= (set fq/DEFAULT_LEVELS) (set (keys (:quantiles fc)))))))

(deftest test-quantiles-are-monotone
  (let [fc   (fq/forecast-next-quantile "s-x" (rising) 7)
        vals (mapv val (sort-by key (:quantiles fc)))]
    (is (= vals (vec (sort vals))))))                ; q10 <= q50 <= q90

(deftest test-leak-free-info-before-target-g5
  (let [fc (fq/forecast-next-quantile "s-x" (rising) 7)]
    (is (< (:info-as-of fc) 7))                     ; G5 — only prior history
    ;; scoring against realized obs at 7 does NOT raise (obs strictly after info)
    (let [s (fq/score-quantile fc 24.0 7)]
      (is (contains? s "pinball")))))

(deftest test-no-prior-history-returns-none
  (is (nil? (fq/forecast-next-quantile "s-x" [[7 24.0]] 7))))

(deftest test-trail-scores-pinball-and-skill-g12
  (let [rows  (mapv (fn [t] {":obs/series"      "s-x"
                              ":obs/observed-at" (long t)
                              ":obs/value"       (double (+ 10 (* 2 t)))})
                    (range 1 8))
        trail (fq/forecast-quantile-trail rows 7)]
    (is (= 1 (count trail)))
    (let [r (first trail)]
      (is (contains? r "pinball"))
      (is (contains? r "baseline_pinball"))
      (is (contains? r "skill"))
      (is (instance? Boolean (get r "skilled"))))))  ; G12

;; ── entry point ──────────────────────────────────────────────────────────────

(when (= *file* (System/getProperty "babashka.file"))
  (let [{:keys [fail error]} (clojure.test/run-tests 'mitooshi.methods.test-forecast-quantile)]
    (System/exit (if (zero? (+ fail error)) 0 1))))
