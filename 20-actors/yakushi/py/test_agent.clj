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

;; ════════════════════════════════════════════════════════════════════════════════
;; Wave 2 — disinfectant / antiseptic formulation (ADR-2606171400)
;; ════════════════════════════════════════════════════════════════════════════════

;; ── G1(Wave 2) reference set ──────────────────────────────────────────────────
(deftest test-disinfectant-wave2-ok
  (is (= true (:ok (agent/disinfectant_ok "ethanol")))))

(deftest test-disinfectant-non-wave2
  ;; a Wave 1 API is NOT a Wave 2 disinfectant
  (is (= false (:ok (agent/disinfectant_ok "sodium-cromoglicate")))))

;; ── G21 efficacy window ───────────────────────────────────────────────────────
(deftest test-efficacy-ethanol-in-window
  ;; 消毒用エタノール 80 vol% — inside [60–90]
  (is (= true (:ok (agent/disinfectant_efficacy_ok "ethanol" 80.0)))))

(deftest test-efficacy-ethanol-too-weak
  (is (= false (:ok (agent/disinfectant_efficacy_ok "ethanol" 50.0)))))

(deftest test-efficacy-ethanol-too-strong
  ;; >90% flash-evaporates before denaturation — blocked
  (is (= false (:ok (agent/disinfectant_efficacy_ok "ethanol" 99.0)))))

(deftest test-efficacy-hypochlorite-surface-in-window
  (is (= true (:ok (agent/disinfectant_efficacy_ok "sodium-hypochlorite" 0.1)))))

(deftest test-efficacy-unknown-active
  (is (= false (:ok (agent/disinfectant_efficacy_ok "bleach-x" 5.0)))))

;; ── G22 no toxic-gas formulation ──────────────────────────────────────────────
(deftest test-toxic-gas-hypochlorite-acid-refused
  (is (= false (:ok (agent/no_toxic_gas_ok "sodium-hypochlorite" ["citric-acid"])))))

(deftest test-toxic-gas-hypochlorite-ammonia-refused
  (is (= false (:ok (agent/no_toxic_gas_ok "sodium-hypochlorite" ["ammonia"])))))

(deftest test-toxic-gas-hypochlorite-water-ok
  (is (= true (:ok (agent/no_toxic_gas_ok "sodium-hypochlorite" ["water"])))))

(deftest test-toxic-gas-ethanol-acid-ok
  ;; ethanol + acid is not a toxic-gas combo — only hypochlorite is gated
  (is (= true (:ok (agent/no_toxic_gas_ok "ethanol" ["citric-acid"])))))

;; ── G24 use class ─────────────────────────────────────────────────────────────
(deftest test-use-class-valid
  (is (= true (:ok (agent/use_class_ok "skin-antiseptic")))))

(deftest test-use-class-invalid
  (is (= false (:ok (agent/use_class_ok "injectable")))))

;; ── G23 flammable label lint ──────────────────────────────────────────────────
(deftest test-flammable-label-present
  (is (= true (:ok (agent/flammable_label_ok "ethanol" "用法用量… 火気厳禁")))))

(deftest test-flammable-label-missing
  (is (= false (:ok (agent/flammable_label_ok "isopropanol" "surface disinfectant")))))

(deftest test-flammable-label-not-required-for-nonflammable
  ;; povidone-iodine is not flammable — no 火気厳禁 needed
  (is (= true (:ok (agent/flammable_label_ok "povidone-iodine" "skin antiseptic")))))

;; ── record_formulation (G1/W2 + G21 + G22 + G23 + G24 + G9) ───────────────────
(deftest test-formulation-povidone-iodine-ok
  (let [result (agent/record_formulation "povidone-iodine" 10.0 "skin-antiseptic" ["op" "qp"])]
    (is (not (contains? result :blocked)))))

(deftest test-formulation-ethanol-with-label-ok
  (let [result (agent/record_formulation "ethanol" 80.0 "hand-hygiene" [] "火気厳禁" ["op" "qp"])]
    (is (not (contains? result :blocked)))))

(deftest test-formulation-ethanol-no-flammable-label-blocked
  (let [result (agent/record_formulation "ethanol" 80.0 "hand-hygiene" [] "" ["op" "qp"])]
    (is (= true (:blocked result)))))

(deftest test-formulation-out-of-window-blocked
  (let [result (agent/record_formulation "ethanol" 50.0 "hand-hygiene" [] "火気厳禁" ["op" "qp"])]
    (is (= true (:blocked result)))))

(deftest test-formulation-toxic-gas-blocked
  (let [result (agent/record_formulation "sodium-hypochlorite" 0.1 "surface" ["citric-acid"] "" ["op" "qp"])]
    (is (= true (:blocked result)))))

(deftest test-formulation-low-witness-blocked
  (let [result (agent/record_formulation "povidone-iodine" 10.0 "skin-antiseptic" ["op"])]
    (is (= true (:blocked result)))))

;; ── runner ────────────────────────────────────────────────────────────────────
(when (= *file* (System/getProperty "babashka.file"))
  (let [{:keys [fail error]} (clojure.test/run-tests 'yakushi.py.test-agent)]
    (System/exit (if (zero? (+ fail error)) 0 1))))
