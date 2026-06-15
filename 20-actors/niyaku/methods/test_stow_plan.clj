#!/usr/bin/env bb
;; Working Clojure port of methods/test_stow_plan.py.
(ns niyaku.methods.test-stow-plan
  "Tests for stow_plan — stowage slotting + discharge sequencing.

  Run:  bb --classpath 20-actors 20-actors/niyaku/methods/test_stow_plan.clj"
  (:require [niyaku.methods.stow-plan :as st]
            [clojure.test :refer [deftest is run-tests]]))

(defn- rot-index [rotation] (into {} (map-indexed (fn [i p] [p i]) rotation)))

(deftest simple-plan-places-all
  (let [rotation ["SHA" "SIN" "ROT"]
        boxes [(st/container "A" 22.0 "ROT")    ; last off → heaviest → bottom
               (st/container "B" 18.0 "SIN")
               (st/container "C" 14.0 "SHA")]   ; first off → lightest → top
        plan (st/build-stow-plan boxes rotation 1 1 3)]
    (is (= (set (keys (:assignments plan))) #{"A" "B" "C"}))
    (is (< (:tier (st/slot-of plan "A")) (:tier (st/slot-of plan "B"))))
    (is (< (:tier (st/slot-of plan "B")) (:tier (st/slot-of plan "C"))))
    (let [box-port (into {} (map (juxt :box-id :discharge-port) boxes))]
      (is (st/validate-no-rehandle plan (rot-index rotation) box-port)))))

(deftest weight-on-top-not-violated
  (let [plan (st/build-stow-plan [(st/container "light" 5.0 "P1")
                                  (st/container "heavy" 25.0 "P1")] ["P1"] 1 1 2)]
    (is (< (:tier (st/slot-of plan "heavy")) (:tier (st/slot-of plan "light"))))))

(deftest capacity-exceeded-raises
  (is (thrown? clojure.lang.ExceptionInfo
               (st/build-stow-plan (map #(st/container (str "b" %) 10.0 "P1") (range 5))
                                   ["P1"] 1 1 4))))

(deftest reefer-only-in-reefer-rows
  (let [plan (st/build-stow-plan [(st/container "r" 10.0 "P1" :reefer true)]
                                 ["P1"] 1 2 1 :reefer-rows [1])]
    (is (= (:row (st/slot-of plan "r")) 1))))

(deftest reefer-infeasible-when-no-reefer-row
  (is (thrown? clojure.lang.ExceptionInfo
               (st/build-stow-plan [(st/container "r" 10.0 "P1" :reefer true)]
                                   ["P1"] 1 1 1 :reefer-rows []))))

(deftest hazmat-segregation-separates-classes
  (let [boxes [(st/container "flam" 10.0 "P1" :hazmat "3")
               (st/container "oxid" 10.0 "P1" :hazmat "5.1")]
        plan (st/build-stow-plan boxes ["P1"] 2 1 2)]
    (is (not= [(:bay (st/slot-of plan "flam")) (:row (st/slot-of plan "flam"))]
              [(:bay (st/slot-of plan "oxid")) (:row (st/slot-of plan "oxid"))]))
    (is (thrown? clojure.lang.ExceptionInfo (st/build-stow-plan boxes ["P1"] 1 1 2)))))

(deftest unknown-port-raises
  (is (thrown? clojure.lang.ExceptionInfo
               (st/build-stow-plan [(st/container "x" 1.0 "ZZZ")] ["P1"] 1 1 1))))

(deftest empty-rotation-raises
  (is (thrown? clojure.lang.ExceptionInfo (st/build-stow-plan [] [] 1 1 1))))

(deftest discharge-sequence-top-first
  (let [boxes (map #(st/container (str "b" %) (- 10.0 %) "P1") (range 3))
        plan (st/build-stow-plan boxes ["P1"] 1 1 3)
        seq* (st/discharge-sequence plan "P1")
        tiers (map #(:tier (st/slot-of plan %)) seq*)]
    (is (= tiers (sort > tiers)))))   ; top tier discharged first

(deftest weight-on-top-forces-new-column
  ;; a heavy early-discharge box cannot sit on a light late-discharge box → fresh column
  (let [plan (st/build-stow-plan [(st/container "late_light" 10.0 "P1")
                                  (st/container "early_heavy" 20.0 "P0")] ["P0" "P1"] 2 1 2)]
    (is (not= (:bay (st/slot-of plan "late_light")) (:bay (st/slot-of plan "early_heavy"))))))

(deftest validate-no-rehandle-detects-violation
  ;; a hand-built plan with a later-discharge box stacked above an earlier one → false
  (let [plan {:assignments {"below_early" (st/slot 0 0 0)    ; P0 (early) at bottom — bad
                            "above_late" (st/slot 0 0 1)}    ; P1 (late) on top — buries early
              :rotation []}]
    (is (false? (st/validate-no-rehandle plan {"P0" 0 "P1" 1}
                                         {"below_early" "P0" "above_late" "P1"})))))

(deftest slot-key-test
  (is (= (st/slot-key (st/slot 1 2 3)) [1 2 3])))

(deftest stow-errors-are-typed
  (is (try (st/build-stow-plan [] [] 1 1 1) false
           (catch clojure.lang.ExceptionInfo e (st/stow-error? e)))))

(when (= *file* (System/getProperty "babashka.file"))
  (let [{:keys [fail error]} (run-tests 'niyaku.methods.test-stow-plan)]
    (System/exit (if (zero? (+ fail error)) 0 1))))
