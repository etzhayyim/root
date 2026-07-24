;; etzhayyim.database — DB schema migration CLI port
;;
;; IO-REWRITE of 70-tools/etzhayyim-py/src/etzhayyim/database.py
;; The .py is KEPT (additive port — both co-exist).
;;
;; PURE-vs-IO split:
;;   PURE (parity-verifiable, unit-tested offline):
;;     redact-url              — strip password from postgres URL string
;;     validate-migrator-args! — check that migrator subcommand args are valid
;;     build-git-root-command  — argv for git rev-parse
;;     build-kysely-migrate-command — argv + env for node kysely migrate runner
;;     build-xrpc-get-request  — request map for GET XRPC
;;     build-xrpc-post-request — request map for POST XRPC
;;     graph-schema-rel        — constant relative path to 30-graph/graph-schema
;;     rw-local-url            — constant local dev postgres URL
;;     valid-subcommands       — set of valid migrator subcommands
;;
;;   IO (subprocess/FS via injectable fns, no live calls in tests):
;;     resolve-db-url           — choose an explicit flag/env-map/default URL
;;     find-git-root            — invoke git root via :proc-fn
;;     list-graph-schema-migs   — list .ts migration files via :fs-fn
;;     run-kysely-migrate       — run node kysely migration via :proc-fn
;;     call-xrpc-get            — GET XRPC endpoint via :http-fn
;;     call-xrpc-post           — POST XRPC endpoint via :http-fn
;;
;; DEFERRED subcommands:
;;   repair-order: uses psycopg (Python PostgreSQL driver) to directly connect
;;     to the DB and reorder migration entries.  psycopg is not available in
;;     babashka.  Full port would require a JDBC-or-JDBC-substitute approach.
;;     Deferred to a future wave (operator manual invocation of .py remains).
;;
;; INJECTABLE PROCESS FN:
;;   Subprocess IO fns accept :proc-fn in opts.
;;   No default authority: callers must inject a process capability.
;;
;; INJECTABLE FS FN:
;;   list-graph-schema-migs accepts :fs-fn (= fn [dir] -> seq of filename strings).
;;   No default authority: callers must inject a filesystem capability.
;;
;; bb load check:
;;   bb --classpath 70-tools/src -e "(require 'etzhayyim.database)(println :ok)"

(ns etzhayyim.database
  (:require [clojure.string :as str]
            [cheshire.core  :as json]))

;; ---------------------------------------------------------------------------
;; Constants (pure data — no IO at load time)
;; ---------------------------------------------------------------------------

(def graph-schema-rel
  "Repo-relative path to the graph schema directory.
  Mirrors Python _GRAPH_SCHEMA_REL constant."
  "30-graph/graph-schema")

(def rw-local-url
  "Default local RisingWave dev URL.
  Mirrors Python _RW_LOCAL_URL constant."
  "postgres://root@127.0.0.1:14566/dev?sslmode=disable")

(def valid-subcommands
  "Set of valid Kysely migrator subcommands.
  Mirrors Python _VALID_SUBCOMMANDS constant."
  #{"latest" "up" "down" "list" "to"})

;; ---------------------------------------------------------------------------
;; Pure: URL redaction
;; ---------------------------------------------------------------------------

(defn redact-url
  "Strip the password from a postgres connection URL, replacing it with '***'.
  Handles both 'postgres://user:pass@host' and 'postgresql://user:pass@host'.
  Mirrors Python _redact_url() — pure string transform.

  Examples:
    (redact-url \"postgres://root:secret@127.0.0.1:14566/dev\")
    ;=> \"postgres://root:***@127.0.0.1:14566/dev\"
    (redact-url \"postgres://root@127.0.0.1:14566/dev\")
    ;=> \"postgres://root@127.0.0.1:14566/dev\""
  [url]
  (if (seq url)
    (str/replace url #"://([^:/@]+):([^@]+)@" "://$1:***@")
    url))

;; ---------------------------------------------------------------------------
;; Pure: migrator args validation
;; ---------------------------------------------------------------------------

(defn validate-migrator-args!
  "Validate that migrator-args is a non-empty vector whose first element is
  one of valid-subcommands.  Raises ex-info on bad args.
  Returns nil on success.
  Mirrors Python _validate_migrator_args() — pure validation."
  [migrator-args]
  (when (empty? migrator-args)
    (throw (ex-info
            "No migrator subcommand provided. Expected one of: latest up down list to"
            {:args migrator-args :valid valid-subcommands})))
  (let [subcmd (first migrator-args)]
    (when-not (contains? valid-subcommands subcmd)
      (throw (ex-info
              (str "Unknown migrator subcommand: '" subcmd
                   "'. Expected one of: " (str/join " " (sort valid-subcommands)))
              {:subcmd subcmd :valid valid-subcommands}))))
  nil)

;; ---------------------------------------------------------------------------
;; Pure: subprocess command-building (argv vectors)
;; argv = vector of strings, injection-safe (no shell-string interpolation)
;; ---------------------------------------------------------------------------

(defn build-git-root-command
  "Return argv vector for 'git rev-parse --show-toplevel'.
  Mirrors Python _find_git_root() subprocess call."
  []
  ["git" "rev-parse" "--show-toplevel"])

(defn build-kysely-migrate-command
  "Build argv + env map for running the Kysely migration script.
  Returns {:argv [...] :env {...}}.

  Mirrors Python _run_kysely_migrate() subprocess.run call:
    node --loader=ts-node/esm scripts/migrate.ts <migrator-args>
  with DATABASE_URL injected into the subprocess environment.

  schema-dir    — absolute path to the 30-graph/graph-schema directory
  db-url        — connection URL string (should be resolved before this call)
  migrator-args — seq of strings like [\"latest\"] or [\"to\" \"00010\"]"
  [schema-dir db-url migrator-args]
  {:argv (into ["node" "--loader=ts-node/esm"
                (str schema-dir "/scripts/migrate.ts")]
               migrator-args)
   :env  {"DATABASE_URL" db-url}})

;; ---------------------------------------------------------------------------
;; Pure: HTTP request-shaping layer
;; ---------------------------------------------------------------------------

(defn- normalize-pds
  "Strip trailing slash from a PDS URL."
  [pds-url]
  (if (str/ends-with? pds-url "/")
    (subs pds-url 0 (dec (count pds-url)))
    pds-url))

(defn- build-auth-headers
  "Build Authorization + Content-Type headers map for XRPC calls."
  [tok]
  {"Authorization" (str "Bearer " tok)
   "Content-Type"  "application/json"})

(defn build-xrpc-get-request
  "Build a GET XRPC request map.
  Returns {:method :url :headers}.
  Mirrors Python httpx.get(pds + '/xrpc/' + nsid, headers=...) calls."
  [pds-url tok nsid]
  {:method  :get
   :url     (str (normalize-pds pds-url) "/xrpc/" nsid)
   :headers (build-auth-headers tok)})

(defn build-xrpc-post-request
  "Build a POST XRPC request map.
  Returns {:method :url :headers :body}.
  Mirrors Python httpx.post(pds + '/xrpc/' + nsid, json=body, headers=...) calls."
  [pds-url tok nsid body]
  {:method  :post
   :url     (str (normalize-pds pds-url) "/xrpc/" nsid)
   :headers (build-auth-headers tok)
   :body    body})

;; ---------------------------------------------------------------------------
;; IO: env-var resolution (lazy — no env access at load time)
;; ---------------------------------------------------------------------------

(defn resolve-db-url
  "Resolve a database connection URL.
  Prefers url-flag (non-empty string) over the value in an explicit env map.
  Falls back to rw-local-url if neither is set.
  Mirrors Python _resolve_db_url()."
  ([url-flag env-name]
   (resolve-db-url url-flag env-name {}))
  ([url-flag env-name env]
   (or (when (seq url-flag) url-flag)
       (get env env-name)
       rw-local-url)))

;; ---------------------------------------------------------------------------
;; IO: default implementations
;; ---------------------------------------------------------------------------

(defn- missing-capability [capability]
  (fn [& _]
    (throw (ex-info (str "database host capability not configured: " capability)
                    {:missing-capability capability}))))

(def ^:private default-proc-fn (missing-capability :process))

(def ^:private default-http-fn (missing-capability :http))

(def ^:private default-fs-fn (missing-capability :filesystem))

;; ---------------------------------------------------------------------------
;; IO: find git root
;; ---------------------------------------------------------------------------

(defn find-git-root
  "Resolve git repo root via subprocess.
  Returns the root path string or raises ex-info.
  Opts: :proc-fn"
  ([] (find-git-root {}))
  ([{:keys [proc-fn] :or {proc-fn default-proc-fn}}]
   (let [argv (build-git-root-command)
         r    (proc-fn argv {})]
     (if (zero? (:exit r))
       (str/trim (:out r))
       (throw (ex-info "not in a git repository"
                       {:argv argv :exit (:exit r)}))))))

;; ---------------------------------------------------------------------------
;; IO: list migration files
;; ---------------------------------------------------------------------------

(defn list-graph-schema-migs
  "List .ts migration filenames in schema-dir/migrations/.
  Returns a sorted seq of filename strings (basenames, no path).
  Mirrors Python _list_graph_schema_migrations().
  Opts: :fs-fn"
  ([schema-dir] (list-graph-schema-migs schema-dir {}))
  ([schema-dir {:keys [fs-fn] :or {fs-fn default-fs-fn}}]
   (let [mig-dir (str schema-dir "/migrations")]
     (->> (fs-fn mig-dir)
          (map (fn [p]
                 ;; strip any leading dir prefix, keep only basename
                 (last (str/split (str p) #"/"))))
          (filter #(str/ends-with? % ".ts"))
          sort
          vec))))

;; ---------------------------------------------------------------------------
;; IO: run Kysely migration
;; ---------------------------------------------------------------------------

(defn run-kysely-migrate
  "Run the Kysely migration script in schema-dir against db-url.
  migrator-args is a seq of strings (e.g. [\"latest\"]).
  Returns the exit code (0 = success).
  Opts: :proc-fn :cwd"
  ([schema-dir db-url migrator-args]
   (run-kysely-migrate schema-dir db-url migrator-args {}))
  ([schema-dir db-url migrator-args {:keys [proc-fn cwd]
                                     :or   {proc-fn default-proc-fn}}]
   (validate-migrator-args! migrator-args)
   (let [{:keys [argv env]} (build-kysely-migrate-command schema-dir db-url migrator-args)
         r                  (proc-fn argv {:env env :cwd (or cwd schema-dir)})]
     (:exit r))))

;; ---------------------------------------------------------------------------
;; IO: XRPC helpers
;; ---------------------------------------------------------------------------

(defn call-xrpc-get
  "GET an XRPC endpoint. Returns parsed JSON body map.
  Raises ex-info on HTTP error (>=400).
  Opts: :http-fn"
  ([req] (call-xrpc-get req {}))
  ([req {:keys [http-fn] :or {http-fn default-http-fn}}]
   (let [resp (http-fn req)]
     (when (>= (:status resp) 400)
       (throw (ex-info (str "XRPC " (:status resp) " GET " (:url req))
                       {:status (:status resp) :body (:body resp)})))
     (json/parse-string (:body resp) true))))

(defn call-xrpc-post
  "POST an XRPC endpoint. Returns parsed JSON body map.
  Raises ex-info on HTTP error (>=400).
  Opts: :http-fn"
  ([req] (call-xrpc-post req {}))
  ([req {:keys [http-fn] :or {http-fn default-http-fn}}]
   (let [resp (http-fn req)]
     (when (>= (:status resp) 400)
       (throw (ex-info (str "XRPC " (:status resp) " POST " (:url req))
                       {:status (:status resp) :body (:body resp)})))
     (json/parse-string (:body resp) true))))
