(ns lg-pregel.graphs.projector-driver
  "pregel `projector_driver` graph — clj twin of
  `kotodama.projector.driver:build_driver_graph` (ADR-2606280030).

  Driven on a `*/15 * * * *` cron in the Python `langgraph.json`. External
  `kotodama` implementation is non-vendored; this twin keeps the registry entry +
  single-node actor containment behind an INJECTABLE seam."
  (:require [langgraph.graph :as g]))

(def ^:dynamic *step*
  (fn [state] (assoc state :graph "projector_driver" :ok true)))

(defn node-step [state] (*step* state))

(defn build
  "Compile the projector_driver StateGraph (START → step → END)."
  []
  (-> (g/state-graph)
      (g/add-node :step node-step)
      (g/set-entry-point :step)
      (g/set-finish-point :step)
      (g/compile-graph)))

(def GRAPH (build))
