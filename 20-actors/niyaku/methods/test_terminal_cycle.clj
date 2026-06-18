#!/usr/bin/env bb
;; Working Clojure port of methods/test_terminal_cycle.py.
(ns niyaku.methods.test-terminal-cycle
  "Tests for terminal_cycle — end-to-end vessel-discharge orchestration.

  Run:  bb --classpath 20-actors 20-actors/niyaku/methods/test_terminal_cycle.clj"
  (:require [niyaku.methods.terminal-cycle :as tc]
            [niyaku.methods.crane-dynamics :as cd]
            [niyaku.methods.agv-transfer :as agv]
            [niyaku.methods.stow-plan :as st]
            [clojure.test :refer [deftest is run-tests]]))

(defn- approx [a b] (<= (Math/abs (double (- a b))) 1e-6))
(defn- boxes
  ([n] (boxes n "JPYOK"))
  ([n port] (map-indexed (fn [i _] (st/container (str "B" i) (- 20.0 i) port)) (range n))))

(deftest basic-discharge-runs-all-boxes
  (let [r (tc/simulate-discharge (boxes 6) ["JPYOK"] "JPYOK" 2 2 3)]
    (is (= (:moves r) 6))
    (is (= (count (:records r)) 6))
    (is (> (:discharge-time-s r) 0))
    (is (< 10 (tc/moves-per-hour r) 200))
    (is (every? #(seq (:agv-id %)) (:records r)))))   ; every box got an AGV

(deftest only-target-port-discharged
  (let [bs (concat (boxes 3 "JPYOK")
                   (map-indexed (fn [i _] (st/container (str "R" i) 15.0 "NLRTM")) (range 3)))
        r (tc/simulate-discharge bs ["JPYOK" "NLRTM"] "JPYOK" 3 2 3)]
    (is (= (:moves r) 3))
    (is (every? #(clojure.string/starts-with? (:box-id %) "B") (:records r)))))

(deftest discharge-is-max-of-crane-and-agv
  (let [r (tc/simulate-discharge (boxes 4) ["JPYOK"] "JPYOK" 2 2 2)]
    (is (approx (:discharge-time-s r) (max (:crane-timeline-s r) (:agv-makespan-s r))))))

(deftest more-agvs-do-not-raise-crane-bound-time
  (let [r2 (tc/simulate-discharge (boxes 6) ["JPYOK"] "JPYOK" 2 2 3 :agv-ids ["A1" "A2"])
        r5 (tc/simulate-discharge (boxes 6) ["JPYOK"] "JPYOK" 2 2 3
                                  :agv-ids ["A1" "A2" "A3" "A4" "A5"])]
    (is (approx (:crane-timeline-s r2) (:crane-timeline-s r5)))
    (is (<= (:agv-makespan-s r5) (:agv-makespan-s r2)))
    (is (approx (:discharge-time-s r5) (:crane-timeline-s r5)))))   ; crane-bound

(deftest empty-port-zero-productivity
  (let [r (tc/simulate-discharge (boxes 3 "JPYOK") ["JPYOK" "SGSIN"] "SGSIN" 2 2 2)]
    (is (= (:moves r) 0))
    (is (= (:discharge-time-s r) 0.0))
    (is (= (tc/moves-per-hour r) 0.0))))

(deftest accepts-prebuilt-plan
  (let [bs (boxes 4)
        plan (st/build-stow-plan bs ["JPYOK"] 2 2 2)
        r (tc/simulate-discharge bs ["JPYOK"] "JPYOK" 2 2 2 :plan plan)]
    (is (= (:moves r) 4))))

(deftest custom-crane-yard-agv
  (let [r (tc/simulate-discharge (boxes 3) ["JPYOK"] "JPYOK" 2 2 2
                                 :crane (cd/make-crane :cable-length 20.0)
                                 :agv (agv/make-agv :v-max 4.0)
                                 :yard (tc/yard-layout :apron-to-yard-m 200.0))]
    (is (= (:moves r) 3))
    (is (>= (:max-residual-sway-m r) 0.0))))

(deftest isaac-path-runs-or-falls-back
  ;; use-isaac=true must produce a valid report (clj port falls back to the analytic model)
  (let [r (tc/simulate-discharge (boxes 3) ["JPYOK"] "JPYOK" 2 2 2 :use-isaac true)]
    (is (= (:moves r) 3))
    (is (> (:discharge-time-s r) 0))))

(when (= *file* (System/getProperty "babashka.file"))
  (let [{:keys [fail error]} (run-tests 'niyaku.methods.test-terminal-cycle)]
    (System/exit (if (zero? (+ fail error)) 0 1))))
