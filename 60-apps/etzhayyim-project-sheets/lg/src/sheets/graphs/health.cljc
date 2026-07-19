(ns sheets.graphs.health
  "lg-sheets `health` graph — minimal liveness probe (clj port of
  lg_sheets/graphs/health.py) as a langgraph-clj StateGraph.

  Faithful topology: START -> probe -> END. The node returns {:ok :ts :version}.
  State is a clj map (the TypedDict _State); langgraph-clj loads under babashka."
  (:require [langgraph.graph :as g]))

(defn probe [state]
  {:ok true
   :ts (System/currentTimeMillis)
   :version (or (get-in state [:host-config :version]) "0.1.0")})

(defn build []
  (-> (g/state-graph)
      (g/add-node :probe probe)
      (g/set-entry-point :probe)
      (g/set-finish-point :probe)
      (g/compile-graph)))

(def graph (build))

(defn run
  "Invoke the health graph once; returns the final state map."
  ([] (run {}))
  ([input] (g/invoke graph input)))
