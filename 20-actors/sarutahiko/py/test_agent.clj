#!/usr/bin/env bb
;; sarutahiko 猿田彦 — agent cell tests (no kotoba host, no network, no LLM).
;;
;; ADR-2605252500 R0 scaffold. Exercises the handlers + settlement + gates with injected
;; functions so the suite runs offline (Murakumo-only invariant untouched; G16).
;;
;; Run: bb --classpath 20-actors 20-actors/sarutahiko/py/test_agent.clj
(ns sarutahiko.py.test-agent
  (:require [clojure.test :refer [deftest is testing run-tests]]
            [sarutahiko.py.agent :as agent]))

;; ── test_handle_vehicle_order_success ────────────────────────────────────────────
(deftest test-handle-vehicle-order-success
  (testing "vehicle order created successfully with SBT active"
    (let [out (agent/handle-vehicle-order
               {"buyer_did"     "did:web:member.example.etzhayyim.com"
                "specs"         "Class-8 truck"
                "initial_state" "placed"
                "sbt_active"    true})]
      (is (contains? out "vehicle_order"))
      (is (= "placed" (get (get out "vehicle_order") ":vehicle-order/state"))))))

;; ── test_handle_vehicle_order_sbt_inactive ───────────────────────────────────────
(deftest test-handle-vehicle-order-sbt-inactive
  (testing "vehicle order refused if SBT inactive"
    (let [out (agent/handle-vehicle-order
               {"buyer_did"     "did:web:member.example.etzhayyim.com"
                "specs"         "Class-8 truck"
                "initial_state" "placed"
                "sbt_active"    false})]
      (is (contains? out "error"))
      (is (= "cancelled" (get out "state"))))))

;; ── test_handle_production_progress_no_cid ───────────────────────────────────────
(deftest test-handle-production-progress-no-cid
  (testing "production progress recorded without CID"
    (let [order-id "vo.test.0001"
          stage    "frame-fabrication"
          out      (agent/handle-production-progress
                    {"order_id" order-id
                     "stage"    stage
                     "details"  "Steel cutting complete."})]
      (is (contains? out "production_progress"))
      (is (nil? (get out "attestation"))))))

;; ── test_handle_production_progress_with_cid ─────────────────────────────────────
(deftest test-handle-production-progress-with-cid
  (testing "production progress recorded with CID and attestation"
    (let [order-id "vo.test.0002"
          stage    "paint-finishing"
          cid      "bafybeicidexample"
          out      (agent/handle-production-progress
                    {"order_id" order-id
                     "stage"    stage
                     "cid"      cid
                     "details"  "White paint applied."})]
      (is (contains? out "production_progress"))
      (is (contains? out "attestation"))
      (is (= cid (get (get out "attestation") ":attestation/cid"))))))

;; ── test_handle_quality_pass ──────────────────────────────────────────────────────
(deftest test-handle-quality-pass
  (testing "quality pass marks order as ready"
    (let [order-id "vo.test.0003"
          out      (agent/handle-quality
                    {"order_id"            order-id
                     "result"              "pass"
                     "inspector_did"       "did:web:inspector.example.com"
                     "current_order_state" "qc"})]
      (is (contains? out "quality_record"))
      (is (= "pass" (get (get out "quality_record") ":quality/result")))
      (is (= "ready" (get out "new_order_state"))))))

;; ── test_handle_quality_fail ──────────────────────────────────────────────────────
(deftest test-handle-quality-fail
  (testing "quality fail marks order as cancelled"
    (let [order-id "vo.test.0004"
          out      (agent/handle-quality
                    {"order_id"            order-id
                     "result"              "fail"
                     "defects"             ["major dent"]
                     "inspector_did"       "did:web:inspector.example.com"
                     "current_order_state" "qc"})]
      (is (contains? out "quality_record"))
      (is (= "fail" (get (get out "quality_record") ":quality/result")))
      (is (= "cancelled" (get out "new_order_state"))))))

;; ── test_handle_quality_rework ────────────────────────────────────────────────────
(deftest test-handle-quality-rework
  (testing "quality rework marks order as in-production"
    (let [order-id "vo.test.0005"
          out      (agent/handle-quality
                    {"order_id"            order-id
                     "result"              "rework"
                     "defects"             ["minor scratch"]
                     "inspector_did"       "did:web:inspector.example.com"
                     "current_order_state" "qc"})]
      (is (contains? out "quality_record"))
      (is (= "rework" (get (get out "quality_record") ":quality/result")))
      (is (= "in-production" (get out "new_order_state"))))))

;; ── test_handle_vin_attestation_success ──────────────────────────────────────────
(deftest test-handle-vin-attestation-success
  (testing "VIN attestation creates vehicle record"
    (let [order-id "vo.test.0006"
          vin      "TESTVIN0000000001"
          out      (agent/handle-vin-attestation
                    {"order_id"               order-id
                     "vin"                    vin
                     "emissions_audit_id"     "emissions.test.0006"
                     "silen_vehicle_review_id" "silen.test.0006"
                     "attestation_ids"        ["attest.test.0006.frame"]})]
      (is (contains? out "vehicle_record"))
      (is (= vin (get (get out "vehicle_record") ":vehicle/vin")))
      (is (= (str "did:web:etzhayyim.com:sarutahiko:vehicle:" vin)
             (get (get out "vehicle_record") ":vehicle/did"))))))

;; ── test_build_settlement_intent_tithe_split ─────────────────────────────────────
(deftest test-build-settlement-intent-tithe-split
  (testing "10% tithe split is correct and state is intent"
    (let [gross-minor 1000000000  ; 10,000 USDC
          out         (agent/build-settlement-intent gross-minor)]
      (is (= 100000000 (:titheMinor out)))
      (is (= 900000000 (:factoryPayoutMinor out)))
      (is (= "intent" (:state out))))))

;; ── test_build_settlement_intent_executed_with_sig ───────────────────────────────
(deftest test-build-settlement-intent-executed-with-sig
  (testing "settlement state is executed with buyer signature"
    (let [gross-minor 500000000  ; 5,000 USDC
          buyer-sig   "0xdeadbeef"
          out         (agent/build-settlement-intent gross-minor buyer-sig)]
      (is (= "executed" (:state out)))
      (is (= buyer-sig (:buyerSigRef out))))))

;; ── runner ────────────────────────────────────────────────────────────────────────
(when (= *file* (System/getProperty "babashka.file"))
  (let [{:keys [fail error]} (clojure.test/run-tests 'sarutahiko.py.test-agent)]
    (System/exit (if (zero? (+ fail error)) 0 1))))
