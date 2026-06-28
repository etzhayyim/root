(ns lg-karma.graphs
  "lg-karma StateGraph factory — clj port of the two graph builders in
  `lg/lg_karma/server.py` (`_make_single_node_graph` + `_make_health_graph`),
  ADR-2606280030.

  Every karma task is a STATELESS single-node graph with identical topology:

      START → execute → END

  The `execute` node reads the request kwargs from `:input`, calls the injected
  handler (lg-karma.handlers/*handlers*), and folds either `{:result …}` (handler
  output) or `{:error …}` (handler threw) into state — byte-for-byte the same
  contract as the python `_node` (return {\"result\": …} | {\"error\": str(exc)[:300]}).

  No checkpointer / no RetryPolicy: the python graphs are `total=False` stateless
  request-response graphs with no postgres checkpointer, so nothing is dropped.
  (langgraph-clj has no RetryPolicy; the python graphs declare none either.)"
  (:require [langgraph.graph :as g]
            [lg-karma.handlers :as h]))

;; ── single-node task graph (≡ _make_single_node_graph) ──────────────────────

(defn execute-node
  "The `execute` node for task graph `name`. Resolves the handler at invoke time
  (so a `binding` of *handlers* swaps behaviour without rebuilding the graph)."
  [name]
  (fn [state]
    (let [kwargs  (or (:input state) {})
          handler (h/handler-for name)]
      (try
        (if handler
          {:result (handler kwargs)}
          {:error (str "no handler: " name)})
        (catch #?(:clj Exception :cljs :default) e
          {:error (h/clip (#?(:clj .getMessage :cljs ex-message) e) 300)})))))

(defn single-node-graph
  "Compile a stateless task StateGraph (START → execute → END) for `name`."
  [name]
  (-> (g/state-graph)
      (g/add-node :execute (execute-node name))
      (g/set-entry-point :execute)
      (g/set-finish-point :execute)
      (g/compile-graph)))

;; ── health graph (≡ _make_health_graph) ─────────────────────────────────────

(defn ping-node [_state]
  {:result {:status "ok" :service "lg-karma"}})

(defn health-graph
  "Compile the health StateGraph (START → ping → END)."
  []
  (-> (g/state-graph)
      (g/add-node :ping ping-node)
      (g/set-entry-point :ping)
      (g/set-finish-point :ping)
      (g/compile-graph)))

(def HEALTH (health-graph))
