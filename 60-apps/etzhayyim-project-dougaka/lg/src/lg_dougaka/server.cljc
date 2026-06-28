(ns lg-dougaka.server
  "lg-dougaka OSS server — clj twin of lg_dougaka/server.py (ADR-2606280030).

  HTTP surface (identical to the FastAPI original):
    POST /runs              → invoke a graph synchronously (LG_API_KEY-gated)
    POST /xrpc/{nsid}       → XRPC shim (NSID → graph mapping), unauthenticated
    GET  /ok  /health       → liveness / readiness

  NSID namespace: com.etzhayyim.apps.dougaka.*

  The HTTP routing/handlers are pure data fns ({:status :body}) so they can be
  unit-tested directly (the Python tests use FastAPI's TestClient). `-main`
  binds them to org.httpkit.server for a real deployment under bb."
  (:require [lg-dougaka.graphs.health :as health]
            [lg-dougaka.graphs.render :as render]
            [langgraph.graph :as g]
            [cheshire.core :as json]
            [clojure.string :as str]))

;; GRAPHS / NSID_MAP keyed on strings to match the wire (assistant_id / nsid).
(def GRAPHS
  {"health" health/GRAPH
   "render" render/GRAPH})

(def NSID-MAP
  {"com.etzhayyim.apps.dougaka.render" "render"})

(defn- api-key [] (or (System/getenv "LG_API_KEY") ""))

(defn check-api-key
  "Returns nil when authorized, or a 401 response map when the configured
  LG_API_KEY does not match the supplied x-api-key header."
  [x-api-key]
  (let [k (api-key)]
    (when (and (seq k) (not= x-api-key k))
      {:status 401 :body {:detail "invalid api key"}})))

(defn- serialize
  "Project a graph result into a JSON-serializable value (clj maps/vectors are
  already serializable; this is the structural analogue of the Python _serialize)."
  [obj] obj)

(defn health-handler
  "GET /ok | /health → {:ok true :graphs [...]}."
  []
  {:status 200 :body {:ok true :graphs (vec (keys GRAPHS))}})

(defn runs-handler
  "POST /runs — invoke GRAPHS[assistant_id] on the request input."
  [body]
  (let [assistant-id (get body "assistant_id" "")
        graph (get GRAPHS assistant-id)]
    (if (nil? graph)
      {:status 404 :body {:error (str "unknown graph: " assistant-id)}}
      (let [input (or (get body "input") (get body "inputs") {})]
        (try
          {:status 200 :body (serialize (g/invoke graph input))}
          (catch Exception e
            {:status 500 :body {:error (subs (str (.getMessage e)) 0 (min 300 (count (str (.getMessage e)))))}}))))))

(defn xrpc-handler
  "POST /xrpc/{nsid} — map NSID → graph and invoke it on the request body."
  [nsid body]
  (let [graph-name (get NSID-MAP nsid)]
    (if (nil? graph-name)
      {:status 404 :body {:error (str "unknown nsid: " nsid)}}
      (let [graph (get GRAPHS graph-name)]
        (try
          {:status 200 :body (serialize (g/invoke graph body))}
          (catch Exception e
            {:status 500 :body {:error (subs (str (.getMessage e)) 0 (min 300 (count (str (.getMessage e)))))}}))))))

;; ── httpkit wiring (deployment entry point) ─────────────────────────────────
(defn- json-response [{:keys [status body]}]
  {:status status
   :headers {"Content-Type" "application/json"}
   :body (json/generate-string body)})

(defn- read-json-body [req]
  (let [b (:body req)]
    (if (and b (not (string? b)))
      (try (json/parse-string (slurp b)) (catch Exception _ {}))
      (try (json/parse-string (or b "{}")) (catch Exception _ {})))))

(defn handler
  "Ring-style request handler dispatching the dougaka HTTP surface."
  [{:keys [request-method uri headers] :as req}]
  (let [uri (or uri "/")]
    (cond
      (and (= request-method :get) (#{"/ok" "/health"} uri))
      (json-response (health-handler))

      (and (= request-method :post) (= uri "/runs"))
      (json-response (or (check-api-key (get headers "x-api-key" ""))
                         (runs-handler (read-json-body req))))

      (and (= request-method :post) (str/starts-with? uri "/xrpc/"))
      (json-response (xrpc-handler (subs uri (count "/xrpc/")) (read-json-body req)))

      :else
      (json-response {:status 404 :body {:error "not found"}}))))

(defn -main [& _args]
  (let [server (requiring-resolve 'org.httpkit.server/run-server)
        port (Integer/parseInt (or (System/getenv "PORT") "8000"))]
    (server handler {:port port})
    (println (str "lg-dougaka listening on :" port " graphs=" (vec (keys GRAPHS))))
    @(promise)))
