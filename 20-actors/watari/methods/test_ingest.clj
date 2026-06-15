#!/usr/bin/env bb
;; Working Clojure port of methods/test_ingest.py.
(ns watari.methods.test-ingest
  "Tests for the watari 渡り offline AIS/ADS-B normalizer (methods/ingest.clj).

  Covers offline normalization (public-broadcast → :craft/:craft.fix records, all
  :representative) AND the G7 outward gate (live network fetch refused without operator gate).

  Run:  bb --classpath 20-actors 20-actors/watari/methods/test_ingest.clj"
  (:require [watari.methods.ingest :as ing]
            [cheshire.core :as json]
            [clojure.java.io :as io]
            [clojure.string :as str]
            [clojure.test :refer [deftest is run-tests]]))

(def ^:private this-file *file*)
(defn- batch []
  (json/parse-string
   (slurp (-> this-file io/file .getAbsoluteFile .getParentFile .getParentFile
              (io/file "data" "ingest" "sample-batch.json")))
   true))

(deftest normalize-emits-vessel-and-aircraft-craft
  (let [{:keys [craft fixes]} (ing/normalize (batch))
        kinds (set (map :craft/kind (vals craft)))]
    (is (contains? kinds :vessel))
    (is (contains? kinds :aircraft))
    (is (>= (count fixes) (count craft)))))      ; at least one fix per craft

(deftest normalized-records-are-representative
  (let [{:keys [craft fixes]} (ing/normalize (batch))]
    (is (every? #(= (:craft/sourcing %) :representative) (vals craft)))
    (is (every? #(= (:craft.fix/sourcing %) :representative) fixes))))

(deftest fix-carries-source-tag
  (let [{:keys [fixes]} (ing/normalize (batch))
        sources (set (map :craft.fix/source fixes))]
    (is (clojure.set/subset? sources #{:ais :adsb}))))   ; only public-broadcast sources

(deftest g4-no-person-fields-in-normalized-output
  (let [{:keys [craft fixes]} (ing/normalize (batch))]
    (doseq [rec (concat (vals craft) fixes)
            k (keys rec)]
      (is (not (str/includes? (str k) ":person")) "craft, never a person (G4)"))))

(deftest counts-match-sample
  (let [{:keys [craft fixes]} (ing/normalize (batch))]
    (is (= (count craft) 4))     ; 2 vessels + 2 aircraft
    (is (= (count fixes) 4))))

(deftest g7-live-fetch-refused-without-operator-gate
  (is (some? (ing/live-refusal ["--live"] nil)) "--live refused without the operator gate")
  (is (str/includes? (ing/live-refusal ["--live"] nil) "G7"))
  (is (str/includes? (ing/live-refusal ["--live"] "1") "not implemented")) ; gated → R0 scaffold
  (is (nil? (ing/live-refusal ["--batch" "x.json"] nil))))                 ; offline not refused

(when (= *file* (System/getProperty "babashka.file"))
  (require 'clojure.set)
  (let [{:keys [fail error]} (run-tests 'watari.methods.test-ingest)]
    (System/exit (if (zero? (+ fail error)) 0 1))))
