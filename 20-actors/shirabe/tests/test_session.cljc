(ns shirabe.tests.test-session
  "shirabe — session orchestrator e2e (fixture fetcher + infer). kotoba-clj."
  (:require [clojure.test :refer [deftest is]]
            [clojure.edn :as edn]
            [clojure.java.io :as io]
            [shirabe.methods.session :as session]))

(def fx (edn/read-string (slurp (io/resource "shirabe/data/fixtures/shimada-aoyama.kotoba.edn"))))
(defn fixture-fetcher [_] (get-in fx [:search "*"]))
(def fixture-infer (with-meta (fn [_] (:answer fx)) {:model-id "fixture:gemma4@127.0.0.1:11434"}))

(deftest end-to-end
  (let [s (session/research (:question fx) fixture-fetcher fixture-infer (:asof fx))]
    (is (string? (:id s)))
    (is (= 16 (count (:id s))) "session id is a 16-hex content address")
    (is (seq (:evidence s)) "evidence retrieved")
    (is (= (:answer fx) (:answer (:result s))) "gemma4 answer threaded through")
    (is (= [1] (:citations (:result s))) "the fixture answer cites source [1]")
    (is (<= (:rounds s) session/max-rounds) "ReAct loop bounded (G5)")))

(deftest deterministic-id
  (let [a (session/research (:question fx) fixture-fetcher fixture-infer (:asof fx))
        b (session/research (:question fx) fixture-fetcher fixture-infer (:asof fx))]
    (is (= (:id a) (:id b)) "same (question, as-of) → same session id")))
