;; etzhayyim.kotoba.test-graph — transitive reachability + tier-depth + centrality. Run: bb test:kotoba
;; Pins the recursive traversal the supply-chain/power-relations mirrors use
;; (kabuto tier-depth, watatsuna chokepoint betweenness, components fragmentation).
(ns etzhayyim.kotoba.test-graph
  (:require [clojure.test :refer [deftest is testing run-tests]]
            [etzhayyim.kotoba.graph :as g]))

(def edges [["a" "b"] ["b" "c"] ["a" "c"] ["c" "d"]])
(def adj (g/adjacency edges))

(deftest adjacency-map
  (is (= {"a" #{"b" "c"} "b" #{"c"} "c" #{"d"}} adj)))

(deftest reachability-cycle-safe
  (testing "transitive successors; start excluded with no cycle back"
    (is (= #{"b" "c" "d"} (g/reachable adj "a")))
    (is (= #{"d"} (g/reachable adj "c"))))
  (testing "a cycle returns to the start"
    (let [cadj (g/adjacency [["x" "y"] ["y" "x"]])]
      (is (= #{"x" "y"} (g/reachable cadj "x"))))))

(deftest bfs-depth-and-tier
  (testing "BFS hop distances from the source"
    (is (= {"a" 0 "b" 1 "c" 1 "d" 2} (g/depth adj "a"))))
  (testing "tier-depth = longest hop count (0 for a leaf)"
    (is (= 2 (g/tier-depth adj "a")))
    (is (= 0 (g/tier-depth adj "d")))))

(deftest roots-and-nodes
  (testing "roots = sources (a `from` never a `to`)"
    (is (= ["a"] (g/roots edges))))
  (is (= #{"a" "b" "c" "d"} (g/nodes edges))))

(deftest weakly-connected-components
  (testing "two disjoint chains → two components"
    (is (= #{#{"a" "b"} #{"c" "d"}} (g/components [["a" "b"] ["c" "d"]])))
    (is (= 2 (g/component-count [["a" "b"] ["c" "d"]]))))
  (testing "a connected chain → one component"
    (is (= 1 (g/component-count [["a" "b"] ["b" "c"]])))))

(deftest betweenness-chokepoint
  (testing "the middle node of a→b→c is the sole broker (CB=1)"
    (let [cb (g/betweenness [["a" "b"] ["b" "c"]])]
      (is (== 1.0 (get cb "b")))
      (is (== 0.0 (get cb "a")))
      (is (== 0.0 (get cb "c")))))
  (testing "diamond a→{b,c}→d splits broker credit evenly"
    (let [cb (g/betweenness [["a" "b"] ["a" "c"] ["b" "d"] ["c" "d"]])]
      (is (== 0.5 (get cb "b")))
      (is (== 0.5 (get cb "c"))))))

(defn -main [& _]
  (let [{:keys [fail error]} (run-tests 'etzhayyim.kotoba.test-graph)]
    (System/exit (if (pos? (+ fail error)) 1 0))))
