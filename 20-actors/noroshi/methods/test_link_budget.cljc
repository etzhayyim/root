(ns noroshi.methods.test-link-budget
  "Tests for the noroshi optical link-budget core (ADR-2606051600).
  1:1 Clojure port of methods/test_link_budget.py (pytest → clojure.test)."
  (:require [clojure.test :refer [deftest is run-tests]]
            [clojure.string :as str]
            [noroshi.methods.link-budget :as L]))

(defn- approx?
  ([a b] (approx? a b 1e-6))
  ([a b tol] (<= (Math/abs (- (double a) (double b))) tol)))

(defn- rel-approx? [a b rel]
  (<= (Math/abs (- (double a) (double b))) (* rel (max (Math/abs (double a)) (Math/abs (double b)) 1e-30))))

(deftest test-cpo-reference-link-closes-with-margin
  (let [b (L/compute L/CPO-REFERENCE)]
    (is (get b "closes"))
    (is (> (get b "margin_db") 0.0))))

(deftest test-total-loss-is-sum-of-components
  (let [b (L/compute L/CPO-REFERENCE)]
    (is (approx? (get b "total_loss_db") (reduce + (vals (get b "breakdown")))))))

(deftest test-received-power-is-launch-minus-loss
  (let [d L/CPO-REFERENCE b (L/compute d)]
    (is (approx? (get b "received_dbm") (- (get d "laser_power_dbm") (get b "total_loss_db"))))))

(deftest test-fibre-loss-scales-with-distance
  (let [short (L/compute (L/link-design :name "s" :fibre_m 1000.0))
        long  (L/compute (L/link-design :name "l" :fibre_m 10000.0))]
    (is (> (get-in long ["breakdown" "fibre"]) (get-in short ["breakdown" "fibre"])))
    (is (approx? (- (get-in long ["breakdown" "fibre"]) (get-in short ["breakdown" "fibre"])) (* 9.0 0.35)))))

(deftest test-long-span-eventually-fails-to-close
  (let [b (L/compute (L/link-design :name "too-long" :fibre_m 200000.0))]
    (is (not (get b "closes")))
    (is (< (get b "margin_db") 0.0))))

(deftest test-cpo-beats-pluggable-on-energy-per-bit
  (let [cpo (L/compute L/CPO-REFERENCE) plug (L/compute L/PLUGGABLE-REFERENCE)]
    (is (< (get cpo "energy_pj_per_bit") (get plug "energy_pj_per_bit")))))

(deftest test-zero-line-rate-rejected
  (is (thrown? #?(:clj Exception :cljs js/Error) (L/compute (L/link-design :name "bad" :line_rate_gbps 0.0)))))

(deftest test-photocurrent-positive-and-finite
  (let [b (L/compute L/CPO-REFERENCE)]
    (is (> (get b "received_current_ua") 0.0))
    (is (not (Double/isInfinite (double (get b "received_current_ua")))))))

(deftest test-report-renders-both-designs-and-advantage
  (let [txt (L/report)]
    (is (str/includes? txt "cpo-2km-100g"))
    (is (str/includes? txt "pluggable-2km-100g"))
    (is (str/includes? txt "CPO energy advantage"))))

(deftest test-breakdown-has-all-six-loss-components
  (let [b (L/compute L/CPO-REFERENCE)]
    (is (= (set (keys (get b "breakdown")))
           #{"modulator_il" "tx_grating_coupler" "rx_grating_coupler" "waveguide" "fibre" "connector"}))))

(deftest test-closes-is-consistent-with-margin-sign
  (doseq [d [L/CPO-REFERENCE L/PLUGGABLE-REFERENCE (L/link-design :name "x" :fibre_m 200000.0)]]
    (let [b (L/compute d)]
      (is (= (get b "closes") (>= (get b "margin_db") 0.0))))))

(deftest test-energy-per-bit-includes-tx-rx-and-laser
  (let [b (L/compute L/CPO-REFERENCE)]
    (is (> (get b "energy_pj_per_bit")
           (+ (get L/CPO-REFERENCE "tx_energy_pj_per_bit") (get L/CPO-REFERENCE "rx_energy_pj_per_bit"))))))

(deftest test-higher-line-rate-lowers-laser-energy-per-bit
  (let [slow (L/compute (L/link-design :name "slow" :line_rate_gbps 50.0))
        fast (L/compute (L/link-design :name "fast" :line_rate_gbps 400.0))]
    (is (< (get fast "energy_pj_per_bit") (get slow "energy_pj_per_bit")))))

(deftest test-q-factor-matches-textbook-values
  (is (approx? (L/q-factor-for-ber 1e-9) 6.0 0.05))
  (is (approx? (L/q-factor-for-ber 1e-12) 7.03 0.05))
  (is (approx? (L/q-factor-for-ber 1e-3) 3.09 0.05)))

(deftest test-q-factor-monotone-in-ber
  (is (> (L/q-factor-for-ber 1e-12) (L/q-factor-for-ber 1e-9) (L/q-factor-for-ber 1e-3))))

(deftest test-q-factor-rejects-out-of-range-ber
  (doseq [bad [0.0 -1e-9 0.5 0.9 1.0]]
    (is (thrown? #?(:clj Exception :cljs js/Error) (L/q-factor-for-ber bad)))))

(deftest test-stricter-ber-needs-more-power-higher-sensitivity-dbm
  (let [loose (L/receiver-sensitivity-dbm 1e-3 106.25)
        strict (L/receiver-sensitivity-dbm 1e-12 106.25)]
    (is (> strict loose))))

(deftest test-higher-line-rate-worsens-sensitivity
  (let [s-slow (L/receiver-sensitivity-dbm 1e-12 25.0)
        s-fast (L/receiver-sensitivity-dbm 1e-12 400.0)]
    (is (> s-fast s-slow))))

(deftest test-sensitivity-rejects-non-positive-line-rate
  (is (thrown? #?(:clj Exception :cljs js/Error) (L/receiver-sensitivity-dbm 1e-12 0.0))))

(deftest test-with-ber-sensitivity-sets-field-and-cpo-still-closes
  (let [d (L/with-ber-sensitivity L/CPO-REFERENCE 1e-12)]
    (is (approx? (get d "rx_sensitivity_dbm") (L/receiver-sensitivity-dbm 1e-12 (get d "line_rate_gbps")) 1e-3))
    (is (get (L/compute d) "closes"))))

(deftest test-excess-noise-factor-is-unity-at-unity-gain
  (doseq [k [0.0 0.3 0.5 1.0]]
    (is (approx? (L/excess-noise-factor 1.0 k) 1.0))))

(deftest test-excess-noise-factor-grows-with-gain-and-k
  (is (> (L/excess-noise-factor 20 0.3) (L/excess-noise-factor 5 0.3)))
  (is (> (L/excess-noise-factor 10 0.5) (L/excess-noise-factor 10 0.1))))

(deftest test-excess-noise-factor-k-zero-closed-form
  (is (approx? (L/excess-noise-factor 10 0.0) (- 2 (/ 1 10)))))

(deftest test-excess-noise-factor-rejects-bad-inputs
  (doseq [[m k] [[0.5 0.3] [10 -0.1] [10 1.1]]]
    (is (thrown? #?(:clj Exception :cljs js/Error) (L/excess-noise-factor m k)))))

(deftest test-apd-is-more-sensitive-than-pin
  (let [pin (L/receiver-sensitivity-dbm 1e-12 106.25)
        apd (L/apd-sensitivity-dbm 1e-12 106.25 10 0.3)]
    (is (< apd pin))))

(deftest test-apd-reduces-to-pin-at-unity-gain
  (let [pin (L/receiver-sensitivity-dbm 1e-12 106.25)
        apd (L/apd-sensitivity-dbm 1e-12 106.25 1.0 0.3)]
    (is (approx? apd pin 1e-9))))

(deftest test-apd-higher-excess-noise-gives-less-improvement
  (let [low-k  (L/apd-sensitivity-dbm 1e-12 106.25 10 0.1)
        high-k (L/apd-sensitivity-dbm 1e-12 106.25 10 0.5)]
    (is (> high-k low-k))))

#?(:clj (defn -main [& _] (run-tests 'noroshi.methods.test-link-budget)))
