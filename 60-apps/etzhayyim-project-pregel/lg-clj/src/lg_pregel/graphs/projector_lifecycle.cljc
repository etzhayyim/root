(ns lg-pregel.graphs.projector-lifecycle
  "pregel `projector_lifecycle` graph — clj twin of
  `kotodama.projector.graph:build_lifecycle_graph` (ADR-2606280030).

  External `kotodama` implementation is non-vendored; this twin keeps the
  registry entry + single-node actor containment behind an INJECTABLE seam."
  (:require [langgraph.graph :as g]))

(def ^:dynamic *step*
  (fn [state] (assoc state :graph "projector_lifecycle" :ok true)))

(defn node-step [state] (*step* state))

(defn build
  "Compile the projector_lifecycle StateGraph (START → step → END)."
  []
  (-> (g/state-graph)
      (g/add-node :step node-step)
      (g/set-entry-point :step)
      (g/set-finish-point :step)
      (g/compile-graph)))

(def GRAPH (build))
