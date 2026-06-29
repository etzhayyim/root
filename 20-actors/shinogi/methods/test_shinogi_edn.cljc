#!/usr/bin/env bb
;; shinogi 鎬 — seed loader tests.
(ns shinogi.methods.test-shinogi-edn
  (:require [shinogi.methods.shinogi-edn :as se]
            [clojure.test :refer [deftest is run-tests]]))

(def seed-path "20-actors/shinogi/kotoba/seed.exam-involution.edn")

(deftest loads-drivers
  (let [ds (se/drivers seed-path)]
    (is (vector? ds))
    (is (<= 18 (count ds)) "at least the seed 18 drivers")
    (is (every? #(= :driver (:type %)) ds) "all rows are drivers")))

(deftest classify-splits-by-type
  (let [c (se/classify [{:type :driver :id "a"} {:type :other :id "b"} {:type :driver :id "c"}])]
    (is (= 2 (count (:drivers c))) "keeps only :driver rows")))

(deftest every-driver-has-required-keys
  (doseq [d (se/drivers seed-path)]
    (is (string? (:id d)) (str "id on " (:id d)))
    (is (string? (:name d)))
    (is (string? (:jurisdiction d)))
    (is (keyword? (:kind d)))
    (is (keyword? (:stock d)))
    (is (keyword? (:polarity d)))
    (is (string? (:enactor d)) (str "enactor (誰が) on " (:id d)))
    (is (string? (:origin d)) (str "origin (経緯) on " (:id d)))
    (is (seq (:stakeholders d)) (str "stakeholders (関係者) on " (:id d)))))

(deftest china-is-primary
  (let [ds (se/drivers seed-path)
        cn (filter #(= "CN" (:jurisdiction %)) ds)]
    (is (<= 8 (count cn)) "China is the primary subject (gaokao + ≥8 CN drivers)")
    (is (some #(= "cn-gaokao" (:id %)) ds) "the gaokao itself is present")
    (is (some #(= "cn-neijuan-norm" (:id %)) ds) "内卷 involution norm is present")))

#?(:clj
   (defn -main [& _]
     (let [r (run-tests 'shinogi.methods.test-shinogi-edn)]
       (System/exit (if (zero? (+ (:fail r) (:error r))) 0 1)))))
