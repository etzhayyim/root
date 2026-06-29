#!/usr/bin/env bb
;; kanmon 関門 — content-addressed ledger writer tests.
(ns kanmon.methods.test-kotoba
  (:require [kanmon.methods.kotoba :as k]
            [clojure.java.io :as io]
            [clojure.test :refer [deftest is run-tests]]))

(def ^:private tmp
  (str (System/getProperty "java.io.tmpdir") "/kanmon-test-kotoba.kotoba.edn"))
(defn- fresh! [] (let [f (io/file tmp)] (when (.exists f) (.delete f))) tmp)

(deftest tx-cid-deterministic-and-prev-sensitive
  (let [ds [[":db/add" "cn-gaokao" ":kanmon.rem/route" ":destake"]]]
    (is (= (k/tx-cid ds "") (k/tx-cid ds "")) "deterministic")
    (is (not= (k/tx-cid ds "") (k/tx-cid ds "bPREV")) "prev-cid changes the CID")
    (is (= \b (first (k/tx-cid ds))) "CID is b-prefixed")))

(deftest append-read-roundtrip
  (let [path (fresh!)
        ds [[":db/add" "kr-suneung" ":kanmon.rem/route" ":destake"]
            [":db/add" "kr-suneung" ":kanmon/derived" true]]
        tx (k/make-tx ds "t0" "as0" "")
        cid (k/append-tx tx path)]
    (is (= cid (k/head-cid path)) "head = appended cid")
    (let [txs (k/read-log path)]
      (is (= 1 (count txs)))
      (is (= ds (get (first txs) ":tx/datoms")) "datoms round-trip exactly"))))

(deftest verify-chain-detects-tamper
  (let [path (fresh!)
        ds1 [[":db/add" "a" ":kanmon.rem/route" ":monitor"]]
        ds2 [[":db/add" "b" ":kanmon.rem/route" ":open-pathway"]]
        c1 (k/append-tx (k/make-tx ds1 "t0" "a0" "") path)
        _  (k/append-tx (k/make-tx ds2 "t1" "a1" c1) path)]
    (is (:ok (k/verify-chain path)) "intact chain verifies")
    (is (= 2 (:length (k/verify-chain path))))
    (spit path (str (k/tx->edn (k/make-tx [[":db/add" "x" ":kanmon.rem/route" ":monitor"]]
                                          "t2" "a2" "bWRONGPREV")) "\n") :append true)
    (is (not (:ok (k/verify-chain path))) "broken prev-cid is detected")))

(when (= *file* (System/getProperty "babashka.file"))
  (let [{:keys [fail error]} (run-tests 'kanmon.methods.test-kotoba)]
    (when (pos? (+ fail error)) (System/exit 1))))
