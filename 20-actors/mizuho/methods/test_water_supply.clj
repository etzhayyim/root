#!/usr/bin/env bb
;; Working Clojure port of methods/test_water_supply.py.
(ns mizuho.methods.test-water-supply
  "Tests for mizuho water-supply operational loop.

  Run:  bb --classpath 20-actors 20-actors/mizuho/methods/test_water_supply.clj"
  (:require [mizuho.methods.substrate :as s]
            [mizuho.methods.water-supply :as ws]
            [clojure.test :refer [deftest is run-tests]]))

(defn- approx [a b tol] (<= (Math/abs (double (- a b))) tol))

(deftest supply-restores-level-after-demand-step
  (let [r (ws/commission-water-supply {:demand-step-lps 20.0})]
    (is (:level-restored r))
    (is (approx (:final-level-m r) 3.0 1e-2))   ; back to service setpoint
    (is (> (:settling-seconds r) 0))
    (is (> (:final-pressure-bar r) 0))))        ; service pressure restored

(deftest supply-restores-for-large-demand-step
  (let [r (ws/commission-water-supply {:demand-step-lps 80.0 :service-population 1500})]
    (is (:level-restored r))
    (is (approx (:final-level-m r) 3.0 1e-2))))

(deftest non-civilian-use-refused
  (doseq [use ["weapon" "fire-control" "interdiction" "flood"]]
    (is (thrown? clojure.lang.ExceptionInfo
                 (ws/commission-water-supply {:demand-step-lps 20.0 :use use}))
        (str "N1 must refuse use " use))))

(deftest community-scale-cap-enforced-g3
  ;; A service population above the community-scale cap is N1 (a municipal utility), refused.
  (is (thrown? clojure.lang.ExceptionInfo
               (ws/commission-water-supply {:demand-step-lps 20.0
                                            :service-population (inc ws/MAX-SERVICE-POPULATION)}))))

(deftest at-cap-is-allowed
  (let [r (ws/commission-water-supply {:demand-step-lps 20.0
                                       :service-population ws/MAX-SERVICE-POPULATION})]
    (is (= (:service-population r) ws/MAX-SERVICE-POPULATION))
    (is (:level-restored r))))

(deftest reservoir-self-regulates
  ;; No pump command: a gravity-fed tank with a head-dependent leak drains toward a lower
  ;; equilibrium (real first-order dynamics, not free fall to 0).
  (let [tank (ws/reservoir-plant {:area-m2 20.0 :level-m 3.0 :demand-lps 10.0})
        start ((:measure tank))]
    (dotimes [_ 100] ((:step tank) 0.0 1.0))
    (is (< ((:measure tank)) start))
    (is (>= ((:measure tank)) 0.0))))

(deftest datoms-are-aggregate-dry-run-no-server-key
  (let [d (ws/to-datoms (ws/commission-water-supply {:demand-step-lps 20.0}) "spring-001")]
    (is (true? (:water.supply/dry-run d)))
    (is (false? (:water.supply/server-held-key d)))
    (is (true? (:water.supply/representative d)))
    (is (true? (:water.supply/level-restored d)))
    (is (<= (:water.supply/service-population d) ws/MAX-SERVICE-POPULATION))))

;; the N1/G3 refusals are SafetyError-typed
(deftest refusals-are-safety-errors
  (doseq [args [{:demand-step-lps 20.0 :use "weapon"}
                {:demand-step-lps 20.0 :service-population (inc ws/MAX-SERVICE-POPULATION)}]]
    (is (try (ws/commission-water-supply args) false
             (catch clojure.lang.ExceptionInfo e (s/safety-error? e))))))

(when (= *file* (System/getProperty "babashka.file"))
  (let [{:keys [fail error]} (run-tests 'mizuho.methods.test-water-supply)]
    (System/exit (if (zero? (+ fail error)) 0 1))))
