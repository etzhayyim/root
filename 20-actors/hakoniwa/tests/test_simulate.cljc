(ns hakoniwa.tests.test-simulate
  "test_simulate.py — hakoniwa 箱庭 world-load + simulation-kernel tests (ADR-2606111500).
  1:1 Clojure port of tests/test_simulate.py (stdlib asserts → clojure.test)."
  (:require [clojure.test :refer [deftest is run-tests]]
            #?(:clj [clojure.java.io :as io])
            [hakoniwa.methods.world :as w]
            [hakoniwa.methods.simulate :as s]))

(def ^:private actor-dir (-> *file* io/file .getParentFile .getParentFile))
(def ^:private scenario (io/file actor-dir "data" "seed-scenario.kotoba.edn"))

(deftest test-load-nontrivial-and-synthetic
  (let [[nodes edges] (w/load scenario)
        P (w/personas nodes)]
    (is (>= (count P) 12))
    (is (>= (count edges) 30))
    (doseq [[_ n] P] (is (true? (get n ":persona/synthetic"))))
    (doseq [e edges]
      (is (contains? nodes (get e ":en/from")))
      (is (contains? nodes (get e ":en/to"))))))

(deftest test-g1-refuses-real-person
  (let [base (fn [extra] (str "[{:sim/id \"persona.x\" :sim/kind :persona :sim/label \"x\" " extra "}]"))
        load-nodes (fn [text]
                     (reduce (fn [acc f] (if (map? f) (assoc acc (get f ":sim/id") f) acc))
                             {} (w/read-edn text)))]
    ;; missing synthetic marker
    (is (thrown? #?(:clj Exception :cljs js/Error)
                 (w/assert-synthetic (load-nodes (base "")))))
    ;; PII-bearing persona, even if marked synthetic
    (is (thrown? #?(:clj Exception :cljs js/Error)
                 (w/assert-synthetic (load-nodes (base ":persona/synthetic true :email \"a@b.c\"")))))))

(deftest test-kernel-converges-in-unit-interval
  (let [[nodes edges] (w/load scenario)
        {:keys [pids sus base-anchor incoming exposure]} (s/build-topology nodes edges)
        x (s/run-replica pids sus base-anchor incoming exposure 12 7 0 0.0)]
    (is (= (set (keys x)) (set pids)))
    (doseq [[_ v] x] (is (<= 0.0 v 1.0)))))

(deftest test-row-normalised-influence
  (let [[nodes edges] (w/load scenario)
        {:keys [incoming]} (s/build-topology nodes edges)]
    (doseq [[_ lst] incoming]
      (when (seq lst)
        (is (< (Math/abs (- (reduce + 0.0 (map second lst)) 1.0)) 1e-9))))))

(deftest test-determinism
  (let [[n1 e1] (w/load scenario)
        [a ma] (s/ensemble n1 e1 {:steps 10 :replicas 32 :seed 3})
        [n2 e2] (w/load scenario)
        [b mb] (s/ensemble n2 e2 {:steps 10 :replicas 32 :seed 3})]
    (is (= a b))
    (is (= ma mb))))

(deftest test-stronger-relay-raises-mean
  (let [[nodes edges] (w/load scenario)
        [base _] (s/ensemble nodes edges {:steps 12 :replicas 48 :seed 7})
        nodes2 (update nodes "signal.s1" assoc ":signal/push" 0.40)
        [boosted _] (s/ensemble nodes2 edges {:steps 12 :replicas 48 :seed 7})]
    (is (> (/ (reduce + 0.0 boosted) (count boosted))
           (+ (/ (reduce + 0.0 base) (count base)) 1e-3)))))

(deftest test-ensemble-has-spread
  (let [[nodes edges] (w/load scenario)
        [results _] (s/ensemble nodes edges {:steps 12 :replicas 64 :seed 7})]
    (is (> (- (apply max results) (apply min results)) 1e-4))))

#?(:clj (defn -main [& _] (run-tests 'hakoniwa.tests.test-simulate)))
