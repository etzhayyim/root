(ns etzhayyim.ecl-test
  "Tests for the reusable ECL objective function (ADR-2606182359)."
  (:require [clojure.test :refer [deftest is testing]]
            [etzhayyim.ecl :as ecl]))

(deftest spec-loads
  (testing "the Tier-0/1 objective-function spec is readable"
    (is (true? (ecl/available?)))))

(deftest catastrophe-term-is-non-negotiable
  (testing "maximal harm to 子/孫 wellbecoming (≤ threshold) → :non-aligned regardless of J"
    (let [r (ecl/route {:ko-wellbecoming -2.0})]
      (is (= :non-aligned (:route r)))
      (is (= :catastrophe (:reason r))))
    (is (true? (ecl/catastrophe? {:mago-wellbecoming -2.0})))
    (is (false? (ecl/catastrophe? {:ko-wellbecoming 1.0 :mago-wellbecoming 1.0})))))

(deftest objective-J-bands
  (testing "J = Σ weight·score, routed by the thresholds"
    (is (= 0.0 (ecl/objective {})))                       ; all-neutral
    (let [aligned (ecl/route {:ko-wellbecoming 2.0 :mago-wellbecoming 2.0})]
      (is (= :aligned (:route aligned)))
      (is (pos? (:J aligned))))))
