#!/usr/bin/env bb
;; Working Clojure port of methods/test_agv_transfer.py.
(ns niyaku.methods.test-agv-transfer
  "Tests for agv_transfer — AGV horizontal-transport planning core.

  Run:  bb --classpath 20-actors 20-actors/niyaku/methods/test_agv_transfer.clj"
  (:require [niyaku.methods.agv-transfer :as a]
            [clojure.test :refer [deftest is run-tests]]))

(defn- approx [x y] (<= (Math/abs (double (- x y))) 1e-6))

(deftest zero-and-negative-distance
  (let [agv (a/make-agv)]
    (is (= (a/travel-time 0.0 agv) 0.0))
    (is (thrown? clojure.lang.ExceptionInfo (a/travel-time -1.0 agv)))))

(deftest trapezoidal-long-leg-reaches-cruise
  (let [agv (a/make-agv :v-max 6.0 :a-max 0.8)
        d 200.0
        t (a/travel-time d agv)
        expected (+ (* 2 (/ (:v-max agv) (:a-max agv)))
                    (/ (- d (/ (* (:v-max agv) (:v-max agv)) (:a-max agv))) (:v-max agv)))]
    (is (approx t expected))
    (is (< (/ d t) (:v-max agv)))))                ; average speed below v_max

(deftest triangular-short-leg-below-cruise
  (let [agv (a/make-agv :v-max 6.0 :a-max 0.8)
        d 10.0                                      ; too short to reach v_max (needs 45 m)
        t (a/travel-time d agv)
        vp (Math/sqrt (* (:a-max agv) d))]
    (is (< vp (:v-max agv)))
    (is (approx t (/ (* 2 vp) (:a-max agv))))))

(deftest travel-time-monotone-in-distance
  (let [agv (a/make-agv)
        ts (map #(a/travel-time % agv) [5 20 45 100 300])]
    (is (= ts (sort ts)))))

(deftest reservation-conflict-same-segment-overlap
  (is (a/reservations-conflict? (a/reservation "S1" "AGV1" 0.0 10.0)
                                (a/reservation "S1" "AGV2" 5.0 15.0))))

(deftest reservation-touching-endpoints-no-conflict
  (is (not (a/reservations-conflict? (a/reservation "S1" "AGV1" 0.0 10.0)
                                     (a/reservation "S1" "AGV2" 10.0 20.0)))))

(deftest reservation-different-segment-or-same-agv
  (let [base (a/reservation "S1" "AGV1" 0.0 10.0)]
    (is (not (a/reservations-conflict? base (a/reservation "S2" "AGV2" 0.0 10.0))))
    (is (not (a/reservations-conflict? base (a/reservation "S1" "AGV1" 0.0 10.0))))))

(deftest find-conflicts-pairs
  (let [rs [(a/reservation "S1" "A" 0 10)
            (a/reservation "S1" "B" 5 12)          ; conflicts with 0
            (a/reservation "S2" "C" 0 10)]]        ; different segment
    (is (= (a/find-conflicts rs) [[0 1]]))))

(deftest dispatch-balances-makespan
  (let [agv (a/make-agv)
        moves (map-indexed (fn [i d] (a/move (str "m" i) d)) [100 100 100 100])
        res (a/dispatch moves ["AGV1" "AGV2"] agv)]
    (is (every? #(= (count %) 2) (vals (:assignment res))))   ; 2 each, balanced
    (is (approx (a/makespan res) (* 2 (a/travel-time 100 agv))))))

(deftest dispatch-lpt-puts-long-jobs-first
  (let [agv (a/make-agv)
        moves [(a/move "big" 300) (a/move "s1" 20) (a/move "s2" 20)]
        res (a/dispatch moves ["AGV1" "AGV2"] agv)
        sizes (sort (map count (vals (:assignment res))))]
    (is (= sizes [1 2]))                            ; big alone, two small together
    (is (> (a/makespan res) 0))))

(deftest dispatch-requires-agv
  (is (thrown? clojure.lang.ExceptionInfo (a/dispatch [(a/move "m" 10)] [] (a/make-agv)))))

(when (= *file* (System/getProperty "babashka.file"))
  (let [{:keys [fail error]} (run-tests 'niyaku.methods.test-agv-transfer)]
    (System/exit (if (zero? (+ fail error)) 0 1))))
