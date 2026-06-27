(ns lg-drive.graphs.health
  "lg-drive `health` graph — minimal liveness probe, as a langgraph-clj
  StateGraph. clj twin of lg_drive/graphs/health.py (ADR-2606280030).

  Same topology as the Python `langgraph.graph.StateGraph`: START → probe → END,
  one node returning {:ok :ts :version}. langgraph-clj loads under babashka."
  (:require [langgraph.graph :as g]))

(defn probe [_state]
  {:ok true
   :ts (System/currentTimeMillis)
   :version (or (System/getenv "LG_DRIVE_VERSION") "0.1.0")})

(def GRAPH
  (-> (g/state-graph)
      (g/add-node :probe probe)
      (g/set-entry-point :probe)
      (g/set-finish-point :probe)
      (g/compile-graph)))
