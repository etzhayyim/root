;; etzhayyim.mitama — Actor manifest management (Clojure/bb port of mitama.py).
;;
;; IO-REWRITE of 70-tools/etzhayyim-py/src/etzhayyim/mitama.py
;; The .py is KEPT (additive port — both co-exist).
;;
;; PURE-vs-IO split:
;;   PURE (parity-verifiable, unit-tested offline):
;;     build-schema-status-stmt — builds SHOW ALTER TABLE COLUMN SQL with optional WHERE
;;     clamp-timeout-ms         — max(1000, min(60000, timeout_sec * 1000))
;;     build-set-status-body    — {:id did-or-nanoid :status status}
;;     build-shinka-payload     — {} or {:model model} if model non-empty
;;
;;   IO (request-shaping verified via injectable HTTP fn, not live calls):
;;     build-register-request   — shape for com.etzhayyim.actor.register POST
;;     build-list-actors-request — shape for com.etzhayyim.actor.listActors GET
;;     build-inspect-request    — shape for com.etzhayyim.actor.getActor GET
;;     build-set-status-request — shape for com.etzhayyim.actor.setStatus POST
;;     build-shinka-request     — shape for com.etzhayyim.actor.shinka POST
;;     build-schema-status-request — shape for com.etzhayyim.kagami.sql POST
;;
;; INJECTABLE HTTP CLIENT:
;;   Every IO fn accepts :http-fn in opts.
;;   Default = real babashka.http-client; tests inject a fake.
;;
;; bb load check:
;;   bb --classpath 70-tools/src -e "(require 'etzhayyim.mitama)(println :ok)"

(ns etzhayyim.mitama
  (:require [clojure.string :as str]
            [cheshire.core  :as json]
            #?(:bb [babashka.http-client :as http])))

;; ---------------------------------------------------------------------------
;; Pure: build-schema-status-stmt
;; ---------------------------------------------------------------------------

(defn build-schema-status-stmt
  "Build the SHOW ALTER TABLE COLUMN SQL statement with optional WHERE clauses.
  table: table name filter (empty → not included unless all-tables? is true)
  all-tables?: if true, skip table filter
  state: state filter (e.g. RUNNING, FINISHED)
  Returns the SQL string.
  Mirrors Python stmt construction in mitama_schema_status()."
  [table all-tables? state]
  (let [base         "SHOW ALTER TABLE COLUMN FROM graphar"
        ;; Safe string quoting: replace single quote with double single-quote
        safe-quote   (fn [s] (str/replace s "'" "''"))
        where-parts  (cond-> []
                       ;; table filter: only if not all-tables? AND table is non-empty
                       (and (not all-tables?) (seq (str/trim (str table))))
                       (conj (str "TableName = '" (safe-quote (str/trim (str table))) "'"))
                       ;; state filter: only if state is non-empty
                       (seq (str/trim (str state)))
                       (conj (str "State = '" (safe-quote (str/upper-case (str/trim (str state)))) "'")))]
    (if (seq where-parts)
      (str base " WHERE " (str/join " AND " where-parts))
      base)))

;; ---------------------------------------------------------------------------
;; Pure: clamp-timeout-ms
;; ---------------------------------------------------------------------------

(defn clamp-timeout-ms
  "Convert timeout in seconds to milliseconds, clamped to [1000, 60000].
  Mirrors Python: max(1000, min(60000, timeout_sec * 1000))."
  [timeout-sec]
  (max 1000 (min 60000 (* timeout-sec 1000))))

;; ---------------------------------------------------------------------------
;; Pure: build-set-status-body
;; ---------------------------------------------------------------------------

(defn build-set-status-body
  "Build the request body for com.etzhayyim.actor.setStatus.
  Mirrors Python json={'id': did_or_nanoid, 'status': status}."
  [did-or-nanoid status]
  {:id     did-or-nanoid
   :status status})

;; ---------------------------------------------------------------------------
;; Pure: build-shinka-payload
;; ---------------------------------------------------------------------------

(defn build-shinka-payload
  "Build the request body for com.etzhayyim.actor.shinka.
  Returns {} if model is empty/nil, {:model model} otherwise.
  Mirrors Python: payload = {}; if model: payload['model'] = model."
  [model]
  (if (seq model)
    {:model model}
    {}))

;; ---------------------------------------------------------------------------
;; IO: default-http-fn
;; ---------------------------------------------------------------------------

(defn- default-http-fn
  "Real babashka.http-client dispatch."
  [{:keys [method url headers params body]}]
  #?(:bb
     (let [opts (cond-> {:headers (or headers {}) :timeout 60000}
                  params (assoc :query-params params)
                  body   (assoc :body (json/generate-string body)))
           resp (case method
                  :get    (http/get    url opts)
                  :post   (http/post   url opts)
                  :patch  (http/patch  url opts)
                  :delete (http/delete url opts))]
       {:status (:status resp) :body (:body resp)})
     :default
     (throw (ex-info "babashka.http-client only available under bb"
                     {:method method :url url}))))

;; ---------------------------------------------------------------------------
;; IO: build-auth-headers
;; ---------------------------------------------------------------------------

(defn- build-auth-headers
  "Build Authorization + Content-Type headers from token string."
  [token]
  (cond-> {"Content-Type" "application/json"}
    (seq token) (assoc "Authorization" (str "Bearer " token))))

;; ---------------------------------------------------------------------------
;; IO request-shaping: all return {:method :url :headers :body/:params}
;; ---------------------------------------------------------------------------

(defn build-register-request
  "Shape for com.etzhayyim.actor.register POST.
  data is the kotodama.jsonld map."
  [pds-url token data]
  {:method  :post
   :url     (str pds-url "/xrpc/com.etzhayyim.actor.register")
   :headers (build-auth-headers token)
   :body    data})

(defn build-list-actors-request
  "Shape for com.etzhayyim.actor.listActors GET.
  opts: :limit (default 100)."
  [pds-url token {:keys [limit] :or {limit 100}}]
  {:method  :get
   :url     (str pds-url "/xrpc/com.etzhayyim.actor.listActors")
   :headers (build-auth-headers token)
   :params  {"limit" (str limit)}})

(defn build-inspect-request
  "Shape for com.etzhayyim.actor.getActor GET.
  did-or-nanoid is the actor identifier."
  [pds-url token did-or-nanoid]
  {:method  :get
   :url     (str pds-url "/xrpc/com.etzhayyim.actor.getActor")
   :headers (build-auth-headers token)
   :params  {"id" did-or-nanoid}})

(defn build-set-status-request
  "Shape for com.etzhayyim.actor.setStatus POST.
  status is e.g. 'dormant' or 'active'."
  [pds-url token did-or-nanoid status]
  {:method  :post
   :url     (str pds-url "/xrpc/com.etzhayyim.actor.setStatus")
   :headers (build-auth-headers token)
   :body    (build-set-status-body did-or-nanoid status)})

(defn build-shinka-request
  "Shape for com.etzhayyim.actor.shinka POST.
  model is an optional model override (empty string = no override)."
  [pds-url token model]
  {:method  :post
   :url     (str pds-url "/xrpc/com.etzhayyim.actor.shinka")
   :headers (build-auth-headers token)
   :body    (build-shinka-payload model)})

(defn build-schema-status-request
  "Shape for com.etzhayyim.kagami.sql POST.
  table, all-tables?, state are passed to build-schema-status-stmt.
  timeout-sec is clamped via clamp-timeout-ms."
  [pds-url token table all-tables? state timeout-sec]
  (let [stmt       (build-schema-status-stmt table all-tables? state)
        timeout-ms (clamp-timeout-ms timeout-sec)]
    {:method  :post
     :url     (str pds-url "/xrpc/com.etzhayyim.kagami.sql")
     :headers (build-auth-headers token)
     :body    {:statement stmt
               :params    {}
               :timeoutMs timeout-ms}}))

;; ---------------------------------------------------------------------------
;; IO: register-actor
;; ---------------------------------------------------------------------------

(defn register-actor
  "Register an actor manifest via com.etzhayyim.actor.register.
  data is the kotodama.jsonld map.
  Returns parsed response data or throws on HTTP error."
  [pds-url token data {:keys [http-fn]
                        :or   {http-fn default-http-fn}}]
  (let [req  (build-register-request pds-url token data)
        resp (http-fn req)]
    (when (>= (:status resp) 400)
      (throw (ex-info (str "actor.register HTTP " (:status resp))
                      {:status (:status resp) :body (:body resp)})))
    (json/parse-string (:body resp) true)))

;; ---------------------------------------------------------------------------
;; IO: list-actors
;; ---------------------------------------------------------------------------

(defn list-actors
  "List actors via com.etzhayyim.actor.listActors.
  Returns parsed data or throws on HTTP error."
  [pds-url token filter-opts {:keys [http-fn]
                               :or   {http-fn default-http-fn}}]
  (let [req  (build-list-actors-request pds-url token filter-opts)
        resp (http-fn req)]
    (when (>= (:status resp) 400)
      (throw (ex-info (str "actor.listActors HTTP " (:status resp))
                      {:status (:status resp) :body (:body resp)})))
    (json/parse-string (:body resp) true)))

;; ---------------------------------------------------------------------------
;; IO: set-actor-status (dry-run aware)
;; ---------------------------------------------------------------------------

(defn set-actor-status
  "Set actor status via com.etzhayyim.actor.setStatus.
  With :dry-run? true, returns the request shape without making a network call.
  Returns the response data map (or request shape on dry-run)."
  [pds-url token did-or-nanoid status {:keys [dry-run? http-fn]
                                        :or   {dry-run? false http-fn default-http-fn}}]
  (let [req (build-set-status-request pds-url token did-or-nanoid status)]
    (if dry-run?
      {:dry-run true :request req}
      (let [resp (http-fn req)]
        (when (>= (:status resp) 400)
          (throw (ex-info (str "actor.setStatus HTTP " (:status resp))
                          {:status (:status resp) :body (:body resp)})))
        (json/parse-string (or (:body resp) "{}") true)))))

;; ---------------------------------------------------------------------------
;; IO: run-shinka (dry-run aware)
;; ---------------------------------------------------------------------------

(defn run-shinka
  "Run shinka via com.etzhayyim.actor.shinka.
  With :dry-run? true, returns the request shape without making a network call.
  Returns the response data map (or request shape on dry-run)."
  [pds-url token model {:keys [dry-run? http-fn]
                         :or   {dry-run? false http-fn default-http-fn}}]
  (let [req (build-shinka-request pds-url token model)]
    (if dry-run?
      {:dry-run true :request req}
      (let [resp (http-fn req)]
        (when (>= (:status resp) 400)
          (throw (ex-info (str "actor.shinka HTTP " (:status resp))
                          {:status (:status resp) :body (:body resp)})))
        (json/parse-string (:body resp) true)))))
