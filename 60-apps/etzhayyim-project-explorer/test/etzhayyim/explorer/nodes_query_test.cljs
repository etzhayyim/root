(ns etzhayyim.explorer.nodes-query-test
  "Proves /nodes is built by QUERYING kotoba Datoms (vitals EAVT snapshot +
   census commit-log), not by reading organism.json."
  (:require [cljs.test :refer-macros [deftest is testing]]
            [cljs.reader :as edn]
            [etzhayyim.explorer.chain.datom :as d]
            ["fs" :as fs]))

(def vitals
  (binding [edn/*default-data-reader-fn* (atom (fn [_t v] v))]
    (edn/read-string
     (.readFileSync fs "public/organism/vitals.kotoba.edn" "utf8"))))

(def census-text
  (.readFileSync fs "public/kotoba/log/actor-census.kotoba.edn" "utf8"))

(deftest vitals-eavt-materializes-living-cells
  (let [eavt (d/materialize-snapshot vitals)
        cells (->> (vals eavt) (filter :vitals.actor/name))]
    (testing "the vitals EAVT snapshot yields the living cells"
      (is (= 104 (count cells))))
    (testing "each cell carries the heartbeat attributes we render"
      (let [a (first cells)]
        (is (contains? a :vitals.actor/cells))
        (is (contains? a :vitals.clj/reflex))
        (is (contains? a :vitals.score/actor))))))

(deftest census-log-verifies-and-queries
  (let [txs (d/parse-log census-text)
        v (d/verify-chain txs)
        eavt (d/materialize-snapshot
              (vec (mapcat (fn [tx]
                             (map (fn [[_op e a vv]] [e a vv (:tx/id tx) :add])
                                  (:tx/datoms tx)))
                           txs)))
        tiers (d/entities-where eavt ":census/tier")]
    (testing "the census commit-log chain verifies (real codec)"
      (is (:ok v)))
    (testing "querying :census/tier returns the actor tiers incl. unispsc 18342"
      (is (<= 5 (count tiers)))
      (let [counts (into {} (map (fn [[_ a]]
                                   [(get a ":census/tier") (get a ":census/count")])
                                 tiers))]
        (is (= 104 (get counts "living-cells")))
        (is (= 18342 (get counts "unispsc")))))))
