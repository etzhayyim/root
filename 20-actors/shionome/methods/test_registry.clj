#!/usr/bin/env bb
;; Clojure port of test_registry.py — 潮目 (shionome) registry access + sourcing honesty.
;; ADR-2606072200.
(ns shionome.methods.test-registry
  (:require [clojure.test :refer [deftest is run-tests testing]]
            [shionome.methods.registry :as registry]))

;; ── tests (7, matching test_registry.py exactly) ────────────────────────────────

(deftest test-source-ids-nonempty
  (testing "source-ids returns at least 10 entries"
    (is (>= (count (registry/source-ids)) 10))))

(deftest test-get-source-known
  (testing "get-source for us-fred returns jurisdiction=us"
    (let [s (registry/get-source "us-fred")]
      (is (= (get s "jurisdiction") "us")))))

(deftest test-get-source-unknown-raises
  (testing "get-source with unknown id throws ex-info containing 'no such source'"
    (is (thrown-with-msg? clojure.lang.ExceptionInfo #"no such source"
                          (registry/get-source "nope")))))

(deftest test-sourcing-unverified-is-representative
  (testing "sourcing-for an unverified-seed source returns :representative"
    (is (= (registry/sourcing-for "us-fred") ":representative"))))

(deftest test-sourcing-unknown-is-representative
  (testing "sourcing-for an unknown source id returns :representative conservatively"
    (is (= (registry/sourcing-for "nope") ":representative"))))

(deftest test-assert-source-allowed-blocks-terminal
  (testing "assert-source-allowed raises on a prohibited commercial terminal (Rider §2(e))"
    (is (thrown-with-msg? clojure.lang.ExceptionInfo #"Rider"
                          (registry/assert-source-allowed "via refinitiv eikon")))))

(deftest test-assert-source-allowed-passes-public
  (testing "assert-source-allowed passes clean public-source text without throwing"
    (is (nil? (registry/assert-source-allowed "https://fred.stlouisfed.org/")))))

;; ── runner ───────────────────────────────────────────────────────────────────────

(when (= *file* (System/getProperty "babashka.file"))
  (let [{:keys [fail error]} (clojure.test/run-tests 'shionome.methods.test-registry)]
    (System/exit (if (zero? (+ fail error)) 0 1))))
