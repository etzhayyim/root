#!/usr/bin/env bb
;; Clojure port of py/test_agent.py (hodoki ELV disassembly — 25 tests).
(ns hodoki.py.test-agent
  "hodoki 解き test harness. Verifies structural invariants of ADR-2605261215:
    G5  charter-rider scan      — military/weapon/covert vehicles blocked
    G6  f-gas capture           — ≥95% threshold enforced
    G8  ecu-data-wipe mandatory — requires BOTH wiped + witness ≥2
    G12 right-to-repair parts   — DID issued with VIN provenance
    G13 material recovery ≥95%  — recovery rate + ASR cap
    G14 pgm recovery ≥95%       — PGM yield audit
    S2/S3/S4 settlement         — USDC + TitheRouter 10%, stops at :intent"
  (:require [clojure.test :refer [deftest is testing run-tests]]
            [hodoki.py.agent :as agent]))

;; ── G5 Charter scan ───────────────────────────────────────────────────────────
(deftest test-charter-scan-passes-civilian
  (let [result (agent/scan-charter-compliance "ABC123" "2024 Toyota Corolla")]
    (is (= (:ok result) true))
    (is (= (:status result) "passed"))))

(deftest test-charter-scan-blocks-military
  (let [result (agent/scan-charter-compliance "XYZ789" "Military armored platform")]
    (is (= (:ok result) false))
    (is (= (:status result) "failed"))))

(deftest test-charter-scan-blocks-weapon
  (let [result (agent/scan-charter-compliance "XYZ789" "Weapon delivery system")]
    (is (= (:ok result) false))))

;; ── G6 F-gas capture ──────────────────────────────────────────────────────────
(deftest test-fgas-capture-below-threshold
  (let [result (agent/check-fgas-compliance 100.0 94.0)]
    (is (= (:ok result) false))))

(deftest test-fgas-capture-at-threshold
  (let [result (agent/check-fgas-compliance 100.0 95.0)]
    (is (= (:ok result) true))))

;; ── G8 ECU data wipe ──────────────────────────────────────────────────────────
(deftest test-ecu-wipe-requires-both
  (let [result (agent/ecu-data-wipe-mandatory false 2)]
    (is (= (:ok result) false))
    (is (= (:blocked result) true))))

(deftest test-ecu-wipe-requires-witness-quorum
  (let [result (agent/ecu-data-wipe-mandatory true 1)]
    (is (= (:ok result) false))
    (is (= (:blocked result) true))))

(deftest test-ecu-wipe-with-quorum
  (let [result (agent/ecu-data-wipe-mandatory true 2)]
    (is (= (:ok result) true))))

;; ── G12 Part DID generation ───────────────────────────────────────────────────
(deftest test-part-did-generation
  (let [did (agent/issue-part-did "VIN123" "Engine Block")]
    (is (clojure.string/starts-with? did "did:web:hodoki.etzhayyim.com:part:"))))

;; ── G14 PGM yield audit ───────────────────────────────────────────────────────
(deftest test-pgm-yield-below-threshold
  (let [result (agent/audit-pgm-yield 94.0)]
    (is (= (:ok result) false))
    (is (= (:blocked result) true))))

(deftest test-pgm-yield-at-threshold
  (let [result (agent/audit-pgm-yield 95.0)]
    (is (= (:ok result) true))))

;; ── G13 Material recovery rate ────────────────────────────────────────────────
(deftest test-recovery-rate-below-threshold
  ;; 700+100+40 = 840; 840/1040*100 ≈ 80.77% < 95%
  (let [result (agent/calc-recovery-rate 700 100 40 200 1040)]
    (is (= (:ok result) false))
    (is (= (:blocked result) true))))

(deftest test-recovery-rate-at-threshold
  ;; 800+150+50 = 1000; 1000/1000*100 = 100%
  (let [result (agent/calc-recovery-rate 800 150 50 20 1000)]
    (is (= (:ok result) true))
    (is (= (:recovery_pct result) 100))))

(deftest test-asr-landfill-cap
  ;; 850+150+0 = 1000; 1000/1000*100 = 100%; asr 50/1000*100 = 5% >= 5% → blocked
  (let [result (agent/calc-recovery-rate 850 150 0 50 1000)]
    (is (= (:ok result) false))
    (is (= (:blocked result) true))))

(deftest test-asr-landfill-below-cap
  ;; 850+150+0 = 1000; 1000/1000*100 = 100%; asr 40/1000*100 = 4% < 5% → ok
  (let [result (agent/calc-recovery-rate 850 150 0 40 1000)]
    (is (= (:ok result) true))
    (is (= (:asr_landfill_pct result) 4))))

;; ── Settlement (S2/S3/S4) ────────────────────────────────────────────────────
(deftest test-settlement-tithe-split
  ;; 10% tithe + stops at intent (S2/S4) — no buyer-sig-ref → state "intent"
  (let [s (agent/build-settlement-intent 10000000)]
    (is (= (:titheMinor s) 1000000))
    (is (= (:state s) "intent"))
    (is (= (:rail s) "usdc-base-l2"))))

(deftest test-settlement-executed-with-sig
  ;; settlement executes only with operator signature (S3)
  ;; NOTE: agent.py build_settlement_intent returns state "executed" when buyer_sig_ref
  ;; is provided — this is hodoki R0 behaviour (not the R2 Autonomous pattern of omise/ainori
  ;; where state is unconditionally "executed"). We port to the ACTUAL impl behaviour.
  (let [s (agent/build-settlement-intent 10000000 "0xsig")]
    (is (= (:state s) "executed"))))

;; ── Handler tests ─────────────────────────────────────────────────────────────
(deftest test-intake-audit-handler
  (let [out (agent/handle-intake-audit
             {:vin "VIN123"
              :vehicle_desc "2024 Honda Civic"})]
    (is (= (:charter_status out) "passed"))))

(deftest test-depollution-handler-passes
  (let [out (agent/handle-depollution
             {:vin "VIN123"
              :ecu_wiped true
              :witness_count 2
              :fgas_mass_g 100.0
              :fgas_target_pct 96.0})]
    (is (= (:status out) "passed"))))

(deftest test-battery-routing-soh-high
  (let [out (agent/handle-battery-handling
             {:vin "VIN123" :soh_pct 75})]
    (is (= (:routing_decision out) "hikari-second-life"))))

(deftest test-battery-routing-soh-medium
  (let [out (agent/handle-battery-handling
             {:vin "VIN123" :soh_pct 50})]
    (is (= (:routing_decision out) "cell-recycle"))))

(deftest test-battery-routing-soh-low
  (let [out (agent/handle-battery-handling
             {:vin "VIN123" :soh_pct 30})]
    (is (= (:routing_decision out) "kanayama-reclaim"))))

(deftest test-parts-harvest-handler
  (let [out (agent/handle-parts-harvest
             {:vin "VIN123" :part_name "Engine Block"})]
    (is (clojure.string/starts-with?
         (get out :part_did "")
         "did:web:hodoki.etzhayyim.com"))))

(deftest test-catalyst-recovery-handler
  (let [out (agent/handle-catalyst-recovery
             {:pgm_yield_pct 96.0})]
    (is (= (:status out) "passed"))))

(deftest test-body-shred-handler
  (let [out (agent/handle-body-shred
             {:ferrous_kg 800.0
              :non_ferrous_kg 150.0
              :copper_kg 50.0
              :asr_kg 20.0
              :input_mass_kg 1000.0})]
    (is (= (:recovery_pct out) 100))))

;; ── runner ────────────────────────────────────────────────────────────────────
(when (= *file* (System/getProperty "babashka.file"))
  (let [{:keys [fail error]} (clojure.test/run-tests 'hodoki.py.test-agent)]
    (System/exit (if (zero? (+ fail error)) 0 1))))
