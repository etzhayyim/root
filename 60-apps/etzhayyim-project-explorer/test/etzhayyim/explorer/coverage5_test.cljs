(ns etzhayyim.explorer.coverage5-test
  "Coverage for multi-tx commit-DAG verification (the prev-linking the single-tx
   tests don't exercise) and the base58btc decoder used to read a did:key."
  (:require [cljs.test :refer-macros [deftest is testing]]
            [kotoba.datom :as kd]
            [etzhayyim.explorer.chain.datom :as d]
            [etzhayyim.explorer.chain.agent :as agent]))

;; ── multi-tx chain: prev-linking + tamper localisation ──────────────────────
(def ^:private chain
  (let [t1 (kd/make-tx [[:db/add "e" ":a" "v1"]] {:tx-id 1 :as-of 1 :prev-cid ""})
        t2 (kd/make-tx [[:db/add "e" ":a" "v2"]] {:tx-id 2 :as-of 2 :prev-cid (:tx/cid t1)})
        t3 (kd/make-tx [[:db/add "e" ":b" "v3"]] {:tx-id 3 :as-of 3 :prev-cid (:tx/cid t2)})]
    [t1 t2 t3]))

(deftest multi-tx-chain-verifies
  (testing "a 3-tx chain verifies and the head is the last cid"
    (let [r (d/verify-chain chain)]
      (is (:ok r))
      (is (= 3 (:length r)))
      (is (= (:tx/cid (last chain)) (:head r))))))

(deftest tamper-localises-to-its-tx
  (testing "altering a middle tx's datom breaks verification at that index"
    (let [bad (assoc-in (vec chain) [1 :tx/datoms 0 3] "EVIL")
          r (d/verify-chain bad)]
      (is (not (:ok r)))
      (is (= 1 (:broken-at r)))))
  (testing "re-pointing a tx's prev breaks the link"
    (let [bad (assoc-in (vec chain) [2 :tx/prev] "bdeadbeef")
          r (d/verify-chain bad)]
      (is (not (:ok r)))
      (is (= 2 (:broken-at r))))))

;; ── base58btc decoder (did:key reading) ─────────────────────────────────────
(defn- bytes->vec [u8] (vec (array-seq u8)))

(deftest base58-decode-values
  (testing "base58btc digit math (alphabet starts at '1'=0)"
    (is (= [1] (bytes->vec (agent/base58-decode "2"))))
    (is (= [57] (bytes->vec (agent/base58-decode "z"))))
    (is (= [58] (bytes->vec (agent/base58-decode "21"))))))

(deftest base58-decode-leading-zero
  (testing "a leading '1' decodes to a leading zero byte"
    (is (= [0] (bytes->vec (agent/base58-decode "1"))))
    (is (= [0 0 1] (bytes->vec (agent/base58-decode "112"))))))
