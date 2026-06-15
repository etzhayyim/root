#!/usr/bin/env bb
;; Working Clojure port of methods/test_analyze.py.
(ns kabuto.methods.test-analyze
  "Tests for the kabuto 兜 supply-chain concentration analyzer (methods/analyze.clj).

  Covers the concentration roll-ups (single-source, per-commodity HHI, jurisdiction load,
  diversification, intermediaries) + their mathematical bounds, plus the load-bearing charter
  invariant: a resilience/accountability map, NEVER a target-list (G2).

  Run:  bb --classpath 20-actors 20-actors/kabuto/methods/test_analyze.clj"
  (:require [kabuto.methods.kabuto-edn :as e]
            [kabuto.methods.analyze :as ka]
            [clojure.java.io :as io]
            [clojure.string :as str]
            [clojure.test :refer [deftest is run-tests]]))

(def ^:private this-file *file*)
(defn- seed []
  (-> this-file io/file .getAbsoluteFile .getParentFile .getParentFile
      (io/file "data" "seed-public-companies.kotoba.edn")))
(defn- g [] (e/classify (e/load-edn (seed))))
(defn- a [] (let [gr (g)] (ka/analyze (:companies gr) (:edges gr))))

(deftest classify-buckets-the-seed
  (let [{:keys [companies edges]} (g)]
    (is (>= (count companies) 100))   ; a substantial public-company seed
    (is (>= (count edges) 50))))      ; disclosed supply edges present

(deftest single-source-findings-are-high-criticality
  (doseq [[_ _ _ crit] (:single-source (a))]
    (is (>= crit 0.7))))

(deftest commodity-hhi-is-bounded-zero-to-one
  (let [res (a)]
    (is (seq (:commodity-hhi res)) "expected per-commodity HHI rows")
    (doseq [[_ n-sup hhi] (:commodity-hhi res)]
      (is (and (< 0.0 hhi) (<= hhi 1.0)))
      (when (= n-sup 1) (is (= hhi 1.0))))))   ; a single disclosed supplier ⇒ HHI 1.0

(deftest jurisdiction-load-is-non-negative
  (let [res (a)]
    (is (seq (:jurisdiction-load res)))
    (is (every? #(>= % 0) (vals (:jurisdiction-load res))))))

(deftest diversification-sorted-brittle-first
  (let [idxs (map #(nth % 3) (:diversification (a)))]
    (is (= idxs (sort idxs)))))        ; lowest (most brittle) diversification index first

(deftest intermediaries-score-is-in-times-out
  (doseq [[_ ind outd score] (:intermediaries (a))]
    (is (= score (* ind outd)))))      ; betweenness proxy = in-degree × out-degree

(deftest render-datoms-marked-derived
  (let [{:keys [companies edges]} (g)
        edn (ka/render-datoms companies (ka/analyze companies edges))]
    (is (str/includes? edn "derived"))))   ; never re-ingested as authoritative

(deftest g2-report-is-not-a-target-list
  (let [gr (g)
        md (ka/render-report gr (ka/analyze (:companies gr) (:edges gr)))]
    (is (str/includes? md "target-list"))))   ; framing invariant stated in the report

(when (= *file* (System/getProperty "babashka.file"))
  (let [{:keys [fail error]} (run-tests 'kabuto.methods.test-analyze)]
    (System/exit (if (zero? (+ fail error)) 0 1))))
