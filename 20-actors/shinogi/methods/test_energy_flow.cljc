#!/usr/bin/env bb
;; shinogi 鎬 — wellbecoming energy-flow design tests.
(ns shinogi.methods.test-energy-flow
  (:require [shinogi.methods.energy-flow :as ef]
            [clojure.test :refer [deftest is run-tests]]))

(deftest channels-conserve-the-flow
  (let [total (reduce + (map :current ef/channels))]
    (is (< (Math/abs (- total 1.0)) 1e-9) "effort-energy shares sum to 1.0 (conserved flow)")))

(deftest design-increases-wellbecoming
  (let [d (ef/design)]
    (is (> (:designed-wellbecoming d) (:current-wellbecoming d))
        "the re-routing raises wellbecoming")
    (is (pos? (:wellbecoming-gain d)))
    (is (pos? (:effort-re-routed d)) "some effort is actually re-routed")))

(deftest design-conserves-flow
  (let [d (ef/design)
        total (reduce + (vals (:designed-allocation d)))]
    (is (< (Math/abs (- total 1.0)) 1e-6) "designed allocation still sums to 1.0 (energy conserved)")))

(deftest design-is-a-candidate-not-a-directive
  (let [d (ef/design)]
    (is (false? (:prescription? d)) "G11 — a candidate, never a directive")
    (is (true? (:hypothesis? d)) "G5 hypothesis")))

(deftest two-ledgers-never-conflated
  ;; uzu G1/G2 — effort (flow) and wellbecoming (index) are distinct; the note says so
  (let [d (ef/design)]
    (is (re-find #"never an identity" (:two-ledger-note d))
        "the design states effort-energy and wellbecoming are never the same unit")))

(deftest drive-overrides-are-relief-only
  ;; every override is a RELIEF (negative drive delta) — the re-routing never adds pressure
  (let [d (ef/design)]
    (is (seq (:drive-overrides d)) "produces drive-overrides for simulate")
    (is (every? #(<= % 0.0) (vals (:drive-overrides d)))
        "every drive-override is relief (≤0), never added pressure")))

#?(:clj
   (defn -main [& _]
     (let [r (run-tests 'shinogi.methods.test-energy-flow)]
       (System/exit (if (zero? (+ (:fail r) (:error r))) 0 1)))))
