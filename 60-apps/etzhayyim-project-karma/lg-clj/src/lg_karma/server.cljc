(ns lg-karma.server
  "lg-karma HTTP server — clj port of `lg/lg_karma/server.py` (ADR-2606280030).

  FastAPI/uvicorn → org.httpkit.server (a babashka built-in); JSON → cheshire.
  Same endpoint surface:

    GET  /ok                 → {\"ok\": true}
    GET  /health             → health graph result {\"status\":\"ok\",\"service\":\"lg-karma\"}
    POST /runs               → invoke graph by assistant_id; {output, elapsed_s}
    POST /xrpc/{nsid:path}   → NSID → graph; body is the graph input
    GET  /xrpc/{nsid:path}   → NSID → graph; query params are the graph input

  GRAPHS = {\"health\" …} ∪ {task-name → single-node-graph} for all 45 tasks, built
  from `lg-karma.handlers/task-names` exactly like the python comprehension. The
  NSID→assistant map mirrors `_NSID_TO_ASSISTANT`.

  The graphs are stateless (no RW checkpointer — substrate boundary). The native
  task primitives live behind `lg-karma.handlers/*handlers*` (swap seam). The
  python `lg/` server remains the deployed runtime and COEXISTS (py_removed=0)."
  (:require [langgraph.graph :as lg]
            [cheshire.core :as json]
            [clojure.string :as str]
            [org.httpkit.server :as srv]
            [lg-karma.handlers :as h]
            [lg-karma.graphs :as graphs]))

;; ── graph registry (≡ GRAPHS) ───────────────────────────────────────────────

(def GRAPHS
  (into {"health" graphs/HEALTH}
        (map (fn [n] [n (graphs/single-node-graph n)]))
        h/task-names))

;; ── NSID → assistant map (≡ _NSID_TO_ASSISTANT) ─────────────────────────────

(def NSID-MAP
  (into {(h/nsid-for "health") "health"}
        (map (fn [n] [(h/nsid-for n) n]))
        h/task-names))

;; ── helpers ─────────────────────────────────────────────────────────────────

(defn- env [k default] (or (System/getenv k) default))

(defn- round3 [x] (/ (Math/round (* (double x) 1000.0)) 1000.0))

(defn- safe-json
  "≡ _safe_json: pass `obj` through if cheshire can encode it, else stringify."
  [obj]
  (try (json/generate-string obj) obj
       (catch Exception _ (str obj))))

(defn- invoke-timed
  "Invoke `graph` with {:input input}; return {:state .. :elapsed-s ..}."
  [graph input]
  (let [t0    (System/nanoTime)
        state (lg/invoke graph {:input (or input {})})
        el    (/ (- (System/nanoTime) t0) 1.0e9)]
    {:state state :elapsed-s (round3 el)}))

;; ── pure dispatch (testable without a running server) ───────────────────────

(defn run
  "POST /runs body → {:status n :body map}. body keys: assistant_id, input.
  Default assistant_id = \"health\" (≡ python). Unknown graph → 404."
  [body]
  (let [aid   (get body "assistant_id" "health")
        graph (get GRAPHS aid)]
    (if (nil? graph)
      {:status 404 :body {:detail (str "graph '" aid "' not found")}}
      (let [{:keys [state elapsed-s]} (invoke-timed graph (get body "input"))]
        (if (:error state)
          {:status 500 :body {:error (:error state) :elapsed_s elapsed-s}}
          {:status 200 :body {:output (safe-json (:result state)) :elapsed_s elapsed-s}})))))

(defn xrpc
  "POST|GET /xrpc/{nsid} input → {:status n :body map}. NSID → graph; `input` is
  the graph input (JSON body for POST, query params for GET).

  DEVIATION: the python server raises 501 for an unmapped NSID; this twin returns
  404 — matching both the python `tests/test_smoke.py` expectation AND the merged
  wave-1 twins (recap/webmk) which all use 404 for an unknown nsid."
  [nsid input]
  (let [gname (get NSID-MAP nsid)]
    (if (nil? gname)
      {:status 404 :body {:detail (str "NSID not mapped: " nsid)}}
      (let [{:keys [state elapsed-s]} (invoke-timed (get GRAPHS gname) input)]
        (if (:error state)
          {:status 500 :body {:error (:error state) :elapsed_s elapsed-s}}
          {:status 200 :body {:output (safe-json (:result state)) :elapsed_s elapsed-s}})))))

(defn health
  "GET /health → the health graph result (≡ python /health)."
  []
  (let [state (lg/invoke graphs/HEALTH {:input {}})]
    {:status 200 :body (or (:result state) {:status "ok"})}))

;; ── http handler (httpkit) ──────────────────────────────────────────────────

(defn- json-resp [{:keys [status body]}]
  {:status (or status 200)
   :headers {"Content-Type" "application/json"}
   :body (json/generate-string body)})

(defn- parse-body [req]
  (when-let [b (:body req)]
    (try (json/parse-string (slurp b)) (catch Exception _ nil))))

(defn- query->map [^String qs]
  (if (str/blank? qs)
    {}
    (into {} (for [pair (str/split qs #"&")
                   :let [[k v] (str/split pair #"=" 2)]
                   :when (seq k)]
               [k (or v "")]))))

(defn handler [req]
  (let [uri (:uri req) method (:request-method req)]
    (cond
      (and (= method :get) (= uri "/ok"))
      (json-resp {:status 200 :body {:ok true}})

      (and (= method :get) (= uri "/health"))
      (json-resp (health))

      (and (= method :post) (= uri "/runs"))
      (json-resp (run (or (parse-body req) {})))

      (str/starts-with? uri "/xrpc/")
      (let [nsid (subs uri (count "/xrpc/"))]
        (json-resp
         (case method
           :post (xrpc nsid (or (parse-body req) {}))
           :get  (xrpc nsid (query->map (:query-string req)))
           {:status 405 :body {:detail "method not allowed"}})))

      :else
      (json-resp {:status 404 :body {:detail "not found"}}))))

(defn -main [& args]
  (let [port (Integer/parseInt (or (first args) (env "PORT" "2024")))]
    (srv/run-server handler {:port port})
    (println (str "lg-karma server up on :" port
                  " — " (count GRAPHS) " graphs loaded"))
    @(promise)))
