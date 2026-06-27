(ns lg-pregel.graphs.projector-ops
  "pregel `projector_ops` graph — clj twin of
  `kotodama.projector.ops:build_ops_graph` (ADR-2606280030).

  NOTE: `projector_ops` is registered in the Python `server.py` GRAPHS map but is
  NOT declared in `langgraph.json` nor in that file's `_EXPECTED_GRAPHS` test set
  (a pre-existing drift in the Python app). This twin faithfully mirrors the
  *server registry* (which includes projector_ops); see `lg-pregel.smoke-test`
  for the documented drift. External `kotodama` impl is non-vendored; INJECTABLE
  seam below."
  (:require [langgraph.graph :as g]))

(def ^:dynamic *step*
  (fn [state] (assoc state :graph "projector_ops" :ok true)))

(defn node-step [state] (*step* state))

(defn build
  "Compile the projector_ops StateGraph (START → step → END)."
  []
  (-> (g/state-graph)
      (g/add-node :step node-step)
      (g/set-entry-point :step)
      (g/set-finish-point :step)
      (g/compile-graph)))

(def GRAPH (build))
