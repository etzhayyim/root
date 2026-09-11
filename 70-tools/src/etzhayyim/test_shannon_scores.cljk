;; etzhayyim.test-shannon-scores — Shannon scoring/DSM pure invariants (cljc port; IO-free).
;; Run via the aggregate: bb test:helpers
;; Covers cap · sh-entropy · build-report (weighted overall + hotspots) ·
;; dsm-cuthill-mckee · dsm-detect-cycles.
(ns etzhayyim.test-shannon-scores
  (:require [clojure.test :refer [deftest is testing run-tests]]
            [etzhayyim.shannon-scores :as ss]))

(defn- approx= [a b] (< (Math/abs (double (- a b))) 1e-9))

(deftest cap-clamp-and-round
  (is (= 50.0 (ss/cap 50.0)))
  (is (= 0.0 (ss/cap -10)))
  (is (= 100.0 (ss/cap 150)))
  (testing "rounded to one decimal"
    (is (= 33.3 (ss/cap 33.33)))
    (is (= 66.7 (ss/cap 66.66)))))

(deftest shannon-entropy-bits
  (testing "empty / all-zero / singleton → 0 bits"
    (is (approx= 0.0 (ss/sh-entropy {})))
    (is (approx= 0.0 (ss/sh-entropy {:a 0})))
    (is (approx= 0.0 (ss/sh-entropy {:a 5}))))
  (testing "uniform distributions → log2(n) bits"
    (is (approx= 1.0 (ss/sh-entropy {:a 1 :b 1})))
    (is (approx= 2.0 (ss/sh-entropy {:a 1 :b 1 :c 1 :d 1}))))
  (testing "skew lowers entropy below the uniform max"
    (is (< (ss/sh-entropy {:a 3 :b 1}) 1.0))))

(deftest build-report-weighting-and-hotspots
  (testing "a weighted check → overall = its score; redundancy = 1 - overall/100"
    (let [r (ss/build-report [{:name "claude_md_duplication" :score 80.0
                               :violations 0 :details "" :items []}])]
      (is (= 80.0 (:overall-score r)))
      (is (= 0.2 (:redundancy-rate r)))
      (is (= 0.25 (:weight (first (:checks r)))))))     ;; weight annotated from the table
  (testing "an unknown check has weight 0 → overall defaults to 100"
    (is (= 100.0 (:overall-score (ss/build-report
                                  [{:name "unknown_check" :score 50.0
                                    :violations 0 :details "" :items []}])))))
  (testing "hotspots are items sorted by redundancy descending"
    (let [r (ss/build-report [{:name "x" :score 50.0 :violations 1 :details ""
                               :items [{:redundancy 0.2} {:redundancy 0.9} {:redundancy 0.5}]}])]
      (is (= [0.9 0.5 0.2] (mapv :redundancy (:hotspots r)))))))

(deftest dsm-cuthill-mckee-permutation
  (testing "returns a valid permutation of 0..n-1"
    (let [perm (ss/dsm-cuthill-mckee [[0 1 0] [1 0 1] [0 1 0]] 3)]
      (is (= 3 (count perm)))
      (is (= #{0 1 2} (set perm))))))

(deftest dsm-detect-cycles-basic
  (testing "a 2-node mutual edge is one cycle"
    (let [cs (ss/dsm-detect-cycles ["a" "b"] {"a" {"b" 1} "b" {"a" 1}})]
      (is (= 1 (count cs)))
      (is (= 2 (:length (first cs))))))
  (testing "an acyclic graph has no cycles"
    (is (= [] (ss/dsm-detect-cycles ["a" "b"] {"a" {"b" 1}})))))

(defn -main [& _]
  (let [{:keys [fail error]} (run-tests 'etzhayyim.test-shannon-scores)]
    (System/exit (if (pos? (+ fail error)) 1 0))))
