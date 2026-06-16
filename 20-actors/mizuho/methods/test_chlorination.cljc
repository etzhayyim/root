(ns mizuho.methods.test-chlorination
  "Tests for mizuho residual-dosing (chlorination) operational loop.
  1:1 Clojure port of methods/test_chlorination.py (pytest → clojure.test)."
  (:require [clojure.test :refer [deftest is]]
            [mizuho.methods.-substrate :as sub]
            [mizuho.methods.chlorination :as chl]))

(defn- approx?
  "pytest.approx(target, abs=tol) — |v - target| <= tol."
  [v target tol]
  (<= (Math/abs (double (- v target))) (double tol)))

(deftest test-chlorine-holds-target-residual-without-consent
  ;; Community-wide disinfection: no per-member consent needed (G6).
  (let [res (chl/commission-dosing :agent "disinfect" :target-residual-mgl 0.5)]
    (is (get res "residual_held"))
    (is (approx? (get res "final_residual_mgl") 0.5 1e-2))
    (is (get res "ceiling_respected"))
    (is (> (get res "settling_seconds") 0))))

(deftest test-residual-never-exceeds-regulatory-ceiling
  ;; Even commanding a target right at the ceiling, the modeled residual must never
  ;; cross MAX-RESIDUAL-MGL.
  (let [res (chl/commission-dosing :agent "disinfect" :target-residual-mgl 3.9)]
    (is (<= (get res "max_residual_mgl") (+ chl/MAX-RESIDUAL-MGL 1e-9)))
    (is (get res "ceiling_respected"))))

(deftest test-clamp-holds-even-with-aggressive-gains
  ;; The clamp is structural — no choice of gains can drive the residual over the
  ;; regulatory ceiling.
  (let [plant (chl/make-residual-chlorine-plant :residual-mgl 0.0 :k-decay 0.0)
        pid (sub/make-pid :kp 1000.0 :ki 1000.0 :out-min 0.0 :out-max 1e6)
        doser (chl/make-clamped-doser plant pid 0.1)
        res (sub/simulate plant doser 999.0 3000 0.1 :tol 1e-3)
        worst (reduce (fn [m [_ pv _]] (max m pv)) Double/NEGATIVE_INFINITY
                      (:trajectory res))]
    (is (<= worst (+ chl/MAX-RESIDUAL-MGL 1e-9)))))

(deftest test-target-above-ceiling-refused
  (is (thrown? #?(:clj Exception :cljs js/Error)
               (chl/commission-dosing :agent "disinfect"
                                      :target-residual-mgl (+ chl/MAX-RESIDUAL-MGL 0.1)))))

(deftest test-fluoride-without-consent-refused-g6
  ;; No mandatory fluoridation — anti-paternalism (G6).
  (is (thrown? #?(:clj Exception :cljs js/Error)
               (chl/commission-dosing :agent "fluoridate" :target-residual-mgl 0.7))))

(deftest test-fluoride-with-consent-passes
  (let [res (chl/commission-dosing :agent "fluoridate" :target-residual-mgl 0.7
                                   :per-member-consent true)]
    (is (get res "residual_held"))
    (is (approx? (get res "final_residual_mgl") 0.7 1e-2))
    (is (get res "ceiling_respected"))))

(deftest test-unknown-agent-refused
  (is (thrown? #?(:clj Exception :cljs js/Error)
               (chl/commission-dosing :agent "bleach-the-river" :target-residual-mgl 0.5))))

(deftest test-datoms-are-dry-run-no-server-key
  (let [res (chl/commission-dosing :agent "disinfect" :target-residual-mgl 0.5)
        d (chl/to-datoms res "spring-001")]
    (is (= (get d ":water.dosing/dry-run") true))
    (is (= (get d ":water.dosing/server-held-key") false))
    (is (= (get d ":water.dosing/ceiling-respected") true))
    (is (= (get d ":water.dosing/ceiling-mgl") chl/MAX-RESIDUAL-MGL))))
