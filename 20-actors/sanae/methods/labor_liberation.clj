#!/usr/bin/env bb
;; Working Clojure port of methods/labor_liberation.py.
(ns sanae.methods.labor-liberation
  "labor_liberation — empirical Liberation Priority Score (LPS) + freed-labour-hours.

  Per ADR-2606032100. Two computations:
    1. lps                    — the ranking score used to prioritize which toil to automate.
    2. freed-labor-hours      — labour-hours/year freed by automating a fraction of an
                                occupation's tasks (feeds the ADR-2606032130 dividend pool).

  Everything is order-of-magnitude and :representative (G8). The point is the SHAPE of the
  priority, not a sourced dataset; R2 replaces the seed with measured ISCO-occupation gap data.

  Run:  bb --classpath 20-actors 20-actors/sanae/methods/labor_liberation.clj"
  (:require [clojure.string :as str]))

;; A sector-gap is {:name :isic :isco :unspsc :headcount :misery :automatability
;;                  :charter-fit :coverage-gap}.
(defn sector-gap [name isic isco unspsc headcount misery automatability charter-fit coverage-gap]
  {:name name :isic isic :isco isco :unspsc unspsc :headcount (double headcount)
   :misery (double misery) :automatability (double automatability)
   :charter-fit (double charter-fit) :coverage-gap (double coverage-gap)})

(defn lps
  "Liberation Priority Score = log10(headcount) × misery × automatability × charter-fit ×
  coverage-gap. headcount is logged so a 0.8B sector does not swamp everything else by 10^4."
  [g]
  (* (Math/log10 (max (:headcount g) 1.0))
     (:misery g) (:automatability g) (:charter-fit g) (:coverage-gap g)))

(defn freed-labor-hours
  "Human labour-hours/year removed by automating `task-automation-fraction` of the work."
  [headcount hours-per-worker-yr task-automation-fraction]
  (* (double headcount) (double hours-per-worker-yr) (double task-automation-fraction)))

(defn displacement-cohort-size
  "Approx number of workers whose role is displaced (and thus owed the dividend)."
  [headcount task-automation-fraction]
  (long (Math/round (* (double headcount) (double task-automation-fraction)))))

;; :representative seed for the ADR-2606032100 ranking (order-of-magnitude).
(def seed-gaps
  [(sector-gap "sanae (field agriculture)" "A01" "6111/9211" "70" 7.0e8 2.6 0.55 1.0 0.85)
   (sector-gap "hataori (garment/apparel)" "C13-14" "7531/8219" "53" 6.5e7 2.9 0.45 1.0 1.0)
   (sector-gap "kiyome (domestic/cleaning)" "T/N81" "9111/9112" "76" 1.1e8 2.4 0.55 1.0 1.0)
   (sector-gap "kamado (food service)" "I56" "5120/9412" "90" 1.0e8 2.1 0.45 1.0 1.0)
   (sector-gap "kuramori (warehouse)" "H52" "9333/8219" "24" 4.0e7 2.2 0.70 1.0 0.9)
   (sector-gap "tatekata (construction)" "F" "7119/9313" "72" 2.6e8 2.6 0.45 1.0 0.5)
   (sector-gap "hofuri (meat processing)" "C10" "7511/9211" "23" 3.0e7 2.9 0.50 1.0 0.9)
   (sector-gap "soma (forestry)" "A02" "6210/9215" "70" 5.0e6 3.0 0.40 1.0 1.0)
   (sector-gap "ama (fishing/aquaculture)" "A03" "6222/9216" "70" 3.8e7 2.9 0.35 1.0 0.9)
   ;; excluded by N1 — charter-fit 0 → LPS 0, proving the gate zeroes it out
   (sector-gap "MINING (excluded N1)" "B" "8111/9311" "20" 2.5e7 3.0 0.6 0.0 1.0)])

(defn ranked-seed []
  (sort-by second > (map (fn [g] [(:name g) (lps g)]) seed-gaps)))

(defn main [& _]
  (println "Liberation Priority Score ranking (:representative seed):")
  (doseq [[i [name score]] (map-indexed vector (ranked-seed))]
    (println (format "  %2d. %-34s LPS=%5.2f" (inc i) name (double score))))
  (let [fh (freed-labor-hours 7.0e8 2000 0.3)]
    (println (format "\nsanae illustrative: automating 30%% of field-labour tasks frees %.1fB labour-hours/yr; cohort ≈ %.0fM workers."
                     (/ fh 1e9) (/ (displacement-cohort-size 7.0e8 0.3) 1e6)))))

(when (= *file* (System/getProperty "babashka.file"))
  (main))
