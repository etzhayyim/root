#!/usr/bin/env bb
;; Working Clojure port of methods/test_chlorination.py.
(ns mizuho.methods.test-chlorination
  "Tests for mizuho residual-dosing (chlorination) operational loop.

  Run:  bb --classpath 20-actors 20-actors/mizuho/methods/test_chlorination.clj"
  (:require [mizuho.methods.substrate :as s]
            [mizuho.methods.chlorination :as ch]
            [clojure.test :refer [deftest is run-tests]]))

(defn- approx [a b tol] (<= (Math/abs (double (- a b))) tol))

(deftest chlorine-holds-target-residual-without-consent
  ;; Community-wide disinfection: no per-member consent needed (G6).
  (let [r (ch/commission-dosing {:agent "disinfect" :target-residual-mgl 0.5})]
    (is (:residual-held r))
    (is (approx (:final-residual-mgl r) 0.5 1e-2))
    (is (:ceiling-respected r))
    (is (> (:settling-seconds r) 0))))

(deftest residual-never-exceeds-regulatory-ceiling
  ;; Even commanding a target right at the ceiling, the residual must never cross it.
  (let [r (ch/commission-dosing {:agent "disinfect" :target-residual-mgl 3.9})]
    (is (<= (:max-residual-mgl r) (+ ch/MAX-RESIDUAL-MGL 1e-9)))
    (is (:ceiling-respected r))))

(deftest clamp-holds-even-with-aggressive-gains
  ;; The clamp is structural — no choice of gains can drive the residual over the ceiling.
  (let [plant (ch/residual-chlorine-plant 0.0 0.0)
        pid (s/make-pid {:kp 1000.0 :ki 1000.0 :out-min 0.0 :out-max 1e6})
        doser (ch/clamped-doser plant pid)
        res (s/simulate plant doser 999.0 3000 0.1 :tol 1e-3)
        worst (reduce max (map second (:trajectory res)))]
    (is (<= worst (+ ch/MAX-RESIDUAL-MGL 1e-9)))))

(deftest target-above-ceiling-refused
  (is (thrown? clojure.lang.ExceptionInfo
               (ch/commission-dosing {:agent "disinfect"
                                      :target-residual-mgl (+ ch/MAX-RESIDUAL-MGL 0.1)}))))

(deftest fluoride-without-consent-refused-g6
  ;; No mandatory fluoridation — anti-paternalism (G6).
  (is (thrown? clojure.lang.ExceptionInfo
               (ch/commission-dosing {:agent "fluoridate" :target-residual-mgl 0.7}))))

(deftest fluoride-with-consent-passes
  (let [r (ch/commission-dosing {:agent "fluoridate" :target-residual-mgl 0.7
                                 :per-member-consent true})]
    (is (:residual-held r))
    (is (approx (:final-residual-mgl r) 0.7 1e-2))
    (is (:ceiling-respected r))))

(deftest unknown-agent-refused
  (is (thrown? clojure.lang.ExceptionInfo
               (ch/commission-dosing {:agent "bleach-the-river" :target-residual-mgl 0.5}))))

(deftest datoms-are-dry-run-no-server-key
  (let [d (ch/to-datoms (ch/commission-dosing {:agent "disinfect" :target-residual-mgl 0.5}) "spring-001")]
    (is (true? (:water.dosing/dry-run d)))
    (is (false? (:water.dosing/server-held-key d)))
    (is (true? (:water.dosing/ceiling-respected d)))
    (is (= (:water.dosing/ceiling-mgl d) ch/MAX-RESIDUAL-MGL))))

;; the G6 refusals are SafetyError-typed (not generic) — assert the type too
(deftest refusals-are-safety-errors
  (doseq [args [{:agent "fluoridate" :target-residual-mgl 0.7}
                {:agent "bleach-the-river" :target-residual-mgl 0.5}
                {:agent "disinfect" :target-residual-mgl 99.0}]]
    (is (try (ch/commission-dosing args) false
             (catch clojure.lang.ExceptionInfo e (s/safety-error? e))))))

(when (= *file* (System/getProperty "babashka.file"))
  (let [{:keys [fail error]} (run-tests 'mizuho.methods.test-chlorination)]
    (System/exit (if (zero? (+ fail error)) 0 1))))
