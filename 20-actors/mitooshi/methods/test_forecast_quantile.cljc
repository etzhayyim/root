(ns mitooshi.methods.test-forecast-quantile
  "Cross-language oracle tests for mitooshi.methods.forecast-quantile — the Clojure
  port of methods/forecast_quantile.py.

  Ported 1:1 from the REAL Python test_forecast_quantile.py: distribution-only (G1),
  resilience use (G2), leak-free info-before-target (G5), monotone quantiles, and
  pinball + skill scoring vs a documented persistence baseline (G12). The fixtures
  are the same rising series 10+2t over t=1..7, so the quantile shape and the
  leak-check are exercised identically to the Python."
  (:require [clojure.test :refer [deftest is testing]]
            [mitooshi.methods.forecast-quantile :as fq]))

(defn- rising []
  (mapv (fn [t] [t (double (+ 10 (* 2 t)))]) (range 1 8)))   ; t=1..7

(deftest forecast-is-quantile-distribution-g1
  (let [fc (fq/forecast-next-quantile "s-x" (rising) 7)]
    (is (some? fc))
    (is (= "quantile" (:dist-kind fc)))
    (is (= false (:point-asserted fc)))               ; G1
    (is (= ":resilience" (:use fc)))                  ; G2
    (is (= (set fq/DEFAULT-LEVELS) (set (keys (:quantiles fc)))))))

(deftest quantiles-are-monotone
  (let [fc   (fq/forecast-next-quantile "s-x" (rising) 7)
        vals (mapv #(get (:quantiles fc) %) (sort (keys (:quantiles fc))))]
    (is (= vals (vec (sort vals))))))                 ; q10 <= q50 <= q90

(deftest leak-free-info-before-target-g5
  (let [fc (fq/forecast-next-quantile "s-x" (rising) 7)]
    (is (< (:info-as-of fc) 7))                       ; G5 — only prior history
    (let [s (fq/score-quantile fc 24.0 7)]            ; obs strictly after info → no raise
      (is (contains? s "pinball")))))

(deftest no-prior-history-returns-nil
  (is (nil? (fq/forecast-next-quantile "s-x" [[7 24.0]] 7))))

(deftest trail-scores-pinball-and-skill-g12
  (let [rows (mapv (fn [t] {":obs/series" "s-x" ":obs/observed-at" t
                            ":obs/value" (double (+ 10 (* 2 t)))})
                   (range 1 8))
        trail (fq/forecast-quantile-trail rows 7)
        r (first trail)]
    (is (= 1 (count trail)))
    (is (contains? r "pinball"))
    (is (contains? r "baseline_pinball"))
    (is (contains? r "skill"))
    (is (boolean? (get r "skilled")))))               ; G12: only skilled if it beats baseline
