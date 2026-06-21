(ns etzhayyim.explorer.aliveness-test
  (:require [cljs.test :refer-macros [deftest is testing]]
            [etzhayyim.explorer.organism.aliveness :as a]
            [etzhayyim.explorer.nodes.graph :as g]))

(deftest shannon-entropy
  (testing "zero counts → 0"
    (is (= 0.0 (a/shannon [0 0 0]))))
  (testing "single class → 0 entropy"
    (is (= 0.0 (a/shannon [10 0 0]))))
  (testing "even split → max entropy (ln 3)"
    (is (< (Math/abs (- (a/shannon [5 5 5]) (Math/log 3))) 1e-9))))

(deftest motion+diversity-computed
  (let [traj {:runs [{:run 1 :alive 3 :dormant 74 :stub 18 :sum 3000}
                     {:run 2 :alive 0 :dormant 49 :stub 46 :sum 2086}]}
        tuple (a/compute {:trajectory traj :vitals nil})
        by-key (into {} (map (juxt :key identity) tuple))]
    (testing "M and D are computed (not read)"
      (is (= :computed (:source (by-key :M))))
      (is (= :computed (:source (by-key :D)))))
    (testing "M reflects the activity delta"
      (is (pos? (:value (by-key :M)))))
    (testing "absent vitals → C/P/G unknown"
      (is (= :unknown (:status (by-key :C)))))))

(deftest band-status-classifies
  (is (= :ok (a/band-status :C 0.4)))
  (is (= :low (a/band-status :C 0.05)))
  (is (= :high (a/band-status :C 0.9)))
  (is (= :unknown (a/band-status :C nil))))

(deftest layout-is-deterministic
  (let [nodes [{:id "a" :score 20 :cells 0 :reflex "green" :class "dormant"}
               {:id "b" :score 33 :cells 5 :reflex "red" :class "dormant"}]
        l1 (g/layout nodes)
        l2 (g/layout nodes)]
    (testing "same input → same positions (no Math/random)"
      (is (= (get-in l1 ["a" :x]) (get-in l2 ["a" :x])))
      (is (= (get-in l1 ["b" :y]) (get-in l2 ["b" :y]))))
    (testing "every node placed"
      (is (= 2 (count l1))))))
