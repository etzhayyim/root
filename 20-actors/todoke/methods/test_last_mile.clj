#!/usr/bin/env bb
;; Working Clojure port of methods/test_last_mile.py + the ainori reuse-parity check.
(ns todoke.methods.test-last-mile
  "Tests for methods/last_mile.clj — sequencer correctness, G7 envelope, courier sizing, and the
  cross-actor reuse parity: ainori's clj sequencer returns the SAME visiting order as todoke's
  plan-last-mile (the ADR-2606071500 'one engine, not a fork' claim, now both in clj).

  Run:  bb --classpath 20-actors 20-actors/todoke/methods/test_last_mile.clj"
  (:require [todoke.methods.last-mile :as lm]
            [ainori.methods.pooled-route :as pr]
            [clojure.test :refer [deftest is run-tests]]))

(defn- collinear []
  [(lm/stop 0 0.0 0.0 "sidewalk") (lm/stop 1 30.0 0.0 "doorpath") (lm/stop 2 10.0 0.0 "sidewalk")
   (lm/stop 3 20.0 0.0 "doorpath") (lm/stop 4 5.0 0.0 "crosswalk")])

(deftest parity-collinear-matches-rust
  (let [[order length] (lm/plan-last-mile (collinear) :sae-level 4 :commanded-mps 1.0)]
    (is (= order [0 4 2 3 1]))                 ; identical to the Rust crate + Python fixture
    (is (< (Math/abs (- length 30.0)) 1e-6))))

(deftest two-opt-removes-crossing-on-square
  (let [sq [(lm/stop 0 0.0 0.0 "sidewalk") (lm/stop 1 0.0 10.0 "sidewalk")
            (lm/stop 2 10.0 10.0 "sidewalk") (lm/stop 3 10.0 0.0 "sidewalk")]
        [_ length] (lm/plan-last-mile sq :commanded-mps 1.5)]
    (is (<= length (+ 30.0 1e-6)))))

(deftest g7-refuses-sae-5
  (is (thrown? clojure.lang.ExceptionInfo (lm/plan-last-mile (collinear) :sae-level 5 :commanded-mps 1.0))))

(deftest g7-refuses-road-zone
  (is (thrown? clojure.lang.ExceptionInfo
               (lm/plan-last-mile (conj (collinear) (lm/stop 9 40.0 0.0 "road")) :commanded-mps 1.0))))

(deftest g7-refuses-speed-over-cap
  (is (thrown? clojure.lang.ExceptionInfo (lm/plan-last-mile (collinear) :commanded-mps 3.0))))

(deftest empty-refused
  (is (thrown? clojure.lang.ExceptionInfo (lm/plan-last-mile []))))

(deftest refusals-are-envelope-violations
  (is (try (lm/plan-last-mile []) false
           (catch clojure.lang.ExceptionInfo e (lm/envelope-violation? e)))))

(deftest courier-sizing-is-positive
  (is (> (lm/courier-freed-hours 1.0e7 2200 0.3) 0))
  (is (= (lm/displacement-cohort-size 1.0e7 0.3) 3000000)))

;; ── cross-actor reuse parity: ainori reuses todoke's sequencer, not a fork ──
(deftest ainori-sequencer-matches-todoke
  (let [fixture [{:id 0 :x 0.0 :y 0.0 :zone "sidewalk"} {:id 1 :x 3.0 :y 0.0 :zone "sidewalk"}
                 {:id 2 :x 3.0 :y 3.0 :zone "sidewalk"} {:id 3 :x 0.0 :y 3.0 :zone "sidewalk"}
                 {:id 4 :x 1.0 :y 1.0 :zone "sidewalk"}]
        [order-a len-a] (pr/sequence-stops fixture)
        [order-t len-t] (lm/plan-last-mile (mapv #(lm/stop (:id %) (:x %) (:y %) (:zone %)) fixture)
                                           :sae-level 4 :commanded-mps 1.5)]
    (is (= order-a order-t) "ainori clj sequencer == todoke clj plan-last-mile (one engine, not a fork)")
    (is (< (Math/abs (- len-a len-t)) 1e-9))))

(when (= *file* (System/getProperty "babashka.file"))
  (let [{:keys [fail error]} (run-tests 'todoke.methods.test-last-mile)]
    (System/exit (if (zero? (+ fail error)) 0 1))))
