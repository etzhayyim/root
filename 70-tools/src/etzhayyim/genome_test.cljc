(ns etzhayyim.genome-test
  "Tests for the kotoba-genome W2 closed learning loop (ADR-2606302205 D1).
  Run: bb test:genome"
  (:require [clojure.test :refer [deftest is testing]]
            [etzhayyim.genome :as g]))

(def catalog
  [{:mechanism :deepen-tests :base 1.0}
   {:mechanism :widen-perception :base 1.0}
   {:mechanism :prune-stubs :base 1.0}])

(deftest scoring-is-proper-and-leak-free
  (testing "a confident correct prediction scores high; a confident wrong one low"
    (let [st {:pending {:mechanism :deepen-tests :predicted-up 0.9 :reading-at-act 100}}]
      (is (> (:score (g/score-pending st 120)) 0.95))   ; predicted up, reading rose
      (is (true? (:actual-up (g/score-pending st 120))))
      (is (< (:score (g/score-pending st 80)) 0.25))))  ; predicted up, reading fell
  (testing "no pending → nil (first beat)"
    (is (nil? (g/score-pending {} 100)))))

(deftest kaizen-update-amplifies-and-suppresses
  (testing "verified (score>0.5) amplifies; falsified suppresses; bounded"
    (is (> (get (g/update-weights {} :m 0.9) :m) 1.0))
    (is (< (get (g/update-weights {} :m 0.1) :m) 1.0))
    (is (= g/weight-ceil (get (g/update-weights {:m 1.95} :m 1.0) :m)))   ; clamped high
    (is (= g/weight-floor (get (g/update-weights {:m 0.3} :m 0.0) :m))))) ; clamped low

(deftest prior-consensus-folds-history
  (testing "a mechanism scored up repeatedly gains confidence"
    (let [hist [{:scored {:mechanism :deepen-tests :actual-up true :score 0.9}}
                {:scored {:mechanism :deepen-tests :actual-up true :score 0.8}}
                {:scored {:mechanism :prune-stubs :actual-up false :score 0.2}}]
          pc (g/prior-consensus {:history hist})]
      (is (= 2 (get-in pc [:deepen-tests :n])))
      (is (> (get-in pc [:deepen-tests :confidence]) 0.7))
      (is (< (get-in pc [:prune-stubs :confidence]) 0.5)))))

(deftest beat-closes-the-loop
  (testing "first beat: no score yet, pre-registers a prediction"
    (let [s1 (g/beat g/empty-state catalog 100)]
      (is (= 1 (:beat s1)))
      (is (some? (:pending s1)))
      (is (= :dry-run (get-in s1 [:recommendation :status])))
      (is (nil? (:scored (last (:history s1)))))))
  (testing "second beat scores the first prediction against the new reading"
    (let [s1 (g/beat g/empty-state catalog 100)
          s2 (g/beat s1 catalog 130)]                  ; reading rose
      (is (= 2 (:beat s2)))
      (is (some? (:scored (last (:history s2)))))
      ;; the mechanism chosen at s1 was scored; if it predicted-up and reading rose it is amplified
      (let [m (get-in s1 [:pending :mechanism])]
        (is (not= 1.0 (get-in s2 [:weights m])))))))

(deftest replay-is-deterministic
  (testing "folding the same readings twice yields identical state (crash-resume)"
    (let [readings [100 120 110 140 90 160]
          a (g/replay g/empty-state catalog readings)
          b (g/replay g/empty-state catalog readings)]
      (is (= a b))
      (is (= 6 (:beat a)))
      (is (= 6 (count (:history a)))))))

(deftest learning-favours-the-calibrated-mechanism
  (testing "a mechanism that keeps predicting-up correctly accrues weight + is chosen"
    ;; drive a monotonically rising reading; the loop's chosen mechanism that
    ;; predicts up and is verified gets amplified beat over beat.
    (let [s (g/replay g/empty-state catalog [100 110 120 130 140 150 160])
          ws (:weights s)
          maxw (apply max (vals ws))]
      (is (> maxw 1.0))                                  ; at least one mechanism amplified
      (is (<= maxw g/weight-ceil)))))                    ; bounded
