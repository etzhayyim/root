#!/usr/bin/env bb
;; Clojure port of py/test_agent.py (futawa motorcycle agent gate tests).
(ns futawa.py.test-agent
  "futawa 二輪 — agent gate tests (offline, no kotoba host, no network, no LLM).

  ADR-2605261330. Exercises the motorcycle manufacturing constitutional gates: capacity
  caps (G11), ABS-mandatory (G7), sound limit (G6), anti-surveillance (G8), and the
  USDC + tithe settlement (G16/G17/G18).

      bb --classpath 20-actors 20-actors/futawa/py/test_agent.clj"
  (:require [clojure.test :refer [deftest is testing run-tests]]
            [futawa.py.agent :as agent]))

;; ── G11 capacity caps ─────────────────────────────────────────────────────────

(deftest test-g11-displacement-cap
  (testing "displacement over 250cc rejected (G11)"
    (is (false? (:ok (agent/g11_capacity_caps 300 12.0 150.0))))))

(deftest test-g11-power-cap
  (testing "power over 15kW rejected (G11)"
    (is (false? (:ok (agent/g11_capacity_caps 200 16.0 150.0))))))

(deftest test-g11-weight-cap
  (testing "dry weight over 200kg rejected (G11)"
    (is (false? (:ok (agent/g11_capacity_caps 200 12.0 250.0))))))

(deftest test-g11-within-caps
  (testing "within G11 caps accepted"
    (is (true? (:ok (agent/g11_capacity_caps 200 12.0 150.0))))))

;; ── G7 ABS-mandatory ──────────────────────────────────────────────────────────

(deftest test-g7-abs-mandatory-low-cc
  (testing "ABS optional below 125cc (G7)"
    (is (false? (:abs_mandatory (agent/g7_abs_mandatory 100 8.0))))))

(deftest test-g7-abs-mandatory-high-cc
  (testing "ABS mandatory >=125cc / >=6kW (G7)"
    (is (true? (:abs_mandatory (agent/g7_abs_mandatory 150 8.0))))))

;; ── G6 sound limit ────────────────────────────────────────────────────────────

(deftest test-g6-sound-under-limit
  (testing "sound under 80dB accepted (G6)"
    (is (true? (:ok (agent/g6_sound_check 75.0))))))

(deftest test-g6-sound-over-limit
  (testing "sound over 80dB rejected (G6)"
    (is (false? (:ok (agent/g6_sound_check 85.0))))))

;; ── G8 anti-surveillance ──────────────────────────────────────────────────────

(deftest test-g8-surveillance-clean
  (testing "clean BOM accepted (G8)"
    (is (true? (:ok (agent/g8_surveillance_check ["harness" "ecu" "battery"]))))))

(deftest test-g8-surveillance-gps
  (testing "GPS in BOM rejected (G8)"
    (is (false? (:ok (agent/g8_surveillance_check ["harness" "GPS module" "ecu"]))))))

(deftest test-g8-surveillance-v2x
  (testing "V2X in BOM rejected (G8)"
    (is (false? (:ok (agent/g8_surveillance_check ["harness" "v2x modem"]))))))

;; ── stage handlers ────────────────────────────────────────────────────────────

(deftest test-engine-assembly-blocked-on-caps
  (testing "engine assembly blocked on G11 cap (G11)"
    (let [out (agent/handle_engine_assembly {:engine_id "e1" :displacement_cc 300 :power_kw 12.0 :dry_weight_kg 150.0})]
      (is (true? (get-in out [:engine_attestation :blocked]))))))

(deftest test-engine-assembly-passes-caps
  (testing "engine assembly within G11 caps passes"
    (let [out (agent/handle_engine_assembly {:engine_id "e1" :displacement_cc 200 :power_kw 12.0 :dry_weight_kg 150.0})]
      (is (true? (get-in out [:engine_attestation :g11_cap_verified]))))))

(deftest test-electrical-harness-blocks-surveillance
  (testing "electrical harness blocks surveillance (G8)"
    (let [out (agent/handle_electrical_harness {:bom_items ["harness" "telematics modem"]})]
      (is (true? (get-in out [:electrical_attestation :blocked]))))))

(deftest test-suspension-brake-abs-check
  (testing "suspension brake marks ABS-mandatory >=125cc/>=6kW (G7)"
    (let [out (agent/handle_suspension_brake {:displacement_cc 150 :power_kw 10.0 :suspension_brake_id "sb1"})]
      (is (true? (get-in out [:suspension_brake_attestation :abs_mandatory_certified]))))))

(deftest test-test-dyno-sound-limit
  (testing "dyno test blocks sound > 80dB (G6)"
    (let [out (agent/handle_test_dyno_road {:sound_db 85.0 :test_id "t1"})]
      (is (true? (get-in out [:test_record :blocked]))))))

(deftest test-test-dyno-passes
  (testing "dyno test passes under 80dB (G6)"
    (let [out (agent/handle_test_dyno_road {:sound_db 75.0 :dyno_power_kw 12.0 :dyno_torque_nm 50.0 :abs_pass true :test_id "t1"})]
      (is (= "pass" (get-in out [:test_record :result]))))))

;; ── settlement ────────────────────────────────────────────────────────────────

(deftest test-settlement-tithe-split
  (testing "10% tithe + stops at intent (G16/G17)"
    (let [s (agent/build_settlement_intent 20000000)]
      (is (= 2000000 (:titheMinor s)))
      (is (= "intent" (:state s)))
      (is (= "usdc-base-l2" (:rail s))))))

(deftest test-settlement-executed-with-sig
  (testing "settlement executes only with member signature (G17)"
    (let [s (agent/build_settlement_intent 10000000 "0xsig")]
      (is (= "executed" (:state s))))))

;; ── runner ────────────────────────────────────────────────────────────────────

(when (= *file* (System/getProperty "babashka.file"))
  (let [{:keys [fail error]} (clojure.test/run-tests 'futawa.py.test-agent)]
    (System/exit (if (zero? (+ fail error)) 0 1))))
