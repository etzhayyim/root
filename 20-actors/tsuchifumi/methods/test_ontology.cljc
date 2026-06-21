#!/usr/bin/env bb
;; tsuchifumi 土踏み — ontology ↔ seed parity + negative-space (unrepresentable) tests.
;; Run: bb --classpath 20-actors 20-actors/tsuchifumi/methods/test_ontology.cljc
(ns tsuchifumi.methods.test-ontology
  (:require [tsuchifumi.methods.tsuchifumi-edn :as te]
            [tsuchifumi.methods.analyze :as an]
            [tsuchifumi.methods.risk :as risk]
            [clojure.edn :as edn]
            [clojure.test :refer [deftest is run-tests]]))

(def onto (edn/read-string (slurp "20-actors/tsuchifumi/kotoba/ontology.tsuchifumi.edn")))
(def seed (te/load-seed "20-actors/tsuchifumi/kotoba/seed.edn"))

(deftest seed-kinds-declared
  (is (seq (:regions seed)))
  (is (seq (:evidence seed)))
  (is (seq (:drivers seed))))

(deftest region-kinds-in-enum
  (let [ok (get-in onto [:enums :region-kind])]
    (doseq [r (:regions seed)]
      (is (contains? ok (:kind r)) (str (:id r) " kind in enum")))))

(deftest evidence-tiers-valid
  (let [tiers (get-in onto [:enums :tier])]
    (doseq [e (:evidence seed)]
      (is (contains? tiers (:tier e)) (str (:id e) " tier in enum")))))

(deftest tier-weights-cover-all-tiers
  (let [tiers (get-in onto [:enums :tier])
        weights (:tier-weights onto)]
    (doseq [t tiers] (is (contains? weights t) (str t " has a confidence weight")))
    ;; the code's weight map must agree with the ontology's
    (is (= (:tier-weights onto) an/tier-weights) "analyze tier-weights ≡ ontology")))

;; ── negative space: unrepresentable attributes never appear in ANY datom ─────
(deftest unrepresentable-never-emitted
  (let [bad (set (:unrepresentable onto))
        an-ds (an/datoms (an/assess (:regions seed) (:evidence seed)))
        risk-ds (risk/datoms (risk/assess (:drivers seed)))
        attrs (set (map (fn [[_ _ a _]] a) (concat an-ds risk-ds)))]
    (doseq [b bad]
      (is (not (contains? attrs b)) (str b " is structurally unrepresentable")))))

(deftest verdict-enum-matches-code
  (let [onto-verdicts (get-in onto [:enums :verdict])
        code-verdicts (set (map :verdict (map an/verdict (:regions seed))))]
    (is (clojure.set/subset? code-verdicts onto-verdicts)
        "every verdict the gate can return is declared in the ontology enum")))

(let [{:keys [fail error]} (run-tests 'tsuchifumi.methods.test-ontology)]
  (when (pos? (+ fail error)) (System/exit 1)))
