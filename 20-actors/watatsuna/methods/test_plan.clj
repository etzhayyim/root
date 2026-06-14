#!/usr/bin/env bb
;; Working Clojure port of methods/test_plan.py.
(ns watatsuna.methods.test-plan
  "Tests for the watatsuna 綿津綱 → watatsumi resilience plan (methods/plan.clj).

  Load-bearing invariant (G2 + watatsumi N8): the plan can ONLY add resilience —
  :lay-diverse-route / :pre-stage-repair / :monitor. NO interdiction/cut output by construction.

  Run:  bb --classpath 20-actors 20-actors/watatsuna/methods/test_plan.clj"
  (:require [watatsuna.methods.analyze :as a]
            [watatsuna.methods.plan :as p]
            [clojure.java.io :as io]
            [clojure.string :as str]
            [clojure.set :as set]
            [clojure.test :refer [deftest is run-tests]]))

(def ^:private this-file *file*)
(defn- seed []
  (-> this-file io/file .getAbsoluteFile .getParentFile .getParentFile
      (io/file "data" "seed-cable-graph.kotoba.edn")))
(def allowed #{:lay-diverse-route :pre-stage-repair :monitor})

(defn- plan []
  (let [g (a/classify (a/load-edn (seed)))
        an (a/analyze g)]
    [g an (p/build-plan g an)]))

(deftest plan-is-non-empty
  (let [[_ _ recs] (plan)]
    (is (pos? (count recs)))))

(deftest every-plan-kind-is-resilience-only
  (let [[_ _ recs] (plan)
        kinds (set (map :plan/kind recs))]
    (is (set/subset? kinds allowed) (str "non-resilience kind: " (set/difference kinds allowed)))))

(deftest no-interdiction-kind-representable
  (let [[_ _ recs] (plan)]
    (doseq [r recs]
      (let [k (name (:plan/kind r))]
        (is (not-any? #(str/includes? k %) ["cut" "sever" "interdict" "disable" "attack"]))))))

(deftest lay-diverse-route-targets-redundancy-gaps
  (let [[_ an recs] (plan)
        lay (filter #(= (:plan/kind %) :lay-diverse-route) recs)]
    (is (or (>= (count lay) (count (:redundancy-gap an))) (zero? (count (:redundancy-gap an)))))))

(deftest rendered-edn-marks-g2-invariant
  (let [[_ _ recs] (plan)
        edn (p/render-edn recs)]
    (is (str/includes? edn "redundancy + repair + monitor ONLY"))
    (is (not (str/includes? (str/lower-case edn) "interdiction")))))

(deftest rendered-md-states-watatsuna-knows-watatsumi-acts
  (let [[_ _ recs] (plan)
        md (p/render-md recs)]
    (is (str/includes? md "watatsuna knows"))
    (is (str/includes? md "watatsumi acts"))
    (is (str/includes? md "No interdiction output by construction"))))

(when (= *file* (System/getProperty "babashka.file"))
  (let [{:keys [fail error]} (run-tests 'watatsuna.methods.test-plan)]
    (System/exit (if (zero? (+ fail error)) 0 1))))
