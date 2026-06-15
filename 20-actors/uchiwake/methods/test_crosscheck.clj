#!/usr/bin/env bb
;; Working Clojure test for methods/crosscheck.clj (no Python test existed; new coverage).
(ns uchiwake.methods.test-crosscheck
  "Tests for the uchiwake ⇄ kabuto supply-chain coverage-linkage crosscheck (methods/crosscheck.clj).

  Guards the MEASURED cross-actor supply-chain integration (linkage % into kabuto's company
  universe + reverse product-BOM coverage + the ingest worklist) and pins it to the values
  crosscheck.py reports — so the two actors' coverage figure cannot silently drift.

  Run:  bb --classpath 20-actors 20-actors/uchiwake/methods/test_crosscheck.clj"
  (:require [uchiwake.methods.crosscheck :as x]
            [clojure.set]
            [clojure.test :refer [deftest is run-tests]]))

(def ^:private s (delay (x/crosscheck)))

(deftest kabuto-seed-resolves
  (is (:kabuto-available @s))
  (is (= (:kabuto-company-count @s) 1719)))

(deftest linkage-matches-py
  ;; parity with crosscheck.py: 26 distinct refs, 21 resolved → 80.8% linkage
  (is (= (:distinct-company-refs @s) 26))
  (is (= (:distinct-resolved @s) 21))
  (is (= (:linkage-pct @s) 80.8)))

(deftest linkage-bounds
  (is (<= 0.0 (:linkage-pct @s) 100.0))
  (is (<= (:distinct-resolved @s) (:distinct-company-refs @s)))
  (doseq [[_ v] (:by-kind @s)]
    (is (<= (:resolved v) (:total v)))))   ; per-kind resolved never exceeds total

(deftest reverse-coverage-matches-py
  (let [rev (:reverse @s)]
    (is (some? rev))
    (is (= (:reverse-pct rev) 6.438))           ; % of kabuto supply companies w/ product detail
    (is (= (:all-company-coverage-pct rev) 1.163))
    (is (<= (:with-product-detail rev) (:kabuto-supply-companies rev)))))

(deftest worklist-is-sorted-and-uncovered
  (let [wl (get-in @s [:reverse :worklist])]
    (is (= (count wl) 15))                       ; top-15 ingest worklist
    (is (= (map :supply-out-degree wl) (sort > (map :supply-out-degree wl))))  ; centrality desc
    (is (every? :company wl))))

(when (= *file* (System/getProperty "babashka.file"))
  (let [{:keys [fail error]} (run-tests 'uchiwake.methods.test-crosscheck)]
    (System/exit (if (zero? (+ fail error)) 0 1))))
