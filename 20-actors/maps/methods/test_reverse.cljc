(ns maps.methods.test-reverse
  "test_reverse.py — kotoba-native reverse-geocode tests (ADR-2606064500 R2). unittest →
  clojure.test. Ports TestHaversine (pure ranker) — always runs.

  The TestReverseE2E class is @unittest.skipUnless(_HAS_H3); `h3` is unavailable on this host, so
  — exactly as the Python suite does without h3 — it is omitted. The test_no_h3_returns_empty
  case (which runs precisely WHEN h3 is absent) IS ported. The __main__ runner is omitted."
  (:require [clojure.test :refer [deftest is]]
            [maps.methods.reverse :as reverse]))

(deftest test-zero
  (is (= (reverse/haversine-m 35.0 139.0 35.0 139.0) 0.0)))

(deftest test-known-distance-tokyo-haneda
  (let [d (reverse/haversine-m 35.6812 139.7671 35.5494 139.7798)]  ; ~14.7 km
    (is (< (Math/abs (- d 14700.0)) 500))))

(deftest test-one-degree-lat
  (let [d (reverse/haversine-m 0.0 0.0 1.0 0.0)]  ; ~111.2 km
    (is (< (Math/abs (- d 111195.0)) 200))))

(deftest test-monotonic
  (let [near (reverse/haversine-m 35.6812 139.7671 35.6809 139.7644)
        far (reverse/haversine-m 35.6812 139.7671 35.5494 139.7798)]
    (is (< near far))))

(deftest test-no-h3-returns-empty
  ;; reverse-geocode degrades to [] without h3 (h3 is absent on this host); ranker stays pure.
  (is (= (reverse/reverse-geocode "http://127.0.0.1:1" 35.68 139.77) [])))
