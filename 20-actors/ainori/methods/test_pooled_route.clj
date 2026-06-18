#!/usr/bin/env bb
;; Working Clojure port of methods/test_pooled_route.py.
(ns ainori.methods.test-pooled-route
  "test_pooled_route — pins ainori's pooled sequencing to the todoke route core (ADR-2606071500).

  The headline test (`parity-with-todoke`) is the proof of the reuse claim: on todoke's shared
  pedestrian fixture, ainori's `sequence-stops` returns the SAME visiting order + length that
  todoke's `plan_last_mile` produces ([0 4 1 2 3], len 9.650282, captured from the Python
  todoke core). A Clojure ns cannot import the Python module across the language boundary, so
  the parity is pinned statically against that known-good order — if ainori's sequencer ever
  forks from the todoke algorithm, the order/length changes and this test breaks.

  Run:  bb --classpath 20-actors 20-actors/ainori/methods/test_pooled_route.clj"
  (:require [ainori.methods.pooled-route :as pr]
            [clojure.test :refer [deftest is run-tests]]))

(defn- fixture []
  ;; the same pedestrian fixture todoke.plan_last_mile accepts
  [{:id 0 :x 0.0 :y 0.0 :zone "sidewalk"}
   {:id 1 :x 3.0 :y 0.0 :zone "sidewalk"}
   {:id 2 :x 3.0 :y 3.0 :zone "sidewalk"}
   {:id 3 :x 0.0 :y 3.0 :zone "sidewalk"}
   {:id 4 :x 1.0 :y 1.0 :zone "sidewalk"}])

;; ── parity with the todoke route core (the reuse proof) ──────────────────────
(deftest parity-with-todoke
  (let [[order length] (pr/sequence-stops (fixture))]
    (is (= order [0 4 1 2 3]) "SAME visiting order as todoke.plan_last_mile (not a fork)")
    (is (< (Math/abs (- length 9.650282)) 1e-5) "SAME path length as the todoke core")))

;; ── pooled-route ─────────────────────────────────────────────────────────────
(deftest origin-pinned-first
  (let [out (pr/pooled-route [0.0 0.0] [{:id 1 :x 5.0 :y 0.0} {:id 2 :x 1.0 :y 0.0}])]
    (is (= (first (:order out)) 0) "carrier origin pinned")
    (is (= (:occupancy out) 2))))

(deftest vehicular-zone-sequences
  ;; ainori uses road/arterial zones — sequencing works WITHOUT todoke's pedestrian envelope
  (let [out (pr/pooled-route [0.0 0.0]
                             [{:id 1 :x 10.0 :y 0.0 :zone "expressway"}
                              {:id 2 :x 2.0 :y 0.0 :zone "arterial"}])]
    (is (= (:order out) [0 2 1]) "nearest-first sequencing")
    (is (> (:lengthM out) 0))))

(deftest empty-route
  (is (= (pr/sequence-stops []) [[] 0.0])))

;; ── plan-pooled-trip (route + no-surge cost-share) ──────────────────────────
(deftest composes-route-and-cost-share
  (let [out (pr/plan-pooled-trip [0.0 0.0]
                                 [{:id 1 :x 5.0 :y 0.0} {:id 2 :x 1.0 :y 0.0}] 1200000)]
    (is (= (first (:order out)) 0))                         ; routing (todoke core)
    (is (= (:occupancy out) 2))
    (is (= (:costSharePerRiderMinor out) 600000))))        ; cost_share split (no surge)

(deftest no-profit-invariant
  ;; odd cost: per-rider rounds down; total collected ≤ real fuel/wear (carrier absorbs rest)
  (let [out (pr/plan-pooled-trip [0.0 0.0]
                                 [{:id 1 :x 5.0 :y 0.0} {:id 2 :x 1.0 :y 0.0}
                                  {:id 3 :x 3.0 :y 0.0}] 1000000)]
    (is (<= (:totalCollectedMinor out) (:fuelWearMinor out)))))

(deftest pooling-lowers-each-share
  (let [two   (pr/plan-pooled-trip [0.0 0.0]
                                   [{:id 1 :x 1.0 :y 0.0} {:id 2 :x 2.0 :y 0.0}] 1200000)
        three (pr/plan-pooled-trip [0.0 0.0]
                                   [{:id 1 :x 1.0 :y 0.0} {:id 2 :x 2.0 :y 0.0}
                                    {:id 3 :x 3.0 :y 0.0}] 1200000)]
    (is (< (:costSharePerRiderMinor three) (:costSharePerRiderMinor two)))))

(deftest cost-share-is-no-surge-floor
  ;; no demand/time term: share depends only on real cost ÷ occupancy, monotone-decreasing
  (is (= (pr/cost-share 1000000 1) 1000000))
  (is (= (pr/cost-share 1000000 4) 250000))
  (is (= (pr/cost-share 1000000 0) 1000000)))               ; occupancy floored to 1

(when (= *file* (System/getProperty "babashka.file"))
  (let [{:keys [fail error]} (run-tests 'ainori.methods.test-pooled-route)]
    (System/exit (if (zero? (+ fail error)) 0 1))))
