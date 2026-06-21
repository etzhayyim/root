(ns etzhayyim.explorer.coverage-test
  "Coverage for the pure helpers that the view-level namespaces depend on:
   the router, the node-graph rendering helpers, the Datom snapshot/query
   functions, and the aliveness axis scoring."
  (:require [cljs.test :refer-macros [deftest is testing]]
            [etzhayyim.explorer.router :as router]
            [etzhayyim.explorer.nodes.graph :as g]
            [etzhayyim.explorer.chain.datom :as d]
            [etzhayyim.explorer.organism.aliveness :as a]))

;; ── router ──────────────────────────────────────────────────────────────────
(deftest router-path->view
  (testing "each path maps to its view; unknown + nil default to :organism"
    (is (= :organism (router/path->view "/")))
    (is (= :organism (router/path->view "/organism")))
    (is (= :explorer (router/path->view "/explorer")))
    (is (= :nodes (router/path->view "/nodes")))
    (is (= :organism (router/path->view nil)))
    (is (= :organism (router/path->view "/does-not-exist")))))

;; ── node graph rendering helpers ────────────────────────────────────────────
(deftest graph-reflex-color
  (testing "reflex → colour, case-insensitive, with a gold fallback for unknown"
    (is (= "var(--leaf)" (g/reflex-color "green")))
    (is (= "var(--leaf)" (g/reflex-color "GREEN")))
    (is (= "var(--clay)" (g/reflex-color "red")))
    (is (= "var(--absent)" (g/reflex-color "absent")))
    (is (= "var(--gold)" (g/reflex-color "timeout")))
    (is (= "var(--gold)" (g/reflex-color nil)))))

(deftest graph-node-radius
  (testing "radius grows with score+cells but is capped at 14"
    (is (<= 3 (g/node-radius {:score 0 :cells 0})))
    (is (= 14 (g/node-radius {:score 100 :cells 100})))
    (is (< (g/node-radius {:score 0 :cells 0})
           (g/node-radius {:score 20 :cells 5})))))

;; ── Datom snapshot + query helpers ──────────────────────────────────────────
(def ^:private txs
  [{:tx/id 1 :tx/count 2
    :tx/datoms [[":db/add" "e1" ":k/a" "v1"]
                [":db/add" "e1" ":k/a" "v2"]]}
   {:tx/id 2 :tx/count 1
    :tx/datoms [[":db/add" "e2" ":k/b" "x"]]}])

(deftest datom-materialize-eavt-multivalue
  (testing "repeated (e,a) accumulates into a vector (multi-valued EAVT)"
    (let [eavt (d/materialize-eavt txs)]
      (is (= ["v1" "v2"] (get-in eavt ["e1" ":k/a"])))
      (is (= "x" (get-in eavt ["e2" ":k/b"])))
      (is (= ["e1" "e2"] (d/entities eavt))))))

(deftest datom-query-and-attributes
  (testing "query by attribute, optionally filtered by value"
    (is (= #{["e1" "v1"] ["e1" "v2"]} (set (d/query txs {:attr ":k/a"}))))
    (is (= [["e1" "v2"]] (d/query txs {:attr ":k/a" :value "v2"}))))
  (testing "attributes lists the distinct attribute names"
    (is (= [":k/a" ":k/b"] (d/attributes txs)))))

(deftest datom-snapshot-add-and-retract
  (testing "a retract op removes the attribute in tx order"
    (let [snap [["e" ":k/a" "v" 1 :add]
                ["e" ":k/b" "y" 1 :add]
                ["e" ":k/a" "v" 2 :retract]]
          eavt (d/materialize-snapshot snap)]
      (is (nil? (get-in eavt ["e" ":k/a"])))
      (is (= "y" (get-in eavt ["e" ":k/b"])))))
  (testing "entities-where can filter by an exact value"
    (let [eavt (d/materialize-snapshot [["e1" ":k/c" "on" 1 :add]
                                        ["e2" ":k/c" "off" 1 :add]])]
      (is (= 2 (count (d/entities-where eavt ":k/c"))))
      (is (= ["e1"] (mapv first (d/entities-where eavt ":k/c" "on")))))))

;; ── aliveness scoring ───────────────────────────────────────────────────────
(deftest aliveness-in-band
  (is (true? (a/in-band? :C 0.4)))
  (is (false? (a/in-band? :C 0.05)))
  (is (false? (a/in-band? :C nil))))

(deftest aliveness-axis-scores
  (testing "axis scores read from vitals :axes, else nil per axis"
    (let [scored (a/axis-scores {:vitals {:axes {:autopoiesis 9 :metabolism 6}}})
          by-key (into {} (map (juxt :key identity) scored))]
      (is (= 10 (count scored)))
      (is (= 9 (:score (by-key :autopoiesis))))
      (is (= 6 (:score (by-key :metabolism))))
      (is (nil? (:score (by-key :sanctify)))))
    (testing "no vitals → every axis nil but all 10 axes present"
      (let [scored (a/axis-scores {:vitals nil})]
        (is (= 10 (count scored)))
        (is (every? #(nil? (:score %)) scored))))))
