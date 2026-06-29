#!/usr/bin/env bb
;; kanmon 関門 — seed loader tests.
(ns kanmon.methods.test-kanmon-edn
  (:require [kanmon.methods.kanmon-edn :as ke]
            [clojure.test :refer [deftest is run-tests]]))

(def seed-path "20-actors/kanmon/kotoba/seed.edn")

(deftest loads-and-classifies
  (let [exams (ke/exams seed-path)]
    (is (vector? exams))
    (is (>= (count exams) 12) "seed has the full CN/KR/JP exam set")
    (is (every? #(= :exam (:type %)) exams))))

(deftest all-three-countries-present
  (let [cs (set (map :country (ke/exams seed-path)))]
    (is (contains? cs :cn) "China covered")
    (is (contains? cs :kr) "Korea covered")
    (is (contains? cs :jp) "Japan covered")))

(deftest factors-in-unit-range
  (doseq [e (ke/exams seed-path)
          k [:selectivity :single-shot :stakes :alt-pathways :transparency :equity]]
    (is (<= 0.0 (double (k e)) 1.0) (str (:id e) " " k " in 0..1"))))

(deftest no-person-attributes-in-seed
  (doseq [e (ke/exams seed-path)]
    (is (nil? (:student e)) "no per-student data (G2)")
    (is (nil? (:person e)) "no person data (G2)")
    (is (nil? (:rank e)) "no ranking field (N3)")))

(when (= *file* (System/getProperty "babashka.file"))
  (let [{:keys [fail error]} (run-tests 'kanmon.methods.test-kanmon-edn)]
    (when (pos? (+ fail error)) (System/exit 1))))
