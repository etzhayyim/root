;; etzhayyim.kotoba.test-datom — EAVT datom model + four-index arrangement. Run: bb test:kotoba
;; Pins the [e a v tx op] canonical tuple, add/retract log folding, and the
;; eavt/aevt/avet/vaet index round-trip (ADR-2605312345).
(ns etzhayyim.kotoba.test-datom
  (:require [clojure.test :refer [deftest is testing run-tests]]
            [etzhayyim.kotoba.datom :as d]))

(deftest tuple-and-accessors
  (testing "4-arity defaults op to :add; 5-arity is explicit"
    (is (= ["e" :a "v" 1 :add] (d/datom "e" :a "v" 1)))
    (is (= ["e" :a "v" 2 :retract] (d/datom "e" :a "v" 2 :retract))))
  (let [dm (d/datom "gene.apc" :genome/kind :gene 7 :add)]
    (is (= "gene.apc" (d/d-e dm)))
    (is (= :genome/kind (d/d-a dm)))
    (is (= :gene (d/d-v dm)))
    (is (= 7 (d/d-tx dm)))
    (is (= :add (d/d-op dm))))
  (testing "assert?/retract? predicates"
    (is (true? (d/assert? (d/datom "e" :a "v" 1))))
    (is (false? (d/retract? (d/datom "e" :a "v" 1))))
    (is (true? (d/retract? (d/datom "e" :a "v" 2 :retract))))))

(deftest live-datoms-folding
  (testing "asserts accumulate as live [e a v] triples"
    (is (= #{["e" :a "v1"] ["e" :a "v2"]}
           (d/live-datoms [(d/datom "e" :a "v1" 1) (d/datom "e" :a "v2" 2)]))))
  (testing "a retract removes the matching triple"
    (is (= #{} (d/live-datoms [(d/datom "e" :a "v" 1) (d/datom "e" :a "v" 2 :retract)]))))
  (testing "re-assert after retract makes it live again (tx order matters)"
    (is (= #{["e" :a "v"]}
           (d/live-datoms [(d/datom "e" :a "v" 1)
                           (d/datom "e" :a "v" 2 :retract)
                           (d/datom "e" :a "v" 3)])))))

(deftest index-arrangement
  (let [live #{["e1" :name "alice"] ["e1" :friend "e2"]}
        idx  (d/index live)]
    (testing "EAVT: e → {a → #{v}}"
      (is (= #{"alice"} (get-in idx [:eavt "e1" :name]))))
    (testing "AVET: a → {v → #{e}} (the value index)"
      (is (= #{"e1"} (get-in idx [:avet :name "alice"]))))
    (testing "VAET: v → {a → #{e}} (reverse ref navigation)"
      (is (= #{"e1"} (get-in idx [:vaet "e2" :friend]))))
    (testing "live-triples flattens the index back to the original live set"
      (is (= live (set (d/live-triples idx)))))))

(defn -main [& _]
  (let [{:keys [fail error]} (run-tests 'etzhayyim.kotoba.test-datom)]
    (System/exit (if (pos? (+ fail error)) 1 0))))
