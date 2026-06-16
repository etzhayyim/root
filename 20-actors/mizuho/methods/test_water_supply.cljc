(ns mizuho.methods.test-water-supply
  "Tests for mizuho water-supply operational loop.
  1:1 Clojure port of methods/test_water_supply.py (pytest → clojure.test).

  The Python @pytest.mark.parametrize over ['weapon','fire-control','interdiction',
  'flood'] is folded into one deftest iterating those uses (one `is` per case)."
  (:require [clojure.test :refer [deftest is]]
            [mizuho.methods.water-supply :as ws]))

(defn- approx?
  "pytest.approx(target, abs=tol) — |v - target| <= tol."
  [v target tol]
  (<= (Math/abs (double (- v target))) (double tol)))

(deftest test-supply-restores-level-after-demand-step
  (let [res (ws/commission-water-supply :demand-step-lps 20.0)]
    (is (get res "level_restored"))
    (is (approx? (get res "final_level_m") 3.0 1e-2)) ; back to service setpoint
    (is (> (get res "settling_seconds") 0))
    (is (> (get res "final_pressure_bar") 0))))         ; service pressure restored

(deftest test-supply-restores-for-large-demand-step
  ;; A bigger demand (more taps open) is also rejected back to the setpoint.
  (let [res (ws/commission-water-supply :demand-step-lps 80.0 :service-population 1500)]
    (is (get res "level_restored"))
    (is (approx? (get res "final_level_m") 3.0 1e-2))))

(deftest test-non-civilian-use-refused
  (doseq [use ["weapon" "fire-control" "interdiction" "flood"]]
    (is (thrown? #?(:clj Exception :cljs js/Error)
                 (ws/commission-water-supply :demand-step-lps 20.0 :use use)))))

(deftest test-community-scale-cap-enforced-g3
  ;; A service population above the community-scale cap is N1 (a municipal utility)
  ;; and is structurally refused before any run.
  (is (thrown? #?(:clj Exception :cljs js/Error)
               (ws/commission-water-supply
                :demand-step-lps 20.0
                :service-population (inc ws/MAX-SERVICE-POPULATION)))))

(deftest test-at-cap-is-allowed
  (let [res (ws/commission-water-supply :demand-step-lps 20.0
                                        :service-population ws/MAX-SERVICE-POPULATION)]
    (is (= (get res "service_population") ws/MAX-SERVICE-POPULATION))
    (is (get res "level_restored"))))

(deftest test-reservoir-self-regulates
  ;; No pump command: a gravity-fed tank with a head-dependent leak drains toward a
  ;; lower equilibrium (real first-order dynamics, not free fall to 0).
  (let [tank (ws/make-reservoir-plant :area-m2 20.0 :level-m 3.0 :demand-lps 10.0)
        start (ws/reservoir-measure tank)]
    (dotimes [_ 100]
      ((:step! tank) tank 0.0 1.0))
    (is (< (ws/reservoir-measure tank) start))
    (is (>= (ws/reservoir-measure tank) 0.0))))

(deftest test-datoms-are-aggregate-dry-run-no-server-key
  (let [res (ws/commission-water-supply :demand-step-lps 20.0)
        d (ws/to-datoms res "spring-001")]
    (is (= (get d ":water.supply/dry-run") true))
    (is (= (get d ":water.supply/server-held-key") false))
    (is (= (get d ":water.supply/representative") true))
    (is (= (get d ":water.supply/level-restored") true))
    (is (<= (get d ":water.supply/service-population") ws/MAX-SERVICE-POPULATION))))
