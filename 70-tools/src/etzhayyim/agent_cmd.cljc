;; etzhayyim.agent-cmd — XRPC agent management + organism control (cljc port).
;;
;; IO-REWRITE of 70-tools/etzhayyim-py/src/etzhayyim/agent_cmd.py
;; The .py is KEPT (additive port — both co-exist).
;;
;; PURE-vs-IO split:
;;   PURE (parity-verifiable, unit-tested offline):
;;     build-list-agents-url        — XRPC URL for listAgents
;;     build-list-agents-request    — full HTTP request map for listAgents
;;     build-get-agent-request      — full HTTP request map for getAgent
;;     build-stop-agent-request     — full HTTP request map for stopAgent
;;     build-organism-status-request — full HTTP request map for organism /status
;;     build-git-toplevel-command   — argv vector for git rev-parse --show-toplevel
;;     parse-list-response          — parse listAgents JSON body → agent seq
;;     parse-get-response           — parse getAgent JSON body → agent map
;;     build-auth-headers           — assemble Authorization headers from token string
;;     build-stop-body              — build JSON body for stopAgent POST
;;
;;   IO (injectable :http-fn or :proc-fn, no live IO in tests):
;;     auth-headers!                — resolve actual token from auth file or env + build headers
;;     list-agents                  — XRPC GET listAgents (injectable http-fn + auth-fn)
;;     get-agent                    — XRPC GET getAgent  (injectable http-fn + auth-fn)
;;     stop-agent                   — XRPC POST stopAgent (injectable http-fn + auth-fn)
;;     organism-status              — GET organism /status (injectable http-fn)
;;     verify-agent                 — git root + local proof-file check (injectable proc-fn)
;;     agent-run                    — not portable: Go binary required, throws ex-info
;;     agent-organism-publish       — not portable: Go binary required, throws ex-info
;;
;; INJECTABLE CLIENTS:
;;   :http-fn  — (fn [req-map] {:status N :body string})  (default: real babashka.http-client)
;;   :proc-fn  — (fn [{:keys [argv cwd]}] {:exit N :out str :err str}) (default: real babashka.process)
;;   :auth-fn  — (fn [] {"Authorization" "Bearer <tok>" "Content-Type" "application/json"})
;;               (default: reads local auth file or etzhayyim_TOKEN env)
;;
;; bb load check:
;;   bb --classpath 70-tools/src -e "(require 'etzhayyim.agent-cmd)(println :ok)"

(ns etzhayyim.agent-cmd
  (:require [clojure.string :as str]
            [cheshire.core  :as json]
            #?(:bb [babashka.process     :as proc])
            #?(:bb [babashka.http-client :as http])))

;; ---------------------------------------------------------------------------
;; Constants
;; ---------------------------------------------------------------------------

(def ^:private default-timeout-ms 30000)
(def ^:private organism-timeout-ms 10000)

;; ---------------------------------------------------------------------------
;; Pure: auth header builder
;; ---------------------------------------------------------------------------

(defn build-auth-headers
  "Assemble standard Authorization + Content-Type headers from a token string.
  Pure: no file reads, no env calls.
  Mirrors Python _auth_headers() result."
  [token]
  {"Authorization"  (str "Bearer " token)
   "Content-Type"   "application/json"})

;; ---------------------------------------------------------------------------
;; Pure: XRPC URL / request builders
;; ---------------------------------------------------------------------------

(defn build-list-agents-url
  "Build the XRPC listAgents endpoint URL from a PDS base URL.
  Pure: no IO."
  [pds-url]
  (str (str/replace pds-url #"/$" "")
       "/xrpc/com.etzhayyim.agent.listAgents"))

(defn build-list-agents-request
  "Build a full HTTP request map for com.etzhayyim.agent.listAgents (GET).
  auth-headers — map from build-auth-headers.
  filters       — optional map {:status 'running'} etc.
  Returns {:method :get :url string :headers map :params map}."
  ([pds-url auth-headers]
   (build-list-agents-request pds-url auth-headers {}))
  ([pds-url auth-headers filters]
   {:method  :get
    :url     (build-list-agents-url pds-url)
    :headers auth-headers
    :params  (or filters {})}))

(defn build-get-agent-request
  "Build a full HTTP request map for com.etzhayyim.agent.getAgent (GET).
  agent-id — string agent ID.
  Returns {:method :get :url string :headers map :params map}."
  [pds-url auth-headers agent-id]
  {:method  :get
   :url     (str (str/replace pds-url #"/$" "")
                 "/xrpc/com.etzhayyim.agent.getAgent")
   :headers auth-headers
   :params  {"id" agent-id}})

(defn build-stop-body
  "Build the JSON body map for a stopAgent POST.
  Pure: no IO."
  [agent-id]
  {"id" agent-id})

(defn build-stop-agent-request
  "Build a full HTTP request map for com.etzhayyim.agent.stopAgent (POST).
  Returns {:method :post :url string :headers map :body string}."
  [pds-url auth-headers agent-id]
  {:method  :post
   :url     (str (str/replace pds-url #"/$" "")
                 "/xrpc/com.etzhayyim.agent.stopAgent")
   :headers auth-headers
   :body    (json/generate-string (build-stop-body agent-id))})

(defn build-organism-status-request
  "Build a full HTTP request map for the organism /status endpoint (GET).
  organism-url — base URL without trailing slash.
  Returns {:method :get :url string :timeout ms}."
  [organism-url]
  {:method  :get
   :url     (str (str/replace organism-url #"/$" "") "/status")
   :timeout organism-timeout-ms})

;; ---------------------------------------------------------------------------
;; Pure: subprocess command builder
;; ---------------------------------------------------------------------------

(defn build-git-toplevel-command
  "Return argv vector for git rev-parse --show-toplevel.
  Mirrors Python _agent_verify() subprocess call."
  []
  ["git" "rev-parse" "--show-toplevel"])

;; ---------------------------------------------------------------------------
;; Pure: response parsers
;; ---------------------------------------------------------------------------

(defn parse-list-response
  "Parse listAgents HTTP response body string → seq of agent maps.
  Returns [] on failure / empty body.
  Mirrors Python agent_list() output display logic."
  [body]
  (try
    (let [data (json/parse-string body true)]
      (or (get data :agents) (get data :rows) []))
    (catch Exception _ [])))

(defn parse-get-response
  "Parse getAgent HTTP response body string → agent map or nil.
  Mirrors Python agent_get() result."
  [body]
  (try
    (json/parse-string body true)
    (catch Exception _ nil)))

;; ---------------------------------------------------------------------------
;; IO: default process fn
;; ---------------------------------------------------------------------------

(defn- default-proc-fn
  "Real babashka.process dispatch.
  Expects {:argv [string...] :cwd string}."
  [{:keys [argv cwd]}]
  #?(:bb
     (let [result (apply proc/sh {:dir (or cwd ".")} argv)]
       {:exit (:exit result) :out (:out result) :err (:err result)})
     :default
     (throw (ex-info "babashka.process only available under bb" {:argv argv}))))

;; ---------------------------------------------------------------------------
;; IO: default http fn
;; ---------------------------------------------------------------------------

(defn- default-http-fn
  "Real babashka.http-client dispatch for GET/POST.
  Expects {:method :get/:post :url string :headers map :params? map :body? string :timeout? ms}."
  [{:keys [method url headers params body timeout]}]
  #?(:bb
     (let [base-opts (cond-> {:headers (or headers {})
                              :timeout (or timeout default-timeout-ms)}
                       (seq params) (assoc :query-params params)
                       (seq body)   (assoc :body body))
           resp (case method
                  :get  (http/get  url base-opts)
                  :post (http/post url base-opts)
                  (throw (ex-info "unsupported method" {:method method})))]
       {:status (:status resp) :body (:body resp)})
     :default
     (throw (ex-info "babashka.http-client only available under bb" {:method method :url url}))))

;; ---------------------------------------------------------------------------
;; IO: default auth fn
;; ---------------------------------------------------------------------------

(defn- default-auth-fn
  "Read auth token from local auth file (~/.config/etzhayyim/session.json) or env.
  Returns built-auth-headers map."
  []
  ;; Try env first (CI / headless), then local session file
  (let [token (or (System/getenv "etzhayyim_TOKEN")
                  (try
                    (let [session-path (str (System/getProperty "user.home")
                                           "/.config/etzhayyim/session.json")
                          data         (json/parse-string (slurp session-path) true)]
                      (or (get data :accessJwt) (get data :access_jwt) (get data :token) ""))
                    (catch Exception _ "")))]
    (build-auth-headers token)))

;; ---------------------------------------------------------------------------
;; IO: resolve PDS URL
;; ---------------------------------------------------------------------------

(defn- resolve-pds-url
  "Read PDS URL from env or derive from service name.
  NEVER called at load time."
  []
  (or (System/getenv "etzhayyim_PDS_URL")
      "https://etzhayyim-pds-2603241700.etzhayyim.com"))

;; ---------------------------------------------------------------------------
;; IO: list-agents
;; ---------------------------------------------------------------------------

(defn list-agents
  "Call com.etzhayyim.agent.listAgents and return seq of agent maps.
  opts:
    :http-fn   — injectable HTTP fn (default = real babashka.http-client)
    :auth-fn   — injectable auth fn (default = reads local session file / env)
    :pds-url   — PDS base URL (default = from env)
    :filters   — optional map of query params

  Mirrors Python agent_list() HTTP call."
  ([]
   (list-agents {}))
  ([{:keys [http-fn auth-fn pds-url filters]
     :or   {http-fn  default-http-fn
            auth-fn  default-auth-fn}}]
   (let [pds    (or pds-url (resolve-pds-url))
         hdrs   (auth-fn)
         req    (build-list-agents-request pds hdrs (or filters {}))
         resp   (http-fn req)]
     (when-not (< (:status resp) 300)
       (throw (ex-info (str "listAgents HTTP " (:status resp))
                       {:status (:status resp) :body (:body resp)})))
     (parse-list-response (:body resp)))))

;; ---------------------------------------------------------------------------
;; IO: get-agent
;; ---------------------------------------------------------------------------

(defn get-agent
  "Call com.etzhayyim.agent.getAgent and return agent map.
  opts:
    :http-fn  — injectable HTTP fn
    :auth-fn  — injectable auth fn
    :pds-url  — PDS base URL

  Mirrors Python agent_get() HTTP call."
  ([agent-id]
   (get-agent agent-id {}))
  ([agent-id {:keys [http-fn auth-fn pds-url]
              :or   {http-fn default-http-fn
                     auth-fn default-auth-fn}}]
   (let [pds   (or pds-url (resolve-pds-url))
         hdrs  (auth-fn)
         req   (build-get-agent-request pds hdrs agent-id)
         resp  (http-fn req)]
     (when-not (< (:status resp) 300)
       (throw (ex-info (str "getAgent HTTP " (:status resp))
                       {:agent-id agent-id :status (:status resp) :body (:body resp)})))
     (parse-get-response (:body resp)))))

;; ---------------------------------------------------------------------------
;; IO: stop-agent
;; ---------------------------------------------------------------------------

(defn stop-agent
  "Call com.etzhayyim.agent.stopAgent (POST).
  Returns true on success.
  opts:
    :http-fn  — injectable HTTP fn
    :auth-fn  — injectable auth fn
    :pds-url  — PDS base URL

  Mirrors Python agent_stop() HTTP call."
  ([agent-id]
   (stop-agent agent-id {}))
  ([agent-id {:keys [http-fn auth-fn pds-url]
              :or   {http-fn default-http-fn
                     auth-fn default-auth-fn}}]
   (let [pds   (or pds-url (resolve-pds-url))
         hdrs  (auth-fn)
         req   (build-stop-agent-request pds hdrs agent-id)
         resp  (http-fn req)]
     (when-not (< (:status resp) 300)
       (throw (ex-info (str "stopAgent HTTP " (:status resp))
                       {:agent-id agent-id :status (:status resp) :body (:body resp)})))
     true)))

;; ---------------------------------------------------------------------------
;; IO: organism-status
;; ---------------------------------------------------------------------------

(defn organism-status
  "GET organism /status endpoint.
  Returns parsed status map or throws ex-info.
  opts:
    :http-fn      — injectable HTTP fn
    :organism-url — base URL (default = from env etzhayyim_ORGANISM_URL)

  Mirrors Python agent_organism_status() HTTP call."
  ([]
   (organism-status {}))
  ([{:keys [http-fn organism-url]
     :or   {http-fn default-http-fn}}]
   (let [url  (or organism-url
                  (System/getenv "etzhayyim_ORGANISM_URL")
                  "http://localhost:8088")
         req  (build-organism-status-request url)
         resp (http-fn req)]
     (when-not (< (:status resp) 300)
       (throw (ex-info (str "organism /status HTTP " (:status resp))
                       {:url url :status (:status resp) :body (:body resp)})))
     (try
       (json/parse-string (:body resp) true)
       (catch Exception _ {:raw (:body resp)})))))

;; ---------------------------------------------------------------------------
;; IO: verify-agent (git root + proof files)
;; ---------------------------------------------------------------------------

(defn verify-agent
  "Verify an agent by checking git root and reading local proof JSON files.
  Returns a map {:git-root string :proofs [...]} on success.
  opts:
    :proc-fn  — injectable process fn (default = real babashka.process)
    :read-fn  — injectable file-read fn (fn [path] -> string-or-nil)
                (default = slurp)

  Mirrors Python agent_verify() — git subprocess + local file reads."
  ([comp-dir]
   (verify-agent comp-dir {}))
  ([comp-dir {:keys [proc-fn read-fn]
              :or   {proc-fn default-proc-fn
                     read-fn (fn [p] (try (slurp p) (catch Exception _ nil)))}}]
   (let [argv    (build-git-toplevel-command)
         result  (proc-fn {:argv argv :cwd (or comp-dir ".")})
         _       (when-not (zero? (:exit result))
                   (throw (ex-info "git rev-parse --show-toplevel failed"
                                   {:exit (:exit result) :err (:err result)})))
         git-root (str/trim (:out result))
         proof-paths [(str git-root "/80-data/agent-proofs/proof-1.json")
                      (str git-root "/80-data/agent-proofs/proof-2.json")
                      (str git-root "/80-data/agent-proofs/proof-3.json")]
         proofs (mapv (fn [p]
                        (when-let [content (read-fn p)]
                          (try
                            (json/parse-string content true)
                            (catch Exception _ {:raw content :path p}))))
                      proof-paths)]
     {:git-root git-root
      :proofs   proofs})))

;; ---------------------------------------------------------------------------
;; Stubs: Go-binary-required operations (not portable to cljc)
;; ---------------------------------------------------------------------------

(defn agent-run
  "NOT portable: requires the Go etzhayyim binary.
  Throws ex-info with a clear message mirroring Python agent_run() sys.exit(1)."
  [& _args]
  (throw (ex-info
          "agent-run requires the Go etzhayyim binary (not available in bb cljc).
Use `etzhayyim agent run <agent-id>` via the Go CLI."
          {:go-binary-required true})))

(defn agent-organism-publish
  "NOT portable: requires the Go etzhayyim binary.
  Throws ex-info with a clear message mirroring Python agent_organism_publish()."
  [& _args]
  (throw (ex-info
          "agent-organism-publish requires the Go etzhayyim binary (not available in bb cljc).
Use `etzhayyim agent organism publish <organism-url>` via the Go CLI."
          {:go-binary-required true})))

;; ---------------------------------------------------------------------------
;; CLI -main — mirrors the python `agent` click group argv contract:
;;   e7m agent <list|get|stop|run|verify|organism> [args] [--opts]
;;   e7m agent organism <status|publish> [--opts]
;; SAFETY: stop (POST stopAgent) is side-effecting → gated behind --yes.
;; run / organism publish require the Go binary (mirror python sys.exit).
;; list/get/organism-status are read-only XRPC (need a live PDS).
;; verify is local (git + proof file reads) and runs for real.
;; ---------------------------------------------------------------------------

(defn- cli-parse
  [args bool-flags]
  (loop [a (seq args) pos [] flags {}]
    (if-not a
      [pos flags]
      (let [t (first a)]
        (cond
          (and (str/starts-with? t "--") (contains? bool-flags (subs t 2)))
          (recur (next a) pos (assoc flags (subs t 2) true))
          (str/starts-with? t "--")
          (recur (nnext a) pos (assoc flags (subs t 2) (fnext a)))
          :else
          (recur (next a) (conj pos t) flags))))))

(defn- emit-json [data] (println (json/generate-string data {:pretty true})))

(defn -main [& args]
  (let [[pos flags] (cli-parse args #{"json" "dry-run" "yes" "confirm"})
        sub   (first pos)
        json? (boolean (get flags "json"))
        pds   (get flags "pds")
        opts  (cond-> {} pds (assoc :pds-url pds))]
    (case sub
      "list"
      (try
        (let [agents (list-agents (cond-> opts
                                    (get flags "status")
                                    (assoc :filters {"status" (get flags "status")})))]
          (if json?
            (emit-json agents)
            (doseq [a agents]
              (println (str "  " (get a :id "") "  " (get a :name "") "  " (get a :status ""))))))
        (catch Exception e (println (str "list failed: " (ex-message e)))))

      "get"
      (if-let [id (second pos)]
        (try
          (let [a (get-agent id opts)]
            (if json? (emit-json a)
                (doseq [[k v] a] (println (str "  " (name k) ": " v)))))
          (catch Exception e (println (str "get failed: " (ex-message e)))))
        (println "usage: agent get <agent-id> [--pds URL] [--json]"))

      "stop"
      (if-let [id (second pos)]
        (if (or (get flags "yes") (get flags "confirm"))
          (try (stop-agent id opts) (println (str "stopped: " id))
               (catch Exception e (println (str "stop failed: " (ex-message e)))))
          (println (str "would stop agent " id
                        " (side-effecting POST stopAgent; pass --yes to execute)")))
        (println "usage: agent stop <agent-id> [--yes] [--pds URL]"))

      "run"
      (try (agent-run)
           (catch Exception e (println (str "agent run: " (ex-message e)))))

      "verify"
      (try
        (let [res (verify-agent ".")]
          (if json?
            (emit-json res)
            (do (println (str "agent verify  git-root=" (:git-root res)))
                (doseq [[i p] (map-indexed vector (:proofs res))]
                  (println (str "  proof-" (inc i) ": " (if p "loaded" "absent")))))))
        (catch Exception e (println (str "verify failed: " (ex-message e)))))

      "organism"
      (let [osub (second pos)]
        (case osub
          "status"
          (try
            (let [st (organism-status (cond-> {} (get flags "url")
                                              (assoc :organism-url (get flags "url"))))]
              (if json? (emit-json st)
                  (println (str "organism status: " (get st :status "unknown")))))
            (catch Exception e (println (str "organism status: probe failed: " (ex-message e)))))
          "publish"
          (if (get flags "dry-run")
            (println (str "dry-run: would publish organism registration for DID="
                          (or (get flags "agent-did") "—")))
            (try (agent-organism-publish)
                 (catch Exception e (println (str "organism publish: " (ex-message e))))))
          (println "usage: agent organism <status|publish> [--opts]")))

      (println "usage: agent <list|get|stop|run|verify|organism> [args] [--opts]"))))
