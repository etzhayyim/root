#!/usr/bin/env bb
;; Clojure port of py/test_agent.py (makura foam pillow agent gate tests).
(ns makura.py.test-agent
  "makura 枕 — agent gate tests (offline, no kotoba host, no network, no LLM).

  ADR-2605261115. Exercises the foam-pillow constitutional gates: KPI caps (G11),
  isocyanate exposure (G6), FR-chemistry exclusion (G8), no-embedded-sensors (G14),
  and the USDC + tithe settlement (G17/G18).

      bb --classpath 20-actors 20-actors/makura/py/test_agent.clj"
  (:require [clojure.test :refer [deftest is testing run-tests]]
            [makura.py.agent :as agent]))

;; ── G11 KPI caps ──────────────────────────────────────────────────────────────

(deftest test-kpi-mass-cap
  (testing "foam mass over 2.0 kg rejected (G11)"
    (is (false? (:ok (agent/kpi_caps_ok 2.5 [50 40 20] 3.0))))))

(deftest test-kpi-dims-cap
  (testing "dims over 80x50x25 rejected (G11)"
    (is (false? (:ok (agent/kpi_caps_ok 1.5 [90 40 20] 3.0))))))

(deftest test-kpi-within
  (testing "within KPI caps accepted (G11)"
    (is (true? (:ok (agent/kpi_caps_ok 1.5 [60 40 20] 3.0))))))

;; ── G6 isocyanate exposure ────────────────────────────────────────────────────

(deftest test-exposure-mdi-ceiling
  (testing "MDI over 5 ppb rejected (G6)"
    (is (false? (:ok (agent/exposure_ok 6.0 1.0))))))

(deftest test-exposure-tdi-ceiling
  (testing "TDI over 2 ppb rejected (G6)"
    (is (false? (:ok (agent/exposure_ok 3.0 3.0))))))

;; ── G8 FR-chemistry exclusion ─────────────────────────────────────────────────

(deftest test-fr-chemistry-excluded
  (testing "PBDE/TDCPP rejected (G8)"
    (is (false? (:ok (agent/fr_chemistry_ok ["polyol" "TDCPP"]))))))

(deftest test-fr-free-ok
  (testing "FR-free chemistry accepted (G8)"
    (is (true? (:ok (agent/fr_chemistry_ok ["polyol" "mdi" "surfactant"]))))))

;; ── G14 no embedded sensors ───────────────────────────────────────────────────

(deftest test-bom-rejects-embedded
  (testing "RFID/NFC in BoM rejected (G14)"
    (is (false? (:ok (agent/bom_no_embedded ["foam" "fabric" "RFID tag"]))))))

(deftest test-bom-clean
  (testing "clean BoM accepted (G14)"
    (is (true? (:ok (agent/bom_no_embedded ["foam" "fabric" "zipper"]))))))

;; ── record_foam_batch ─────────────────────────────────────────────────────────

(deftest test-foam-batch-blocked-on-fr
  (testing "foam batch blocked on prohibited FR (G8)"
    (let [out (agent/record_foam_batch "b" ["pbde"] 1.0 1.0)]
      (is (true? (:blocked out))))))

(deftest test-foam-batch-blocked-on-exposure
  (testing "foam batch blocked on MDI over-exposure (G6)"
    (let [out (agent/record_foam_batch "b" ["polyol"] 9.0 1.0)]
      (is (true? (:blocked out))))))

;; ── finalize_pillow_lot ────────────────────────────────────────────────────────

(deftest test-lot-blocked-over-kpi
  (testing "pillow lot blocked over KPI (G11)"
    (let [out (agent/finalize_pillow_lot "l" 3.0 [50 40 20] 3.0 [])]
      (is (true? (:blocked out))))))

;; ── settlement ────────────────────────────────────────────────────────────────

(deftest test-settlement-tithe-split
  (testing "10% tithe + stops at intent (G17/G18)"
    (let [s (agent/build_settlement_intent 20000000)]
      (is (= 2000000 (:titheMinor s)))
      (is (= "intent" (:state s)))
      (is (= "usdc-base-l2" (:rail s))))))

(deftest test-settlement-executed-with-sig
  (testing "settlement executes only with member signature (G18)"
    (let [s (agent/build_settlement_intent 1000000 "0xsig")]
      (is (= "executed" (:state s))))))

;; ── runner ────────────────────────────────────────────────────────────────────

(when (= *file* (System/getProperty "babashka.file"))
  (let [{:keys [fail error]} (clojure.test/run-tests 'makura.py.test-agent)]
    (System/exit (if (zero? (+ fail error)) 0 1))))
