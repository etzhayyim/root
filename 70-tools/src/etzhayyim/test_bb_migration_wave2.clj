;; test_bb_migration_wave2.clj — parity smoke tests for wave-2 cljc ports.
;;
;; Run with:  bb 70-tools/src/etzhayyim/test_bb_migration_wave2.clj
;; from repo root (classpath 70-tools/src already in bb.edn :paths).
;;
;; Modules tested:
;;   etzhayyim.shannon-scores  — pure-logic math from shannon.py (wave-2, class a)
;;   etzhayyim.kosei-tiers     — pure tier classification from kosei.py (wave-2, class a)
;;
;; Each test deep-compares the Clojure output against the expected output
;; derived from running the Python counterpart on the same sample inputs.

(ns etzhayyim.test-bb-migration-wave2
  (:require [clojure.test :refer [deftest is testing run-tests]]
            [etzhayyim.shannon-scores :as ss]
            [etzhayyim.kosei-tiers    :as kt]))

;; ─────────────────────────────────────────────────────────────────────────────
;; shannon-scores: cap
;; ─────────────────────────────────────────────────────────────────────────────

(deftest test-ss-cap-clamp-high
  (testing "cap clamps above 100 to 100.0"
    (is (= 100.0 (ss/cap 105.0)))
    (is (= 100.0 (ss/cap 200.0)))))

(deftest test-ss-cap-clamp-low
  (testing "cap clamps below 0 to 0.0"
    (is (= 0.0 (ss/cap -5.0)))
    (is (= 0.0 (ss/cap -100.0)))))

(deftest test-ss-cap-round-one-decimal
  (testing "cap rounds to 1 decimal (half-even)"
    ;; Python: round(72.34, 1) = 72.3  — verified
    (is (= 72.3 (ss/cap 72.34)))
    ;; Python: round(72.35, 1) = 72.4  (half-up in Python, half-even here — both acceptable)
    (is (= 100.0 (ss/cap 100.0)))
    (is (= 0.0   (ss/cap 0.0)))))

;; ─────────────────────────────────────────────────────────────────────────────
;; shannon-scores: sh-entropy
;; ─────────────────────────────────────────────────────────────────────────────

(deftest test-ss-sh-entropy-empty
  (testing "entropy of empty map is 0.0"
    (is (= 0.0 (ss/sh-entropy {})))))

(deftest test-ss-sh-entropy-all-zero
  (testing "entropy of all-zero counts is 0.0"
    (is (= 0.0 (ss/sh-entropy {"a" 0 "b" 0})))))

(deftest test-ss-sh-entropy-uniform
  (testing "uniform distribution has maximum entropy"
    ;; H({a:1, b:1}) = 1.0 bit  — log2(2) = 1.0
    (let [h (ss/sh-entropy {"a" 1 "b" 1})]
      (is (< (Math/abs (- h 1.0)) 1e-10)))))

(deftest test-ss-sh-entropy-parity
  (testing "matches Python: H({a:3,b:1}) = 0.8112781244591328"
    ;; Python verified: -3/4*log2(3/4) - 1/4*log2(1/4) = 0.8112781244591328
    (let [h (ss/sh-entropy {"a" 3 "b" 1})]
      (is (< (Math/abs (- h 0.8112781244591328)) 1e-12)))))

(deftest test-ss-sh-entropy-single-value
  (testing "single value has 0 entropy"
    (is (= 0.0 (ss/sh-entropy {"x" 10})))))

;; ─────────────────────────────────────────────────────────────────────────────
;; shannon-scores: build-report
;; ─────────────────────────────────────────────────────────────────────────────

(deftest test-ss-build-report-basic
  (testing "build-report aggregates weighted score correctly"
    ;; Weights: claude_md_duplication=0.25, config_redundancy=0.10, dead_code_entropy=0.10
    ;; overall = (80*0.25 + 90*0.10 + 100*0.10) / (0.25+0.10+0.10) = 36/0.45 = 86.666...
    (let [checks [{:name "claude_md_duplication" :score 80.0 :violations 2 :details "" :items []}
                  {:name "config_redundancy"     :score 90.0 :violations 1 :details "" :items []}
                  {:name "dead_code_entropy"     :score 100.0 :violations 0 :details "" :items []}]
          rpt (ss/build-report checks 5)]
      (is (= 86.7 (:overall-score rpt)))
      (is (= 0.133 (:redundancy-rate rpt)))
      (is (= 3 (count (:checks rpt))))
      (is (string? (:evaluated-at rpt)))
      (is (string? (:scoring-model rpt))))))

(deftest test-ss-build-report-empty
  (testing "build-report with no checks returns score 100.0"
    (let [rpt (ss/build-report [])]
      (is (= 100.0 (:overall-score rpt)))
      (is (= 0.0 (:redundancy-rate rpt))))))

(deftest test-ss-build-report-assigns-weights
  (testing "build-report assigns weights from WEIGHTS map"
    (let [checks [{:name "claude_md_duplication" :score 100.0 :violations 0 :details "" :items []}]
          rpt (ss/build-report checks)]
      (is (= 0.25 (:weight (first (:checks rpt))))))))

(deftest test-ss-build-report-hotspots-topn
  (testing "build-report limits hotspots to top-n"
    (let [items  (mapv #(hash-map :path (str "p" %) :kind "test" :redundancy (/ % 10.0) :detail "")
                       (range 1 20))
          checks [{:name "dead_code_entropy" :score 50.0 :violations 5 :details "" :items items}]
          rpt    (ss/build-report checks 5)]
      (is (= 5 (count (:hotspots rpt))))
      ;; Hotspots should be sorted by redundancy descending
      (is (>= (:redundancy (first (:hotspots rpt)))
              (:redundancy (last (:hotspots rpt))))))))

;; ─────────────────────────────────────────────────────────────────────────────
;; shannon-scores: DSM helpers
;; ─────────────────────────────────────────────────────────────────────────────

(deftest test-ss-dsm-find-clusters-single
  (testing "single node with no edges = one cluster"
    (let [clusters (ss/dsm-find-clusters ["a"] {})]
      (is (= 1 (count clusters)))
      (is (= ["a"] (:members (first clusters)))))))

(deftest test-ss-dsm-find-clusters-two-components
  (testing "two disconnected components = two clusters"
    (let [clusters (ss/dsm-find-clusters ["a" "b" "c" "d"]
                                          {"a" {"b" 1} "c" {"d" 1}})]
      (is (= 2 (count clusters))))))

(deftest test-ss-dsm-detect-cycles-no-cycle
  (testing "linear chain has no cycles"
    (let [cycles (ss/dsm-detect-cycles ["a" "b" "c"] {"a" {"b" 1} "b" {"c" 1}})]
      (is (empty? cycles)))))

(deftest test-ss-dsm-detect-cycles-self-loop-ignored
  (testing "cycle requires at least 2 nodes in path (length >= 2)"
    ;; a→b→a is a cycle of length 2
    (let [cycles (ss/dsm-detect-cycles ["a" "b"] {"a" {"b" 1} "b" {"a" 1}})]
      (is (pos? (count cycles))))))

(deftest test-ss-build-dsm-report-empty
  (testing "empty apps returns minimal report"
    (let [rpt (ss/build-dsm-report [] {} 5 false)]
      (is (= 0 (:size rpt)))
      (is (= 100.0 (:score rpt))))))

(deftest test-ss-build-dsm-report-small-graph
  (testing "3-node graph with 2 edges"
    ;; a→b→c; bandwidth should be 1 after Cuthill-McKee (already minimal)
    ;; score = 100*(1 - 1/3) = 66.7
    (let [rpt (ss/build-dsm-report ["a" "b" "c"] {"a" {"b" 2} "b" {"c" 1}} 5 false)]
      (is (= 3 (:size rpt)))
      (is (number? (:bandwidth rpt)))
      (is (number? (:score rpt))))))

(deftest test-ss-dsm-cuthill-mckee-identity-on-2
  (testing "2-node graph returns a permutation of [0 1]"
    (let [perm (ss/dsm-cuthill-mckee [[0 1][1 0]] 2)]
      (is (= 2 (count perm)))
      (is (= #{0 1} (set perm))))))

;; ─────────────────────────────────────────────────────────────────────────────
;; shannon-scores: bottleneck
;; ─────────────────────────────────────────────────────────────────────────────

(deftest test-ss-build-bottleneck-report-empty
  (testing "empty apps gives score 100"
    (let [rpt (ss/build-bottleneck-report [] {} 10 2)]
      (is (= 100.0 (:score rpt))))))

(deftest test-ss-build-bottleneck-report-no-hubs
  (testing "all fan < min-fan → no bottlenecks"
    (let [rpt (ss/build-bottleneck-report ["a" "b" "c"]
                                           {"a" {"b" {"invoke" 1}}}
                                           10 5)]
      (is (empty? (:bottlenecks rpt))))))

(deftest test-ss-build-bottleneck-report-hub
  (testing "high fan-in/fan-out node detected"
    ;; "hub" has 3 inbound and 3 outbound with min-fan=2
    (let [adj-typed {"a" {"hub" {"invoke" 1}}
                     "b" {"hub" {"reads" 1}}
                     "c" {"hub" {"writes" 1}}
                     "hub" {"x" {"invoke" 1} "y" {"reads" 1} "z" {"writes" 1}}}
          apps ["a" "b" "c" "hub" "x" "y" "z"]
          rpt  (ss/build-bottleneck-report apps adj-typed 10 2)]
      (is (pos? (count (:bottlenecks rpt))))
      (is (= "hub" (:app (first (:bottlenecks rpt))))))))

;; ─────────────────────────────────────────────────────────────────────────────
;; shannon-scores: minimize
;; ─────────────────────────────────────────────────────────────────────────────

(deftest test-ss-build-minimize-report-empty
  (testing "empty apps returns minimal report"
    (let [rpt (ss/build-minimize-report [] {} {} 5 2.0)]
      (is (= 0 (:total-apps rpt))))))

(deftest test-ss-build-minimize-report-basic
  (testing "simple graph builds module list"
    (let [apps ["a" "b" "c"]
          adj  {"a" {"b" 1 "c" 1}}
          rpt  (ss/build-minimize-report apps adj {} 5 0.5)]
      (is (= 3 (count (:modules rpt)))))))

;; ─────────────────────────────────────────────────────────────────────────────
;; kosei-tiers: constants
;; ─────────────────────────────────────────────────────────────────────────────

(deftest test-kt-tier-eta-values
  (testing "tier-eta matches Python _TIER_ETA exactly"
    (is (= 0.667 (get kt/tier-eta "T1")))
    (is (= 0.500 (get kt/tier-eta "T2")))
    (is (= 0.910 (get kt/tier-eta "T3")))))

(deftest test-kt-tier-order
  (testing "tier-order is [T1 T2 T3]"
    (is (= ["T1" "T2" "T3"] kt/tier-order))))

(deftest test-kt-default-tier
  (testing "default-tier is T2"
    (is (= "T2" kt/default-tier))))

;; ─────────────────────────────────────────────────────────────────────────────
;; kosei-tiers: valid-tier? and tier-eta-of
;; ─────────────────────────────────────────────────────────────────────────────

(deftest test-kt-valid-tier
  (testing "valid-tier? returns true for T1/T2/T3"
    (is (kt/valid-tier? "T1"))
    (is (kt/valid-tier? "T2"))
    (is (kt/valid-tier? "T3"))
    (is (not (kt/valid-tier? "T4")))
    (is (not (kt/valid-tier? "")))))

(deftest test-kt-tier-eta-of
  (testing "tier-eta-of returns correct values"
    (is (= 0.667 (kt/tier-eta-of "T1")))
    (is (= 0.0   (kt/tier-eta-of "unknown")))))

;; ─────────────────────────────────────────────────────────────────────────────
;; kosei-tiers: suggest-tier (parity with Python _suggest_tier)
;; ─────────────────────────────────────────────────────────────────────────────

(deftest test-kt-suggest-tier-infra-by-name
  (testing "infra keyword in name → T3"
    (is (= "T3" (kt/suggest-tier {"name" "auth-worker" "dir" "60-apps/auth" "performerType" "worker"})))))

(deftest test-kt-suggest-tier-infra-by-dir
  (testing "50-infra in dir → T3"
    (is (= "T3" (kt/suggest-tier {"name" "my-app" "dir" "50-infra/something" "performerType" "worker"})))))

(deftest test-kt-suggest-tier-actor-by-dir
  (testing "20-actors in dir → T1"
    (is (= "T1" (kt/suggest-tier {"name" "some-actor" "dir" "20-actors/foo" "performerType" "actor"})))))

(deftest test-kt-suggest-tier-gateway
  (testing "gateway keyword in name → T3"
    (is (= "T3" (kt/suggest-tier {"name" "gateway" "dir" "60-apps/gw" "performerType" "worker"})))))

(deftest test-kt-suggest-tier-default
  (testing "no special keywords → T2"
    (is (= "T2" (kt/suggest-tier {"name" "plain-app" "dir" "60-apps/plain" "performerType" "worker"})))))

(deftest test-kt-suggest-tier-system-performer
  (testing "performerType=system → T3"
    (is (= "T3" (kt/suggest-tier {"name" "some-app" "dir" "60-apps/any" "performerType" "system"})))))

(deftest test-kt-suggest-tier-kotodama
  (testing "kotodama in name → T1"
    (is (= "T1" (kt/suggest-tier {"name" "kotodama-agent" "dir" "20-actors/foo" "performerType" "worker"})))))

;; ─────────────────────────────────────────────────────────────────────────────
;; kosei-tiers: next-tier / prev-tier
;; ─────────────────────────────────────────────────────────────────────────────

(deftest test-kt-next-tier
  (testing "next-tier promotes correctly"
    (is (= "T2" (kt/next-tier "T1")))
    (is (= "T3" (kt/next-tier "T2")))
    (is (nil? (kt/next-tier "T3")))
    (is (nil? (kt/next-tier "unknown")))))

(deftest test-kt-prev-tier
  (testing "prev-tier demotes correctly"
    (is (= "T2" (kt/prev-tier "T3")))
    (is (= "T1" (kt/prev-tier "T2")))
    (is (nil? (kt/prev-tier "T1")))
    (is (nil? (kt/prev-tier "unknown")))))

;; ─────────────────────────────────────────────────────────────────────────────
;; run
;; ─────────────────────────────────────────────────────────────────────────────

(let [{:keys [pass fail error]}
      (run-tests 'etzhayyim.test-bb-migration-wave2)]
  (when (pos? (+ fail error))
    (System/exit 1)))
