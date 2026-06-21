(ns etzhayyim.explorer.coverage6-test
  "Boundary-condition coverage for the aliveness bands and the compute edge
   cases (empty / single-run trajectory)."
  (:require [cljs.test :refer-macros [deftest is testing]]
            [etzhayyim.explorer.organism.aliveness :as a]))

(deftest band-status-boundaries-are-inclusive
  (testing "a value exactly on lo/hi is in-band (:ok); just outside is low/high"
    (let [{:keys [lo hi]} (:C a/bands)]   ; C = [0.20 0.70]
      (is (= :ok   (a/band-status :C lo)))
      (is (= :ok   (a/band-status :C hi)))
      (is (= :low  (a/band-status :C (- lo 0.01))))
      (is (= :high (a/band-status :C (+ hi 0.01))))
      (is (= :unknown (a/band-status :C nil))))))

(deftest in-band?-is-inclusive
  (testing "in-band? matches band-status on the boundaries"
    (let [{:keys [lo hi]} (:G a/bands)]   ; G = [1.00 2.00]
      (is (true? (a/in-band? :G lo)))
      (is (true? (a/in-band? :G hi)))
      (is (false? (a/in-band? :G (- lo 0.001))))
      (is (false? (a/in-band? :G (+ hi 0.001)))))))

(deftest compute-handles-empty-and-single-run
  (testing "no trajectory → M and D are 0 (still computed, not unknown)"
    (let [tuple (a/compute {:trajectory {:runs []} :vitals nil})
          by-key (into {} (map (juxt :key identity) tuple))]
      (is (= 0.0 (:value (by-key :M))))
      (is (= 0.0 (:value (by-key :D))))
      (is (= :computed (:source (by-key :M))))))
  (testing "a single run → motion 0 (no delta), diversity from that run"
    (let [tuple (a/compute {:trajectory {:runs [{:run 1 :sum 100 :alive 1 :dormant 1 :stub 1}]}
                            :vitals nil})
          by-key (into {} (map (juxt :key identity) tuple))]
      (is (= 0.0 (:value (by-key :M))))           ; needs ≥2 runs for motion
      (is (pos? (:value (by-key :D)))))))          ; 3 non-zero classes → entropy > 0

(deftest shannon-two-class
  (testing "two equiprobable classes → ln 2"
    (is (< (js/Math.abs (- (a/shannon [4 4]) (js/Math.log 2))) 1e-9))
    (is (= 0.0 (a/shannon [])))))
