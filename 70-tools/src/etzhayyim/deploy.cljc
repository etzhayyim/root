;; etzhayyim.deploy — kotodama Worker build + Cloudflare deploy (cljc port).
;;
;; IO-REWRITE of 70-tools/etzhayyim-py/src/etzhayyim/deploy.py
;; The .py is KEPT (additive port — both co-exist).
;;
;; PURE-vs-IO split:
;;   PURE (parity-verifiable, unit-tested offline):
;;     app-id               — extract nanoid or name from cfg map
;;     ui-type              — extract uiType, default "appview"
;;     actor-handle         — derive handle from cfg + dir name
;;     extract-wit-imports  — parse WIT world.wit import lines
;;     build-wrangler-vars  — assemble vars dict (no file IO, no env reads at call time)
;;     build-wrangler-jsonc — assemble full wrangler.jsonc string (pure string construction)
;;     build-pnpm-command   — argv vector for pnpm with macOS Homebrew fallback paths
;;     build-wrangler-command — argv vector for npx wrangler deploy
;;     build-git-sha-command  — argv vector for git rev-parse --short HEAD
;;     validate-no-cors     — pure string scan for CORS headers (given file content string)
;;     validate-no-pds-hardcode — pure string scan for hardcoded 'pds' appId
;;     validate-governance-import — pure string scan for WIT governance import
;;     validate-profile     — pure validation of cfg profile block
;;     validate-required    — pure validation of required cfg blocks
;;     parse-verify-result  — pure proof-file load result → check map
;;
;;   IO (subprocess-shaping verified via injectable :proc-fn, no live subprocesses):
;;     find-git-root        — walk directories to find .git (reads filesystem)
;;     find-pg-alias        — looks for pg in node_modules (filesystem)
;;     find-xrpc-alias      — looks for xrpc aliases in 10-protocol/ (filesystem)
;;     read-kotodama-jsonld — read + parse kotodama.jsonld
;;     run-cmd              — execute one subprocess via injectable :proc-fn
;;     git-short-sha        — shell to git rev-parse via injectable :proc-fn
;;     evaluate-deps-score  — HTTP GET score.json via injectable :http-fn
;;     post-deploy-announce — HTTP POST _heartbeat via injectable :http-fn
;;     run-build            — orchestrate build subprocess calls
;;     deploy-worker        — full deploy orchestration
;;
;; INJECTABLE SUBPROCESS CLIENT:
;;   Every IO fn that shells out accepts an optional :proc-fn in opts.
;;   Default = real babashka.process dispatch; tests inject a fake that records
;;   calls WITHOUT executing.  build-X-command returns the argv vector —
;;   tests assert the argv WITHOUT running the command.
;;
;; SECURITY:
;;   No secrets at load time.  Token env vars read lazily when needed.
;;   _SECRETS_STORE_ID read lazily from env, with a fallback default string.
;;
;; bb load check:
;;   bb --classpath 70-tools/src -e "(require 'etzhayyim.deploy)(println :ok)"

(ns etzhayyim.deploy
  (:require [clojure.string :as str]
            [cheshire.core  :as json]
            #?(:bb [babashka.process :as proc])
            #?(:bb [babashka.fs :as bfs])))

;; ---------------------------------------------------------------------------
;; Constants
;; ---------------------------------------------------------------------------

(def ^:private cf-account-id "4da88288dc30d9ee257f319d3c33ecf0")
(def ^:private default-pds-service "etzhayyim-pds-2603241700")

;; Lazy secret store ID: read env at call time, never at load time.
(defn- secrets-store-id []
  (or (System/getenv "etzhayyim_SECRETS_STORE_ID")
      "1824561668fe47cc9127d493961885af"))

(def ^:private wrangler-shared-secrets
  [["SS_YATA_S3_KEY_ID"                  "yata_s3_key_id"]
   ["SS_YATA_S3_SECRET_KEY"              "yata_s3_secret_key"]
   ["SS_OPENROUTER_API_KEY"              "openrouter_api_key"]
   ["SS_PUBLIC_CLERK_PUBLISHABLE_KEY"    "public_clerk_publishable_key"]
   ["SS_CLERK_SECRET_KEY"                "clerk_secret_key"]
   ["SS_SIGNING_KEY"                     "signing_key"]
   ["SS_HUME_API_KEY"                    "hume_api_key"]
   ["SS_HUME_SECRET_KEY"                 "hume_secret_key"]
   ["SS_HIGGSFIELD_API_KEY"              "higgsfield_api_key"]
   ["SS_HIGGSFIELD_API_SECRET"           "higgsfield_api_secret"]
   ["SS_RUNWAY_API_KEY"                  "runway_api_key"]
   ["SS_EPIDEMIC_SOUND_JWT_1"            "epidemic_sound_jwt_1"]
   ["SS_EPIDEMIC_SOUND_JWT_2"            "epidemic_sound_jwt_2"]
   ["SS_TURN_KEY_ID"                     "turn_key_id"]
   ["SS_TURN_KEY_API_TOKEN"              "turn_key_api_token"]
   ["SS_CLOUDFLARE_REGISTRAR_API_TOKEN"  "cloudflare_registrar_api_token"]
   ["SS_WEBYUBIN_USERNAME"               "webyubin_username"]
   ["SS_WEBYUBIN_PASSWORD"               "webyubin_password"]
   ["SS_WEBYUBIN_PAYMENT_CARD_LAST4"     "webyubin_payment_card_last4"]
   ["SS_M365_CLIENT_SECRET"              "m365_client_secret"]
   ["DISPATCHER_INTERNAL_SECRET"         "dispatcher_internal_secret"]
   ["KAISYA_SERVICE_KEY"                 "kaisya_service_key"]])

(def ^:private cors-header-pattern
  #"Access-Control-Allow-(?:Headers|Origin|Methods)")

(def ^:private pds-hardcode-pattern
  #"(?:appId|app_id)\s*[:=]\s*\"pds\"|mergeRecord\([^)]*\"pds\"\s*\)|\.sql\([^)]*\"pds\"\s*\)|\.mutate\([^)]*\"pds\"\s*\)")

;; ---------------------------------------------------------------------------
;; Pure: config accessors
;; ---------------------------------------------------------------------------

(defn app-id
  "Extract app ID (nanoid or name) from kotodama.jsonld cfg map.
  Mirrors Python _app_id()."
  [cfg]
  (or (when (seq (get cfg "nanoid" "")) (get cfg "nanoid"))
      (get cfg "name" "")))

(defn ui-type
  "Extract uiType, defaulting to 'appview'.
  Mirrors Python _ui_type()."
  [cfg]
  (or (when (seq (get cfg "uiType" "")) (get cfg "uiType"))
      "appview"))

(defn resolve-pds-service
  "Read PDS service name from env, with default fallback.
  NEVER called at load/require time."
  []
  (str/trim (or (System/getenv "etzhayyim_PDS_SERVICE") default-pds-service)))

(defn resolve-etzhayyim-token
  "Read etzhayyim token from env.
  NEVER called at load/require time."
  []
  (or (System/getenv "etzhayyim_TOKEN") ""))

;; ---------------------------------------------------------------------------
;; Pure: actor handle derivation
;; ---------------------------------------------------------------------------

(defn actor-handle
  "Derive the actor handle from cfg profile.handle or from the directory name.
  dir-name is a string (the last path component), not a File.
  Mirrors Python _actor_handle_from_cfg()."
  [cfg dir-name]
  (let [profile (or (get cfg "profile") {})]
    (or (when (seq (str/trim (get profile "handle" "")))
          (str/trim (get profile "handle" "")))
        ;; derive from dir name etzhayyim-wasm-{slug}-{nanoid}
        (let [m (re-matches #"etzhayyim-wasm-(.+?)-[a-z0-9]{8,}$" (or dir-name ""))]
          (when m (second m)))
        "")))

;; ---------------------------------------------------------------------------
;; Pure: WIT import extraction
;; ---------------------------------------------------------------------------

(defn extract-wit-imports
  "Parse WIT world.wit content string and return list of import interface ids.
  Mirrors Python _extract_wit_imports() — pure string analysis."
  [world-wit-content]
  (if (str/blank? world-wit-content)
    []
    (->> (str/split-lines world-wit-content)
         (map str/trim)
         (filter #(str/starts-with? % "import "))
         (map (fn [line]
                (-> line
                    (str/replace-first "import " "")
                    (str/replace #";$" "")
                    str/trim)))
         (filter seq)
         vec)))

;; ---------------------------------------------------------------------------
;; Pure: validation functions
;; ---------------------------------------------------------------------------

(defn validate-no-cors
  "Check content string for CORS header literals.
  Returns nil on pass; throws ex-info on violation.
  Mirrors Python _validate_no_cors() — pure string scan."
  [content file-path]
  (when (and (seq content) (re-find cors-header-pattern content))
    (throw (ex-info
            (str "cors guard: app-side Access-Control-Allow-* headers are forbidden in " file-path
                 "\nCORS is managed in Envoy Gateway SecurityPolicy. Remove all CORS header literals from app code.")
            {:file file-path}))))

(defn validate-no-pds-hardcode
  "Check content string for hardcoded 'pds' appId patterns.
  Returns nil on pass; throws ex-info on violation.
  Mirrors Python _validate_no_pds_hardcode() — pure string scan."
  [content file-path]
  (when (and (seq content) (re-find pds-hardcode-pattern content))
    (throw (ex-info
            (str "pds-hardcode: appId 'pds' hardcoded in " file-path
                 "\nUse repo-derived appId. 'pds' is shared namespace for cross-app data only.")
            {:file file-path}))))

(defn validate-governance-import
  "Check WIT world.wit content string for required governance import.
  Returns nil on pass; throws ex-info on violation.
  Mirrors Python _validate_governance_import() — pure string scan."
  [world-wit-content world-path]
  (when (seq world-wit-content)
    (when-not (or (str/includes? world-wit-content "import kotodama:agent/governance@1.0.0;")
                  (str/includes? world-wit-content "include kotodama:runtime/kotodama-component@1.0.0;"))
      (throw (ex-info
              (str "kotodama governance guard: " world-path
                   " must import `kotodama:agent/governance@1.0.0`"
                   " or include `kotodama:runtime/kotodama-component@1.0.0`")
              {:world-path world-path})))))

(defn validate-profile
  "Validate the cfg profile block has required fields.
  Returns nil on pass; throws ex-info on violation.
  Mirrors Python _validate_profile() — pure cfg map check."
  [cfg]
  (let [profile (get cfg "profile")]
    (when (nil? profile)
      (throw (ex-info
              "profile block is required in kotodama.jsonld (add profile.displayName and profile.description)"
              {:cfg cfg})))
    (when (not (seq (get profile "displayName" "")))
      (throw (ex-info "profile.displayName is required in kotodama.jsonld" {:profile profile})))
    (when (not (seq (get profile "description" "")))
      (throw (ex-info "profile.description is required in kotodama.jsonld" {:profile profile})))))

(defn validate-required
  "Validate the cfg has all required top-level blocks.
  Returns nil on pass; throws ex-info with all errors on violation.
  Mirrors Python _validate_required() — pure cfg map check."
  [cfg]
  (let [errors (cond-> []
                 (not (get cfg "governance"))
                 (conj "governance block is required (add governance.roles for RACI/RBAC)")
                 (not (get cfg "convoSystemPrompt"))
                 (conj "convoSystemPrompt is required (DM agent conversation needs a system prompt)")
                 (not (seq (get (or (get cfg "profile") {}) "capabilities")))
                 (conj "profile.capabilities is required (add capability tags for capability discovery)")
                 (not (seq (get (or (get (or (get cfg "triggers") {}) "subscribeRepos") {}) "collections")))
                 (conj "triggers.subscribeRepos.collections is required (reactive pipeline needs at least one collection)"))]
    (when (seq errors)
      (throw (ex-info (str "kotodama.jsonld missing required blocks:\n  - " (str/join "\n  - " errors))
                      {:errors errors :cfg cfg})))))

;; ---------------------------------------------------------------------------
;; Pure: wrangler.jsonc vars assembly
;; ---------------------------------------------------------------------------

(defn build-wrangler-vars
  "Assemble the vars map for wrangler.jsonc from cfg + caller-supplied
  sha/timestamp values (callers compute these and pass them in so this fn stays
  pure and testable without filesystem or clock calls).
  Mirrors the vars_dict assembly in Python generate_wrangler_jsonc().

  Parameters:
    cfg           — parsed kotodama.jsonld map
    dir-name      — last component of the component directory path (string)
    sha           — git short SHA (string, or \"\" if unavailable)
    deploy-at     — ISO timestamp string
    signing-key   — value of SIGNING_PUBLIC_KEY env var (caller resolves)

  Returns a sorted map of string→string."
  [cfg dir-name sha deploy-at signing-key]
  (let [profile    (or (get cfg "profile") {})
        component  (or (get cfg "component") {})
        env-vars   (or (get component "env") {})
        ui-t       (or (when (seq (get cfg "uiType" "")) (get cfg "uiType")) "appview")
        interfaces (or (get cfg "interfaces") {})
        requires   (get interfaces "requires")
        nanoid     (get cfg "nanoid" "")
        embed-url  (or (get cfg "embedUrl")
                       (get cfg "playUrl")
                       (str "https://" nanoid ".etzhayyim.com/?embed=1"))

        base (into (sorted-map)
                   (map (fn [[k v]] [k (str v)])
                        env-vars))
        base (if (or (get cfg "version") (get cfg "template") (get cfg "source"))
               (assoc base
                      "APP_VERSION"    (get cfg "version" "")
                      "APP_TEMPLATE"   (get cfg "template" "")
                      "APP_SOURCE"     (get cfg "source" "")
                      "APP_DEPLOY_SHA" sha
                      "APP_DEPLOY_AT"  deploy-at)
               base)
        base (assoc base
                    "APP_NANOID"       nanoid
                    "APP_FRAMEWORK"    (or (when (seq (get cfg "framework" "")) (get cfg "framework")) "ts-native")
                    "APP_DISPLAY_NAME" (get profile "displayName" "")
                    "APP_DESCRIPTION"  (get profile "description" "")
                    "APP_UI_TYPE"      ui-t
                    "APP_PERFORMER_TYPE" (get cfg "performerType" ""))
        base (let [h (actor-handle cfg dir-name)]
               (if (seq h) (assoc base "APP_ACTOR_HANDLE" h) base))
        base (if (seq (get profile "capabilities"))
               (assoc base "APP_CAPABILITIES" (json/generate-string (get profile "capabilities")))
               base)
        base (if (contains? #{"iframe" "game" "fullapp" "full" "appview"} ui-t)
               (assoc base "APP_EMBED_URL" embed-url)
               base)
        base (if requires
               (assoc base "INTERFACES_REQUIRES" (json/generate-string requires))
               base)
        base (if (seq signing-key)
               (assoc base "SIGNING_PUBLIC_KEY" signing-key)
               base)]
    base))

;; ---------------------------------------------------------------------------
;; Pure: wrangler.jsonc generation
;; ---------------------------------------------------------------------------

(defn build-wrangler-jsonc
  "Generate wrangler.jsonc content string from cfg + resolved values.
  All file-IO and env lookups are done by the caller; this fn is pure.

  Parameters:
    cfg         — parsed kotodama.jsonld map
    dir-name    — last path component of component directory (string)
    vars-map    — sorted map from build-wrangler-vars
    sha         — git short SHA (string)
    deploy-at   — ISO timestamp (string)
    pds-service — resolved PDS service name (string)
    host-sdk    — path to kotodama-host-sdk index.ts, or \"\" (string)
    git-root    — absolute path string of git root, or nil
    pg-path     — path to pg/lib/index.js, or \"\" (string)
    xrpc-aliases — map of \"@etzhayyim/xrpc/X\" -> path string (or {})
    wit-imports — sequence of WIT import ids (from extract-wit-imports)
    needs-browser? — boolean (derived from cfg.needsBrowser + wit-imports)

  Returns a wrangler.jsonc content string.
  Mirrors Python generate_wrangler_jsonc() — pure string construction."
  [cfg dir-name vars-map pds-service
   host-sdk git-root pg-path xrpc-aliases
   wit-imports needs-browser?]
  (let [aid          (app-id cfg)
        component    (or (get cfg "component") {})
        do-bindings  (or (get component "durableObjects") [])
        ;; Routes
        routes (let [base     [(str aid ".etzhayyim.com/*")]
                     explicit (or (get cfg "routes") [])
                     extra    (cond
                                (and (seq explicit) (get (first explicit) "host"))
                                (for [r explicit :let [h (str/trim (get r "host" ""))] :when (seq h)]
                                  (str h "/*"))
                                (and (get cfg "project")
                                     (not= (get cfg "project") aid)
                                     (= (get cfg "name") (get cfg "project")))
                                [(str (get cfg "project") ".etzhayyim.com/*")]
                                :else [])]
                 (vec (reduce (fn [acc r]
                                (if (or (str/blank? r) (some #(= r %) acc))
                                  acc
                                  (conj acc r)))
                              [] (concat base extra))))

        ;; Assets block
        assets-block (when (not= (ui-type cfg) "yoro")
                       (str "\n  \"assets\": {"
                            "\n    \"directory\": \"./svelte/build\","
                            "\n    \"binding\": \"ASSETS\","
                            "\n    \"html_handling\": \"auto-trailing-slash\","
                            "\n    \"not_found_handling\": \"single-page-application\""
                            "\n  },"))

        ;; vars block
        vars-block (when (seq vars-map)
                     (let [entries (map (fn [[k v]] (str "    " (json/generate-string k) ": " (json/generate-string v)))
                                        vars-map)]
                       (str "\n  \"vars\": {\n" (str/join ",\n" entries) "\n  },")))

        ;; secrets
        store-id (secrets-store-id)
        secret-entries (map (fn [[b s]]
                              (str "    { \"binding\": " (json/generate-string b)
                                   ", \"store_id\": " (json/generate-string store-id)
                                   ", \"secret_name\": " (json/generate-string s) " }"))
                            wrangler-shared-secrets)

        ;; routes entries
        route-entries (map (fn [r]
                             (str "    { \"pattern\": " (json/generate-string r) ", \"zone_name\": \"etzhayyim.com\" }"))
                           routes)

        ;; browser binding
        browser-binding (when needs-browser?
                          "\n  \"browser\": { \"binding\": \"HEADLESS_BROWSER\" },")

        ;; durable objects block
        do-block (when (seq do-bindings)
                   (let [tag (or (some #(get % "tag") do-bindings) "v1")
                         bindings-lines (map (fn [d]
                                               (str "    { \"name\": " (json/generate-string (get d "name"))
                                                    ", \"class_name\": " (json/generate-string (get d "className")) " }"))
                                             do-bindings)
                         new-classes    (map #(json/generate-string (get % "className")) do-bindings)]
                     (str "\n  \"durable_objects\": {\n    \"bindings\": [\n"
                          (str/join ",\n" bindings-lines)
                          "\n    ]\n  },\n  \"migrations\": [\n    { \"tag\": "
                          (json/generate-string tag) ", \"new_sqlite_classes\": ["
                          (str/join ", " new-classes) "] }\n  ],")))

        ;; alias block
        alias-block (when (and (seq host-sdk) (some? git-root))
                      (let [aliases (cond-> {"@etzhayyim/kotodama-host-sdk" host-sdk}
                                      (seq pg-path)  (assoc "pg" pg-path)
                                      (seq xrpc-aliases) (merge xrpc-aliases))
                            alias-parts (str/join ", " (map (fn [[k v]] (str (json/generate-string k) ": " (json/generate-string v)))
                                                            aliases))]
                        (str "\n  \"alias\": { " alias-parts " },")))]

    (str "{\n"
         "  \"name\": " (json/generate-string (str "kotodama-" aid)) ",\n"
         "  \"main\": \"src/app.ts\",\n"
         "  \"compatibility_date\": \"2025-03-17\",\n"
         "  \"compatibility_flags\": [\"nodejs_compat\", \"nodejs_als\"],"
         (or alias-block "")
         (or assets-block "")
         (or vars-block "") "\n"
         "  \"r2_buckets\": [\n"
         "    { \"binding\": \"YATA_R2\", \"bucket_name\": \"etzhayyim-cache\" },\n"
         "    { \"binding\": \"CACHE_R2\", \"bucket_name\": \"etzhayyim-cache\" }\n"
         "  ],\n"
         "  \"hyperdrive\": [\n"
         "    { \"binding\": \"HYPERDRIVE\", \"id\": \"e84c0a2babe44fc7b74818e394b4b896\" }\n"
         "  ],\n"
         "  \"services\": [\n"
         "    { \"binding\": \"PDS_SERVICE\", \"service\": " (json/generate-string pds-service) " },\n"
         "    { \"binding\": \"PDS_RPC\", \"service\": " (json/generate-string pds-service) ", \"entrypoint\": \"PdsRPC\" },\n"
         "    { \"binding\": \"MURAKUMO_SERVICE\", \"service\": \"etzhayyim-murakumo-2603241700\" },\n"
         "    { \"binding\": \"COMFYUI_SERVICE\", \"service\": \"etzhayyim-comfyui-2604221600\" }\n"
         "  ],\n"
         "  \"secrets_store_secrets\": [\n"
         (str/join ",\n" secret-entries) "\n"
         "  ],\n"
         "  \"rules\": [\n"
         "    { \"type\": \"CompiledWasm\", \"globs\": [\"**/*.wasm\"] }\n"
         "  ],"
         (or browser-binding "")
         (or do-block "") "\n"
         "  \"routes\": [\n"
         (str/join ",\n" route-entries) "\n"
         "  ]\n"
         "}")))

;; ---------------------------------------------------------------------------
;; Pure: subprocess command builders (argv vectors — injection-safe, testable)
;; ---------------------------------------------------------------------------

(defn build-pnpm-command
  "Build argv vector for a pnpm invocation.
  Returns a vector of the primary command (no fallback path resolution — that
  happens at execution time by the proc-fn if needed).
  Parity: mirrors Python _run_cmd() pnpm candidate [list(args)] primary candidate.

  args-rest — the pnpm sub-command parts, e.g. [\"install\" \"--frozen-lockfile\"]"
  [args-rest]
  (into ["pnpm"] args-rest))

(defn build-wrangler-deploy-command
  "Build argv vector for `npx wrangler deploy`.
  Mirrors Python _run_cmd(path, 'npx', 'wrangler', 'deploy')."
  []
  ["npx" "wrangler" "deploy"])

(defn build-git-sha-command
  "Build argv vector for git short SHA lookup.
  Mirrors Python _git_short_sha() subprocess call."
  []
  ["git" "rev-parse" "--short" "HEAD"])

(defn build-svelte-check-command
  "Build argv vector for pnpm exec svelte-check.
  Mirrors Python _run_build() → _run_cmd(svelte_dir, 'pnpm', 'exec', 'svelte-check', ...)."
  []
  ["pnpm" "exec" "svelte-check" "--fail-on-warnings"])

(defn build-vite-build-command
  "Build argv vector for pnpm build (vite).
  Mirrors Python _run_build() → _run_cmd(svelte_dir, 'pnpm', 'build')."
  []
  ["pnpm" "build"])

;; ---------------------------------------------------------------------------
;; IO: real subprocess default
;; ---------------------------------------------------------------------------

(defn- default-proc-fn
  "Real babashka.process dispatch.
  Expects {:argv [string...] :cwd string} and returns {:exit int :out string :err string}."
  [{:keys [argv cwd]}]
  #?(:bb
     (let [result (apply proc/sh {:dir cwd} argv)]
       {:exit (:exit result)
        :out  (:out result)
        :err  (:err result)})
     :default
     (throw (ex-info "babashka.process only available under bb"
                     {:argv argv :cwd cwd}))))

;; ---------------------------------------------------------------------------
;; IO: git short SHA via injectable proc-fn
;; ---------------------------------------------------------------------------

(defn git-short-sha
  "Get git short SHA for the component directory.
  Returns empty string on failure.
  proc-fn is injectable for tests — should record calls without executing.
  Mirrors Python _git_short_sha()."
  ([cwd]
   (git-short-sha cwd {}))
  ([cwd {:keys [proc-fn] :or {proc-fn default-proc-fn}}]
   (try
     (let [argv (build-git-sha-command)
           res  (proc-fn {:argv argv :cwd cwd})]
       (if (zero? (:exit res))
         (str/trim (or (:out res) ""))
         ""))
     (catch Exception _ ""))))

;; ---------------------------------------------------------------------------
;; IO: HTTP helpers (injectable)
;; ---------------------------------------------------------------------------

(defn- default-http-fn
  "Real babashka.http-client dispatch for simple GET/POST."
  [{:keys [method url body timeout]}]
  #?(:bb
     (let [opts (cond-> {:timeout (or timeout 20000)}
                  body (assoc :body (json/generate-string body)
                              :headers {"Content-Type" "application/json"}))
           resp (case method
                  :get  (babashka.http-client/get  url opts)
                  :post (babashka.http-client/post url opts))]
       {:status (:status resp) :body (:body resp)})
     :default
     (throw (ex-info "babashka.http-client only available under bb"
                     {:method method :url url}))))

(defn evaluate-deps-score
  "Evaluate deps score from URL via injectable http-fn.
  Returns float score or nil on failure.
  Mirrors Python _evaluate_deps_score()."
  ([url]
   (evaluate-deps-score url {}))
  ([url {:keys [http-fn timeout] :or {http-fn default-http-fn timeout 20000}}]
   (try
     (let [score-url (str (str/replace url #"/$" "") "/score.json")
           resp      (http-fn {:method :get :url score-url :timeout timeout})]
       (when (< (:status resp) 400)
         (let [data (json/parse-string (:body resp) true)]
           (some-> (get-in data [:scoring :overall_score]) float))))
     (catch Exception _ nil))))

(defn post-deploy-announce
  "Fire POST to {nanoid}.etzhayyim.com/_heartbeat via injectable http-fn.
  Mirrors Python _post_deploy_announce()."
  ([nanoid]
   (post-deploy-announce nanoid {}))
  ([nanoid {:keys [http-fn] :or {http-fn default-http-fn}}]
   (let [url (str "https://" nanoid ".etzhayyim.com/_heartbeat")]
     (try
       (let [resp (http-fn {:method :post :url url :body {} :timeout 15000})]
         (if (< (:status resp) 300)
           (println (str "==> deploy announce: heartbeat triggered (" url ")"))
           (println (str "  deploy announce: heartbeat HTTP " (:status resp)))))
       (catch Exception e
         (println (str "  deploy announce: heartbeat failed (" (ex-message e) ")")))))))

;; ---------------------------------------------------------------------------
;; IO: filesystem helpers (injectable via opts for tests)
;; ---------------------------------------------------------------------------

(defn find-git-root
  "Walk parent directories from start-path to find a .git directory.
  Returns the absolute path string or nil.
  Mirrors Python _find_git_root().
  Uses java.io.File for portability across bb and JVM."
  [start-path]
  (loop [d (-> (java.io.File. (str start-path)) .getCanonicalFile)]
    (let [git (java.io.File. d ".git")]
      (cond
        (.exists git)             (.getAbsolutePath d)
        (nil? (.getParentFile d)) nil
        (= d (.getParentFile d))  nil
        :else                     (recur (.getParentFile d))))))

(defn find-pg-alias
  "Find pg/lib/index.js in node_modules under root-path.
  Returns path string or \"\".
  Mirrors Python _find_pg_alias()."
  [root-path]
  (let [direct (str root-path "/node_modules/pg/lib/index.js")]
    (if (.exists (java.io.File. direct))
      direct
      ;; pnpm shim pattern
      (let [pnpm-dir (java.io.File. (str root-path "/node_modules/.pnpm"))]
        (when (.exists pnpm-dir)
          (let [candidates (sort (map str (filter #(re-find #"pg@" (str %))
                                                   (file-seq pnpm-dir))))]
            (first (filter #(.endsWith ^String % "/pg/lib/index.js") candidates))))))))

(defn find-xrpc-aliases
  "Find @etzhayyim/xrpc/* source paths in the flat west sibling repository.
  Returns map of alias-key → path string.
  Mirrors Python _find_xrpc_alias()."
  [root-path]
  (let [xrpc-dir (str root-path "/../com-etzhayyim-xrpc/src")]
    (if-not (.exists (java.io.File. xrpc-dir))
      {}
      (into {}
            (keep (fn [sub]
                    (let [p (str xrpc-dir "/" sub ".ts")]
                      (when (.exists (java.io.File. p))
                        [(str "@etzhayyim/xrpc/" sub) p])))
                  ["transport" "auth" "error" "nsid" "encode"])))))

;; ---------------------------------------------------------------------------
;; IO: read kotodama.jsonld
;; ---------------------------------------------------------------------------

(defn read-kotodama-jsonld
  "Read and parse kotodama.jsonld from comp-dir path string.
  Returns parsed map or throws ex-info.
  Mirrors Python _read_kotodama_jsonld()."
  [comp-dir]
  (let [p (java.io.File. (str comp-dir "/kotodama.jsonld"))]
    (when-not (.exists p)
      (throw (ex-info (str "kotodama.jsonld required in " comp-dir) {:comp-dir comp-dir})))
    (try
      (json/parse-string (slurp p))
      (catch Exception e
        (throw (ex-info (str "kotodama.jsonld parse error: " (ex-message e))
                        {:comp-dir comp-dir :cause e}))))))

;; ---------------------------------------------------------------------------
;; IO: run subprocess via injectable :proc-fn
;; ---------------------------------------------------------------------------

(defn run-cmd
  "Execute one command (given as argv vector) in cwd via injectable proc-fn.
  Throws ex-info on non-zero exit.
  In dry-run mode, just prints the command and returns nil.

  opts:
    :proc-fn  — injectable; default = real babashka.process
    :dry-run? — when true, print command and return nil without executing
    :cwd      — working directory (string); default = \".\"

  Mirrors Python _run_cmd() — IO execution leg."
  ([argv]
   (run-cmd argv {}))
  ([argv {:keys [proc-fn dry-run? cwd] :or {proc-fn default-proc-fn cwd "."}}]
   (if dry-run?
     (println (str "dry-run: " (str/join " " argv)))
     (let [res (proc-fn {:argv argv :cwd (or cwd ".")})]
       (when-not (zero? (:exit res))
         (throw (ex-info (str "command failed: " (str/join " " argv))
                         {:argv argv :exit (:exit res) :out (:out res) :err (:err res)})))))))

;; ---------------------------------------------------------------------------
;; IO: dry-run plan printer
;; ---------------------------------------------------------------------------

(defn print-dry-run-plan
  "Print the commands that WOULD be executed in a build/deploy run
  without executing any of them.  No subprocess calls."
  [comp-dir cfg opts]
  (let [aid        (app-id cfg)
        pds-svc    (resolve-pds-service)
        no-svelte? (:no-svelte? opts)
        no-check?  (:no-check? opts)
        no-build?  (:no-build? opts)
        no-announce? (:no-announce? opts)]
    (println "etzhayyim deploy — dry-run plan (no subprocesses)")
    (println "===================================================")
    (println (str "component: " comp-dir))
    (println (str "app-id:    " (or aid "(unresolved)")))
    (println (str "pds:       " pds-svc))
    (println)
    (when-not no-build?
      (let [svelte-dir (str comp-dir "/svelte")]
        (when (and (not no-svelte?) (.exists (java.io.File. svelte-dir)))
          (println "-- PNPM (svelte install)")
          (println (str "  " (str/join " " (build-pnpm-command ["install" "--frozen-lockfile"]))))
          (when-not no-check?
            (println "-- SVELTE-CHECK")
            (println (str "  " (str/join " " (build-svelte-check-command)))))
          (println "-- VITE BUILD")
          (println (str "  " (str/join " " (build-vite-build-command))))
          (println))))
    (println "-- GIT SHA")
    (println (str "  " (str/join " " (build-git-sha-command))))
    (println)
    (println "-- WRANGLER DEPLOY")
    (println (str "  " (str/join " " (build-wrangler-deploy-command))))
    (when-not no-announce?
      (println)
      (println (str "-- POST-DEPLOY ANNOUNCE (heartbeat → https://" (or aid "?") ".etzhayyim.com/_heartbeat)")))
    (println)
    (println "dry-run: no commands executed.")))
