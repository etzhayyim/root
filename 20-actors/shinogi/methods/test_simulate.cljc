#!/usr/bin/env bb
;; shinogi 鎬 — stock-flow simulation tests.
(ns shinogi.methods.test-simulate
  (:require [shinogi.methods.shinogi-edn :as se]
            [shinogi.methods.simulate :as sim]
            [shinogi.methods.energy-flow :as ef]
            [clojure.test :refer [deftest is run-tests]]))

(def seed-path "20-actors/shinogi/kotoba/seed.exam-involution.edn")
(defn- ds* [] (se/drivers seed-path))

(deftest baseline-runs-deterministically
  (let [r1 (sim/run (ds*))
        r2 (sim/run (ds*))]
    (is (= r1 r2) "deterministic — same drivers → identical trajectory (no Math/random)")
    (is (= 9 (count (:equilibrium r1))) "all nine stocks reach an equilibrium")
    (is (number? (:involution-index r1)))
    (is (true? (:hypothesis? r1)) "flagged hypothesis (G5)")))

(deftest baseline-spiral-is-elevated
  (let [eq (:equilibrium (sim/run (ds*)))]
    ;; the vicious involution core climbs high without intervention
    (is (>= (get eq "effort-inflation") 0.6) "effort-inflation runs hot in the baseline")
    (is (>= (get eq "effort-efficacy-collapse") 0.5) "頑張れない climbs in the baseline")))

(deftest intervention-eases-the-spiral
  ;; the energy-flow design's drive-overrides should LOWER the involution index
  (let [overrides (:drive-overrides (ef/design))
        cmp (sim/compare-scenarios (ds*) overrides)]
    (is (false? (:forecast? cmp)) "a structural what-if, never a forecast (N3)")
    (is (pos? (:index-improvement cmp))
        "the wellbecoming energy-flow re-routing eases the involution (index improves)")
    ;; every stock should be ≤ baseline (relief, not displacement)
    (is (every? #(<= % 0.0) (vals (:stock-deltas cmp)))
        "no stock is made worse by the relief intervention")))

#?(:clj
   (defn -main [& _]
     (let [r (run-tests 'shinogi.methods.test-simulate)]
       (System/exit (if (zero? (+ (:fail r) (:error r))) 0 1)))))
