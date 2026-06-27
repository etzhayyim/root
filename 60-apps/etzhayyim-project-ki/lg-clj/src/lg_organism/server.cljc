(ns lg-organism.server
  "lg-organism dispatch surface — clj port of `lg/lg_organism/server.py`
  (ADR-2606280030). The Python file is a FastAPI app exposing:

    GET  /ok            → liveness {ok, graphs}
    GET  /health        → health graph result
    POST /runs          → invoke a graph by assistant_id
    POST /xrpc/{nsid}   → XRPC shim (NSID → graph), also GET

  This namespace ports the GRAPH REGISTRY (23 single-node organism graphs), the
  NSID→assistant map, and the invoke/serialize/elapsed logic as pure clj fns
  (`ok`, `health`, `dispatch-run`, `dispatch-xrpc`). An optional org.httpkit
  socket leg (`ring-handler` / `start!`) is provided behind requiring-resolve so
  every cljc ns still loads under bb without the http dep present.

  COEXIST: the DEPLOYED runtime is still the FastAPI pod (`lg/`, via
  langgraph.json/Dockerfile/Helm). This clj twin is additive and runs alongside
  until a human cuts over — it never disturbs the live pod."
  (:require [langgraph.graph :as g]
            [clojure.string :as str]
            [lg-organism.graph :as graph]
            [lg-organism.tasks :as tasks]
            [lg-organism.audit :as audit]))

;; ── graph registry (parity with server.py GRAPHS / langgraph.json) ──────────

(def ^:private task-graphs
  (into {}
        (for [nsid (keys tasks/*task-handlers*)]
          (let [assistant (tasks/nsid->assistant nsid)]
            [assistant
             (graph/single-node-graph
              ;; resolve the handler at invoke time so *task-handlers* swaps win
              (fn [input] ((get tasks/*task-handlers* nsid) input))
              assistant)]))))

(def GRAPHS
  "assistant-id → compiled single-node graph (+ the health graph)."
  (assoc task-graphs "health" (graph/health-graph)))

(def NSID-MAP
  "canonical XRPC NSID → assistant-id (parity with `_NSID_TO_ASSISTANT`)."
  (into {"com.etzhayyim.apps.organism.health" "health"}
        (for [nsid (keys tasks/*task-handlers*)]
          [nsid (tasks/nsid->assistant nsid)])))

;; ── invoke + serialize ──────────────────────────────────────────────────────

(defn- now-ns [] #?(:clj (System/nanoTime) :cljs (* 1e6 (.now js/Date))))

(defn- elapsed-s [t0]
  (/ (Math/round (* 1000.0 (/ (double (- (now-ns) t0)) 1.0e9))) 1000.0))

(defn- safe-json
  "Best-effort: keep JSON-serializable values, else stringify (parity with
  `_safe_json`). Under bb our worker results are plain maps already."
  [obj]
  #?(:clj (try
            (when-let [gen (requiring-resolve 'cheshire.core/generate-string)]
              (gen obj))
            obj
            (catch Exception _ (str obj)))
     :cljs obj))

(defn- invoke-graph
  "Invoke `graph` with {:input input}; return the merged state map."
  [graph input]
  (g/invoke graph {:input (or input {})}))

(defn- run [assistant graph input]
  (let [t0    (now-ns)
        state (invoke-graph graph input)
        secs  (elapsed-s t0)]
    (if-let [err (:error state)]
      (do (audit/record! assistant input "error")
          {:status 500 :body {:error err :elapsed_s secs}})
      (do (audit/record! assistant input "ok")
          {:status 200 :body {:output (safe-json (:result state)) :elapsed_s secs}}))))

;; ── endpoints (pure dispatchers) ────────────────────────────────────────────

(defn ok
  "GET /ok → {:ok true :graphs [...]}"
  []
  {:status 200 :body {:ok true :graphs (vec (sort (keys GRAPHS)))}})

(defn health
  "GET /health → the health graph's liveness map."
  []
  (let [state (invoke-graph (GRAPHS "health") {})]
    {:status 200 :body (or (:result state) {:status "ok"})}))

(defn dispatch-run
  "POST /runs body → {:status :body}. body keys: :assistant_id (default
  \"health\"), :input. Unknown assistant → 404 (parity with server.py)."
  [body]
  (let [aid   (or (:assistant_id body) "health")
        graph (get GRAPHS aid)]
    (if (nil? graph)
      {:status 404 :body {:detail (str "graph '" aid "' not found")}}
      (run aid graph (or (:input body) {})))))

(defn dispatch-xrpc
  "POST|GET /xrpc/{nsid} → {:status :body}. Unmapped NSID → 501, mapped-but-
  missing graph → 404 (exact parity with server.py's xrpc handlers)."
  [nsid body]
  (let [assistant (get NSID-MAP nsid)]
    (cond
      (nil? assistant) {:status 501 :body {:detail (str "NSID not mapped: " nsid)}}
      :else (let [graph (get GRAPHS assistant)]
              (if (nil? graph)
                {:status 404 :body {:detail (str "graph '" assistant "' not found")}}
                (run assistant graph (or body {})))))))

;; ── optional org.httpkit socket leg (deferred; live pod untouched) ──────────

(defn ring-handler
  "Ring handler over the pure dispatchers. JSON in/out via cheshire. Routes:
  GET /ok, GET /health, POST /runs, POST|GET /xrpc/{nsid}."
  [{:keys [request-method uri body headers]}]
  #?(:clj
     (let [parse (requiring-resolve 'cheshire.core/parse-string)
           gen   (requiring-resolve 'cheshire.core/generate-string)
           read-body (fn [] (try (when body (parse (slurp body) true)) (catch Exception _ nil)))
           {:keys [status body] :as _resp}
           (cond
             (and (= :get request-method) (= uri "/ok"))      (ok)
             (and (= :get request-method) (= uri "/health"))  (health)
             (and (= :post request-method) (= uri "/runs"))   (dispatch-run (read-body))
             (str/starts-with? uri "/xrpc/")
             (dispatch-xrpc (subs uri (count "/xrpc/"))
                            (when (= :post request-method) (read-body)))
             :else {:status 404 :body {:detail "not found"}})]
       {:status status
        :headers {"Content-Type" "application/json"}
        :body (gen body)})
     :cljs nil))

(defn start!
  "Start an org.httpkit server on `port` (default 8000). Requires httpkit on the
  classpath; intentionally NOT auto-started (the FastAPI pod is the live runtime)."
  ([] (start! 8000))
  ([port]
   #?(:clj (let [run-server (requiring-resolve 'org.httpkit.server/run-server)]
             (run-server ring-handler {:port port}))
      :cljs nil)))
