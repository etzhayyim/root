#!/usr/bin/env bb
;; shinan 指南 — content-addressed ledger writer tests.
(ns shinan.methods.test-kotoba
  (:require [shinan.methods.kotoba :as k]
            [clojure.java.io :as io]
            [clojure.test :refer [deftest is run-tests]]))

(def ^:private tmp
  (str (System/getProperty "java.io.tmpdir") "/shinan-test-kotoba.kotoba.edn"))
(defn- fresh! [] (let [f (io/file tmp)] (when (.exists f) (.delete f))) tmp)

(deftest tx-cid-deterministic-and-prev-sensitive
  (let [ds [[":db/add" "t-jp-math" ":shinan.rem/route" ":covered"]]]
    (is (= (k/tx-cid ds "") (k/tx-cid ds "")) "deterministic")
    (is (not= (k/tx-cid ds "") (k/tx-cid ds "bPREV")) "prev-cid changes the CID")
    (is (= \b (first (k/tx-cid ds))) "CID is b-prefixed")))

(deftest append-read-roundtrip-with-vector-value
  (let [path (fresh!)
        ds [[":db/add" "r-wikibooks" ":shinan.resource/languages" [":en" ":ja" ":zh" ":ko"]]
            [":db/add" "r-wikibooks" ":shinan/derived" true]]
        tx (k/make-tx ds "t0" "as0" "")
        cid (k/append-tx tx path)]
    (is (= cid (k/head-cid path)) "head = appended cid")
    (let [txs (k/read-log path)]
      (is (= 1 (count txs)))
      (is (= ds (get (first txs) ":tx/datoms")) "datoms (incl. vector value) round-trip exactly"))))

(deftest verify-chain-detects-tamper
  (let [path (fresh!)
        ds1 [[":db/add" "t-a" ":shinan.rem/route" ":covered"]]
        ds2 [[":db/add" "t-b" ":shinan.rem/route" ":coverage-gap"]]
        c1 (k/append-tx (k/make-tx ds1 "t0" "a0" "") path)
        _  (k/append-tx (k/make-tx ds2 "t1" "a1" c1) path)]
    (is (:ok (k/verify-chain path)) "intact chain verifies")
    (is (= 2 (:length (k/verify-chain path))))
    (spit path (str (k/tx->edn (k/make-tx [[":db/add" "x" ":shinan.rem/route" ":covered"]]
                                          "t2" "a2" "bWRONGPREV")) "\n") :append true)
    (is (not (:ok (k/verify-chain path))) "broken prev-cid is detected")))

(when (= *file* (System/getProperty "babashka.file"))
  (let [{:keys [fail error]} (run-tests 'shinan.methods.test-kotoba)]
    (when (pos? (+ fail error)) (System/exit 1))))
