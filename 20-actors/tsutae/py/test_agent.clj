#!/usr/bin/env bb
;; tsutae 伝え — agent cell tests (no kotoba host, no network, no LLM).
;; Port of py/test_agent.py — ADR-2605261300 R0 scaffold.
;;
;; Run:  bb --classpath 20-actors 20-actors/tsutae/py/test_agent.clj
(ns tsutae.py.test-agent
  (:require [clojure.test :refer [deftest is run-tests testing]]
            [tsutae.py.agent :as agent]))

;; ── tests ─────────────────────────────────────────────────────────────────────

(deftest test-device-order-success
  (testing "device order created with active SBT + open SoC"
    (let [out (agent/handle_device_order
               {"buyer_did"     "did:web:member.example.etzhayyim.com"
                "specs"         "handheld"
                "soc"           "StarFive-JH7110"
                "initial_state" "placed"
                "sbt_active"    true})]
      (is (contains? out "device_order"))
      (is (= "placed" (get (get out "device_order") ":device-order/state"))))))

(deftest test-device-order-sbt-inactive
  (testing "device order refused if SBT inactive (N9)"
    (let [out (agent/handle_device_order {"buyer_did" "did:web:m" "sbt_active" false})]
      (is (contains? out "error"))
      (is (= "cancelled" (get out "state"))))))

(deftest test-device-order-rejects-proprietary-soc
  (testing "device order refused for proprietary SoC (G9/N1)"
    (let [out (agent/handle_device_order
               {"buyer_did"  "did:web:m"
                "soc"        "Snapdragon-8-Gen3"
                "sbt_active" true})]
      (is (contains? out "error"))
      (is (= "cancelled" (get out "state"))))))

(deftest test-is-open-soc
  (testing "is_open_soc accepts RISC-V, rejects proprietary"
    (let [open? (every? agent/is_open_soc ["StarFive-JH7110" "iwakura" "SiFive-HiFive-Unmatched"])
          none-proprietary? (not (some agent/is_open_soc ["Snapdragon-8" "Apple-A17" "Exynos-2400"]))]
      (is open?)
      (is none-proprietary?))))

(deftest test-production-progress-no-cid
  (testing "production progress without CID → no attestation"
    (let [out (agent/handle_production_progress {"order_id" "do.t.1" "stage" "pcb-smt"})]
      (is (contains? out "production_progress"))
      (is (nil? (get out "attestation"))))))

(deftest test-production-progress-with-cid
  (testing "production progress with CID → attestation"
    (let [out (agent/handle_production_progress
               {"order_id" "do.t.2"
                "stage"    "display-attachment"
                "cid"      "bafkreicid"
                "details"  "laminated"})]
      (is (= "bafkreicid" (get (get out "attestation") ":attestation/cid"))))))

(deftest test-production-progress-unknown-stage
  (testing "unknown (truck) stage rejected"
    (let [out (agent/handle_production_progress {"order_id" "do.t.3" "stage" "frame-weld"})]
      (is (contains? out "error")))))

(deftest test-quality-pass-fail-rework
  (testing "quality pass→ready / fail→cancelled / rework→in-production"
    (let [base {"order_id" "do.t.4" "inspector_did" "did:web:insp" "current_order_state" "qc"}
          p    (agent/handle_quality (merge base {"result" "pass"}))
          f    (agent/handle_quality (merge base {"result" "fail" "defects" ["dead pixel"]}))
          r    (agent/handle_quality (merge base {"result" "rework"}))]
      (is (= "ready"         (get p "new_order_state")))
      (is (= "cancelled"     (get f "new_order_state")))
      (is (= "in-production" (get r "new_order_state"))))))

(deftest test-device-attestation-quorum
  (testing "device attestation needs ≥2 robot signers (G4) + mints DID (G14)"
    (let [ok  (agent/handle_device_attestation
               {"order_id"        "do.t.5"
                "serial"          "SN0001"
                "robot_signers"   ["did:web:etzhayyim.com:mimi-1" "did:web:etzhayyim.com:otete-1"]
                "bom_lineage_cids" ["bafpcb" "bafchassis"]})
          bad (agent/handle_device_attestation
               {"order_id"      "do.t.5"
                "serial"        "SN0002"
                "robot_signers" ["did:web:etzhayyim.com:mimi-1"]})]
      (is (= true (get ok "accept")))
      (is (= "did:web:etzhayyim.com:tsutae:device:SN0001"
             (get (get ok "device_record") ":device/did")))
      (is (= false (get bad "accept"))))))

(deftest test-settlement-tithe-split
  (testing "10% tithe split + state intent"
    (let [out (agent/build_settlement_intent 60000000)]
      (is (= 6000000  (get out "titheMinor")))
      (is (= 54000000 (get out "factoryPayoutMinor")))
      (is (= "intent" (get out "state"))))))

(deftest test-settlement-executed-with-sig
  (testing "settlement executed with buyer signature (G15)"
    (let [out (agent/build_settlement_intent 50000000 "0xdeadbeef")]
      (is (= "executed"    (get out "state")))
      (is (= "0xdeadbeef" (get out "buyerSigRef"))))))

;; ── runner ────────────────────────────────────────────────────────────────────
(when (= *file* (System/getProperty "babashka.file"))
  (let [{:keys [fail error]} (clojure.test/run-tests 'tsutae.py.test-agent)]
    (System/exit (if (zero? (+ fail error)) 0 1))))
