(ns etzhayyim.explorer.datom-test
  "Proves the kotoba Datom layer is REAL, not a stub: the canonical kotoba.datom
   codec, run in cljs, byte-compatibly verifies a real committed kotoba Datom log
   (mimamori's golden fixture) and the tamper-detection actually fires."
  (:require [cljs.test :refer-macros [deftest is testing]]
            [kotoba.datom :as kd]
            [etzhayyim.explorer.chain.datom :as d]
            ["fs" :as fs]))

(def fixture
  (.readFileSync fs "public/kotoba/log/mimamori.kotoba.edn" "utf8"))

(deftest sha256-seam-bound
  (testing "tx-cid produces the b+hex CID shape using the real sha256 seam"
    (let [cid (kd/tx-cid [[:db/add "e" ":a" "v"]] "")]
      (is (string? cid))
      (is (= \b (first cid)))
      (is (= 65 (count cid))))))   ;; "b" + 64 hex chars

(deftest verifies-real-committed-log
  (let [txs (d/parse-log fixture)
        result (d/verify-chain txs)]
    (testing "the real mimamori log parses to ≥1 tx"
      (is (pos? (count txs))))
    (testing "byte-compatible CID recomputation verifies the committed chain"
      ;; If this is :ok, the cljs codec reproduced the EXACT :tx/cid that the
      ;; clj/Python writer stored — i.e. this is a genuine kotoba Datom reader.
      (is (:ok result) (str "broken-at " (:broken-at result)
                            " expected " (:expected result)
                            " actual " (:actual result))))
    (testing "head CID is the last tx's stored CID"
      (is (= (:head result) (:tx/cid (last txs)))))))

(deftest tamper-detection-fires
  (let [txs (d/parse-log fixture)
        ;; flip one datom value in the first tx → its CID must no longer match
        tampered (update-in (vec txs) [0 :tx/datoms 0 3]
                            (fn [v] (str v "-TAMPERED")))
        result (d/verify-chain tampered)]
    (testing "a single altered datom breaks verification at that tx"
      (is (not (:ok result)))
      (is (= 0 (:broken-at result))))))

(deftest materializes-eavt
  (let [txs (d/parse-log fixture)
        eavt (d/materialize-eavt txs)]
    (testing "EAVT fold yields entities with attribute maps"
      (is (pos? (count (d/entities eavt))))
      (let [e (first (d/entities eavt))]
        (is (map? (get eavt e)))))
    (testing "attributes are discoverable for querying"
      (is (pos? (count (d/attributes txs)))))))
