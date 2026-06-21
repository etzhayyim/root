(ns etzhayyim.explorer.wire-test
  "Transit (transit+json) wire: round-trip type fidelity, and decoding the real
   clj-generated Datom query response (the Datomic-client wire standard)."
  (:require [cljs.test :refer-macros [deftest is testing]]
            [etzhayyim.explorer.wire :as wire]
            ["fs" :as fs]))

(deftest roundtrip-preserves-rich-types
  (testing "transit+json preserves keywords, sets, nested maps (JSON would not)"
    (let [data {:cell/id "busshi"
                :cell/class :alive
                :tags #{:a :b}
                :n 42
                :nested {:k/w [:x :y]}}
          decoded (-> data wire/encode wire/decode)]
      (is (= data decoded))
      (is (keyword? (:cell/class decoded)))
      (is (set? (:tags decoded))))))

(deftest decodes-the-clj-generated-query-response
  (testing "the transit+json a kotoba node emits decodes with keyword fidelity"
    (let [json (.readFileSync fs "public/kotoba/wire/cells.transit.json" "utf8")
          resp (wire/decode json)
          cells (:result/cells resp)]
      (is (= "transit+json" (:wire/format resp)))
      (is (= 104 (:result/count resp)))
      (is (= 104 (count cells)))
      (testing "attribute keys AND values arrive as real keywords, not strings"
        (let [c (first cells)]
          (is (contains? c :cell/class))
          (is (keyword? (:cell/class c)))
          (is (keyword? (:cell/reflex c)))
          (is (string? (:cell/id c))))))))
