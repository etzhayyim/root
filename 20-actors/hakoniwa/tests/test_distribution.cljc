(ns hakoniwa.tests.test-distribution
  "test_distribution.py — hakoniwa 箱庭 distribution + forecast-record + Datom-emit tests.
  1:1 Clojure port of tests/test_distribution.py (ADR-2606111500)."
  (:require [clojure.test :refer [deftest is run-tests]]
            [clojure.string :as str]
            #?(:clj [clojure.java.io :as io])
            [hakoniwa.methods.world :as w]
            [hakoniwa.methods.simulate :as s]
            [hakoniwa.methods.distribution :as d]
            [hakoniwa.methods.datom-emit :as de]))

(def ^:private actor-dir (-> *file* io/file .getParentFile .getParentFile))
(def ^:private scenario (io/file actor-dir "data" "seed-scenario.kotoba.edn"))

(defn- dist-fixture []
  (let [[nodes edges] (w/load scenario)
        [results meta] (s/ensemble nodes edges {:steps 12 :replicas 64 :seed 7})]
    [nodes edges (d/distribution results) meta]))

(deftest test-quantiles-monotone-and-histogram-total
  (let [[_ _ dist meta] (dist-fixture)
        q (get dist "quantiles")
        order [(get q ":p10") (get q ":p25") (get q ":p50") (get q ":p75") (get q ":p90")]]
    (is (= order (sort order)))
    (is (= (reduce + (get dist "histogram")) (get meta "replicas")))
    (is (<= (get dist "min") (get dist "mean") (get dist "max")))))

(deftest test-forecast-record-is-distribution-only
  (let [[nodes _ dist meta] (dist-fixture)
        rec (d/forecast-record nodes dist meta "2026-06-11T00:00:00Z")]
    (is (= ":distribution" (get rec ":forecast/kind")))
    (is (false? (get rec ":forecast/point-asserted")))
    (is (not (some (fn [k] (and (str/includes? k "point") (not= k ":forecast/point-asserted")))
                   (keys rec))))
    (is (and (contains? rec ":forecast/quantiles") (contains? rec ":forecast/histogram")))))

(deftest test-g3-non-resilience-use-refused
  (let [[nodes _ dist meta] (dist-fixture)]
    (doseq [bad [":trade" ":wager" ":position" ":target" ":manipulate" ":campaign"]]
      (is (thrown? #?(:clj Exception :cljs js/Error)
                   (d/forecast-record nodes dist meta "t" bad))))))

(deftest test-forecast-edn-roundtrips-distribution-only
  (let [[nodes _ dist meta] (dist-fixture)
        rec (d/forecast-record nodes dist meta "2026-06-11T00:00:00Z")
        edn (d/forecast-edn rec)
        payload (->> (str/split-lines edn)
                     (remove (fn [ln] (str/starts-with? (str/triml ln) ";;")))
                     (str/join "\n"))]
    (is (str/includes? edn ":forecast/point-asserted false"))
    (is (str/includes? edn ":forecast/kind :distribution"))
    (is (not (str/includes? payload ":forecast/point ")))))

(deftest test-datom-emit-ground-synthetic-and-transient-distribution
  (let [[nodes edges dist meta] (dist-fixture)
        out (de/emit nodes edges dist meta 5)]
    (is (str/includes? out ":add]"))
    (is (str/includes? out ":persona/synthetic true"))
    (is (str/includes? out ":en/kind :influences"))
    (is (str/includes? out " 5 :add]"))
    (is (str/includes? out ":bond/is-transient true"))
    (is (str/includes? out ":bond/distribution-p50"))
    (is (str/includes? out ":bond/point-asserted false"))
    (doseq [line (str/split-lines out)]
      (when (and (str/starts-with? line "[") (str/includes? line ":bond/distribution"))
        (is (str/includes? line ":derived]"))))))

(deftest test-determinism
  (let [[nodes edges dist meta] (dist-fixture)
        a (de/emit nodes edges dist meta 1)
        [nodes2 edges2 dist2 meta2] (dist-fixture)
        b (de/emit nodes2 edges2 dist2 meta2 1)]
    (is (= a b))))

#?(:clj (defn -main [& _] (run-tests 'hakoniwa.tests.test-distribution)))
