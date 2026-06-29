#!/usr/bin/env bb
;; junkan 循環 — demographic-dynamics read-off tests (incl. the analysis-only invariants).
;; Run:  bb --classpath 20-actors 20-actors/junkan/methods/test_demography.cljc
(ns junkan.methods.test-demography
  (:require [junkan.methods.junkan-edn :as je]
            [junkan.methods.demography :as d]
            [clojure.edn :as edn]
            [clojure.set :as cset]
            [clojure.string :as str]
            [clojure.test :refer [deftest is run-tests]]))

(def seed-path "20-actors/junkan/kotoba/seed.china-one-child.edn")
(def onto-path "20-actors/junkan/kotoba/ontology.junkan-demography.edn")
(defn- is* [] (je/instruments seed-path))
(defn- enums [] (:enums (edn/read-string (slurp onto-path))))
(defn- a [] (d/analyze (is*)))

;; ── contribution sign correctness (suppress = collapse-ward +) ───────────────
(deftest contribution-sign
  (is (pos? (d/contribution {:polarity :suppress :magnitude 0.5 :confidence 1.0})) "suppress → positive (collapse-ward)")
  (is (neg? (d/contribution {:polarity :boost :magnitude 0.5 :confidence 1.0})) "boost → negative (replacement-ward)")
  (is (zero? (d/contribution {:polarity :ambiguous :magnitude 0.5 :confidence 1.0})) "ambiguous → 0"))

;; ── substrate integrity (the seed must validate clean) ───────────────────────
(deftest seed-validates-clean
  (let [{:keys [errors warnings]} (d/validate (is*) (enums))]
    (is (empty? errors) (str "validate errors: " (pr-str errors)))
    (is (empty? warnings) (str "validate warnings: " (pr-str warnings)))))

(deftest seed-has-both-polarities-and-all-stocks
  (let [levers (is*)
        pol (frequencies (map :polarity levers))
        stocks (set (map :stock levers))]
    (is (pos? (get pol :suppress 0)) "has suppressing levers")
    (is (pos? (get pol :boost 0)) "has boosting/corrective levers")
    (is (= (set d/stock-order) stocks) "every demographic stock has at least one lever")))

;; ── full analysis shape ──────────────────────────────────────────────────────
(deftest analysis-has-all-parts
  (let [r (a)]
    (is (map? (get r "stocks")))
    (is (= 5 (count (get r "stocks"))) "5 demographic stocks")
    (is (= 5 (count (get r "loops"))) "5 canonical loops (B1/R1/R2/R3/B2)")
    (is (vector? (get r "trajectory")))
    (is (true? (get r "hypothesis_only")))
    (is (false? (get r "actuation_taken")) "G4 — actuation never taken")))

;; ── system-dynamics read: the small-family-norm lock-in is vicious ───────────
(deftest norm-lockin-is-vicious
  (let [stocks (get (a) "stocks")
        loops (into {} (map (juxt :id identity) (get (a) "loops")))]
    (is (= :vicious (get-in stocks ["small-family-norm" :regime]))
        "the paradigm stock is collapse-ward (R2 lock-in core)")
    (is (= :vicious (:regime (get loops "R2-norm-lockin"))) "R2 norm-lockin reads vicious")
    (is (= :vicious (:regime (get loops "R3-421-squeeze"))) "R3 4-2-1 squeeze reads vicious")))

;; ── Meadows reading: the one-child mandate is the top FLIP (suppress) candidate ──
(deftest top-flip-is-one-child-mandate
  (let [flips (get-in (a) ["leverage" :flip])]
    (is (= "cn-one-child-1979" (:id (first flips)))
        "the one-child mandate is the highest-leverage suppressing lever")
    (is (every? #(= false (:prescription? %)) flips) "G11 — every candidate is prescription? false")))

;; ── G4/G5/G6 invariants on the emitted datoms ────────────────────────────────
(deftest datoms-carry-discipline
  (let [ds (d/datoms (is*) (a))
        attrs (set (map #(nth % 2) ds))]   ;; datom = [":db/add" e a v] → attr is index 2
    (is (pos? (count ds)) "datoms emitted")
    (is (contains? attrs ":junkan/hypothesis") "G5 — hypothesis flag present")
    (is (contains? attrs ":junkan/derived") "derived flag present")
    ;; G4 — no actuation/dispatch attribute is ever emitted
    (is (not (some #(str/includes? (str %) "actuate") attrs)) "G4 — no :actuate attr")
    (is (not (some #(str/includes? (str %) "dispatch") attrs)) "G4 — no :dispatch attr")
    ;; G6 — no person/PII attribute
    (is (not (some #(str/includes? (str %) "person") attrs)) "G6 — no :person attr")))

;; ── ontology negative space is honored (unrepresentables never appear) ───────
(deftest negative-space-absent
  (let [onto (edn/read-string (slurp onto-path))
        unrep (set (:unrepresentable onto))
        attrs (set (map #(nth % 2) (d/datoms (is*) (a))))]
    (is (empty? (cset/intersection unrep attrs))
        "no unrepresentable attribute is ever emitted")))

(defn -main [& _]
  (let [r (run-tests 'junkan.methods.test-demography)]
    (when (= *file* (System/getProperty "babashka.file"))
      (System/exit (if (zero? (+ (:fail r) (:error r))) 0 1)))))

#?(:clj (when (= *file* (System/getProperty "babashka.file")) (-main)))
