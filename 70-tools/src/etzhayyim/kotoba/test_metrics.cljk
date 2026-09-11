;; etzhayyim.kotoba.test-metrics — concentration metrics (HHI / effective-N /
;; top-share) the KG-mirror actors route to redundancy/accountability. Run: bb test:kotoba
(ns etzhayyim.kotoba.test-metrics
  (:require [clojure.test :refer [deftest is testing run-tests]]
            [etzhayyim.kotoba.metrics :as m]))

(deftest shares-normalization
  (is (= [1/4 1/4 1/2] (vec (m/shares [1 1 2]))))
  (testing "empty / zero-total → empty"
    (is (= [] (vec (m/shares []))))
    (is (= [] (vec (m/shares [0 0]))))))

(deftest hhi-scale
  (testing "10000 = monopoly, halving as players equalize"
    (is (== 10000.0 (m/hhi [1])))       ;; single group
    (is (== 10000.0 (m/hhi [5 0 0])))   ;; one group holds everything
    (is (== 5000.0 (m/hhi [1 1])))      ;; 2 equal → 10000·(¼+¼)
    (is (== 2500.0 (m/hhi [1 1 1 1])))) ;; 4 equal
  (is (== 0.0 (m/hhi []))))

(deftest effective-n-competitors
  (testing "1/Σsᵢ² = effective number of equal competitors"
    (is (== 1.0 (m/effective-n [1])))
    (is (== 2.0 (m/effective-n [1 1])))
    (is (== 4.0 (m/effective-n [1 1 1 1]))))
  (is (== 0.0 (m/effective-n []))))

(deftest top-share-largest
  (is (== 0.5 (m/top-share [1 1 2])))   ;; largest = 2/4
  (is (== 0.75 (m/top-share [3 1])))
  (is (== 0.0 (m/top-share []))))

(defn -main [& _]
  (let [{:keys [fail error]} (run-tests 'etzhayyim.kotoba.test-metrics)]
    (System/exit (if (pos? (+ fail error)) 1 0))))
