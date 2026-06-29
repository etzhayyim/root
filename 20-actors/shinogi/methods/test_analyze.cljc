#!/usr/bin/env bb
;; shinogi 鎬 — analysis read-off tests (incl. analysis-only invariants).
(ns shinogi.methods.test-analyze
  (:require [shinogi.methods.shinogi-edn :as se]
            [shinogi.methods.analyze :as az]
            [clojure.string :as str]
            [clojure.test :refer [deftest is run-tests]]))

(def seed-path "20-actors/shinogi/kotoba/seed.exam-involution.edn")
(defn- ds* [] (se/drivers seed-path))
(defn- a [] (az/analyze (ds*)))

;; ── contribution sign correctness ────────────────────────────────────────────
(deftest contribution-sign
  (is (pos? (az/contribution {:polarity :intensify :magnitude 0.5 :confidence 1.0})) "intensify → positive")
  (is (neg? (az/contribution {:polarity :relieve :magnitude 0.5 :confidence 1.0})) "relieve → negative")
  (is (zero? (az/contribution {:polarity :ambiguous :magnitude 0.5 :confidence 1.0})) "ambiguous → 0"))

;; ── regime read-off ──────────────────────────────────────────────────────────
(deftest regime-thresholds
  (is (= :vicious (az/regime-of 0.4 0.4 0.0)))
  (is (= :virtuous (az/regime-of -0.4 0.0 0.4)))
  (is (= :neutral (az/regime-of 0.0 0.05 0.05)))
  (is (= :transitioning (az/regime-of 0.0 0.5 0.5)) "strong intensify+relieve, near-zero net → contested"))

;; ── full analysis shape ──────────────────────────────────────────────────────
(deftest analysis-has-all-parts
  (let [r (a)]
    (is (map? (get r "stocks")))
    (is (= 6 (count (get r "stocks"))) "all six pressure stocks present")
    (is (= 6 (count (get r "loops"))) "six canonical loops")
    (is (map? (get r "failure_cycle")) "the failure-cycle read-off is present")
    (is (contains? (get r "leverage") :amplify))
    (is (contains? (get r "leverage") :flip))
    (is (map? (get r "coverage")))))

;; ── the involution core spins vicious on the seed (the headline finding) ─────
(deftest involution-core-is-vicious
  (let [stocks (get (a) "stocks")]
    (is (= "vicious" (name (:regime (get stocks "effort-inflation"))))
        "effort-inflation (内卷 core) reads vicious on the seed")
    (is (= "vicious" (name (:regime (get stocks "positional-scarcity"))))
        "positional-scarcity reads vicious on the seed")))

;; ── the failure cycle read-off is sober + routed to relief (G7) ──────────────
(deftest failure-cycle-routes-to-relief
  (let [fc (get (a) "failure_cycle")]
    (is (= "R-failure-despair" (:loop fc)))
    (is (true? (:hypothesis? fc)) "failure cycle is a hypothesis (G5)")
    (is (= ["kokoro" "shiori"] (:route-to fc)) "routed to relief, never amplified (G7)")
    (is (number? (:relief-gap fc)))))

;; ── loops grounded in member-stock edges (not dominant alone) ────────────────
(deftest loops-grounded-in-member-stocks
  (let [loops (get (a) "loops")
        involution (first (filter #(= "R-involution-arms-race" (:id %)) loops))]
    (is (= [:positional-scarcity :effort-inflation] (:member-stocks involution))
        "involution loop joins scarcity + effort, not one stock")
    (is (every? #(contains? % :drive) loops) "every loop has a joint drive")))

;; ── leverage candidates are candidates, never directives (G11) ───────────────
(deftest leverage-no-prescription
  (let [lev (get (a) "leverage")]
    (is (false? (:prescription? lev)) "leverage block prescription? false (G11)")
    (is (every? #(false? (:prescription? %)) (:amplify lev)) "amplify candidates carry prescription? false")
    (is (every? #(false? (:prescription? %)) (:flip lev)) "flip candidates carry prescription? false")
    (is (seq (:amplify lev)) "relieving (amplify) candidates exist")
    (is (seq (:flip lev)) "intensifying (flip) candidates exist")))

;; ── analyze advertises analysis-only + hypothesis-only ───────────────────────
(deftest analysis-only-flags
  (let [r (a)]
    (is (= false (get r "actuation_taken")) "actuation_taken false (G4)")
    (is (= true (get r "hypothesis_only")) "hypothesis_only true (G5)")))

;; ── G4/G6/G8 — datoms NEVER emit a forbidden attribute (negative space) ──────
(deftest datoms-have-no-forbidden-attrs
  (let [drivers (ds*)
        ds (az/datoms drivers (az/analyze drivers))
        attrs (set (map #(nth % 2) ds))
        forbidden #"(?i)actuate|dispatch|/person|student/score|student/ranking|proven-cause|prescription"]
    (is (seq ds) "datoms are emitted")
    (is (every? #(= ":db/add" (first %)) ds) "every datom is an append (:db/add only, G9)")
    (is (not-any? #(re-find forbidden %) attrs)
        (str "G4/G6/G8: no forbidden attribute may be emitted; found "
             (filter #(re-find forbidden %) attrs)))
    (is (every? #(re-find #"(?i)enactor|origin|stock|name|jurisdiction|kind|year|contribution|meadows|basis|net|force|regime|drive|count|type|pressure|relief|sourcing|hypothesis|derived"
                          %) attrs)
        "every emitted attribute is an expected aggregate/structural one")))

;; ── G6 — datoms carry no private-individual / per-student data ────────────────
(deftest datoms-aggregate-only
  (let [drivers (ds*)
        ds (az/datoms drivers (az/analyze drivers))
        ;; enactor values are institutional strings; assert no value looks like a bare personal name field
        person-attrs (filter #(re-find #"(?i)person|student" (nth % 2)) ds)]
    (is (empty? person-attrs) "G6: no :*/person or :*/student datom is emitted")))

;; ── report renders sober + names the relief routing (G7) ─────────────────────
(deftest report-is-sober-and-relief-routed
  (let [rep (az/render-report (a))]
    (is (str/includes? rep "受験失敗の system cycle") "the failure cycle is foregrounded")
    (is (str/includes? rep "kokoro") "report routes failure to kokoro (relief)")
    (is (str/includes? rep "ranking ではない") "report disclaims being a ranking (G8)")
    (is (str/includes? rep "actuation_taken=false") "report advertises analysis-only (G4)")))

#?(:clj
   (defn -main [& _]
     (let [r (run-tests 'shinogi.methods.test-analyze)]
       (System/exit (if (zero? (+ (:fail r) (:error r))) 0 1)))))
