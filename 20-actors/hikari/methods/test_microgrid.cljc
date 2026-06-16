(ns hikari.methods.test-microgrid
  "test_microgrid.py — hikari microgrid operational loop tests.
  1:1 Clojure port of methods/test_microgrid.py (pytest → clojure.test)."
  (:require [clojure.test :refer [deftest is run-tests testing]]
            [hikari.methods.substrate :as sub]
            [hikari.methods.microgrid :as mg]))

(defn- approx
  "pytest.approx mirror: |a - b| <= abs-tol."
  [a b abs-tol]
  (<= (Math/abs (double (- a b))) abs-tol))

(deftest test-microgrid-restores-frequency-after-load-step
  (let [res (mg/commission-microgrid 140.0)]
    (is (get res "freq_restored"))
    (is (approx (get res "final_freq_hz") 50.0 2e-2))
    (is (approx (get res "final_generation_kw") 140.0 1.0)) ; gen tracks load
    (is (<= 0.0 (get res "final_soc")))
    (is (<= (get res "final_soc") 1.0))
    (is (> (get res "settling_seconds") 0))))

(deftest test-microgrid-handles-load-shed-direction
  ;; A load drop (below the 100 kW base) is also rejected back to 50 Hz.
  (let [res (mg/commission-microgrid 60.0)]
    (is (get res "freq_restored"))
    (is (approx (get res "final_generation_kw") 60.0 1.0))))

(deftest test-non-civilian-use-refused
  (doseq [use ["weapon" "fire-control" "mining"]]
    (testing use
      (is (thrown? clojure.lang.ExceptionInfo
                   (mg/commission-microgrid 120.0 :use use))))))

(deftest test-normal-load-step-does-not-trip-rocof
  ;; +60 kW step: primary droop arrests the dive, ROCOF stays under the trip.
  (let [res (mg/commission-microgrid 160.0)]
    (is (>= (get res "rocof_max_hz_per_s") 0.0))
    (is (= false (get res "rocof_tripped")))))

(deftest test-islanding-scale-step-trips-rocof
  ;; +80 kW (near-doubling) is an islanding-scale transient: the guard trips.
  (let [res (mg/commission-microgrid 180.0)]
    (is (= true (get res "rocof_tripped")))
    (is (get res "freq_restored")))) ; still recovers in sim, but the relay flags it

(deftest test-rocof-helper-detects-fast-transient
  (let [fast [[0.0 50.0 0.0] [0.01 47.0 0.0]]] ; 3 Hz in 10 ms = 300 Hz/s
    (is (approx (mg/rocof fast 0.01) 300.0 1e-6))))

(deftest test-datoms-are-aggregate-and-dry-run
  (let [res (mg/commission-microgrid 140.0)
        d (mg/to-datoms res "microgrid-001")]
    (is (= true (get d ":microgrid/dry-run")))
    (is (= true (get d ":microgrid/representative")))
    (is (= true (get d ":microgrid/freq-restored")))))

#?(:clj (defn -main [& _] (run-tests 'hikari.methods.test-microgrid)))
