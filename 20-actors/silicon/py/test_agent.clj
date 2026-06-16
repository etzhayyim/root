#!/usr/bin/env bb
;; silicon 珪 — agent gate tests (offline, no kotoba host, no network, no LLM).
;;
;; ADR-2605242500 / 2605242545. Exercises the §2(a)(c) force-review gate (G1),
;; append-only lot traceability (G8), and chip inalienability (G2).
;;
;;   bb --classpath 20-actors 20-actors/silicon/py/test_agent.clj
(ns silicon.py.test-agent
  (:require [clojure.test :refer [deftest is testing run-tests]]
            [silicon.py.agent :as agent]))

;; ── G1 force-review gate ───────────────────────────────────────────────────────

(deftest test-litho-requires-force-review
  (testing "litho without force-review is blocked (G1)"
    (let [g (agent/force-review-gate "litho" nil)]
      (is (false? (:allowed g))))))

(deftest test-implant-denied-verdict-blocks
  (testing "implant with deny verdict blocked (G1)"
    (let [g (agent/force-review-gate "implant" {:verdict "deny"})]
      (is (false? (:allowed g))))))

(deftest test-litho-approve-clears
  (testing "litho with approve-with-conditions clears (G1)"
    (let [g (agent/force-review-gate "litho" {:verdict "approve-with-conditions"})]
      (is (true? (:allowed g))))))

(deftest test-nongated-step-runs
  (testing "non-§2(a)(c) step needs no review"
    (let [g (agent/force-review-gate "etch" nil)]
      (is (true? (:allowed g))))))

;; ── G8 lot traceability ────────────────────────────────────────────────────────

(deftest test-record-step-blocked-without-review
  (testing "record implant blocked without review (G1)"
    (let [out (agent/record-process-step {:id "L" :history []} "implant"
                                         "equip/x" "2026-06-02T00:00:00Z" nil)]
      (is (true? (:blocked out))))))

(deftest test-record-step-monotonic-index
  (testing "monotonic gap-free step chain (G8)"
    (let [rev  {:id "fr.l" :verdict "approve"}
          lot  {:id "L" :history []}
          lot1 (agent/record-process-step lot  "litho"      "e1" "t0" rev)
          lot2 (agent/record-process-step lot1 "deposition" "e2" "t1")
          lot3 (agent/record-process-step lot2 "etch"       "e3" "t2")]
      (is (= [0 1 2] (mapv :stepIndex (:history lot3))))
      (is (true? (agent/lot-traceable lot3))))))

(deftest test-packaging-marks-verified
  (testing "packaging ok → lot verified"
    (let [lot (agent/record-process-step {:id "L" :history []} "packaging"
                                         "e" "t" nil "ok")]
      (is (= "verified" (:state lot))))))

(deftest test-scrap-outcome-sets-state
  (testing "scrapped outcome propagates to lot state"
    (let [lot (agent/record-process-step {:id "L" :history []} "etch"
                                         "e" "t" nil "scrapped")]
      (is (= "scrapped" (:state lot))))))

;; ── G2 chip inalienability ─────────────────────────────────────────────────────

(deftest test-lease-requires-force-review
  (testing "lease/ship requires force-review (G1)"
    (let [out (agent/lease-chip {:id "c"} "did:web:lessee" nil)]
      (is (true? (:blocked out))))))

(deftest test-lease-sets-lessee-not-owner
  (testing "lease sets lessee, no owner attribute (G2)"
    (let [out (agent/lease-chip {:id "c"} "did:web:lessee" "fr.x")]
      (is (= "did:web:lessee" (:leasedToDid out)))
      (is (not (contains? out :owner))))))

(deftest test-sale-is-rejected
  (testing "sell/transfer/burn/set-owner/gift all rejected (G2)"
    (doseq [act ["sell" "transfer" "burn" "set-owner" "gift"]]
      (is (false? (:allowed (agent/assert-no-transfer act)))
          (str act " must be rejected (G2)")))))

(deftest test-lease-is-permitted
  (testing "lease is the only permitted disposition (G2)"
    (is (true? (:allowed (agent/assert-no-transfer "lease"))))))

;; ── runner ────────────────────────────────────────────────────────────────────

(when (= *file* (System/getProperty "babashka.file"))
  (let [{:keys [fail error]} (clojure.test/run-tests 'silicon.py.test-agent)]
    (System/exit (if (zero? (+ fail error)) 0 1))))
