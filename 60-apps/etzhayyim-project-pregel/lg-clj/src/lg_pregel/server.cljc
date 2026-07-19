(ns lg-pregel.server
  "lg-pregel dispatch surface — clj port of `lg/lg_pregel/server.py`
  (ADR-2606280030). The Python file is a FastAPI app exposing:

    POST /runs                           → invoke a registered graph synchronously
    GET  /stats                          → triage stats (HITL)
    POST /threads/search                 → list pending gray-zone / draft items (HITL)
    GET  /threads/{thread_id}/state      → interrupt envelope for one item (HITL)
    POST /threads/{thread_id}/runs/stream→ submit human verdict (SSE response)
    GET  /health /ok                     → liveness
    GET  /graphs                         → list graph IDs

  This ns ports the GRAPHS registry + auth (`enforce-auth`) + all routing and
  envelope shaping as PURE functions, dispatched by `handle-request`
  (req {:method :path :headers :query :body} -> {:status :body}). Wrapping it in a
  concrete socket listener is the one infra leg left to deployment; `serve!`
  accepts an explicit org.httpkit.server capability for parity with the
  wave-1 twins, but the DEPLOYED runtime stays the FastAPI pod (`lg/`) and this
  twin COEXISTS additively (ADR-2606280030).

  HITL state + LLM are behind injectable seams (`lg-pregel.store/*store*`,
  `lg-pregel.murakumo/*llm-chat*`) — the actor swap pattern — so the substrate
  boundary (no RisingWave) and Murakumo loopback (ADR-2605215000) are honored
  without changing the routing."
  (:require #?(:clj [cheshire.core :as json])
            [clojure.string :as str]
            [langgraph.graph :as g]
            [lg-pregel.store :as store]
            [lg-pregel.graphs.outlook-triage :as outlook-triage]
            [lg-pregel.graphs.pregel-triage :as pregel-triage]
            [lg-pregel.graphs.projector-lifecycle :as projector-lifecycle]
            [lg-pregel.graphs.projector-driver :as projector-driver]
            [lg-pregel.graphs.projector-ops :as projector-ops]))

(def GRAPHS
  "Mirrors server.py GRAPHS (note: projector_ops is present in server.py's map but
  absent from langgraph.json — a pre-existing Python drift faithfully reflected)."
  {"outlook_triage"      outlook-triage/GRAPH
   "pregel_triage"       pregel-triage/GRAPH
   "projector_lifecycle" projector-lifecycle/GRAPH
   "projector_driver"    projector-driver/GRAPH
   "projector_ops"       projector-ops/GRAPH})

(def ^:dynamic *api-key* "")
(defn- now-ms [] #?(:clj (System/currentTimeMillis) :cljs (.now js/Date)))

(defn- clamp [v lo hi] (max lo (min hi v)))

(defn- ->int [v default]
  (try (int (cond (number? v) v
                  (and (string? v) (seq v)) (Long/parseLong (str/trim v))
                  :else default))
       (catch Exception _ default)))

;; ── auth (server.py _enforce_auth) ──────────────────────────────────────────

(defn enforce-auth
  "Returns nil when allowed, or a 401 response map. `exempt?` true bypasses (cron
  path, x-cron=1). Open when LG_PREGEL_API_KEY is unset (mirrors server.py)."
  ([x-api-key] (enforce-auth x-api-key false))
  ([x-api-key exempt?]
   (let [expected *api-key*]
     (cond
       exempt?                       nil
       (or (nil? expected) (= "" expected)) nil
       (and (seq x-api-key) (= x-api-key expected)) nil
       :else {:status 401 :body {:detail "x-api-key mismatch"}}))))

;; ── /health /ok /graphs ─────────────────────────────────────────────────────

(defn health []
  {:status 200 :body {:ok true :app "lg-pregel" :ts (now-ms)
                      :graphs (vec (keys GRAPHS))}})

(defn list-graphs []
  {:status 200 :body {:graphs (vec (keys GRAPHS))}})

;; ── /runs (server.py _runs) ─────────────────────────────────────────────────

(defn run
  "POST /runs body -> {:status :body}. graph from :graph | :assistant_id
  (default outlook_triage); 404 unknown; cron (x-cron=1) bypasses auth."
  [body {:keys [x-api-key x-cron]}]
  (or (enforce-auth x-api-key (= x-cron "1"))
      (let [gid   (or (:graph body) (:assistant_id body) "outlook_triage")
            graph (get GRAPHS gid)]
        (if (nil? graph)
          {:status 404 :body {:detail (str "unknown graph: " gid)}}
          (let [t0 (now-ms)]
            (try
              (let [result (g/invoke graph (or (:input body) {}))]
                {:status 200 :body {:ok true :graph gid
                                    :duration_ms (- (now-ms) t0)
                                    :result result}})
              (catch Exception e
                (let [m (str (.getMessage e))]
                  {:status 500 :body {:detail (subs m 0 (min 300 (count m)))}}))))))))

;; ── /stats (server.py _stats) ───────────────────────────────────────────────

(defn stats [days {:keys [x-api-key]}]
  (or (enforce-auth x-api-key)
      {:status 200 :body (store/call :get-all-stats (clamp (->int days 30) 1 365))}))

;; ── /threads/search (server.py _threads_search) ─────────────────────────────

(defn threads-search
  "POST /threads/search -> {:status :body[list]}. status!=interrupted → []. Gray +
  draft pending items merged, sorted by :updated_at desc, clamped to limit."
  [body {:keys [x-api-key]}]
  (or (enforce-auth x-api-key)
      (let [status (str (or (:status body) "interrupted"))]
        (if (not= status "interrupted")
          {:status 200 :body []}
          (let [limit (clamp (->int (:limit body) 50) 1 1000)
                gray  (store/call :list-pending-gray limit)
                draft (store/call :list-pending-drafts limit)
                combined (->> (concat gray draft)
                              (sort-by #(str (:updated_at %)))
                              reverse
                              (take limit)
                              vec)]
            {:status 200 :body combined})))))

;; ── /threads/{id}/state (server.py _thread_state) ───────────────────────────

(defn- draft-envelope [thread-id item]
  {:thread_id thread-id
   :status "interrupted"
   :interrupts
   [{:value {:tool_name "request_draft_approval"
             :question (str "返信下書き: " (or (:from_address item) ""))
             :context (str "送信元: " (or (:from_address item) "") "\n"
                           "件名: " (or (:subject item) ""))
             :options ["approve" "discard"]
             :meta {:type "reply_draft"
                    :draft_text (or (:draft_text item) "")
                    :from_address (or (:from_address item) "")
                    :subject (or (:subject item) "")}}}]})

(defn- gray-envelope [thread-id item]
  (let [from-addr (str (or (:from_address item) ""))
        reasons   (str (or (:triage_reasons item) ""))]
    {:thread_id thread-id
     :status "interrupted"
     :interrupts
     [{:value {:tool_name "request_human_decision"
               :question (str "メール仕分け: " from-addr)
               :context (str "送信元: " from-addr "\n"
                             "スコア: " (or (:triage_score item) 0) "\n"
                             "理由: " reasons)
               :options ["clean" "spam" "gray"]
               :meta {:type "email_triage"
                      :triage_score (or (:triage_score item) 0)
                      :triage_reasons (->> (str/split reasons #",")
                                           (map str/trim)
                                           (remove str/blank?)
                                           vec)
                      :from_address from-addr}}}]}))

(defn thread-state [thread-id {:keys [x-api-key]}]
  (or (enforce-auth x-api-key)
      (if (str/starts-with? (str thread-id) "draft-")
        (if-let [item (store/call :get-draft-item thread-id)]
          {:status 200 :body (draft-envelope thread-id item)}
          {:status 404 :body {:detail "thread not found"}})
        (if-let [item (store/call :get-gray-item thread-id)]
          {:status 200 :body (gray-envelope thread-id item)}
          {:status 404 :body {:detail "thread not found"}}))))

;; ── /threads/{id}/runs/stream (server.py _thread_resume) ────────────────────

(defn- sse [events]
  (str/join (map #(str "data: " % "\n\n") events)))

(defn thread-resume
  "POST /threads/{id}/runs/stream -> SSE body. Applies the human verdict via the
  injected store, returns the updates+end event stream. Returns a map with
  :status, :headers (text/event-stream), :body (raw SSE string) and :verdict."
  [thread-id body {:keys [x-api-key]}]
  (or (enforce-auth x-api-key)
      (let [command (or (:command body) {})
            verdict
            (if (str/starts-with? (str thread-id) "draft-")
              (let [action     (str/lower-case (str (or (:resume command) "discard")))
                    final-text (str (or (:final_text command) ""))]
                (store/call :apply-draft-verdict thread-id action final-text)
                action)
              (let [v0 (str/lower-case (str (or (:resume command) "gray")))
                    v  (if (contains? #{"clean" "spam" "gray"} v0) v0 "gray")]
                (store/call :apply-verdict thread-id v)
                v))]
        {:status 200
         :verdict verdict
         :headers {"content-type" "text/event-stream"}
         :body (sse [(json/generate-string {:event "updates"
                           :data {:verdict verdict :thread_id thread-id}})
                     (json/generate-string {:event "end"})])})))

;; ── pure dispatcher (ring-ish) ──────────────────────────────────────────────

(defn handle-request
  "req {:method :path :headers :query :body} -> {:status :body ...}. The
  x-api-key / x-cron are read from :headers."
  [{:keys [method path headers query body]}]
  (let [m     (keyword (str/lower-case (name (or method :get))))
        hdr   (fn [k] (get headers k))
        auth  {:x-api-key (hdr "x-api-key") :x-cron (hdr "x-cron")}
        parts (vec (remove str/blank? (str/split (str path) #"/")))]
    (cond
      (and (= :get m) (#{"/health" "/ok"} path)) (health)
      (and (= :get m) (= "/graphs" path))        (list-graphs)
      (and (= :post m) (= "/runs" path))         (run body auth)
      (and (= :get m) (= "/stats" path))         (stats (get query "days") auth)
      (and (= :post m) (= "/threads/search" path)) (threads-search body auth)
      ;; /threads/{id}/state
      (and (= :get m) (= 3 (count parts))
           (= "threads" (parts 0)) (= "state" (parts 2)))
      (thread-state (parts 1) auth)
      ;; /threads/{id}/runs/stream
      (and (= :post m) (= 4 (count parts))
           (= "threads" (parts 0)) (= "runs" (parts 2)) (= "stream" (parts 3)))
      (thread-resume (parts 1) body auth)
      :else {:status 404 :body {:detail "not found"}})))

;; ── optional socket binding (org.httpkit.server), parity with wave-1 ─────────

(defn ring-handler
  [{:keys [request-method uri headers query-string] :as req}]
  #?(:clj
     (let [body (when-let [b (:body req)]
                  (try (json/parse-string (slurp b) true) (catch Exception _ {})))
           q (into {} (for [kv (some-> query-string (str/split #"&"))
                            :let [[k v] (str/split kv #"=" 2)]]
                        [k v]))
           {:keys [status body headers]}
           (handle-request {:method request-method :path uri
                            :headers headers :query q :body body})]
       {:status status
        :headers (merge {"content-type" "application/json"} headers)
        :body (if (string? body) body (json/generate-string body))})
     :cljs {:status 501 :body {:detail "host server unavailable"}}))

#?(:clj
   (defn serve!
     "Bind the portable handler through an explicit server capability."
     [run-server {:keys [port] :or {port 8080}}]
     (when-not (fn? run-server)
       (throw (ex-info "Pregel server requires an explicit run-server capability"
                       {:capability :pregel/run-server})))
     (run-server ring-handler {:port port})))
