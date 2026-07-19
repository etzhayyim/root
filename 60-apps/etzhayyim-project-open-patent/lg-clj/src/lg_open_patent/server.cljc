(ns lg-open-patent.server
  "lg-open-patent dispatch surface — clj port of `lg/lg_open_patent/server.py`
  (ADR-2606280030).

  The Python file is a FastAPI app exposing:
    GET  /ok /health      → liveness / readiness
    POST /runs            → invoke graph synchronously
    POST /runs/stream     → SSE event stream
    POST /xrpc/{nsid}     → XRPC shim (NSID → graph mapping)
    GET  /threads/{tid}/state → latest checkpoint values

  This namespace ports the ROUTING + graph registry (GRAPHS / NSID-MAP) and the
  invoke/serialize logic as plain clj functions (`ok`, `health`, `dispatch-run`,
  `dispatch-xrpc`). Wrapping these in a concrete HTTP server (org.httpkit.server)
  is the deployment layer's job — the graphs + dispatch are the load-bearing port.
  The Python FastAPI server (`../lg/`) remains the deployed runtime and COEXISTS.

  NSID namespace: com.etzhayyim.apps.openPatent.*
  Auth: optional LG_API_KEY env enforces x-api-key on /runs (parity with Python)."
  (:require [langgraph.graph :as g]
            [lg-open-patent.graphs.health :as health]
            [lg-open-patent.graphs.ingest-multi :as ingest-multi]
            [lg-open-patent.graphs.synthesize-invention :as synth]))

(def GRAPHS
  {"health"               health/GRAPH
   "ingest_multi"         ingest-multi/GRAPH
   "synthesize_invention" synth/GRAPH})

(def NSID-MAP
  {"com.etzhayyim.apps.openPatent.ingestMulti"        "ingest_multi"
   "com.etzhayyim.apps.openPatent.synthesizeInvention" "synthesize_invention"})

(def version "0.1.0")

(def ^:dynamic *api-key* "")

(defn check-api-key
  "Mirrors server._require_api_key: if LG_API_KEY is set, x-api-key must match."
  [x-api-key]
  (when (and (seq *api-key*) (not= x-api-key *api-key*))
    {:status 401 :body {:error "invalid x-api-key"}}))

(defn- run-graph [graph input]
  (try
    {:status 200 :body (g/invoke graph (or input {}))}
    (catch #?(:clj Exception :cljs :default) e
      {:status 500 :body {:error (let [m (str #?(:clj (.getMessage e) :cljs e))]
                                   (subs m 0 (min 300 (count m))))}})))

(defn ok
  "GET /ok → {:ok true :graphs [...] :version ...} (parity with server.ok)."
  []
  {:status 200 :body {:ok true :graphs (vec (keys GRAPHS)) :version version}})

(defn health
  "GET /health → {:ok true} (clj twin has no checkpointer; liveness only)."
  []
  {:status 200 :body {:ok true}})

(defn dispatch-run
  "POST /runs body → {:status :body}. body keys: :assistant_id :input.
  Enforces the optional x-api-key (pass via opts {:x-api-key ...})."
  ([body] (dispatch-run body {}))
  ([body {:keys [x-api-key]}]
   (or (check-api-key x-api-key)
       (let [aid   (or (:assistant_id body) "")
             graph (get GRAPHS aid)]
         (if (nil? graph)
           {:status 404 :body {:error (str "unknown graph: " aid)}}
           (run-graph graph (or (:input body) {})))))))

(defn dispatch-xrpc
  "POST /xrpc/{nsid} body → {:status :body}. NSID mapped to a graph; body is the
  graph input (minus :threadId). /xrpc is unauthenticated (parity with Python)."
  [nsid body]
  (let [gname (get NSID-MAP nsid)]
    (if (nil? gname)
      {:status 404 :body {:error (str "unknown NSID: " nsid)}}
      (let [input (dissoc (or body {}) :threadId)
            res   (run-graph (get GRAPHS gname) input)]
        (if (= 200 (:status res))
          {:status 200 :body (merge {:ok true} (:body res))}
          res)))))
