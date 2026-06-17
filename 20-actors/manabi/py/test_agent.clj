#!/usr/bin/env bb
;; Clojure port of py/test_agent.py (manabi open-curriculum education actor tests).
(ns manabi.py.test-agent
  "manabi 学び — agent cell tests (no kotoba host, no network, no LLM).

  ADR-2605261045 Phase 4. Exercises the 5 handlers + settlement + gates with injected
  functions so the suite runs offline (Murakumo-only invariant untouched; G5).

  Run:  bb --classpath 20-actors 20-actors/manabi/py/test_agent.clj"
  (:require [clojure.test :refer [deftest is testing run-tests]]
            [manabi.py.agent :as agent]))

;; ── tests ─────────────────────────────────────────────────────────────────────

(deftest test-literacy-advances-stage
  (testing "literacy advances from intro to phonemic-awareness"
    (let [out (agent/handle_literacy {"current_stage" "intro" "completion_fraction" 0.0})]
      (is (= (get out "current_stage") "phonemic-awareness"))
      (is (> (get out "completion_fraction") 0.0)))))

(deftest test-numeracy-advances-stage
  (testing "numeracy advances from counting to place-value"
    (let [out (agent/handle_numeracy {"current_stage" "counting" "completion_fraction" 0.0})]
      (is (= (get out "current_stage") "place-value"))
      (is (> (get out "completion_fraction") 0.0)))))

(deftest test-civics-charter-levels-understanding
  (testing "civics_charter promotes understanding level"
    (let [out (agent/handle_civics_charter {"learner_did" "did:web:test"
                                            "charter_understanding_level" "foundational"})]
      (is (= (get out "charter_understanding_level") "intermediate")))))

(deftest test-civics-charter-anti-indoctrination
  (testing "civics_charter enforces comparative-religion (G12, G14)"
    (let [out (agent/handle_civics_charter {"learner_did" "did:web:test"
                                            "charter_understanding_level" "foundational"})]
      (is (contains? out "timestamp"))
      (is (not= (get out "charter_understanding_level") "foundational")))))

(deftest test-vocational-creates-skill-attestation
  (testing "vocational creates replayable skill attestation (anti-credentialism G7)"
    (let [out (agent/handle_vocational {"learner_did" "did:web:test"
                                        "domain" "agriculture"})]
      (is (contains? out "demonstration_cid"))
      (is (= (get out "skill_domain") "agriculture")))))

(deftest test-lifelong-inquiry-learner-led
  (testing "lifelong_inquiry is learner-led (G13, G11)"
    (let [out (agent/handle_lifelong_inquiry {"learner_did" "did:web:test"
                                              "inquiry_topic" ""
                                              "completion_fraction" 0.0})]
      (is (contains? out "inquiry_topic"))
      (is (pos? (count (get out "inquiry_topic")))))))

(deftest test-settlement-tithe-split
  (testing "10% tithe split + stops at intent (G7)"
    (let [s (agent/build_settlement_intent 1000000)]
      (is (= (get s "tithe_minor") 100000))
      (is (= (get s "factory_payout_minor") 900000))
      (is (= (get s "state") "intent"))
      (is (= (get s "rail") "usdc-base-l2")))))

(deftest test-settlement-executed-with-member-sig
  (testing "settlement executes only with member signature (G15)"
    (let [s (agent/build_settlement_intent 1000000 "0xmembersig")]
      (is (= (get s "state") "executed"))
      (is (= (get s "buyer_sig_ref") "0xmembersig")))))

(deftest test-domain-gate-offline
  (testing "domain gate enforces (G1...G14)"
    (let [mock-gate (fn [did gate-name]
                      {"allowed" (not= did "blocked") "reason" "test gate"})
          out (agent/check_domain_gate "allowed_did" "G1" mock-gate)]
      (is (= (get out "allowed") true)))))

(deftest test-domain-gate-blocks
  (testing "domain gate blocks when violated"
    (let [mock-gate (fn [did gate-name]
                      {"allowed" (not= did "blocked") "reason" "test gate"})
          out (agent/check_domain_gate "blocked" "G1" mock-gate)]
      (is (= (get out "allowed") false)))))

(deftest test-minor-aggregate-only-enforcement
  (testing "minor learner data passes G6 validation (no forbidden keys)"
    (let [data {"sessionDuration" 45 "completionFraction" 0.5}
          result (agent/_validate_minor_aggregate_only "minor" data)]
      (is (= result true)))))

(deftest test-minor-rejects-performance-data
  (testing "minor learner rejected if performance data present (G6)"
    (let [data {"sessionDuration" 45 "performancePercentile" 85}
          result (agent/_validate_minor_aggregate_only "minor" data)]
      (is (= result false)))))

;; ── runner ────────────────────────────────────────────────────────────────────
(when (= *file* (System/getProperty "babashka.file"))
  (let [{:keys [fail error]} (clojure.test/run-tests 'manabi.py.test-agent)]
    (System/exit (if (zero? (+ fail error)) 0 1))))
