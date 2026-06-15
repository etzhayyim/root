#!/usr/bin/env bb
;; Clojure (babashka) port of test_analyze.py — mitooshi backtest analyzer tests.
(ns mitooshi.methods.test-analyze
  "Tests for mitooshi.methods.analyze over the seed forecast graph.

  Run:
    bb --classpath 20-actors 20-actors/mitooshi/methods/test_analyze.clj"
  (:require [clojure.test :refer [deftest is testing run-tests]]
            [clojure.java.io :as io]
            [clojure.edn :as edn]
            [clojure.string :as str]
            [mitooshi.methods.analyze :as analyze]))

(def ^:private this-file *file*)
(def ^:private SEED
  (io/file (-> this-file io/file .getAbsoluteFile .getParentFile .getParentFile)
           "data" "seed-forecast-graph.kotoba.edn"))

(defn- res [] (analyze/backtest (analyze/load-edn SEED)))

(defn- card [r model]
  (first (filter #(= (get % "model") model) (get r "cards"))))

;; ── test_seed_parses_four_models_all_distribution_kinds ──────────────────────
(deftest test-seed-parses-four-models-all-distribution-kinds
  (let [r (res)]
    (is (= 4 (count (get r "cards"))))
    (is (= #{"gaussian" "quantile" "categorical" "ensemble"}
           (set (map #(get % "dist") (get r "cards")))))))

;; ── test_ensemble_model_scored_with_energy_crps ──────────────────────────────
(deftest test-ensemble-model-scored-with-energy-crps
  (let [c (card (res) "m-e-edge")]
    (is (= "CRPS" (get c "metric")))
    (is (= "ensemble" (get c "dist")))
    (is (= 3 (get c "n")))
    (is (<= 0 (get c "mean_primary") 1.0))
    (is (some? (get c "skill_vs_climatology")))))

;; ── test_gaussian_model_skilled_against_both_baselines ───────────────────────
(deftest test-gaussian-model-skilled-against-both-baselines
  (let [c (card (res) "m-ewma-drift")]
    (is (= "CRPS" (get c "metric")))
    (is (= 6 (get c "n")))
    (is (pos? (get c "skill_vs_climatology")))
    (is (pos? (get c "skill_vs_persistence")))
    (is (true? (get c "skilled")))))

;; ── test_quantile_model_scored_with_pinball ──────────────────────────────────
(deftest test-quantile-model-scored-with-pinball
  (let [c (card (res) "m-q-edge")]
    (is (= "pinball" (get c "metric")))
    (is (= 3 (get c "n")))
    (is (< 0 (get c "mean_primary") 1.0))
    (is (nil? (get c "skill_vs_persistence")))))  ; no gaussian-persistence baseline for quantile

;; ── test_categorical_model_scored_with_brier ─────────────────────────────────
(deftest test-categorical-model-scored-with-brier
  (let [c (card (res) "m-c-edge")]
    (is (= "Brier" (get c "metric")))
    (is (= 3 (get c "n")))
    (is (<= 0 (get c "mean_primary") 2.0))
    (is (some? (get c "skill_vs_climatology")))))

;; ── test_gaussian_pit_mean_reflects_slight_positive_bias ─────────────────────
(deftest test-gaussian-pit-mean-reflects-slight-positive-bias
  (let [c (card (res) "m-ewma-drift")]
    (is (< 0.4 (get c "pit_mean") 0.7))))

;; ── test_leak_free_all_forecasts_scored_none_dropped ─────────────────────────
(deftest test-leak-free-all-forecasts-scored-none-dropped
  ;; 6 gaussian + 3 quantile + 3 categorical + 3 ensemble = 15
  (let [r (res)]
    (is (= 15 (reduce + 0 (map #(get % "n") (get r "cards")))))))

;; ── test_reliability_diagram_has_a_section_per_model ─────────────────────────
(deftest test-reliability-diagram-has-a-section-per-model
  (let [r   (res)
        md  (analyze/render-reliability r)]
    (doseq [c (get r "cards")]
      (is (str/includes? md (get c "name"))))
    (is (str/includes? md "PIT mean"))
    (is (str/includes? md "uniform ideal"))))

;; ── test_reliability_datoms_emit_calib_records ───────────────────────────────
(deftest test-reliability-datoms-emit-calib-records
  (let [r   (res)
        edn-str (analyze/render-reliability-datoms r)]
    (is (= (count (get r "cards"))
           (count (re-seq #":fc\.calib/id" edn-str))))
    (is (str/includes? edn-str ":fc.calib/pit-mean"))
    (is (str/includes? edn-str ":fc.calib/hist"))))

;; ── entry point ──────────────────────────────────────────────────────────────
(when (= *file* (System/getProperty "babashka.file"))
  (let [{:keys [fail error]} (clojure.test/run-tests 'mitooshi.methods.test-analyze)]
    (System/exit (if (zero? (+ fail error)) 0 1))))
