#!/usr/bin/env bb
;; Working Clojure port of methods/test_ingest.py.
(ns mitooshi.methods.test-ingest
  "Tests for the mitooshi 見通し offline public-series normalizer (methods/ingest.clj).

  Covers offline normalization (G4 source-class membrane, G11 :representative honesty,
  append-only sorted observations) AND the G10 outward gate (live fetch refused without
  MITOOSHI_OPERATOR_GATE=1).

  Run:  bb --classpath 20-actors 20-actors/mitooshi/methods/test_ingest.clj"
  (:require [mitooshi.methods.ingest :as ing]
            [cheshire.core :as json]
            [clojure.java.io :as io]
            [clojure.string :as str]
            [clojure.test :refer [deftest is run-tests]]))

(def ^:private this-file *file*)
(defn- batch []
  (json/parse-string
   (slurp (-> this-file io/file .getAbsoluteFile .getParentFile .getParentFile
              (io/file "data" "ingest" "sample-batch.json")))))

(deftest sample-batch-normalizes-two-public-series
  (let [n (ing/normalize (batch))]
    (is (= (set (keys (get n "series"))) #{"s-hormuz-transit" "s-port-congestion"}))))

(deftest proprietary-terminal-series-is-refused
  (let [n (ing/normalize (batch))]
    (is (= (count (get n "refused")) 1))
    (let [r (first (get n "refused"))]
      (is (= (get r "id") "s-blocked-terminal"))
      (is (str/includes? (get r "reason") "G4")))))

(deftest observations-are-sorted-append-only
  (let [n      (ing/normalize (batch))
        hormuz (filter #(= (get % ":obs/series") "s-hormuz-transit") (get n "obs"))
        ats    (map #(get % ":obs/observed-at") hormuz)]
    ;; 非終末論: append-only, latest = current
    (is (= ats (sort ats)))
    (is (= (last ats) 3))
    (is (= (get (last hormuz) ":obs/value") 2.7))))

(deftest categorical-class-preserved
  (let [n    (ing/normalize (batch))
        cong (filter #(= (get % ":obs/series") "s-port-congestion") (get n "obs"))]
    (is (some #(= (get % ":obs/class") "up") cong))))

(deftest source-class-normalized-to-keyword
  (let [n (ing/normalize (batch))]
    (is (= (get-in n ["series" "s-hormuz-transit" ":series/source-class"]) ":public-broadcast"))
    (is (= (get-in n ["series" "s-hormuz-transit" ":series/sourcing"]) ":representative"))))

;; G10 live-gate tests — mirror the watari pattern: pass env-gate as an explicit arg to
;; live-refusal (System/getenv is side-effecting; the impl exposes live-refusal as a pure fn
;; so tests can exercise both gate states without mutating process env).
(deftest live-flag-refused-without-operator-gate
  (is (some? (ing/live-refusal ["--live"] nil))
      "--live refused without the operator gate")
  (is (str/includes? (ing/live-refusal ["--live"] nil) "G10"))
  (is (str/includes? (ing/live-refusal ["--live"] nil) "Council+operator gated")))

(deftest live-flag-gated-still-design-only-when-attested
  ;; attested (gate="1") but R0 → exits with design-only message, NOT a live fetch
  (is (some? (ing/live-refusal ["--live"] "1")))
  (is (str/includes? (ing/live-refusal ["--live"] "1") "not implemented (design-only)")))

(when (= *file* (System/getProperty "babashka.file"))
  (let [{:keys [fail error]} (run-tests 'mitooshi.methods.test-ingest)]
    (System/exit (if (zero? (+ fail error)) 0 1))))
