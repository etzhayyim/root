(ns noroshi.methods.test-active-alignment
  "Tests for the noroshi active-alignment + laser-safety core (ADR-2606051600).
  1:1 Clojure port of methods/test_active_alignment.py (pytest → clojure.test)."
  (:require [clojure.test :refer [deftest is run-tests]]
            [clojure.string :as str]
            [noroshi.methods.active-alignment :as A]))

(defn- approx? [a b tol] (<= (Math/abs (- (double a) (double b))) tol))

;; ── laser-safety interlock ──────────────────────────────────────────────────────
(deftest test-class1-civilian-use-energises
  (is (nil? (A/enable-laser (A/laser-spec :laser_class "1" :use "alignment")))))

(deftest test-weaponisation-uses-are-unrepresentable
  (doseq [use ["weapon" "directed-energy" "dazzle" "fire-control"]]
    (is (thrown? #?(:clj Exception :cljs js/Error) (A/enable-laser (A/laser-spec :laser_class "1" :use use))))))

(deftest test-unknown-use-refused
  (is (thrown? #?(:clj Exception :cljs js/Error) (A/enable-laser (A/laser-spec :laser_class "1" :use "mystery")))))

(deftest test-hazardous-class-without-interlock-refused
  (is (thrown? #?(:clj Exception :cljs js/Error)
               (A/enable-laser (A/laser-spec :laser_class "4" :use "soldering" :enclosure_interlock false)))))

(deftest test-hazardous-class-with-interlock-but-no-attestation-refused
  (is (thrown? #?(:clj Exception :cljs js/Error)
               (A/enable-laser (A/laser-spec :laser_class "3B" :use "trimming" :enclosure_interlock true)))))

(deftest test-hazardous-class-fully-attested-energises
  (is (nil? (A/enable-laser (A/laser-spec :laser_class "4" :use "soldering"
                                          :enclosure_interlock true
                                          :safety_attestation_ref "attest:noroshi-lsm-001")))))

;; ── active alignment converges to the unknown peak ──────────────────────────────
(deftest test-align-finds-true-peak
  (let [model (A/coupler-model :opt_x_um 2.3 :opt_y_um -1.7)
        res (A/align model (A/laser-spec))]
    (is (get res "converged"))
    (is (approx? (get res "x_um") (get model "opt_x_um") 0.1))
    (is (approx? (get res "y_um") (get model "opt_y_um") 0.1))))

(deftest test-aligned-coupling-near-peak-efficiency
  (let [model (A/coupler-model :peak_efficiency 0.80)
        res (A/align model (A/laser-spec))]
    (is (approx? (get res "efficiency") 0.80 0.01))
    (is (< (get res "loss_db") 1.0))))

(deftest test-align-refuses-before-probing-when-use-forbidden
  (is (thrown? #?(:clj Exception :cljs js/Error) (A/align (A/coupler-model) (A/laser-spec :use "weapon")))))

(deftest test-align-handles-offset-peak-far-from-start
  (let [model (A/coupler-model :opt_x_um -6.0 :opt_y_um 5.5 :mode_radius_um 6.0)
        res (A/align model (A/laser-spec) :start_x_um 0.0 :start_y_um 0.0)]
    (is (approx? (get res "x_um") -6.0 0.15))
    (is (approx? (get res "y_um") 5.5 0.15))))

(deftest test-align-budget-exhaustion-is-bounded-and-flagged
  (let [model (A/coupler-model :opt_x_um 8.0 :opt_y_um -8.0)
        res (A/align model (A/laser-spec) :step_um 4.0 :tol_um 1e-6 :max_probes 12)]
    (is (<= (get res "probes") (+ 12 4)))
    (is (= (get res "converged") false))))

(deftest test-loss-db-is-monotonic-in-efficiency
  (is (< (A/loss-db 0.9) (A/loss-db 0.5) (A/loss-db 0.1))))

(deftest test-loss-db-handles-zero-efficiency-without-crash
  (let [v (A/loss-db 0.0)]
    (is (and (not (Double/isInfinite (double v))) (> v 100.0)))))

;; ── two-stage coarse acquisition + fine refinement ──────────────────────────────
(deftest test-two-stage-acquires-a-far-narrow-peak-that-single-stage-misses
  (let [model (A/coupler-model :opt_x_um 60.0 :opt_y_um -50.0 :mode_radius_um 2.0)
        single (A/align model (A/laser-spec))]
    (is (< (get single "efficiency") 0.01))
    (let [two (A/align-two-stage model (A/laser-spec))]
      (is (get two "converged"))
      (is (approx? (get two "efficiency") (get model "peak_efficiency") 0.01))
      (is (approx? (get two "x_um") 60.0 0.1))
      (is (approx? (get two "y_um") -50.0 0.1)))))

(deftest test-coarse-scan-lands-inside-the-lobe
  (let [model (A/coupler-model :opt_x_um 30.0 :opt_y_um 20.0 :mode_radius_um 3.0)
        [_ _ eff probes] (A/coarse-scan model (A/laser-spec) :span_um 40.0)]
    (is (> eff 0.0))
    (is (> probes 1))))

(deftest test-coarse-scan-respects-laser-safety-before-probing
  (is (thrown? #?(:clj Exception :cljs js/Error) (A/coarse-scan (A/coupler-model) (A/laser-spec :use "weapon")))))

(deftest test-coarse-scan-rejects-non-positive-span-or-step
  (is (thrown? #?(:clj Exception :cljs js/Error) (A/coarse-scan (A/coupler-model) (A/laser-spec) :span_um 0.0)))
  (is (thrown? #?(:clj Exception :cljs js/Error) (A/coarse-scan (A/coupler-model) (A/laser-spec) :step_um -1.0))))

(deftest test-two-stage-still-converges-on-an-easy-peak
  (let [model (A/coupler-model :opt_x_um 2.3 :opt_y_um -1.7)
        res (A/align-two-stage model (A/laser-spec))]
    (is (get res "converged"))
    (is (approx? (get res "efficiency") (get model "peak_efficiency") 0.01))))

;; ── spiral acquisition ──────────────────────────────────────────────────────────
(deftest test-spiral-uses-far-fewer-probes-than-raster
  (let [model (A/coupler-model :opt_x_um 10.0 :opt_y_um 8.0 :mode_radius_um 3.0)
        [_ _ _ sp] (A/spiral-search model (A/laser-spec))
        [_ _ _ rp] (A/coarse-scan model (A/laser-spec))]
    (is (< sp rp))))

(deftest test-spiral-respects-laser-safety
  (is (thrown? #?(:clj Exception :cljs js/Error) (A/spiral-search (A/coupler-model) (A/laser-spec :use "weapon")))))

(deftest test-spiral-rejects-non-positive-span-or-step
  (is (thrown? #?(:clj Exception :cljs js/Error) (A/spiral-search (A/coupler-model) (A/laser-spec) :span_um -1.0)))
  (is (thrown? #?(:clj Exception :cljs js/Error) (A/spiral-search (A/coupler-model) (A/laser-spec) :step_um 0.0))))

(deftest test-two-stage-spiral-converges-with-fewer-probes-than-raster
  (let [model (A/coupler-model :opt_x_um 10.0 :opt_y_um 8.0 :mode_radius_um 3.0)
        spiral (A/align-two-stage model (A/laser-spec) :acquire "spiral")
        raster (A/align-two-stage model (A/laser-spec) :acquire "raster")]
    (is (get spiral "converged"))
    (is (approx? (get spiral "efficiency") (get model "peak_efficiency") 0.01))
    (is (< (get spiral "probes") (get raster "probes")))))

(deftest test-two-stage-spiral-still-acquires-a-far-narrow-peak
  (let [model (A/coupler-model :opt_x_um 60.0 :opt_y_um -50.0 :mode_radius_um 2.0)
        res (A/align-two-stage model (A/laser-spec) :acquire "spiral")]
    (is (get res "converged"))
    (is (approx? (get res "efficiency") (get model "peak_efficiency") 0.01))))

(deftest test-align-two-stage-rejects-bad-acquire-mode
  (is (thrown? #?(:clj Exception :cljs js/Error) (A/align-two-stage (A/coupler-model) (A/laser-spec) :acquire "zigzag"))))

(deftest test-report-renders
  (let [txt (A/report)]
    (is (str/includes? txt "active alignment"))
    (is (str/includes? txt "IEC 60825"))))

#?(:clj (defn -main [& _] (run-tests 'noroshi.methods.test-active-alignment)))
