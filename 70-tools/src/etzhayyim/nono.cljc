;; etzhayyim.nono — Nono capability worker lifecycle (Clojure/bb port of nono.py).
;;
;; IO-REWRITE of 70-tools/etzhayyim-py/src/etzhayyim/nono.py
;; The .py is KEPT (additive port — both co-exist).
;;
;; PURE-vs-IO split:
;;   PURE (parity-verifiable, unit-tested offline):
;;     parse-manifest-data     — extract nanoid/name/bindings/skills from data map
;;     find-manifest-by-nanoid — linear search in manifests list
;;     build-deploy-reg-body   — construct registerManifest request body from data + nanoid
;;     build-build-command     — determine build command from pkg.json scripts + lockfile
;;     build-deploy-command    — ["npx" "wrangler" "deploy"]
;;
;;   IO (request-shaping verified via injectable fn, not live calls):
;;     build-register-manifest-request  — shape for com.etzhayyim.actor.registerManifest POST
;;     load-manifests   — IO: walk ws for nono-manifest.jsonld files (injectable :fs-fn)
;;     deploy-worker    — IO: wrangler deploy subprocess (injectable :proc-fn)
;;     register-skills  — IO: XRPC registerManifest (injectable :http-fn, dry-run aware)
;;
;; INJECTABLE IO FUNCTIONS:
;;   :http-fn  — default real babashka.http-client
;;   :proc-fn  — default real babashka.process/shell
;;   :fs-fn    — default real babashka.fs/glob
;;
;; bb load check:
;;   bb --classpath 70-tools/src -e "(require 'etzhayyim.nono)(println :ok)"

(ns etzhayyim.nono
  (:require [clojure.string :as str]
            [cheshire.core  :as json]
            #?(:bb [babashka.http-client :as http])
            #?(:bb [babashka.fs          :as fs])
            #?(:bb [babashka.process     :as proc])))

;; ---------------------------------------------------------------------------
;; Pure: parse-manifest-data
;; ---------------------------------------------------------------------------

(defn parse-manifest-data
  "Parse a nono-manifest.jsonld data map into a canonical manifest map.
  Returns {:nanoid :name :bindings :skills} or nil if nanoid is missing.
  Mirrors Python NonoManifest construction in _load_manifests()."
  [data]
  (let [nanoid (or (:nanoid data) (get data "nanoid") "")]
    (when (seq nanoid)
      {:nanoid   nanoid
       :name     (or (:name data)     (get data "name")     "")
       :bindings (or (:bindings data) (get data "bindings") [])
       :skills   (or (:skills data)   (get data "skills")   [])})))

;; ---------------------------------------------------------------------------
;; Pure: find-manifest-by-nanoid
;; ---------------------------------------------------------------------------

(defn find-manifest-by-nanoid
  "Find first manifest in a sequence with matching nanoid.
  Returns the manifest map or nil.
  Mirrors Python next((m for m in manifests if m.nanoid == nanoid), None)."
  [manifests nanoid]
  (some (fn [m]
          (when (= (or (:nanoid m) (get m "nanoid")) nanoid)
            m))
        manifests))

;; ---------------------------------------------------------------------------
;; Pure: build-deploy-reg-body
;; ---------------------------------------------------------------------------

(defn build-deploy-reg-body
  "Build the registerManifest XRPC request body from nono manifest data and nanoid.
  data is the raw JSON-LD map; nanoid overrides the one in data if needed.
  Mirrors Python reg_body construction in nono_deploy()."
  [data nanoid]
  {"@context"        "https://etzhayyim.com/ns/nono/v1"
   "@id"             (or (get data "@id") "")
   "name"            (or (:name data)     (get data "name")     "")
   "nanoid"          (or (:nanoid data)   (get data "nanoid")   nanoid)
   "type"            "nono"
   "bindings"        (or (:bindings data)         (get data "bindings")         [])
   "primitiveBackend" (or (:primitiveBackend data) (get data "primitiveBackend") [])
   "skills"          (or (:skills data)   (get data "skills")   [])
   "status"          "active"})

;; ---------------------------------------------------------------------------
;; Pure: build-build-command
;; ---------------------------------------------------------------------------

(defn build-build-command
  "Determine the build command for a nono worker directory.
  pkg-data is the parsed package.json map (nil if file doesn't exist).
  pnpm-lock-exists? is true if pnpm-lock.yaml is present.
  wrangler-exists? is true if wrangler.jsonc is present.
  Returns the command vector or nil if no build is possible.
  Mirrors Python build_cmd logic in nono_build()."
  [pkg-data pnpm-lock-exists? wrangler-exists?]
  (cond
    ;; package.json with scripts.build → use pnpm or npm
    (and pkg-data
         (seq (get (or (:scripts pkg-data) (get pkg-data "scripts") {}) "build")))
    (if pnpm-lock-exists?
      ["pnpm" "run" "build"]
      ["npm" "run" "build"])

    ;; wrangler.jsonc → dry-run wrangler build
    wrangler-exists?
    ["npx" "wrangler" "deploy" "--dry-run" "--outdir" "dist"]

    ;; nothing found
    :else nil))

;; ---------------------------------------------------------------------------
;; Pure: build-deploy-command
;; ---------------------------------------------------------------------------

(defn build-deploy-command
  "Build the wrangler deploy command for a nono worker.
  Returns a command vector.
  Mirrors Python subprocess.run(['npx', 'wrangler', 'deploy'], ...) in nono_deploy()."
  []
  ["npx" "wrangler" "deploy"])

;; ---------------------------------------------------------------------------
;; IO: default-http-fn
;; ---------------------------------------------------------------------------

(defn- default-http-fn
  "Real babashka.http-client dispatch."
  [{:keys [method url headers body]}]
  #?(:bb
     (let [opts (cond-> {:headers (or headers {}) :timeout 15000}
                  body (assoc :body (json/generate-string body)))
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
;; IO: default-proc-fn
;; ---------------------------------------------------------------------------

(defn- default-proc-fn
  "Real babashka.process/shell dispatch. Returns {:exit-code :stdout :stderr}."
  [{:keys [cmd cwd]}]
  #?(:bb
     (let [result (proc/shell {:dir cwd :out :string :err :string} (str/join " " cmd))]
       {:exit-code (:exit result) :stdout (:out result) :stderr (:err result)})
     :default
     (throw (ex-info "babashka.process only available under bb" {:cmd cmd}))))

;; ---------------------------------------------------------------------------
;; IO: default-fs-fn
;; ---------------------------------------------------------------------------

(defn- default-fs-fn
  "Real filesystem glob for nono-manifest.jsonld files.
  Returns a sequence of {:path str :data map} for successfully parsed manifests."
  [workspace-dir]
  #?(:bb
     (let [glob-results (fs/glob workspace-dir "**nono-manifest.jsonld")]
       (keep (fn [p]
               (try
                 (let [text (slurp (str p))
                       data (json/parse-string text true)]
                   {:path (str p) :data data})
                 (catch Exception _
                   nil)))
             glob-results))
     :default
     (throw (ex-info "babashka.fs only available under bb"
                     {:workspace-dir workspace-dir}))))

;; ---------------------------------------------------------------------------
;; IO: build-register-manifest-request (shape layer — pure enough for tests)
;; ---------------------------------------------------------------------------

(defn build-register-manifest-request
  "Build the HTTP request map for com.etzhayyim.actor.registerManifest.
  Mirrors Python httpx.post() in nono_deploy phase 2."
  [pds-url token reg-body]
  {:method  :post
   :url     (str pds-url "/xrpc/com.etzhayyim.actor.registerManifest")
   :headers {"Authorization" (str "Bearer " token)
             "Content-Type"  "application/json"}
   :body    reg-body})

;; ---------------------------------------------------------------------------
;; IO: load-manifests
;; ---------------------------------------------------------------------------

(defn load-manifests
  "Walk workspace-dir for nono-manifest.jsonld files and parse them.
  Returns a vector of manifest maps {:nanoid :name :bindings :skills}.
  Accepts :fs-fn in opts (injectable for testing).
  Mirrors Python _load_manifests()."
  [workspace-dir {:keys [fs-fn]
                   :or   {fs-fn default-fs-fn}}]
  (vec
   (keep (fn [{:keys [data]}]
           (parse-manifest-data data))
         (fs-fn workspace-dir))))

;; ---------------------------------------------------------------------------
;; IO: register-skills (dry-run aware)
;; ---------------------------------------------------------------------------

(defn register-skills
  "Register nono worker skills via XRPC registerManifest.
  With :dry-run? true, returns the request shape without making a network call.
  nm-data is the raw manifest data map; nanoid is the worker nanoid.
  Returns the response data map (or request shape on dry-run)."
  [pds-url token nm-data nanoid {:keys [dry-run? http-fn]
                                  :or   {dry-run? false http-fn default-http-fn}}]
  (let [reg-body (build-deploy-reg-body nm-data nanoid)
        req      (build-register-manifest-request pds-url token reg-body)]
    (if dry-run?
      {:dry-run true :request req}
      (let [resp (http-fn req)]
        (when (>= (:status resp) 400)
          (throw (ex-info (str "registerManifest HTTP " (:status resp))
                          {:status (:status resp) :body (:body resp)})))
        (json/parse-string (or (:body resp) "{}") true)))))

;; ---------------------------------------------------------------------------
;; IO: run-build (dry-run aware)
;; ---------------------------------------------------------------------------

(defn run-build
  "Run the build command for a nono worker target directory.
  With :dry-run? true, returns the command shape without executing.
  pkg-data is the parsed package.json map (or nil).
  pnpm-lock-exists? and wrangler-exists? are booleans.
  Returns {:exit-code :stdout :stderr} or {:dry-run true :command cmd} on dry-run."
  [target-dir pkg-data pnpm-lock-exists? wrangler-exists?
   {:keys [dry-run? proc-fn]
    :or   {dry-run? false proc-fn default-proc-fn}}]
  (let [cmd (build-build-command pkg-data pnpm-lock-exists? wrangler-exists?)]
    (if (nil? cmd)
      (throw (ex-info "no build command found (no scripts.build in package.json or wrangler.jsonc)"
                      {:target-dir target-dir}))
      (if dry-run?
        {:dry-run true :command cmd :cwd target-dir}
        (proc-fn {:cmd cmd :cwd target-dir})))))

;; ---------------------------------------------------------------------------
;; IO: run-deploy (dry-run aware)
;; ---------------------------------------------------------------------------

(defn run-deploy
  "Run npx wrangler deploy for a nono worker target directory.
  With :dry-run? true, returns the command shape without executing.
  Returns {:exit-code :stdout :stderr} or {:dry-run true :command cmd} on dry-run."
  [target-dir {:keys [dry-run? proc-fn]
                :or   {dry-run? false proc-fn default-proc-fn}}]
  (let [cmd (build-deploy-command)]
    (if dry-run?
      {:dry-run true :command cmd :cwd target-dir}
      (proc-fn {:cmd cmd :cwd target-dir}))))
