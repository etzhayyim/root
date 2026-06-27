(ns lg-pregel.graphs.pregel-triage
  "pregel `pregel_triage` graph — clj twin of `kotodama.pregel.graph:build_graph`
  (ADR-2606280030).

  As with the other graphs in this app, the real implementation lives in the
  external (non-vendored) `kotodama` package; this twin keeps the registry entry
  and the single-node actor containment shape behind an INJECTABLE seam."
  (:require [langgraph.graph :as g]))

(def ^:dynamic *triage*
  (fn [state] (assoc state :graph "pregel_triage" :ok true)))

(defn node-triage [state] (*triage* state))

(defn build
  "Compile the pregel_triage StateGraph (START → triage → END)."
  []
  (-> (g/state-graph)
      (g/add-node :triage node-triage)
      (g/set-entry-point :triage)
      (g/set-finish-point :triage)
      (g/compile-graph)))

(def GRAPH (build))
