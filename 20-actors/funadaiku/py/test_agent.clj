#!/usr/bin/env bb
;; funadaiku 船大工 — agent cell tests (Clojure port of test_agent.py).
;;
;; ADR-2606013400 Phase 4. Exercises the 9 handlers + gate + settlement with no
;; kotoba host, no network, no LLM. Tests focus on zero-emission propulsion
;; enforcement (G8), green-H₂ chain-of-custody (G9), and USDC tithe-split (G7).
;;
;; Run:  bb --classpath 20-actors 20-actors/funadaiku/py/test_agent.clj
(ns funadaiku.py.test-agent
  (:require [clojure.test :refer [deftest is testing run-tests]]
            [funadaiku.py.agent :as agent]))

;; ── L1 steel block fabrication ─────────────────────────────────────────────────
(deftest test-steel-block-fabrication-plan
  (testing "L1: steel block cutting-plan generated"
    (let [out (agent/handle-steel-block-fabrication
               {:blockId "block-001" :dimensions "12000x8000x25"})]
      (is (= "cutting-plan" (:status out)))
      (is (contains? out :cutting_plan)))))

;; ── L2 grand-block assembly ────────────────────────────────────────────────────
(deftest test-grand-block-assembly-needs-minimum-blocks
  (testing "L2: rejects grand-block with <2 sub-blocks"
    (let [out (agent/handle-grand-block-assembly
               {:gblockId "gb-001" :subBlocks []})]
      (is (some? (:error out))))))

(deftest test-grand-block-assembly-success
  (testing "L2: jig design + Oshidashi witness"
    (let [out (agent/handle-grand-block-assembly
               {:gblockId "gb-001" :subBlocks ["block-a" "block-b" "block-c"]})]
      (is (= "jig-designed" (:status out)))
      (is (contains? out :witness_quorum)))))

;; ── L3 weld NDT inspection ─────────────────────────────────────────────────────
(deftest test-weld-ndt-zero-welds-pass
  (testing "L3: NDT pass when zero welds (vacuous)"
    (let [out (agent/handle-weld-ndt-inspection
               {:gblockId "gb-001" :welds []})]
      (is (= "pass" (:result out)))
      (is (= [] (:defects out))))))

(deftest test-weld-ndt-with-welds
  (testing "L3: NDT evaluation result present"
    (let [out (agent/handle-weld-ndt-inspection
               {:gblockId "gb-001" :welds [{:id "w1"} {:id "w2"}]})]
      (is (some? (:ndt_eval out))))))

;; ── G8+G9 zero-emission propulsion gate (DEFINING) ────────────────────────────
(deftest test-gate-g8-rejects-fossil
  (testing "G8: diesel propulsion rejected (DEFINING GATE)"
    (let [out (agent/gate-zero-emission-propulsion {:type "diesel-main-engine"})]
      (is (false? (:ok out)))
      (is (clojure.string/includes? (clojure.string/lower-case (:reason out)) "fossil")))))

(deftest test-gate-g8-rejects-missing-hydrogen
  (testing "G8: missing hydrogen rejected"
    (let [out (agent/gate-zero-emission-propulsion {:type "solar-wind"})]
      (is (false? (:ok out)))
      (is (clojure.string/includes? (clojure.string/lower-case (:reason out)) "hydrogen")))))

(deftest test-gate-g8-rejects-missing-solar
  (testing "G8: missing solar rejected"
    (let [out (agent/gate-zero-emission-propulsion {:type "wind-hydrogen"})]
      (is (false? (:ok out)))
      (is (clojure.string/includes? (clojure.string/lower-case (:reason out)) "solar")))))

(deftest test-gate-g9-rejects-non-green-hydrogen
  (testing "G9: non-green hydrogen rejected (well-to-wake)"
    (let [out (agent/gate-zero-emission-propulsion
               {:type "wind-solar-hydrogen"
                :hydrogen_source_certification "fossil-steam-reforming"})]
      (is (false? (:ok out)))
      (is (clojure.string/includes? (clojure.string/lower-case (:reason out)) "green")))))

(deftest test-gate-g8-g9-pass-green-zero-emission
  (testing "G8+G9: zero-emission + green-H₂ passes (defining gate)"
    (let [out (agent/gate-zero-emission-propulsion
               {:type "wind-solar-hydrogen"
                :hydrogen_source_certification "green-h2-electrolyzer-renewable"})]
      (is (true? (:ok out))))))

;; ── L4 powertrain integration ─────────────────────────────────────────────────
(deftest test-powertrain-integration-blocked-by-non-zero-emission
  (testing "L4: powertrain integration blocked by G8 violation"
    (let [out (agent/handle-powertrain-integration
               {:powertrain {:type "coal-auxiliary-boiler"}})]
      (is (true? (:blocked out)))
      (is (some? (:reason out))))))

(deftest test-powertrain-integration-success
  (testing "L4: zero-emission propulsion verified + settlement intent"
    (let [out (agent/handle-powertrain-integration
               {:vesselId "nagi-0001"
                :powertrain {:type "wind-solar-hydrogen"
                             :wind_rig_type "Flettner rotor"
                             :solar_wattage 160000
                             :fc_power_mw 2.4
                             :battery_capacity_mwh 2.0
                             :hydrogen_source_certification "green-h2-electrolyzer-norway"}
                :gross_minor 500000000})]
      (is (true? (:powertrain_verified out)))
      (is (contains? out :settlement_intent)))))

;; ── L5a outfitting ────────────────────────────────────────────────────────────
(deftest test-outfitting-mep-verify
  (testing "L5a: MEP verification + no fossil aux"
    (let [out (agent/handle-outfitting {:vesselId "nagi-0001"})]
      (is (= "outfitting-complete" (:status out)))
      (is (contains? out :mep_verification)))))

;; ── L5b launch + commissioning ────────────────────────────────────────────────
(deftest test-launch-commissioning-gnc-smoke
  (testing "L5b: launch + GNC smoke-test verify"
    (let [out (agent/handle-launch-commissioning {:vesselId "nagi-0001"})]
      (is (true? (:gnc_ready out)))
      (is (= "launched" (:status out))))))

;; ── L5c sea trial ─────────────────────────────────────────────────────────────
(deftest test-sea-trial-efficiency-measure
  (testing "L5c: sea trial wind/solar/H₂ efficiency measure"
    (let [out (agent/handle-sea-trial {:vesselId "nagi-0001"})]
      (is (true? (:sea_trial_pass out)))
      (is (contains? out :sea_trial_plan)))))

;; ── cross: decarbonization audit ──────────────────────────────────────────────
(deftest test-decarbonization-audit-imo-ghg
  (testing "L5x: well-to-wake IMO GHG audit (EEXI/CII)"
    (let [out (agent/handle-decarbonization-audit {:vesselId "nagi-0001"})]
      (is (some? (:eexi_rating out)))
      (is (some? (:cii_rating out))))))

;; ── terminal: class certification binder ─────────────────────────────────────
(deftest test-class-certification-terminal
  (testing "terminal: ABS/DNV/ClassNK cert binding + IMO registration"
    (let [out (agent/handle-class-certification-binder {:vesselId "nagi-0001"})]
      (is (true? (:imo_registered out)))
      (is (= "class-certified" (:status out))))))

;; ── settlement: G7 tithe split, G12 operator sig ─────────────────────────────
(deftest test-settlement-tithe-split
  (testing "G7: 10% tithe split + stops at intent"
    (let [s (agent/build-settlement-intent 500000000)]
      (is (= 50000000 (:titheMinor s)))
      (is (= 450000000 (:shipyardPayoutMinor s)))
      (is (= "intent" (:state s)))
      (is (= "usdc-base-l2" (:rail s))))))

(deftest test-settlement-executed-only-with-operator-sig
  (testing "G12: settlement executes only with operator signature"
    (let [s (agent/build-settlement-intent 1000000 "0xoperatorsig")]
      (is (= "executed" (:state s))))))

;; ── runner ────────────────────────────────────────────────────────────────────
(when (= *file* (System/getProperty "babashka.file"))
  (let [{:keys [fail error]} (clojure.test/run-tests 'funadaiku.py.test-agent)]
    (System/exit (if (zero? (+ fail error)) 0 1))))
