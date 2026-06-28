(ns lg-organism.graph
  "Single-node StateGraph factory — faithful clj port of the `_make_*_graph`
  helpers in `lg/lg_organism/server.py` (ADR-2606280030).

  The Python server builds every organism task as a one-node LangGraph:

      START → execute → END

  where `execute` pulls kwargs from `state[\"input\"]`, calls the worker handler,
  and merges back `{result: ...}` on success or `{error: ...}` on failure. The
  health graph is the same shape with a `ping` node returning a fixed liveness
  map. This namespace reproduces that topology on `io.github.com-junkawasaki/
  langgraph-clj` so the dispatch surface in `server.cljc` is graph-driven, not a
  bare fn table."
  (:require [langgraph.graph :as g]))

(defn- clip [s n]
  (let [s (str s)] (subs s 0 (min n (count s)))))

(defn single-node-graph
  "Compile a one-node StateGraph (START → execute → END) around `handler`.

  `handler` is a 1-arg fn of the input map. On a thrown exception the node
  merges `{:error <msg, clipped to 300>}` (mirrors the Python `except` arm);
  otherwise `{:result <handler return>}`. The node reads its kwargs from
  `(:input state)` exactly like `_make_single_node_graph`."
  [handler name]
  (-> (g/state-graph)
      (g/add-node :execute
                  (fn [state]
                    (try
                      {:result (handler (or (:input state) {}))}
                      (catch #?(:clj Exception :cljs :default) e
                        {:error (clip (#?(:clj .getMessage :cljs ex-message) e) 300)
                         :graph name}))))
      (g/set-entry-point :execute)
      (g/set-finish-point :execute)
      (g/compile-graph)))

(defn health-graph
  "Compile the liveness graph (START → ping → END). `ping` returns the fixed
  organism status map under :result (parity with `_make_health_graph`)."
  []
  (-> (g/state-graph)
      (g/add-node :ping (fn [_state]
                          {:result {:status "ok" :service "lg-organism"}}))
      (g/set-entry-point :ping)
      (g/set-finish-point :ping)
      (g/compile-graph)))
