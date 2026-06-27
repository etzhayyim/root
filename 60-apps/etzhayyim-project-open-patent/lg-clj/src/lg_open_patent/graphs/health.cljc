(ns lg-open-patent.graphs.health
  "open-patent `health` graph — server liveness probe.

  Faithful clj port of `lg/lg_open_patent/graphs/health.py` (ADR-2606280030).
  Topology: START -> check -> END. The `check` node returns {:ok true}, exactly
  like the Python `_check`. langgraph-clj loads under babashka."
  (:require [langgraph.graph :as g]))

(defn node-check
  "Liveness node — mirrors health.py `_check`: returns {:ok true}."
  [_state]
  {:ok true})

(defn build
  "Compile the health StateGraph (START -> check -> END)."
  []
  (-> (g/state-graph)
      (g/add-node :check node-check)
      (g/set-entry-point :check)
      (g/set-finish-point :check)
      (g/compile-graph)))

(def GRAPH (build))
