#!/usr/bin/env bb
;; Babashka test for mitooshi.methods.score (score.cljc).
;; Port of methods/test_score.py. Run from the worktree root:
;;   bb --classpath 20-actors 20-actors/mitooshi/methods/test_score.clj
(ns mitooshi.methods.test-score
  "Faithful Clojure port of test_score.py — proper-scoring-rule parity tests.
  Constitutional invariants: G1 (point-asserted refused), G2 (speculative use refused),
  G5 (leak-free — obs not strictly after info-as-of RAISES). ADR-2606051800."
  (:require [clojure.test :refer [deftest is are testing run-tests]]
            [mitooshi.methods.score :as score]))

;; ── score-set: local aggregator (score_set from score.py, composed from score.cljc fns) ─
;; score_set is present in score.py but was not ported into score.cljc.
;; Rather than modifying the .cljc, we implement it here as a pure test helper so every
;; test_score.py test case is covered faithfully.
(defn- score-set
  "Aggregate a set of leak-checked pairs into a scorecard + calibration + (optional)
  skill vs a parallel baseline score list. The model is 'skilled' only if mean skill
  on the primary metric is > 0 (G12). Mirrors score.py score_set."
  ([pairs] (score-set pairs nil))
  ([pairs baseline]
   (let [rows (mapv (fn [[fc obs]] (score/score-pair fc obs)) pairs)
         metrics ["crps" "pinball" "log_score" "brier"]
         agg (reduce (fn [m metric]
                       (let [vals (keep #(get % metric) rows)]
                         (if (seq vals)
                           (assoc m metric (/ (reduce + 0.0 vals) (count vals)))
                           m)))
                     {} metrics)
         pit-vals (keep #(get % "pit") rows)
         calib (score/calibration-summary (vec pit-vals))
         [skill skilled]
         (if baseline
           (let [primary (cond (contains? agg "crps")    "crps"
                               (contains? agg "pinball")  "pinball"
                               (contains? agg "brier")    "brier"
                               :else nil)]
             (if primary
               (let [b-vals (keep #(get % primary) baseline)]
                 (if (seq b-vals)
                   (let [b-mean (/ (reduce + 0.0 b-vals) (count b-vals))
                         sk (score/skill-score (get agg primary) b-mean)]
                     [sk (> sk 0.0)])
                   [nil nil]))
               [nil nil]))
           [nil nil])]
     {"n"           (count rows)
      "metrics"     agg
      "calibration" calib
      "skill"       skill
      "skilled"     skilled
      "rows"        rows})))

;; ── CRPS ────────────────────────────────────────────────────────────────────
(deftest test-crps-standard-normal-at-mean
  ;; Known closed-form value: CRPS(N(0,1), 0) = 2*phi(0) - 1/sqrt(pi) ≈ 0.23370.
  (is (< (Math/abs (- (score/gaussian-crps 0.0 1.0 0.0) 0.23370)) 1e-4)))

(deftest test-crps-collapses-to-abs-error-as-sigma-to-zero
  (is (< (Math/abs (- (score/gaussian-crps 10.0 1e-12 11.0) 1.0)) 1e-6)))

(deftest test-crps-nonnegative-and-scales-with-sigma
  (is (> (score/gaussian-crps 0.0 1.0 3.0) 0))
  ;; a wider distribution that still covers the outcome scores better when off-target
  (let [near (score/gaussian-crps 0.0 1.0 5.0)
        wide (score/gaussian-crps 0.0 3.0 5.0)]
    (is (< wide near))))  ; honest uncertainty beats overconfident miss

(deftest test-crps-better-forecast-scores-lower
  (let [good (score/gaussian-crps 10.0 2.0 10.2)
        bad  (score/gaussian-crps 4.0  2.0 10.2)]
    (is (< good bad))))

;; ── log score / PIT ──────────────────────────────────────────────────────────
(deftest test-logscore-minimized-near-mean
  (is (< (score/gaussian-logscore 10.0 2.0 10.0)
         (score/gaussian-logscore 10.0 2.0 16.0))))

(deftest test-pit-is-half-at-mean-and-monotone
  (is (< (Math/abs (- (score/gaussian-pit 5.0 2.0 5.0) 0.5)) 1e-9))
  (is (< (score/gaussian-pit 5.0 2.0 1.0) 0.5))
  (is (> (score/gaussian-pit 5.0 2.0 9.0) 0.5)))

;; ── pinball / quantile ────────────────────────────────────────────────────────
(deftest test-pinball-zero-when-median-equals-outcome
  ;; single median quantile at the outcome → loss 0
  (is (== (score/pinball-loss {0.5 7.0} 7.0) 0.0)))

(deftest test-pinball-positive-and-asymmetric
  (let [q {0.1 2.0, 0.5 5.0, 0.9 8.0}]
    (is (> (score/pinball-loss q 5.0) 0))
    ;; an outcome in the upper tail is penalised by the lower quantiles
    (is (> (score/pinball-loss q 9.0) (score/pinball-loss q 5.0)))))

(deftest test-quantile-pit-brackets
  (let [q {0.1 2.0, 0.5 5.0, 0.9 8.0}]
    (is (== (score/quantile-pit q 1.0) 0.0))   ; below the span
    (is (== (score/quantile-pit q 9.0) 1.0))   ; above the span
    (is (< (Math/abs (- (score/quantile-pit q 5.0) 0.5)) 1e-9))))

;; ── brier / categorical ──────────────────────────────────────────────────────
(deftest test-brier-perfect-confident-is-zero
  (is (== (score/brier-score {"up" 1.0, "flat" 0.0, "down" 0.0} "up") 0.0)))

(deftest test-brier-worst-confident-wrong
  ;; confidently wrong: (1-0)^2 + (0-1)^2 = 2
  (is (< (Math/abs (- (score/brier-score {"up" 1.0, "down" 0.0} "down") 2.0)) 1e-9)))

(deftest test-categorical-logscore-penalises-low-prob-truth
  (is (> (score/categorical-logscore {"a" 0.9, "b" 0.1} "b")
         (score/categorical-logscore {"a" 0.9, "b" 0.1} "a"))))

;; ── ensemble (energy-form CRPS) ───────────────────────────────────────────────
(deftest test-ensemble-crps-known-value
  ;; members {-1, 1}, y=0: term1 = (1+1)/2 = 1; term2 = (0+2+2+0)/(2*4) = 0.5 → 0.5
  (is (< (Math/abs (- (score/ensemble-crps [-1.0 1.0] 0.0) 0.5)) 1e-9)))

(deftest test-ensemble-crps-reduces-to-abs-error-for-singleton
  (is (< (Math/abs (- (score/ensemble-crps [3.0] 5.0) 2.0)) 1e-9)))

(deftest test-ensemble-crps-tight-correct-beats-vague
  (let [tight (score/ensemble-crps [9.9 10.0 10.1] 10.0)
        vague (score/ensemble-crps [2.0 10.0 18.0] 10.0)]
    (is (< tight vague))))

(deftest test-ensemble-pit-fraction-at-or-below
  (is (== (score/ensemble-pit [1.0 2.0 3.0 4.0] 2.5) 0.5)))

(deftest test-score-pair-valid-ensemble
  (let [fc (score/->forecast "e" "ensemble" :info-as-of 100 :members [9.0 10.0 11.0])
        r  (score/score-pair fc (score/->observation "o" :observed-at 101 :value 10.0))]
    (is (contains? r "crps"))
    (is (contains? r "pit"))
    (is (>= (get r "crps") 0))))

;; ── baselines + skill ────────────────────────────────────────────────────────
(deftest test-climatology-and-persistence
  (let [hist [4.0 5.0 6.0 5.0 4.0]
        [mu-c sd-c] (score/climatology-gaussian hist)
        [mu-p sd-p] (score/persistence-gaussian hist)]
    (is (< (Math/abs (- mu-c 4.8)) 1e-9))
    (is (> sd-c 0))
    (is (== mu-p 4.0))
    (is (> sd-p 0))))

(deftest test-skill-positive-when-model-beats-baseline
  (is (== (score/skill-score 0.5 1.0) 0.5))      ; half the error → skill 0.5
  (is (< (score/skill-score 1.5 1.0) 0)))         ; worse than baseline → negative

;; ── leak-free pair scorer (G5) ───────────────────────────────────────────────
(deftest test-score-pair-rejects-lookahead-leak
  (let [fc   (score/->forecast "f" "gaussian" :info-as-of 100 :mean 10.0 :sd 2.0)
        leak (score/->observation "o" :observed-at 100 :value 10.0)]  ; NOT strictly after
    (is (thrown-with-msg? clojure.lang.ExceptionInfo #"G5 LEAK"
                          (score/score-pair fc leak)))))

(deftest test-score-pair-rejects-point-assertion
  (let [fc (score/->forecast "f" "gaussian" :info-as-of 100 :mean 10.0 :sd 2.0
                              :point-asserted true)
        ob (score/->observation "o" :observed-at 101 :value 10.0)]
    (is (thrown-with-msg? clojure.lang.ExceptionInfo #"G1"
                          (score/score-pair fc ob)))))

(deftest test-score-pair-rejects-speculative-use
  (let [fc (score/->forecast "f" "gaussian" :info-as-of 100 :mean 10.0 :sd 2.0
                              :use "trade")
        ob (score/->observation "o" :observed-at 101 :value 10.0)]
    (is (thrown-with-msg? clojure.lang.ExceptionInfo #"G2"
                          (score/score-pair fc ob)))))

(deftest test-score-pair-valid-gaussian
  (let [fc (score/->forecast "f" "gaussian" :info-as-of 100 :mean 10.0 :sd 2.0)
        ob (score/->observation "o" :observed-at 101 :value 11.0)
        r  (score/score-pair fc ob)]
    (is (contains? r "crps"))
    (is (contains? r "log_score"))
    (is (contains? r "pit"))
    (is (> (get r "crps") 0))))

;; ── calibration ──────────────────────────────────────────────────────────────
(deftest test-calibration-uniform-pit-low-deviation
  (let [pits (mapv (fn [i] (/ (+ i 0.5) 20.0)) (range 20))  ; evenly spread → near-uniform
        c    (score/calibration-summary pits 10)]
    (is (< (Math/abs (- (get c "pit_mean") 0.5)) 1e-9))
    (is (< (get c "deviation") 1e-9))))

(deftest test-calibration-clustered-pit-high-deviation
  (let [pits (vec (repeat 20 0.01))  ; all in the first bin → maximally miscalibrated
        c    (score/calibration-summary pits 10)]
    (is (> (get c "deviation") 1.5))))

;; ── set-level skill (G12) via local score-set helper ────────────────────────
(deftest test-score-set-marks-skilled-only-when-beating-baseline
  (let [pairs (mapv (fn [i]
                      [(score/->forecast (str "f" i) "gaussian"
                                         :info-as-of (+ 100 i)
                                         :mean 10.0 :sd 2.0)
                       (score/->observation (str "o" i)
                                            :observed-at (+ 200 i)
                                            :value (+ 10.0 (* 0.1 i)))])
                    (range 5))
        ;; baseline that is much worse (huge CRPS)
        baseline (vec (repeat 5 {"crps" 5.0}))
        res      (score-set pairs baseline)]
    (is (= (get res "n") 5))
    (is (true? (get res "skilled")))
    (is (> (get res "skill") 0))
    ;; a strong baseline the model cannot beat → honest not-skilled
    (let [res2 (score-set pairs (vec (repeat 5 {"crps" 0.01})))]
      (is (false? (get res2 "skilled"))))))

;; ── numeric parity spot-checks (clj vs python) ───────────────────────────────
;; These serve as regression anchors tying the CLJ values to the Python output.
(deftest test-parity-crps-known
  ;; Python: gaussian_crps(0,1,0) = 0.23369498...
  (let [v (score/gaussian-crps 0.0 1.0 0.0)]
    (is (< (Math/abs (- v 0.23369498)) 1e-6))))

(deftest test-parity-ensemble-crps-known
  ;; Python: ensemble_crps([-1,1], 0) = 0.5 (exact)
  (is (< (Math/abs (- (score/ensemble-crps [-1.0 1.0] 0.0) 0.5)) 1e-9)))

(deftest test-parity-pinball-known
  ;; Python: pinball_loss({0.1:2, 0.5:5, 0.9:8}, 5.0) ≈ 0.2
  (let [v (score/pinball-loss {0.1 2.0, 0.5 5.0, 0.9 8.0} 5.0)]
    (is (< (Math/abs (- v 0.2)) 1e-9))))

;; ── entry point ──────────────────────────────────────────────────────────────
(when (= *file* (System/getProperty "babashka.file"))
  (let [{:keys [fail error]} (clojure.test/run-tests 'mitooshi.methods.test-score)]
    (System/exit (if (zero? (+ fail error)) 0 1))))
