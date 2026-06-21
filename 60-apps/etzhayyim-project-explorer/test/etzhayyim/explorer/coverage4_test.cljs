(ns etzhayyim.explorer.coverage4-test
  "Coverage for the derived state subscriptions (the kotoba-Datom query paths
   that back /nodes) and the force-layout bounds — exercising the private
   classify / vitals->node helpers via the public subs."
  (:require [cljs.test :refer-macros [deftest is testing]]
            [re-frame.core :as rf]
            [kotoba.datom :as kd]
            [etzhayyim.explorer.nodes.graph :as g]
            [etzhayyim.explorer.state]))

;; ── /nodes cells + summary, derived by querying a vitals EAVT snapshot ──────
(def ^:private vitals-eavt
  ;; three actors that classify alive / dormant / stub (etzhayyim.vitals rule)
  [["v/alive" :vitals.actor/name "alive" 1 :add]
   ["v/alive" :vitals.actor/cells 12 1 :add]
   ["v/alive" :vitals.clj/reflex "green" 1 :add]
   ["v/alive" :vitals.actor/integrates 3 1 :add]
   ["v/alive" :vitals.atproto/bsky-post true 1 :add]
   ["v/alive" :vitals.actor/in-degree 1 1 :add]
   ["v/alive" :vitals.score/actor 10 1 :add]
   ["v/dorm" :vitals.actor/name "dorm" 1 :add]
   ["v/dorm" :vitals.clj/reflex "green" 1 :add]
   ["v/dorm" :vitals.actor/integrates 0 1 :add]
   ["v/dorm" :vitals.atproto/bsky-post false 1 :add]
   ["v/stub" :vitals.actor/name "stub" 1 :add]
   ["v/stub" :vitals.clj/reflex "absent" 1 :add]
   ["v/stub" :vitals.actor/integrates 0 1 :add]
   ["v/stub" :vitals.clj/port-ratio 0.0 1 :add]
   ["v/stub" :vitals.atproto/bsky-post false 1 :add]])

(deftest nodes-cells-and-summary
  (rf/dispatch-sync [:resource/ok :vitals vitals-eavt])
  (let [cells @(rf/subscribe [:nodes/cells])
        by-id (into {} (map (juxt :id identity) cells))
        summary @(rf/subscribe [:nodes/summary])]
    (testing "every named vitals entity becomes a node with derived class"
      (is (= 3 (count cells)))
      (is (= "alive" (:class (by-id "alive"))))
      (is (= "dormant" (:class (by-id "dorm"))))
      (is (= "stub" (:class (by-id "stub")))))
    (testing "reflex is normalised to a name string the graph can colour"
      (is (= "green" (:reflex (by-id "alive")))))
    (testing "summary folds the class frequencies"
      (is (= {:cells 3 :alive 1 :dormant 1 :stub 1} summary)))))

;; ── /nodes census, parsed + chain-verified + queried from a Datom log ───────
(def ^:private census-datoms
  [[":db/add" "census.x" ":census/tier" "x"]
   [":db/add" "census.x" ":census/count" 5]
   [":db/add" "census.x" ":census/source" "demo"]])

(def ^:private census-log
  (str ";; census log header\n"
       "{:tx/id 1 :tx/prev \"\" :tx/cid " (pr-str (kd/tx-cid census-datoms ""))
       " :tx/count 3 :tx/datoms " (pr-str census-datoms) "}\n"))

(deftest census-derivation
  (rf/dispatch-sync [:resource/ok :census-log census-log])
  (let [c @(rf/subscribe [:census])]
    (testing "the census commit-log chain verifies (real recomputed CID)"
      (is (true? (:verified c))))
    (testing "querying :census/tier yields the tier rows"
      (is (= [{:tier "x" :count 5 :source "demo"}] (:tiers c))))))

;; ── force-layout bounds ─────────────────────────────────────────────────────
(deftest layout-stays-in-bounds
  (testing "every laid-out node sits inside the svg viewBox"
    (let [nodes (mapv (fn [i] {:id (str "n" i) :score (* i 7) :cells (mod i 5)
                               :reflex "green" :class "dormant"})
                      (range 30))
          pos (g/layout nodes)]
      (is (= 30 (count pos)))
      (is (every? (fn [[_ {:keys [x y]}]]
                    (and (<= 0 x 640) (<= 0 y 480)))
                  pos)))))
