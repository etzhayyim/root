(ns etzhayyim-organism-viz.ideal-state-test
  "Coverage for the homeostatic-range model (§1.15 non-eschatology: bands, not
  targets). Pure — no host I/O."
  (:require [clojure.test :refer [deftest is testing]]
            [etzhayyim-organism-viz.ideal-state :as ideal]))

(deftest ranges-shape
  (testing "the encoded bands are the 15 Python RANGES, each a field-keyed map"
    (is (= 15 (count ideal/ranges)))
    (is (= #{:name :symbol :lo :hi :unit :hard :death-signature}
           (set (keys (first ideal/ranges)))))
    (is (= "s_council" (:symbol (first ideal/ranges))))))

(deftest in-range-bounds
  (let [council (first (filter #(= "s_council" (:symbol %)) ideal/ranges))   ; lo=hi=5
        sister  (first (filter #(= "n_sister" (:symbol %)) ideal/ranges))]   ; lo=1 hi=nil
    (testing "two-sided exact band"
      (is (ideal/in-range? council 5))
      (is (not (ideal/in-range? council 4)))
      (is (not (ideal/in-range? council 6))))
    (testing "nil :hi = unbounded above (anti-eschatology)"
      (is (ideal/in-range? sister 1))
      (is (ideal/in-range? sister 1000000))
      (is (not (ideal/in-range? sister 0))))))

(deftest deviation-sign
  (let [council (first (filter #(= "s_council" (:symbol %)) ideal/ranges))]
    (is (= 0.0 (ideal/deviation council 5)) "inside → 0")
    (is (= -1 (ideal/deviation council 4)) "below lo → negative")
    (is (= 1 (ideal/deviation council 6)) "above hi → positive")))
