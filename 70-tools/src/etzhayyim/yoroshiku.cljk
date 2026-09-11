;; etzhayyim.yoroshiku — Workspace onboarding readiness (Clojure/bb port of yoroshiku.py).
;;
;; IO-REWRITE of 70-tools/etzhayyim-py/src/etzhayyim/yoroshiku.py
;; The .py is KEPT (additive port — both co-exist).
;;
;; PURE-vs-IO split:
;;   PURE (parity-verifiable, unit-tested offline):
;;     compute-readiness-checks  — given boolean results map + app-count, returns 4 check maps
;;     build-register-request    — shape for com.etzhayyim.yoroshiku.registerWorkspace POST
;;     format-check-line         — format a single check as [OK  ] / [WARN] display line
;;     format-readiness-summary  — format passing/total summary line
;;
;;   IO (request-shaping verified via injectable fn, not live calls):
;;     run-readiness-checks      — IO: fs.exists checks (injectable :fs-fn)
;;     register-workspace        — IO: XRPC registerWorkspace (injectable :http-fn, dry-run aware)
;;
;; INJECTABLE IO FUNCTIONS:
;;   :http-fn  — default real babashka.http-client
;;   :fs-fn    — default real clojure.java.io/file .exists
;;
;; PDS RESOLUTION:
;;   The library leg takes `pds-url` as a required argument and holds no default —
;;   callers say where to go. The `register` CLI leg resolves an omitted --pds
;;   through etzhayyim.auth/resolve-pds, so the only two hosts reachable are the
;;   one passed on the command line and the workspace-wide auth/default-pds.
;;   See the note above the `register` branch in -main.
;;
;; bb load check:
;;   bb --classpath 70-tools/src -e "(require 'etzhayyim.yoroshiku)(println :ok)"

(ns etzhayyim.yoroshiku
  (:require [clojure.string :as str]
            [cheshire.core  :as json]
            [etzhayyim.auth :as auth]
            #?(:bb [babashka.http-client :as http])
            #?(:bb [babashka.fs          :as fs])))

;; ---------------------------------------------------------------------------
;; Pure: compute-readiness-checks
;; ---------------------------------------------------------------------------

(defn compute-readiness-checks
  "Compute the 4 standard readiness checks from a map of boolean/count results.
  checks-map should have keys:
    :deps-toml  bool   — whether deps.toml exists
    :claude-md  bool   — whether CLAUDE.md exists
    :apps-dir   bool   — whether 60-apps/ directory exists
    :app-count  int    — number of kotodama.jsonld files found in 60-apps/
    :auth       bool   — whether ~/.etzhayyim/auth.json exists
  Returns a vector of 4 check maps {:name :ok :detail}.
  Mirrors Python _run_readiness() in yoroshiku.py."
  [{:keys [deps-toml claude-md apps-dir app-count auth]
    :or   {app-count 0}}]
  [{:name   "deps.toml"
    :ok     (boolean deps-toml)
    :detail (if deps-toml "deps.toml found" "deps.toml missing")}
   {:name   "CLAUDE.md"
    :ok     (boolean claude-md)
    :detail (if claude-md "CLAUDE.md found" "CLAUDE.md missing")}
   {:name   "60-apps"
    :ok     (boolean apps-dir)
    :detail (if apps-dir (str app-count " apps") "missing")}
   {:name   "authn"
    :ok     (boolean auth)
    :detail (if auth "signed in" "not signed in")}])

;; ---------------------------------------------------------------------------
;; Pure: build-register-request
;; ---------------------------------------------------------------------------

(defn build-register-request
  "Build the HTTP request map for com.etzhayyim.yoroshiku.registerWorkspace.
  Mirrors Python httpx.post(...) in yoroshiku_register()."
  [pds-url workspace-str token]
  {:method  :post
   :url     (str pds-url "/xrpc/com.etzhayyim.yoroshiku.registerWorkspace")
   :headers {"Authorization" (str "Bearer " token)
             "Content-Type"  "application/json"}
   :body    {:workspace workspace-str}})

;; ---------------------------------------------------------------------------
;; Pure: format-check-line
;; ---------------------------------------------------------------------------

(defn format-check-line
  "Format a single readiness check as a display string.
  check is {:name :ok :detail}.
  Mirrors Python output in _run_readiness() display loop."
  [{:keys [name ok detail]}]
  (str "  [" (if ok "OK  " "WARN") "] " name "  " detail))

;; ---------------------------------------------------------------------------
;; Pure: format-readiness-summary
;; ---------------------------------------------------------------------------

(defn format-readiness-summary
  "Format the passing/total summary line.
  checks is a seq of {:ok bool} maps.
  Mirrors Python click.echo(f'yoroshiku (よろしく): {passing}/{total} checks passing')."
  [checks]
  (let [total   (count checks)
        passing (count (filter :ok checks))]
    (str "yoroshiku (よろしく): " passing "/" total " checks passing")))

;; ---------------------------------------------------------------------------
;; IO: default-http-fn
;; ---------------------------------------------------------------------------

(defn- default-http-fn
  "Real babashka.http-client dispatch."
  [{:keys [method url headers body]}]
  #?(:bb
     (let [opts (cond-> {:headers (or headers {}) :timeout 30000}
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
;; IO: default-fs-fn
;; ---------------------------------------------------------------------------

(defn- default-fs-fn
  "Real filesystem checks.
  Returns {:deps-toml bool :claude-md bool :apps-dir bool :app-count int :auth bool}."
  [workspace-dir]
  #?(:bb
     (let [ws          (fs/path workspace-dir)
           deps-toml   (fs/exists? (fs/path ws "deps.toml"))
           claude-md   (fs/exists? (fs/path ws "CLAUDE.md"))
           apps-dir-p  (fs/path ws "60-apps")
           apps-dir    (fs/exists? apps-dir-p)
           app-count   (if apps-dir
                         (count (fs/glob apps-dir-p "**kotodama.jsonld"))
                         0)
           auth-path   (fs/path (System/getProperty "user.home") ".etzhayyim" "auth.json")
           auth        (fs/exists? auth-path)]
       {:deps-toml deps-toml
        :claude-md claude-md
        :apps-dir  apps-dir
        :app-count app-count
        :auth      auth})
     :default
     (throw (ex-info "babashka.fs only available under bb"
                     {:workspace-dir workspace-dir}))))

;; ---------------------------------------------------------------------------
;; IO: run-readiness-checks
;; ---------------------------------------------------------------------------

(defn run-readiness-checks
  "Run the 4 standard readiness checks against workspace-dir.
  Returns vector of 4 check maps {:name :ok :detail}.
  Accepts :fs-fn in opts for testing (injectable).
  Mirrors Python _run_readiness()."
  [workspace-dir {:keys [fs-fn]
                   :or   {fs-fn default-fs-fn}}]
  (let [raw (fs-fn workspace-dir)]
    (compute-readiness-checks raw)))

;; ---------------------------------------------------------------------------
;; IO: register-workspace (dry-run aware)
;; ---------------------------------------------------------------------------

(defn register-workspace
  "Register this workspace with the platform via registerWorkspace XRPC.
  With :dry-run? true, returns the request shape without making a network call.
  workspace-str is the absolute workspace path string.
  Returns the response data map (or request shape on dry-run)."
  [pds-url token workspace-str {:keys [dry-run? http-fn]
                                 :or   {dry-run? false http-fn default-http-fn}}]
  (let [req (build-register-request pds-url workspace-str token)]
    (if dry-run?
      {:dry-run true :request req}
      (let [resp (http-fn req)]
        (when (>= (:status resp) 400)
          (throw (ex-info (str "yoroshiku.registerWorkspace HTTP " (:status resp))
                          {:status (:status resp) :body (:body resp)})))
        (json/parse-string (or (:body resp) "{}") true)))))

;; ---------------------------------------------------------------------------
;; CLI entrypoint — mirrors the `yoroshiku` click group (JVM/bb only).
;;
;;   (default, no subcommand) — readiness checks + summary (read-only fs) → live.
;;   check                    — readiness checks, no summary (read-only fs) → live.
;;   register                 — XRPC registerWorkspace (write). -main DEFAULTS TO
;;                              DRY-RUN (the twin's :dry-run? path) printing the
;;                              request shape; live only with --execute + token.
;; ---------------------------------------------------------------------------

#?(:clj
   (do
     (defn- y-parse [args bool-flags]
       (loop [a (seq args) flags {} pos []]
         (if (empty? a)
           [flags pos]
           (let [tok (first a)]
             (cond
               (contains? bool-flags tok) (recur (rest a) (assoc flags tok true) pos)
               (str/starts-with? tok "--") (recur (drop 2 a) (assoc flags tok (second a)) pos)
               :else (recur (rest a) flags (conj pos tok)))))))

     (defn- y-ws [flags] (or (get flags "--workspace-dir") (System/getProperty "user.dir")))

     (defn- y-print-readiness [checks summary?]
       (when summary? (println (format-readiness-summary checks)))
       (doseq [c checks] (println (format-check-line c))))

     (defn -main [& args]
       (let [bool-flags #{"--json" "--execute"}
             [sub & rst] args
             [flags _pos] (y-parse rst bool-flags)]
         (case sub
           ("check" nil)
           (let [checks (run-readiness-checks (y-ws flags) {})]
             (if (get flags "--json")
               (println (json/generate-string checks {:pretty true}))
               (y-print-readiness checks (nil? sub))))
           "register"
           ;; `register` is the only subcommand that transmits a credential, so
           ;; the host it resolves must always be one somebody chose: the --pds
           ;; passed here, or the workspace-wide auth/default-pds. It used to
           ;; fall back to a literal "https://pds.local" — `.local` is the mDNS
           ;; namespace (RFC 6762), claimable by any host on the same link, so
           ;; `--execute` on a shared network could hand the bearer token to
           ;; whoever answered. auth/resolve-pds also trims and strips trailing
           ;; slashes, which the old `or` did not: a --pds of "  " previously
           ;; produced the non-URL "  /xrpc/...".
           ;;
           ;; Deliberately NOT reading etzhayyim_PDS_URL here: removing that
           ;; ambient read from this module's ported twin is what PR #3235
           ;; (30cd480c0f) did, and re-adding it would undo that.
           (let [pds   (auth/resolve-pds (get flags "--pds"))
                 token (or (System/getenv "E7M_TOKEN") "")
                 ws    (y-ws flags)
                 res   (register-workspace pds token ws
                                           {:dry-run? (not (get flags "--execute"))})]
             (if (get flags "--json")
               (println (json/generate-string res {:pretty true}))
               (if (:dry-run res)
                 (do (println "DRY-RUN (registerWorkspace not sent; pass --execute to send):")
                     (println (str "POST " (get-in res [:request :url])))
                     (println (str "  body: " (json/generate-string (get-in res [:request :body])))))
                 (println (str "registered workspace: " (get res "id" ""))))))
           (do (println "usage: yoroshiku [check|register] [--workspace-dir D] [--pds U] [--json] [--execute]")
               (println "  (no subcommand) — run readiness checks with summary")))))))
