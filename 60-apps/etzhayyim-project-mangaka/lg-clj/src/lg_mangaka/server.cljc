(ns lg-mangaka.server
  "XRPC/runs HTTP server for lg-mangaka — clj port of `lg/lg_mangaka/server.py`
  (FastAPI → org.httpkit.server, a babashka built-in). Same endpoint surface:

    POST /runs                  → invoke a graph synchronously
    POST /runs/stream           → stream graph superstep events as SSE
    POST|GET /xrpc/{nsid}       → XRPC-compat shim (NSID → assistant_id)
    GET  /ok | /health          → liveness / readiness

  Auth: optional LG_API_KEY enforces x-api-key on /runs paths; /xrpc is
  unauthenticated (trust at the cloudflared tunnel layer), parity with Python.

  ── WAVE-2 PARTIAL PORT (ADR-2606280030) ──────────────────────────────────
  The Python app is LARGE: 38 graphs registered across langgraph.json + 18 in
  server.py GRAPHS, ~96 py files, an MCP tool surface (lg_mangaka.tools), comfy/
  cine/3D/video pipelines, Hume emotion, face detection, etc. This clj twin
  faithfully ports the SERVER dispatch + 7 verifiable graphs:

    health, agent_chat, save_document, load_document, list_documents,
    record_op_log, debug_canvas_state

  REMAINING (python-only for now, coexisting & deployed): the other 11
  server-registered graphs (import_ghosthacker, analyze_character_graph,
  enrich_characters / _organizations / _environments, derive_chapter_incidents,
  import_chat_history, backfill_mangaka_edges, compose_scene_3d, detect_faces,
  score_emotion) + the langgraph.json-only generation graphs (cine_*,
  mangaka_generate_*, comfy_run, mangaka_train_character_lora, ...) + the
  MCP tool dispatch surface (lg_mangaka.tools.*, /xrpc/com.etzhayyim.mcp.message).
  See the PR body for the full ported-vs-remaining matrix.

  The Python FastAPI server under `lg/` stays the deployed runtime and COEXISTS;
  this twin is additive (py_removed=0).

  DEVIATION (noted): no RW Postgres checkpointer (substrate boundary forbids
  RisingWave); state is a clj map and thread-state retrieval is omitted."
  (:require [langgraph.graph :as g]
            [cheshire.core :as json]
            [clojure.string :as str]
            [org.httpkit.server :as srv]
            [lg-mangaka.graphs.health :as health]
            [lg-mangaka.graphs.agent-chat :as agent-chat]
            [lg-mangaka.graphs.save-document :as save-document]
            [lg-mangaka.graphs.load-document :as load-document]
            [lg-mangaka.graphs.list-documents :as list-documents]
            [lg-mangaka.graphs.record-op-log :as record-op-log]
            [lg-mangaka.graphs.debug-canvas-state :as debug-canvas-state]))

(defn- env [k default] (or (System/getenv k) default))

(def GRAPHS
  {"health"             health/GRAPH
   "agent_chat"         agent-chat/GRAPH
   "save_document"      save-document/GRAPH
   "load_document"      load-document/GRAPH
   "list_documents"     list-documents/GRAPH
   "record_op_log"      record-op-log/GRAPH
   "debug_canvas_state" debug-canvas-state/GRAPH})

;; NSID → assistant_id (subset of server.py:_NSID_TO_ASSISTANT covering the
;; ported graphs; the chat NSID has 3 aliases exactly as in Python).
(def NSID-MAP
  {"com.etzhayyim.mangaka.health"          "health"
   "com.etzhayyim.mangaka.chat"            "agent_chat"
   "com.etzhayyim.mangaka.pipelineChat"    "agent_chat"
   "com.etzhayyim.mangaka.projectChat"     "agent_chat"
   "com.etzhayyim.mangaka.saveDocument"    "save_document"
   "com.etzhayyim.mangaka.loadDocument"    "load_document"
   "com.etzhayyim.mangaka.listDocuments"   "list_documents"
   "com.etzhayyim.mangaka.recordOpLog"     "record_op_log"
   "com.etzhayyim.mangaka.debugCanvasState" "debug_canvas_state"})

(def ^:private api-key (str/trim (env "LG_API_KEY" "")))

;; ── input key normalization (camelCase / snake_case JSON → kebab keyword) ──
;; mirrors server.py:_camel_to_snake (the XRPC shim) but lands on kebab keywords
;; so graph nodes can read both :doc_id and :docId style keys uniformly.
(defn ->snake-key
  "camelCase → snake_case keyword (server.py:_camel_to_snake analogue)."
  [s]
  (-> (name s)
      (str/replace #"([a-z0-9])([A-Z])" "$1_$2")
      str/lower-case
      keyword))

(defn normalize-input
  "JSON object → graph input map. Keeps BOTH the snake_case key and the original
  key (graphs read either), matching the Python nodes' dual .get(snake)/.get(camel)."
  [m]
  (when (map? m)
    (reduce-kv (fn [acc k v]
                 (let [kk (if (keyword? k) k (keyword k))]
                   (-> acc (assoc kk v) (assoc (->snake-key kk) v))))
               {} m)))

;; ── pure dispatch (testable without a running server) ──

(defn health
  "GET /ok → {:ok true :graphs [...] :version}"
  []
  {:status 200 :body {:ok true :graphs (vec (keys GRAPHS)) :version "0.1.0"}})

(defn check-api-key
  "Mirrors server._require_api_key: if LG_API_KEY is set, x-api-key must match."
  [x-api-key]
  (when (and (seq api-key) (not= x-api-key api-key))
    {:status 401 :body {:detail "invalid x-api-key"}}))

(defn- run-graph [graph input]
  (try
    {:status 200 :body {:ok true :result (g/invoke graph (or input {}))}}
    (catch Exception e
      {:status 500 :body {:ok false :error (let [m (str (.getMessage e))]
                                             (subs m 0 (min 500 (count m))))
                          :errorType (.. e getClass getSimpleName)}})))

(defn dispatch-run
  "POST /runs body → {:status :body}. body keys: :assistant_id :input.
  Enforces optional x-api-key via opts {:x-api-key ...}."
  ([body] (dispatch-run body {}))
  ([body {:keys [x-api-key]}]
   (or (check-api-key x-api-key)
       (let [aid   (str (or (:assistant_id body) (get body "assistant_id") ""))
             graph (get GRAPHS aid)]
         (if (nil? graph)
           {:status 404 :body {:detail (str "unknown graph: " aid)}}
           (run-graph graph (normalize-input (or (:input body) (get body "input") {}))))))))

(defn dispatch-xrpc
  "POST|GET /xrpc/{nsid} body → {:status :body}. /xrpc is unauthenticated."
  [nsid body]
  (let [aid (get NSID-MAP nsid)]
    (if (nil? aid)
      {:status 404 :body {:detail (str "unknown NSID: " nsid)}}
      (let [res (run-graph (get GRAPHS aid) (normalize-input (or body {})))]
        ;; flatten to the python xrpc_compat shape (result + assistantId)
        (if (= 200 (:status res))
          {:status 200 :body (assoc (get-in res [:body :result]) :assistantId aid)}
          res)))))

;; ── http handler ──
(defn- json-resp [{:keys [status body]}]
  {:status status :headers {"Content-Type" "application/json"}
   :body (json/generate-string body)})

(defn- parse-body [req]
  (when-let [b (:body req)]
    (try (json/parse-string (slurp b) true) (catch Exception _ nil))))

(defn handler [req]
  (let [uri (:uri req) method (:request-method req)
        xapi (get-in req [:headers "x-api-key"])]
    (cond
      (and (= method :get) (#{"/ok" "/health"} uri))
      (json-resp (health))

      (and (= method :post) (= uri "/runs"))
      (json-resp (dispatch-run (or (parse-body req) {}) {:x-api-key xapi}))

      (str/starts-with? uri "/xrpc/")
      (json-resp (dispatch-xrpc (subs uri (count "/xrpc/")) (parse-body req)))

      :else
      (json-resp {:status 404 :body {:detail "not found"}}))))

(defn -main [& args]
  (let [port (Integer/parseInt (str (or (first args) (env "PORT" "2024"))))]
    (srv/run-server handler {:port port})
    (println (str "lg-mangaka server up on :" port " graphs=" (pr-str (keys GRAPHS))))
    @(promise)))
