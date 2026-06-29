#!/usr/bin/env bb
;; shinan 指南 — seed loader + open-license guard tests.
(ns shinan.methods.test-shinan-edn
  (:require [shinan.methods.shinan-edn :as se]
            [clojure.test :refer [deftest is run-tests]]))

(def seed-path "20-actors/shinan/kotoba/seed.edn")

(deftest loads-topics-and-resources
  (let [ts (se/topics seed-path)
        rs (se/resources seed-path)]
    (is (>= (count ts) 11) "full CN/KR/JP topic set")
    (is (>= (count rs) 11) "open resource set")
    (is (every? #(= :topic (:type %)) ts))
    (is (every? #(= :resource (:type %)) rs))))

(deftest all-three-countries-present
  (let [cs (set (map :country (se/topics seed-path)))]
    (is (= #{:cn :kr :jp} cs) "China, Korea, Japan all covered")))

(deftest every-seed-resource-is-open-licensed
  (is (every? #(se/open-license? (:license %)) (se/resources seed-path))
      "the commons holds only openly-licensed material"))

(deftest non-open-license-is-refused
  ;; 学習解放: a proprietary/paid resource is structurally inadmissible.
  (is (thrown? clojure.lang.ExceptionInfo
               (se/validate-open! [{:id "r-paid" :license :proprietary}]))
      "proprietary cram material is refused on load")
  (is (thrown? clojure.lang.ExceptionInfo
               (se/validate-open! [{:id "r-sub" :license :subscription}]))
      "subscription material is refused on load"))

(deftest no-learner-or-score-fields-in-seed
  (doseq [n (concat (se/topics seed-path) (se/resources seed-path))]
    (is (nil? (:learner n)) "no learner field (学習解放)")
    (is (nil? (:score n)) "no score field")
    (is (nil? (:rank n)) "no rank field")
    (is (nil? (:grade n)) "no grade field")))

(when (= *file* (System/getProperty "babashka.file"))
  (let [{:keys [fail error]} (run-tests 'shinan.methods.test-shinan-edn)]
    (when (pos? (+ fail error)) (System/exit 1))))
