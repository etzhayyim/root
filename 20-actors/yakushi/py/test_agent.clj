#!/usr/bin/env bb
;; Clojure port of py/test_agent.py (yakushi pharmaceutical manufacturing — 26 tests).
(ns yakushi.py.test-agent
  "yakushi 薬師 test harness. Verifies constitutional gates of ADR-2605250500:
    G1   OTC-only, Wave 1 off-patent APIs
    G3   silen-pharma-review baseline
    G4   QP co-sign required
    G5   adverse event aggregation (no patient DID)
    G9   witness invariant N>=2
    G10  patient identity non-traceable
    G17/G18/G19 settlement (USDC + TitheRouter 10%, stops at :intent)"
  (:require [clojure.test :refer [deftest is run-tests]]
            [yakushi.py.agent :as agent]))

;; ── G1 OTC gate ───────────────────────────────────────────────────────────────
(deftest test-api-otc-wave1
  (is (= true (:ok (agent/api_otc_ok "sodium-cromoglicate")))))

(deftest test-api-not-wave1
  (is (= false (:ok (agent/api_otc_ok "omeprazole")))))

;; ── G3 silen-pharma-review ────────────────────────────────────────────────────
(deftest test-review-approved
  (is (= true (:ok (agent/review_attested "approve" "Wave 1")))))

(deftest test-review-rejected
  (is (= false (:ok (agent/review_attested "reject" "Wave 1")))))

;; ── G4 QP signature ───────────────────────────────────────────────────────────
(deftest test-qp-signature-ok
  (is (= true (:ok (agent/qp_signature_ok "did:web:...qp" "passkey-ref")))))

(deftest test-qp-signature-missing
  (is (= false (:ok (agent/qp_signature_ok "" "")))))

;; ── G5/G10 adverse event aggregation ─────────────────────────────────────────
(deftest test-ae-valid-aggregation
  (is (= true (:ok (agent/adverse_event_ok "lot:001" "mild" "recovered")))))

(deftest test-ae-invalid-severity
  (is (= false (:ok (agent/adverse_event_ok "lot:001" "extreme" "unknown")))))

(deftest test-ae-invalid-outcome
  (is (= false (:ok (agent/adverse_event_ok "lot:001" "mild" "cured")))))

(deftest test-ae-missing-lot
  (is (= false (:ok (agent/adverse_event_ok "" "mild" "recovered")))))

;; ── G9 witness quorum ─────────────────────────────────────────────────────────
(deftest test-witness-quorum-ok
  (is (= true (:ok (agent/witness_quorum_ok ["did1" "did2"])))))

(deftest test-witness-quorum-low
  (is (= false (:ok (agent/witness_quorum_ok ["did1"])))))

;; ── record_synthesis (G1 + G2 + G9) ──────────────────────────────────────────
(deftest test-synthesis-wave1-ok
  (let [result (agent/record_synthesis "sodium-cromoglicate" "literature-ref" ["did1" "did2"])]
    (is (not (contains? result :blocked)))))

(deftest test-synthesis-non-wave1
  (let [result (agent/record_synthesis "omeprazole" "literature-ref" ["did1" "did2"])]
    (is (= true (:blocked result)))))

(deftest test-synthesis-low-witness
  (let [result (agent/record_synthesis "sodium-cromoglicate" "literature-ref" ["did1"])]
    (is (= true (:blocked result)))))

;; ── record_fill (G8) ─────────────────────────────────────────────────────────
(deftest test-fill-aseptic-ok
  (let [result (agent/record_fill "eye-drop" "aseptic-0.22µm-filter" "op-did" "qp-did")]
    (is (not (contains? result :blocked)))))

(deftest test-fill-autoclave-ok
  (let [result (agent/record_fill "tablet" "terminal-autoclave" "op-did" "qp-did")]
    (is (not (contains? result :blocked)))))

(deftest test-fill-invalid-sterilization
  (let [result (agent/record_fill "eye-drop" "uv-sterilization" "op-did" "qp-did")]
    (is (= true (:blocked result)))))

;; ── record_qc (G4/G13) ───────────────────────────────────────────────────────
(deftest test-qc-release-ok
  (let [result (agent/record_qc "lot:001" "ICH Q3 compliant" "qp-did" "release")]
    (is (not (contains? result :blocked)))))

(deftest test-qc-release-no-qp
  (let [result (agent/record_qc "lot:001" "ICH Q3 compliant" "" "release")]
    (is (= true (:blocked result)))))

;; ── record_ae (G5/G10) ───────────────────────────────────────────────────────
(deftest test-ae-record-valid
  (let [result (agent/record_ae "lot:001" "moderate" "not-recovered" "ipfs-cid")]
    (is (not (contains? result :blocked)))))

(deftest test-ae-record-invalid
  (let [result (agent/record_ae "lot:001" "bad" "unknown")]
    (is (= true (:blocked result)))))

;; ── settlement (G17/G18/G19) ─────────────────────────────────────────────────
(deftest test-settlement-intent
  ;; 10% tithe + stops at intent (G17/G18/G19) — no qp-sig-ref → state "intent"
  (let [s (agent/build_settlement_intent 10000000)]
    (is (= 1000000 (:titheMinor s)))
    (is (= "intent" (:state s)))
    (is (= "usdc-base-l2" (:rail s)))))

(deftest test-settlement-executed-with-sig
  ;; settlement executes only with QP signature (G18)
  ;; NOTE: agent.py build_settlement_intent returns state "executed" when qp_sig_ref
  ;; is provided — this is yakushi R0 behaviour (not the R2 Autonomous pattern of omise/ainori
  ;; where state is unconditionally "executed"). We port to the ACTUAL impl behaviour.
  (let [s (agent/build_settlement_intent 10000000 "0xsig")]
    (is (= "executed" (:state s)))))

;; ── record_raw_material ───────────────────────────────────────────────────────
(deftest test-raw-material-valid-grade
  (let [result (agent/record_raw_material "sodium cromoglicate" "公定" "low-risk")]
    (is (not (contains? result :blocked)))))

(deftest test-raw-material-invalid-grade
  (let [result (agent/record_raw_material "sodium cromoglicate" "custom" "low-risk")]
    (is (= true (:blocked result)))))

;; ── runner ────────────────────────────────────────────────────────────────────
(when (= *file* (System/getProperty "babashka.file"))
  (let [{:keys [fail error]} (clojure.test/run-tests 'yakushi.py.test-agent)]
    (System/exit (if (zero? (+ fail error)) 0 1))))
