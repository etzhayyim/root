#!/usr/bin/env bb
;; kanmon 関門 — system-dynamics tests (causal loops + Meadows leverage; analysis-only).
(ns kanmon.methods.test-dynamics
  (:require [kanmon.methods.dynamics :as dyn]
            [kanmon.methods.analyze :as az]
            [kanmon.methods.kanmon-edn :as ke]
            [clojure.string :as str]
            [clojure.test :refer [deftest is run-tests]]))

(def seed-path "20-actors/kanmon/kotoba/seed.edn")
(defn- rows [] (get (az/assess (ke/exams seed-path)) "exams"))
(defn- analysis [] (dyn/analyze (rows)))

(deftest all-stocks-present-and-bounded
  (let [st (get (analysis) "stocks")]
    (is (= (set dyn/stocks) (set (keys st))) "all five 受験 stocks modelled")
    (doseq [[s {:keys [net regime]}] st]
      (is (<= -1.0 (double net) 1.0) (str s " net in [-1,1]"))
      (is (#{:vicious :virtuous :neutral :transitioning} regime)))))

(deftest system-is-pressure-dominated-honest-finding
  (let [hd (get (analysis) "headline")]
    (is (= :vicious (:system-regime hd)) "the mirrored 受験 system reads as vicious (honest)")
    (is (contains? (set dyn/stocks) (:dominant-stock hd)))
    (is (pos? (:vicious-loops hd)) "at least one reinforcing loop is vicious")))

(deftest six-loops-typed
  (let [lps (get (analysis) "loops")]
    (is (= 6 (count lps)))
    (is (= 3 (count (filter #(= :reinforcing (:type %)) lps))) "3 reinforcing")
    (is (= 3 (count (filter #(= :balancing (:type %)) lps))) "3 balancing")))

(deftest leverage-deepest-is-destake-and-never-a-prescription
  (let [lev (get (analysis) "leverage")]
    (is (seq lev))
    (is (= lev (sort-by (comp - :score) lev)) "ranked by score desc")
    (is (= :destake (:route (first lev))) "deepest leverage = :destake (Meadows goal level)")
    (is (= 3 (:meadows (first lev))) ":destake sits at Meadows level 3 (goals)")
    (is (every? #(false? (:prescription? %)) lev) "leverage points are hypotheses, NEVER directives")
    (is (not-any? #(= :monitor (:route %)) lev) ":monitor is not a leverage candidate")))

(deftest analysis-only-no-actuation
  (let [a (analysis)
        ds (dyn/datoms a)
        attrs (map (fn [[_ _ at _]] at) ds)]
    (is (false? (get a "actuation-taken")) "no actuation is ever taken")
    (doseq [forbidden [":kanmon/actuate" ":kanmon/dispatch" ":kanmon.dyn.lev/prescription-true"]]
      (is (not-any? #(str/includes? % forbidden) attrs) (str forbidden " absent")))
    ;; the prescription datom is emitted but ALWAYS false
    (is (every? (fn [[_ _ at v]] (or (not= at ":kanmon.dyn.lev/prescription") (false? v))) ds)
        "every leverage datom marks prescription false")))

(deftest datoms-carry-derived
  (let [ds (dyn/datoms (analysis))]
    (is (some (fn [[_ _ a _]] (= a ":kanmon.dyn.stock/net")) ds))
    (is (some (fn [[_ _ a _]] (= a ":kanmon.dyn.loop/regime")) ds))
    (is (some (fn [[_ _ a _]] (= a ":kanmon.dyn.lev/meadows")) ds))
    (is (some (fn [[_ _ a v]] (and (= a ":kanmon/derived") (true? v))) ds))))

(when (= *file* (System/getProperty "babashka.file"))
  (let [{:keys [fail error]} (run-tests 'kanmon.methods.test-dynamics)]
    (when (pos? (+ fail error)) (System/exit 1))))
