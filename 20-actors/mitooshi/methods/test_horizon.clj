#!/usr/bin/env bb
;; Tests for mitooshi multi-horizon skill-decay analysis (methods/horizon.clj).
;; 1:1 port of test_horizon.py — all 6 test cases, every assertion preserved.
;;
;; Run:
;;   bb --classpath 20-actors 20-actors/mitooshi/methods/test_horizon.clj
;;
;; The .cljc sibling (test_horizon.cljc) defines the same ns but its -main is never
;; invoked by bb, so it prints nothing and exits 0 (a false-green). This .clj file
;; runs exactly the 6 tests and confirms "Ran 6 tests" — proof the correct file loaded.
(ns mitooshi.methods.test-horizon
  (:require [clojure.test :refer [deftest is run-tests]]
            [clojure.string :as str]
            [mitooshi.methods.horizon :as horizon]))

;; ── ported test cases ────────────────────────────────────────────────────────

(deftest test-path-is-deterministic-and-mean-reverting
  ;; reproducible (no RNG) + stays near MU=10
  (let [a (horizon/build-path 50)
        b (horizon/build-path 50)]
    (is (= a b) "build-path must be deterministic")
    (is (every? #(and (< 5.0 %) (< % 15.0)) a)
        "path must stay near MU=10 (mean-reverting, not a random walk)")))

(deftest test-short-horizon-has-positive-skill
  ;; clearly beats climatology at h=1
  (let [rows (horizon/horizon-skill)
        h1   (first (filter #(= 1 (get % "h")) rows))]
    (is (> (get h1 "skill_vs_clim") 0.1)
        "h=1 skill must be clearly positive (> 0.1)")))

(deftest test-skill-decays-with-horizon
  ;; skill falls with horizon; long-range → near-zero skill
  (let [rows  (horizon/horizon-skill)
        first* (first rows)
        last*  (peek rows)]
    (is (> (get first* "skill_vs_clim") (get last* "skill_vs_clim"))
        "skill must decrease from first to last horizon")
    (is (< (get last* "skill_vs_clim") 0.1)
        "long-range skill must be near or below zero (≈ climatology)")))

(deftest test-crps-grows-with-horizon
  ;; uncertainty accumulates — CRPS at the longest horizon exceeds the shortest
  (let [rows (horizon/horizon-skill)]
    (is (> (get (peek rows) "mean_crps") (get (first rows) "mean_crps"))
        "mean CRPS must grow with horizon")))

(deftest test-leak-free-every-origin-scored
  ;; many origins scored per horizon; each scored via score-pair which raises on G5 leak
  (let [rows (horizon/horizon-skill)]
    (is (every? #(> (get % "n") 10) rows)
        "every horizon must have > 10 leak-checked origins")))

(deftest test-render-md-has-a-row-per-horizon
  ;; markdown table contains a row for every horizon h
  (let [rows (horizon/horizon-skill)
        md   (horizon/render-md rows)]
    (doseq [r rows]
      (is (str/includes? md (str "| " (get r "h") " |"))
          (str "render-md must contain a row for h=" (get r "h"))))
    (is (str/includes? md "skill vs clim")
        "render-md must contain 'skill vs clim' header")))

;; ── entry point ──────────────────────────────────────────────────────────────

(when (= *file* (System/getProperty "babashka.file"))
  (let [{:keys [fail error]} (clojure.test/run-tests 'mitooshi.methods.test-horizon)]
    (System/exit (if (zero? (+ fail error)) 0 1))))
