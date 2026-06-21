#!/usr/bin/env bb
;; junkan 循環 — analysis read-off tests (incl. the analysis-only invariants).
;; Run:  bb --classpath 20-actors 20-actors/junkan/methods/test_analyze.cljc
(ns junkan.methods.test-analyze
  (:require [junkan.methods.junkan-edn :as je]
            [junkan.methods.analyze :as az]
            [clojure.string :as str]
            [clojure.test :refer [deftest is run-tests]]))

(def seed-path "20-actors/junkan/kotoba/seed.governance-asymmetry.edn")
(defn- is* [] (je/instruments seed-path))
(defn- a [] (az/analyze (is*)))

;; ── contribution sign correctness ────────────────────────────────────────────
(deftest contribution-sign
  (is (pos? (az/contribution {:polarity :widen :magnitude 0.5 :confidence 1.0})) "widen → positive")
  (is (neg? (az/contribution {:polarity :narrow :magnitude 0.5 :confidence 1.0})) "narrow → negative")
  (is (zero? (az/contribution {:polarity :ambiguous :magnitude 0.5 :confidence 1.0})) "ambiguous → 0"))

;; ── regime read-off ──────────────────────────────────────────────────────────
(deftest regime-thresholds
  (is (= :vicious (az/regime-of 0.4 0.4 0.0)))
  (is (= :virtuous (az/regime-of -0.4 0.0 0.4)))
  (is (= :neutral (az/regime-of 0.0 0.05 0.05)))
  (is (= :transitioning (az/regime-of 0.0 0.5 0.5)) "strong widen+narrow, near-zero net → contested"))

;; ── full analysis shape ──────────────────────────────────────────────────────
(deftest analysis-has-all-parts
  (let [r (a)]
    (is (map? (get r "stocks")))
    (is (= 5 (count (get r "stocks"))) "all five stocks present")
    (is (= 5 (count (get r "loops"))) "five canonical loops")
    (is (contains? (get r "leverage") :amplify))
    (is (contains? (get r "leverage") :flip))
    (is (map? (get r "coverage")))))

;; ── G5 — everything is a HYPOTHESIS, never proven causation ──────────────────
(deftest g5-hypothesis-only
  (let [r (a)]
    (is (= true (get r "hypothesis_only")) "analysis flagged hypothesis_only")
    (doseq [[_ sp] (get r "stocks")]
      (is (= true (:hypothesis? sp)) "each stock regime is hypothesis"))
    (doseq [lp (get r "loops")]
      (is (= true (:hypothesis? lp)) "each loop regime is hypothesis"))))

;; ── G4 — analysis-only, no actuation; no outward symbol in this ns ───────────
(deftest g4-analysis-only
  (is (= false (get (a) "actuation_taken")) "actuation_taken false")
  ;; structural: the analyze source carries no dispatch/post/email/tx verb
  (let [src (slurp "20-actors/junkan/methods/analyze.cljc")
        forbidden #"(?im)\((?:post|dispatch|send-mail|smtp|http-post|transact!|broadcast)\b"]
    (is (nil? (re-find forbidden src)) "analyze.cljc has no outward-channel call (G4 by absence)")))

;; ── G11 — leverage points are candidates, never directives ───────────────────
(deftest g11-no-prescription
  (let [lev (get (a) "leverage")]
    (is (= false (:prescription? lev)) "leverage bundle prescription? false")
    (doseq [c (concat (:amplify lev) (:flip lev))]
      (is (= false (:prescription? c)) "each candidate prescription? false"))))

;; ── datom emission: flagged + person-free ────────────────────────────────────
(deftest datoms-flagged-and-person-free
  (let [r (a)
        ds (az/datoms (is*) r)
        attrs (set (map #(nth % 2) ds))]
    (is (pos? (count ds)))
    (is (contains? attrs ":junkan/derived") "datoms carry :junkan/derived")
    (is (contains? attrs ":junkan/hypothesis") "datoms carry :junkan/hypothesis (G5)")
    (is (contains? attrs ":junkan.gov.instr/enactor") "instrument enactor emitted (誰が)")
    (is (contains? attrs ":junkan.gov.instr/origin") "instrument origin emitted (経緯)")
    ;; G4/G6: no actuate/dispatch/person attribute ever emitted
    (doseq [bad [":junkan/actuate" ":junkan/dispatch" ":junkan.gov.instr/person"]]
      (is (not (contains? attrs bad)) (str bad " never emitted")))))

;; ── coverage worklist drives the /loop maturation ────────────────────────────
(deftest coverage-and-worklist
  (let [cov (get (a) "coverage")]
    (is (>= (:jurisdictions cov) 8))
    (is (vector? (:worklist cov)))
    (is (seq (:worklist cov)) "worklist is non-empty (next-iteration guidance)")))

;; ── report renders sober markdown ────────────────────────────────────────────
(deftest report-renders
  (let [md (az/render-report (a))]
    (is (str/includes? md "system-dynamics"))
    (is (str/includes? md "分析専用"))
    (is (str/includes? md "仮説")) ; hypothesis framing present (G5/G7)
    (is (str/includes? md "leverage CANDIDATES"))))

#?(:clj
   (defn -main [& _]
     (let [r (run-tests 'junkan.methods.test-analyze)]
       (System/exit (if (zero? (+ (:fail r) (:error r))) 0 1)))))

#?(:clj
   (when (= *file* (System/getProperty "babashka.file"))
     (-main)))
