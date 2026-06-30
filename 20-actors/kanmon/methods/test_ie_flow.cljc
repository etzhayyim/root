#!/usr/bin/env bb
;; kanmon 関門 — ie-flow embedding tests (energy-flow → wellbecoming, SHARED metrics).
;; Run: bb -cp "20-actors:70-tools/src" 20-actors/kanmon/methods/test_ie_flow.cljc
(ns kanmon.methods.test-ie-flow
  (:require [kanmon.methods.ie-flow :as ief]
            [kanmon.methods.analyze :as az]
            [kanmon.methods.kanmon-edn :as ke]
            [clojure.string :as str]
            [clojure.test :refer [deftest is run-tests]]))

(def seed-path "20-actors/kanmon/kotoba/seed.edn")
(defn- rows [] (get (az/assess (ke/exams seed-path)) "exams"))

(deftest events-well-formed
  (let [evs (ief/flow-events (rows))]
    (is (= 12 (count evs)) "one event per exam")
    (is (every? #(and (:source %) (:target %) (:type %)) evs))
    (is (every? :agent? evs) "kanmon is the agent doing the rectification")
    (is (every? #(>= (double (:value %)) 0.0) evs))
    (is (every? #(= "kanmon" (:actor %)) evs))
    (is (every? :sink evs) "each opening exports to a downstream wellbecoming actor")))

(deftest order-is-added-and-flow-pays
  (let [st (ief/flow-state (rows))]
    (is (pos? (:order-index st)) "kanmon RECTIFIES scattered barrier-load → positive order-index")
    (is (pos? (:net-gain st)) "the information-energy flow pays for itself (Φ>0)")
    (is (not (:parasitic? st)) "non-parasitic — exports more wellbecoming-order than it consumes")))

(deftest eta-export-exceeds-consume
  (let [m (ief/metrics (rows))]
    (is (> (double (:eta m)) 1.0) "η = exported wellbecoming-order ÷ consumed ≫ 1 (a 利得)")
    (is (< (:h-after m) (:h-before m)) "entropy DROPS — scattered barrier-load concentrated onto openings")
    (is (:wellbecoming-served m) "the flow serves wellbecoming")))

(deftest destake-exports-most-wellbecoming
  ;; the deepest-leverage opening carries the highest wellbecoming weight
  (is (= 1.0 (get ief/route->wb-weight :destake)) ":destake exports the most wellbecoming-order")
  (is (> (get ief/route->wb-weight :open-pathway) (get ief/route->wb-weight :monitor))
      ":monitor exports the least"))

(deftest viz-model-is-a-system-of-systems
  (let [vm (ief/viz-model (rows))
        cols (:columns vm)
        ids (set (mapcat (fn [c] (map :id (:nodes c))) cols))]
    (is (= 4 (count cols)) "sources → gate → openings → sinks")
    (is (= ["sources" "gate" "openings" "sinks"] (map :id cols)))
    (doseq [l (:links vm)]
      (is (and (ids (:from l)) (ids (:to l))) (str "link resolves: " (:from l) "→" (:to l))))
    (is (contains? ids "shiori") "wellbecoming sink shiori present")
    (is (contains? ids "shinan") "wellbecoming sink shinan present")))

(deftest html-is-self-contained
  (let [html (ief/render-html (ief/viz-model (rows)))]
    (is (str/includes? html "<canvas"))
    (is (str/includes? html "order-index"))
    (is (str/includes? html "system of systems"))
    (is (str/includes? html "整流"))
    (is (not (str/includes? html "http://")) "no external fetch")
    (is (not (str/includes? html "https://")) "no external fetch")))

(when (= *file* (System/getProperty "babashka.file"))
  (let [{:keys [fail error]} (run-tests 'kanmon.methods.test-ie-flow)]
    (when (pos? (+ fail error)) (System/exit 1))))
