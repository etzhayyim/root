#!/usr/bin/env bb
;; tatekata 建方 — agent gate tests (offline, no kotoba host, no network, no LLM).
;;
;; ADR-2605250715. Exercises the construction constitutional gates: KPI caps (G11),
;; witness quorum (G3), phase advancement (G17), and the USDC + tithe settlement
;; (G15/G16).
;;
;; Run: bb --classpath 20-actors 20-actors/tatekata/py/test_agent.clj
(ns tatekata.py.test-agent
  (:require [clojure.test :refer [deftest is testing run-tests]]
            [tatekata.py.agent :as agent]))

;; ── test-kpi-stories-cap ──────────────────────────────────────────────────────
(deftest test-kpi-stories-cap
  (testing "stories over 2 rejected (G11)"
    (is (false? (:ok (agent/kpi-caps-ok 3 5000))))))

;; ── test-kpi-footprint-cap ────────────────────────────────────────────────────
(deftest test-kpi-footprint-cap
  (testing "footprint over 5000 m² rejected (G11)"
    (is (false? (:ok (agent/kpi-caps-ok 2 6000))))))

;; ── test-kpi-within-caps ──────────────────────────────────────────────────────
(deftest test-kpi-within-caps
  (testing "within KPI caps accepted (G11)"
    (is (true? (:ok (agent/kpi-caps-ok 2 5000))))))

;; ── test-witness-quorum-insufficient ─────────────────────────────────────────
(deftest test-witness-quorum-insufficient
  (testing "witness count <2 rejected (G3)"
    (is (false? (:ok (agent/witness-quorum-ok ["did:web:giemon"]))))))

;; ── test-witness-quorum-sufficient ───────────────────────────────────────────
(deftest test-witness-quorum-sufficient
  (testing "witness count ≥2 accepted (G3)"
    (let [dids ["did:web:giemon.kuni-umi.etzhayyim.com"
                "did:web:mimi.kuni-umi.etzhayyim.com"]]
      (is (true? (:ok (agent/witness-quorum-ok dids)))))))

;; ── test-advance-phase-foundation ────────────────────────────────────────────
(deftest test-advance-phase-foundation
  (testing "foundation → structural advance (G17)"
    (let [result (agent/advance-phase "foundation")]
      (is (= "structural" (:state result)))
      (is (nil? (:blocked result))))))

;; ── test-advance-phase-structural ────────────────────────────────────────────
(deftest test-advance-phase-structural
  (testing "structural → mep advance (G17)"
    (let [result (agent/advance-phase "structural")]
      (is (= "mep" (:state result)))
      (is (nil? (:blocked result))))))

;; ── test-advance-phase-terminal ──────────────────────────────────────────────
(deftest test-advance-phase-terminal
  (testing "commissioning terminal (G17)"
    (let [result (agent/advance-phase "commissioning")]
      (is (= "commissioning" (:state result)))
      (is (some? (:blocked result))))))

;; ── test-foundation-excavation ───────────────────────────────────────────────
(deftest test-foundation-excavation
  (testing "foundation excavation plan recorded (G17)"
    (let [result (agent/handle-foundation-excavation {"spec" "site grid excavation"})]
      (is (= "foundation" (get (get result "plan") "phase"))))))

;; ── test-structural-assembly ─────────────────────────────────────────────────
(deftest test-structural-assembly
  (testing "structural assembly plan recorded (G17)"
    (let [result (agent/handle-structural-assembly {"bim_ref" "freeCAD-model-ref"})]
      (is (= "structural" (get (get result "plan") "phase"))))))

;; ── test-mep-installation ────────────────────────────────────────────────────
(deftest test-mep-installation
  (testing "MEP installation plan recorded (G17)"
    (let [result (agent/handle-mep-installation {"mep_design" "hvac-electrical-plumbing"})]
      (is (= "mep" (get (get result "plan") "phase"))))))

;; ── test-finishing-handoff ────────────────────────────────────────────────────
(deftest test-finishing-handoff
  (testing "finishing handoff plan recorded (G17)"
    (let [result (agent/handle-finishing-handoff {"phase_input" "from-mep-complete"})]
      (is (= "finishing" (get (get result "plan") "phase"))))))

;; ── test-commissioning ───────────────────────────────────────────────────────
(deftest test-commissioning
  (testing "commissioning plan recorded (G17)"
    (let [result (agent/handle-commissioning {"phase_input" "from-finishing-complete"})]
      (is (= "commissioning" (get (get result "plan") "phase"))))))

;; ── test-progress-witness-quorum-fail ────────────────────────────────────────
(deftest test-progress-witness-quorum-fail
  (testing "progress blocked on insufficient witnesses (G3/G17)"
    (let [result (agent/record-phase-progress "foundation" "did:project" ["did:giemon"])]
      (is (true? (:blocked result))))))

;; ── test-progress-witness-quorum-pass ────────────────────────────────────────
(deftest test-progress-witness-quorum-pass
  (testing "progress recorded with witness quorum (G3/G17)"
    (let [dids   ["did:web:giemon.kuni-umi.etzhayyim.com"
                  "did:web:mimi.kuni-umi.etzhayyim.com"]
          result (agent/record-phase-progress "structural" "did:project" dids
                                              "QmPhotos" "QmDepths")]
      (is (= "structural" (get result ":progress/phase"))))))

;; ── test-settlement-tithe-split ──────────────────────────────────────────────
(deftest test-settlement-tithe-split
  (testing "10% tithe + stops at intent (G15/G16)"
    (let [s (agent/build-settlement-intent 50000000)]
      (is (= 5000000 (:titheMinor s)))
      (is (= "intent" (:state s)))
      (is (= "usdc-base-l2" (:rail s))))))

;; ── test-settlement-executed-with-sig ────────────────────────────────────────
(deftest test-settlement-executed-with-sig
  (testing "settlement executes only with owner signature (G16)"
    (let [s (agent/build-settlement-intent 10000000 "0xsig")]
      (is (= "executed" (:state s))))))

;; ── runner ────────────────────────────────────────────────────────────────────
(when (= *file* (System/getProperty "babashka.file"))
  (let [{:keys [fail error]} (clojure.test/run-tests 'tatekata.py.test-agent)]
    (System/exit (if (zero? (+ fail error)) 0 1))))
