#!/usr/bin/env bb
;; Working Clojure port of methods/test_labor_liberation.py.
(ns sanae.methods.test-labor-liberation
  "Tests for the LPS ranking method (ADR-2606032100).

  Run:  bb --classpath 20-actors 20-actors/sanae/methods/test_labor_liberation.clj"
  (:require [sanae.methods.labor-liberation :as ll]
            [clojure.string :as str]
            [clojure.test :refer [deftest is run-tests]]))

(defn- by-name [frag] (first (filter #(str/includes? (:name %) frag) ll/seed-gaps)))

(deftest n1-excluded-sector-scores-zero
  (is (= 0.0 (ll/lps (by-name "MINING")))))   ; charter-fit=0 zeroes the score (N1 gate proof)

(deftest covered-sector-scores-below-uncovered-peer
  ;; construction (coverage-gap 0.5, tatekata exists) vs garment (coverage-gap 1.0)
  (is (> (ll/lps (by-name "hataori")) (ll/lps (by-name "tatekata")))))

(deftest sanae-ranks-first
  (is (str/includes? (first (first (ll/ranked-seed))) "sanae")))

(deftest wave-actors-in-top-band
  (let [top5 (set (map first (take 5 (ll/ranked-seed))))]
    (is (some #(str/includes? % "sanae") top5))
    (is (some #(str/includes? % "hataori") top5))
    (is (some #(str/includes? % "kiyome") top5))))

(deftest freed-hours-scales-linearly
  (is (= 1000000.0 (ll/freed-labor-hours 1000 2000 0.5))))

(deftest cohort-size-rounds
  (is (= 250000 (ll/displacement-cohort-size 1.0e6 0.25))))

(deftest higher-misery-raises-score-all-else-equal
  (let [base  (ll/sector-gap "x" "" "" "" 1e7 2.0 0.5 1.0 1.0)
        worse (ll/sector-gap "y" "" "" "" 1e7 3.0 0.5 1.0 1.0)]
    (is (> (ll/lps worse) (ll/lps base)))))

(deftest fishing-sector-present
  ;; cross-link to umisachi 海幸 — the marine-bounty actor that bodies this fishing gap
  (is (some? (by-name "ama (fishing")))
  (is (pos? (ll/lps (by-name "ama (fishing")))))

(when (= *file* (System/getProperty "babashka.file"))
  (let [{:keys [fail error]} (run-tests 'sanae.methods.test-labor-liberation)]
    (System/exit (if (zero? (+ fail error)) 0 1))))
