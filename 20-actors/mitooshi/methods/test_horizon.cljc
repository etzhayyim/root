(ns mitooshi.methods.test-horizon
  "Cross-language oracle tests for mitooshi.methods.horizon — the Clojure port of
  methods/horizon.py.

  Ported 1:1 from the REAL Python test_horizon.py. The assertions are structural
  (deterministic + mean-reverting path; positive short-horizon skill; skill decay;
  CRPS growth; many leak-checked origins; a markdown row per horizon), so the small
  erf-approximation differences in gaussian-crps are immaterial — the qualitative
  skill-decay property is what is pinned, exactly as the Python test pins it."
  (:require [clojure.test :refer [deftest is testing]]
            [clojure.string :as str]
            [mitooshi.methods.horizon :as horizon]))

(deftest path-is-deterministic-and-mean-reverting
  (let [a (horizon/build-path 50)
        b (horizon/build-path 50)]
    (is (= a b))                                      ; reproducible (no RNG)
    (is (every? #(< 5.0 % 15.0) a))))                 ; mean-reverting near MU=10

(deftest short-horizon-has-positive-skill
  (let [rows (horizon/horizon-skill)
        h1 (first (filter #(= 1 (get % "h")) rows))]
    (is (> (get h1 "skill_vs_clim") 0.1))))           ; clearly beats climatology at h=1

(deftest skill-decays-with-horizon
  (let [rows (horizon/horizon-skill)
        first-r (first rows)
        last-r (last rows)]
    (is (> (get first-r "skill_vs_clim") (get last-r "skill_vs_clim")))   ; decays
    (is (< (get last-r "skill_vs_clim") 0.1))))                            ; → ≈ climatology

(deftest crps-grows-with-horizon
  (let [rows (horizon/horizon-skill)]
    (is (> (get (last rows) "mean_crps") (get (first rows) "mean_crps")))))  ; uncertainty accumulates

(deftest leak-free-every-origin-scored
  (let [rows (horizon/horizon-skill)]
    (is (every? #(> (get % "n") 10) rows))))          ; many leak-checked origins per horizon

(deftest render-md-has-a-row-per-horizon
  (let [rows (horizon/horizon-skill)
        md (horizon/render-md rows)]
    (doseq [r rows]
      (is (str/includes? md (str "| " (get r "h") " |"))))
    (is (str/includes? md "skill vs clim"))))
