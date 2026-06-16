(ns jinushi.methods.test-ingest
  "jinushi 地主 — real-snapshot ingest tests (offline; reads the COMMITTED snapshot, never WDQS)."
  (:require [clojure.test :refer [deftest is run-tests]]
            [clojure.string :as str]
            [clojure.java.io :as io]
            [jinushi.methods.analyze :as a]
            [jinushi.methods.ingest :as ing]))

(def actor-dir (-> *file* io/file .getParentFile .getParentFile))
(def snap-file (io/file actor-dir "data" "acquired" "wikidata-national-parks.kotoba.edn"))
(defn snap [] (ing/load-snapshot snap-file))

(def tiny
  {:records [{:cc "NO" :area-m2 1.605e9 :unit-src "Q712226"}
             {:cc "NO" :area-m2 1.10e9  :unit-src "Q35852"}
             {:cc "FI" :area-m2 5.0e7   :unit-src "Q712226"}]})

(deftest test-snapshot-to-dataset
  (let [{:keys [owners parcels]} (ing/snapshot->dataset tiny)]
    (is (= 2 (count owners)) "one public owner bucket per country")
    (is (every? #(= :public (:owner/type %)) owners) "national-park owners are PUBLIC land")
    (is (= 3 (count parcels)) "one parcel per record")
    (is (apply distinct? (map :parcel/id parcels)) "parcel ids are unique + deterministic")
    (is (every? #(= :wikidata (:parcel/source %)) parcels) "source attribution preserved")))

(deftest test-merge-dedupes-owners
  (let [d1 (ing/snapshot->dataset tiny)
        d2 (ing/snapshot->dataset {:records [{:cc "NO" :area-m2 1.0e7 :unit-src "Q712226"}]})
        m (ing/merge-datasets d1 d2)]
    (is (= (count (distinct (map :owner/key (:owners m)))) (count (:owners m)))
        "merged owners are deduped by :owner/key")
    (is (= 4 (count (:parcels m))) "merged parcels concatenate (3 + 1)")))

(deftest test-g1-public-no-person
  ;; G1: national-park acquisition is public land — no person dimension, no coordinates.
  (let [{:keys [owners parcels]} (ing/snapshot->dataset (snap))]
    (is (every? #(= :public (:owner/type %)) owners) "every acquired owner is PUBLIC")
    (is (not-any? :parcel/centroid parcels) "no per-parcel coordinate from this source (G1)")
    (is (every? #(pos? (:parcel/area-m2 %)) parcels) "every acquired area is positive")))

(deftest test-real-coverage-above-synthetic-floor
  (let [ds (ing/snapshot->dataset (snap))
        res (a/analyze ds)
        cov (:coverage res)]
    (is (>= (:countries-touched cov) 20) "real snapshot touches ≥20 countries")
    (is (> (:world-coverage-frac cov) 0.005)
        "real public-land coverage exceeds the 0.056% synthetic floor")
    (is (every? #(= :wikidata (:parcel/source %)) (:parcels res))
        "every analyzed parcel carries its real source")))

(deftest test-snapshot-is-honest
  (let [s (snap)]
    (is (= (:record-count s) (count (:records s))) "snapshot record-count matches its records")
    (is (number? (:dropped-unknown-unit s)) "snapshot discloses how many rows were dropped (G4)")
    (is (str/includes? (:source s) "wikidata") "snapshot attributes its source")))

(when (= *file* (System/getProperty "babashka.file"))
  (let [{:keys [fail error]} (run-tests 'jinushi.methods.test-ingest)]
    (System/exit (+ (or fail 0) (or error 0)))))
