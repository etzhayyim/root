#!/usr/bin/env bb
;; Working Clojure port of methods/test_crane_dynamics.py.
(ns niyaku.methods.test-crane-dynamics
  "Tests for crane_dynamics — gantry anti-sway physics core.

  Run:  bb --classpath 20-actors 20-actors/niyaku/methods/test_crane_dynamics.clj"
  (:require [niyaku.methods.crane-dynamics :as cd]
            [clojure.test :refer [deftest is run-tests]]))

(defn- approx
  ([a b] (approx a b 1e-6))
  ([a b tol] (<= (Math/abs (double (- a b))) tol)))

(deftest natural-frequency-and-period
  (let [c (cd/make-crane :cable-length 30.0 :gravity 9.81)
        w (cd/natural-frequency c)]
    (is (approx w (Math/sqrt (/ 9.81 30.0))))
    (is (approx (cd/sway-period c) (/ (* 2 Math/PI) w)))
    (is (< (cd/natural-frequency (cd/make-crane :cable-length 60.0)) w))))

(deftest hanging-load-is-stable-equilibrium
  ;; no input, small initial sway → decays (gravity restores)
  (let [c (cd/make-crane :cable-length 20.0 :sway-damping 0.05)
        peak0 (Math/abs 0.15)
        final (reduce (fn [s _] (cd/step c s 0.0 (/ 1.0 100.0)))
                      [0.0 0.0 0.15 0.0] (range 4000))]
    (is (< (Math/abs (nth final 2)) peak0))
    (is (< (Math/abs (nth final 2)) 0.05))
    (is (every? #(Double/isFinite %) final))))

(deftest trolley-velocity-envelope-enforced
  (let [c (cd/make-crane :velocity-max 2.0 :accel-max 5.0)
        final (reduce (fn [s _] (cd/step c s 5.0 (/ 1.0 100.0)))
                      [0.0 0.0 0.0 0.0] (range 2000))]
    (is (<= (Math/abs (nth final 1)) (+ 2.0 1e-6)))))

(deftest accel-command-is-saturated
  (let [c (cd/make-crane :accel-max 0.6)]
    (is (approx (nth (cd/derivatives c [0 0 0 0] 100.0) 1) 0.6))
    (is (approx (nth (cd/derivatives c [0 0 0 0] -100.0) 1) -0.6))))

(deftest simulate-traverse-reaches-and-damps-sway
  (let [c (cd/make-crane :cable-length 25.0 :accel-max 0.7 :velocity-max 4.0)
        res (cd/simulate-traverse c 30.0 :max-time-s 300.0)]
    (is (:reached res))
    (is (<= (Math/abs (- (:final-x res) 30.0)) 0.10))
    (is (<= (:residual-sway-m res) 0.05))
    (is (> (:settle-time-s res) 0.0))))

(deftest anti-sway-beats-no-control-on-residual
  (let [c (cd/make-crane :cable-length 25.0)
        with-ctrl (cd/simulate-traverse c 25.0 :controller (cd/make-controller) :max-time-s 300.0)
        naive (cd/simulate-traverse c 25.0 :controller (cd/make-controller :k-theta 0.0 :k-thetad 0.0)
                                    :max-time-s 300.0)]
    (is (< (:peak-sway-m with-ctrl) (:peak-sway-m naive)))))

(deftest traverse-target-beyond-rail-raises
  (let [c (cd/make-crane :rail-length 60.0)]
    (is (thrown? clojure.lang.ExceptionInfo (cd/simulate-traverse c 80.0)))))

(deftest zv-shaper-amplitudes-sum-to-one
  (let [c (cd/make-crane :cable-length 30.0 :sway-damping 0.02)
        [[t0 a0] [t1 a1]] (cd/zv-shaper c)]
    (is (= t0 0.0))
    (is (approx (+ a0 a1) 1.0))
    (is (approx t1 (/ (cd/sway-period c) 2.0) (* 0.05 (/ (cd/sway-period c) 2.0))))))

(deftest traverse-records-trajectory-when-requested
  (let [c (cd/make-crane :cable-length 25.0)
        res (cd/simulate-traverse c 20.0 :max-time-s 300.0 :record true)]
    (is (:reached res))
    (is (= (count (:trajectory res)) (:steps res)))
    (is (every? #(= (count %) 4) (:trajectory res)))))

(deftest traverse-not-settled-within-short-window
  (let [c (cd/make-crane :cable-length 40.0)
        res (cd/simulate-traverse c 55.0 :max-time-s 2.0 :dt (/ 1.0 50.0))]
    (is (false? (:reached res)))
    (is (approx (:settle-time-s res) 2.0))))

(deftest cycle-time-and-productivity
  (let [c (cd/make-crane :cable-length 25.0)
        t (cd/lift-cycle-time c 30.0 20.0 18.0)
        mph (cd/moves-per-hour t)]
    (is (> t 0.0))
    (is (< 5.0 mph 120.0))
    (is (thrown? clojure.lang.ExceptionInfo (cd/moves-per-hour 0.0)))))

(when (= *file* (System/getProperty "babashka.file"))
  (let [{:keys [fail error]} (run-tests 'niyaku.methods.test-crane-dynamics)]
    (System/exit (if (zero? (+ fail error)) 0 1))))
