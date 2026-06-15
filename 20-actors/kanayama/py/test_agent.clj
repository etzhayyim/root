#!/usr/bin/env bb
;; Clojure port of py/test_agent.py (kanayama circular metallurgy — 18 tests).
(ns kanayama.py.test-agent
  "kanayama 金山 test harness. Verifies structural invariants of ADR-2605252400:
    G2   mass-balance ≥98%       — closure threshold enforced
    G4   witness quorum ≥2       — Ed25519, DID-bound robots per pour
    G12  KPI caps                — recovery ≥95%, energy ≤6 kWh/kg
    G7/G11/G15 settlement        — USDC + TitheRouter 10%, stops at :intent"
  (:require [clojure.test :refer [deftest is run-tests]]
            [kanayama.py.agent :as agent]))

;; ── intake QA ─────────────────────────────────────────────────────────────────
(deftest test-intake-qa-pass
  (let [out (agent/intake-qa 500.0 0.8 2.1 45)]
    (is (= (get out ":intake/qaPassed") true))))

(deftest test-intake-qa-fail-cl-residue
  (let [out (agent/intake-qa 500.0 3.0 2.0 45)]
    (is (= (get out ":intake/blocked") true))))

(deftest test-intake-qa-fail-moisture
  (let [out (agent/intake-qa 500.0 0.8 6.0 45)]
    (is (= (get out ":intake/blocked") true))))

(deftest test-intake-qa-fail-fe-contamination
  (let [out (agent/intake-qa 500.0 0.8 2.0 600)]
    (is (= (get out ":intake/blocked") true))))

;; ── mass-balance audit (G2) ───────────────────────────────────────────────────
(deftest test-mass-balance-ok
  ;; 475+20+5=500; 500/500*100=100% ≥98%
  (let [out (agent/check-mass-balance 500.0 475.0 20.0 5.0)]
    (is (= (:ok out) true))
    (is (>= (:closure_pct out) 98.0))))

(deftest test-mass-balance-fail-low-closure
  ;; 300+50+50=400; 400/500*100=80% <98%
  (let [out (agent/check-mass-balance 500.0 300.0 50.0 50.0)]
    (is (= (:ok out) false))
    (is (< (:closure_pct out) 98.0))))

(deftest test-mass-balance-invalid-input
  (let [out (agent/check-mass-balance 0.0 1.0 1.0 1.0)]
    (is (= (:ok out) false))))

;; ── KPI caps (G12) ────────────────────────────────────────────────────────────
(deftest test-kpi-recovery-below-min
  ;; recovery 90.0% < 95.0% → fail
  (let [out (agent/check-kpi-caps 90.0 5.0)]
    (is (= (:ok out) false))))

(deftest test-kpi-energy-above-cap
  ;; energy 7.0 > 6.0 kWh/kg → fail
  (let [out (agent/check-kpi-caps 96.0 7.0)]
    (is (= (:ok out) false))))

(deftest test-kpi-both-ok
  ;; recovery 96.0% ≥ 95.0% AND energy 5.5 ≤ 6.0 → pass
  (let [out (agent/check-kpi-caps 96.0 5.5)]
    (is (= (:ok out) true))))

;; ── witness quorum (G4) ───────────────────────────────────────────────────────
(deftest test-witness-quorum-ok
  (let [out (agent/check-witness-sigs ["did:web:robot.yokin" "did:web:robot.kamado"])]
    (is (= (:ok out) true))
    (is (= (:witness_count out) 2))))

(deftest test-witness-quorum-fail-one
  (let [out (agent/check-witness-sigs ["did:web:robot.yokin"])]
    (is (= (:ok out) false))))

(deftest test-witness-quorum-fail-empty
  (let [out (agent/check-witness-sigs [])]
    (is (= (:ok out) false))))

;; ── settlement — USDC + TitheRouter (G7/G11/G15) ────────────────────────────
(deftest test-settlement-tithe-split
  ;; 10% tithe + stops at intent (G7/G11) — no operator-sig-ref → state "intent"
  (let [s (agent/build-settlement-intent 1000000000)]
    (is (= (:titheMinor s) 100000000))
    (is (= (:operatorPayoutMinor s) 900000000))
    (is (= (:state s) "intent"))
    (is (= (:rail s) "usdc-base-l2"))))

(deftest test-settlement-executed-only-with-sig
  ;; settlement executes only with operator signature (G15)
  ;; NOTE: agent.py build_settlement_intent returns state "executed" when operator_sig_ref
  ;; is provided — this is kanayama R0 behaviour (not the R2 Autonomous pattern of omise/ainori
  ;; where state is unconditionally "executed"). We port to the ACTUAL impl behaviour.
  (let [s (agent/build-settlement-intent 500000000 "0xoperatorsig")]
    (is (= (:state s) "executed"))))

;; ── batch settlement (G2 + G12 compose) ──────────────────────────────────────
(deftest test-batch-settlement-ok
  ;; mb: 475+20+5=500; 100% ≥98%; kpi: 96% ≥95%, 5.5 ≤6.0 → pass
  (let [out (agent/finalize-batch-settlement "b1" 500.0 475.0 20.0 5.0 96.0 5.5)]
    (is (not (= (:blocked out) true)))
    (is (contains? out ":batchSettlement/id"))))

(deftest test-batch-settlement-blocked-mass-balance
  ;; mb: 300+50+50=400; 80% <98% → blocked
  (let [out (agent/finalize-batch-settlement "b2" 500.0 300.0 50.0 50.0 96.0 5.5)]
    (is (= (:blocked out) true))))

(deftest test-batch-settlement-blocked-kpi
  ;; mb passes; kpi: 90% <95% → blocked
  (let [out (agent/finalize-batch-settlement "b3" 500.0 475.0 20.0 5.0 90.0 5.5)]
    (is (= (:blocked out) true))))

;; ── runner ────────────────────────────────────────────────────────────────────
(when (= *file* (System/getProperty "babashka.file"))
  (let [{:keys [fail error]} (clojure.test/run-tests 'kanayama.py.test-agent)]
    (System/exit (if (zero? (+ fail error)) 0 1))))
