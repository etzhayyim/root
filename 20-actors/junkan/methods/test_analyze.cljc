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

;; ── loops grounded in member-stock edges (not dominant alone) ────────────────
(deftest loops-grounded-in-member-stocks
  (let [r (a)
        loops (get r "loops")
        secrecy (first (filter #(= "R-secrecy-spiral" (:id %)) loops))
        stocks (get r "stocks")]
    (is (= [:information-asymmetry :economic-capture] (:member-stocks secrecy))
        "secrecy-spiral couples information + economic stocks")
    (is (contains? secrecy :drive) "loop carries a joint drive")
    ;; drive = mean of the member stocks' net pressures (HYPOTHESIS read-off)
    (let [info (get stocks "information-asymmetry")
          econ (get stocks "economic-capture")
          expect (/ (Math/round (* (/ (+ (:net info) (:net econ)) 2.0) 1000.0)) 1000.0)]
      (is (= expect (:drive secrecy)) "drive is the mean net of member stocks"))))

(deftest loop-drive-fn
  (let [stocks {:a {:net 0.4 :widen-force 1.0 :narrow-force 0.2}
                :b {:net -0.2 :widen-force 0.3 :narrow-force 0.9}}
        d (az/loop-drive stocks [:a :b])]
    (is (= 0.1 (:drive d)) "mean of 0.4 and -0.2")
    (is (= 1.3 (:widen-force d)))
    (is (= 1.1 (:narrow-force d)))))

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

;; ── temporal era trajectory (structural over time; not a ranking) ────────────
(deftest era-bucketing
  (is (nil? (az/era-of 0)) "undated → nil")
  (is (= "pre-1800" (az/era-of 1215)))
  (is (= "pre-1800" (az/era-of 1766)) "1766 is pre-1800")
  (is (= "1800–1899" (az/era-of 1863)))
  (is (= "1900–1944" (az/era-of 1917)))
  (is (= "1945–1989" (az/era-of 1966)))
  (is (= "1990–2009" (az/era-of 2005)))
  (is (= "2010–" (az/era-of 2020))))

(deftest era-trajectory-shape
  (let [t (get (a) "trajectory")]
    (is (seq t) "trajectory has dated eras")
    (is (every? :hypothesis? t) "each era reading is a hypothesis (G5)")
    (is (every? #(contains? % :net) t))
    ;; eras are in chronological order
    (let [idx (zipmap az/era-order (range))]
      (is (apply <= (map #(get idx (:era %)) t)) "eras chronological"))
    ;; undated GLOBAL values are excluded from the trajectory
    (let [dated-count (reduce + (map :count t))
          total (count (is*))]
      (is (< dated-count total) "undated transnational values excluded from era fold"))))

(deftest era-datoms-emitted
  (let [r (a)
        ds (az/datoms (is*) r)
        attrs (set (map #(nth % 2) ds))]
    (is (contains? attrs ":junkan.gov.era/net") "era net datom emitted")
    (is (contains? attrs ":junkan.gov.era/widen-force"))))

;; ── report renders sober markdown ────────────────────────────────────────────
(deftest report-renders
  (let [md (az/render-report (a))]
    (is (str/includes? md "system-dynamics"))
    (is (str/includes? md "分析専用"))
    (is (str/includes? md "仮説")) ; hypothesis framing present (G5/G7)
    (is (str/includes? md "Era trajectory"))
    (is (str/includes? md "leverage CANDIDATES"))))

#?(:clj
   (defn -main [& _]
     (let [r (run-tests 'junkan.methods.test-analyze)]
       (System/exit (if (zero? (+ (:fail r) (:error r))) 0 1)))))

#?(:clj
   (when (= *file* (System/getProperty "babashka.file"))
     (-main)))
