;; ported from 70-tools/etzhayyim-py/src/etzhayyim/yoroshiku.py — real port replacing the
;; unit_refactor stage-0 "TODO: port-failed" stubs. NS fixed
;; (etzhayyim-py.src.etzhayyim.yoroshiku -> etzhayyim.yoroshiku, the src/ source-root package
;; matching src/etzhayyim/yoroshiku.py per pyproject.toml).
;; Self-contained: the sibling shannon._resolve_root / authn._load_auth / auth.resolve_pds
;; helpers are inlined rather than (:require)-ing sibling stub namespaces; all host/file/env/
;; network I/O is behind #?(:clj ...). The httpx XRPC POST in register is the host network edge.
;;
;; yoroshiku (よろしく) — Onboarding and workspace welcome commands.
(ns etzhayyim.yoroshiku
  "yoroshiku (よろしく) — onboarding / workspace readiness.
  1:1 Clojure port of `src/etzhayyim/yoroshiku.py`. Readiness checks are string-keyed maps
  (the same shapes the Python dicts produced); host/file/env/network I/O at the #?(:clj ...) edge."
  (:require [clojure.string :as str]))

;; ── inlined sibling helpers (auth.resolve_pds / authn._AUTH_FILE+_load_auth) ───
(def ^:private default-pds "https://atproto.etzhayyim.com")

#?(:clj
   (defn- auth-file []
     (clojure.java.io/file (System/getProperty "user.home") ".etzhayyim" "auth.json")))

#?(:clj
   (defn- minimal-json-get
     "Best-effort extract a top-level string value for `key` from a flat auth.json — used only
      to read accessJwt/access_token without pulling in a JSON dep. Returns nil if absent."
     [text key]
     (let [m (re-find (re-pattern (str "\"" (java.util.regex.Pattern/quote key) "\"\\s*:\\s*\"([^\"]*)\"")) text)]
       (when m (second m)))))

#?(:clj
   (defn- load-auth
     "authn._load_auth — read ~/.etzhayyim/auth.json, returning a map (string-keyed) or {}."
     []
     (try
       (let [text (slurp (auth-file))]
         {"accessJwt"    (minimal-json-get text "accessJwt")
          "access_token" (minimal-json-get text "access_token")})
       (catch java.io.IOException _ {}))))

#?(:clj
   (defn resolve-pds
     "Normalize an explicitly supplied PDS URL, falling back to the public default."
     ([] (resolve-pds nil))
     ([pds]
      (str/replace (or (not-empty pds) default-pds) #"/+$" ""))))

;; ── workspace-root resolution (inlined shannon._resolve_root / _find_git_root) ─
#?(:clj
   (defn- find-git-root [start]
     (loop [p (.getCanonicalFile (clojure.java.io/file start))]
       (let [parent (.getParentFile p)]
         (cond
           (.exists (clojure.java.io/file p ".git")) (.getPath p)
           (nil? parent) (.getPath p)
           :else (recur parent))))))

#?(:clj
   (defn resolve-root [override]
     (if (and override (not (str/blank? (str override))))
       (.getPath (.getCanonicalFile (clojure.java.io/file (str override))))
       (find-git-root (System/getProperty "user.dir")))))

;; ── _auth_headers ──────────────────────────────────────────────────────────────
#?(:clj
   (defn auth-headers
     "Bearer auth headers from the stored session. Returns the header map, or raises an
      ex-info with :exit-code 1 (faithful to the Python sys.exit(1)) when not signed in."
     []
     (let [auth (load-auth)
           tok  (or (not-empty (get auth "accessJwt"))
                    (not-empty (get auth "access_token"))
                    "")]
       (if (str/blank? tok)
         (throw (ex-info "not signed in — run: etzhayyim authn signin" {:exit-code 1}))
         {"Authorization" (str "Bearer " tok)
          "Content-Type"  "application/json"}))))

;; ── _run_readiness (pure given file-existence predicates) ──────────────────────
#?(:clj
   (defn run-readiness
     "Compute the 4 workspace readiness checks against a workspace directory path.
      Each check is a string-keyed map {name ok detail}. File I/O edge."
     [ws]
     (let [f          (fn [& parts] (apply clojure.java.io/file (str ws) parts))
           deps-ok    (.exists (f "deps.toml"))
           claude-ok  (.exists (f "CLAUDE.md"))
           apps-dir   (f "60-apps")
           apps-ok    (.exists apps-dir)
           apps-count (if apps-ok
                        (->> (file-seq apps-dir)
                             (filter #(and (.isFile ^java.io.File %)
                                           (= (.getName ^java.io.File %) "kotodama.jsonld")))
                             count)
                        0)
           auth-ok    (.exists (auth-file))]
       [{"name" "deps.toml"
         "ok" deps-ok
         "detail" (if deps-ok "deps.toml found" "deps.toml missing")}
        {"name" "CLAUDE.md"
         "ok" claude-ok
         "detail" (if claude-ok "CLAUDE.md found" "CLAUDE.md missing")}
        {"name" "60-apps"
         "ok" apps-ok
         "detail" (if apps-ok (str apps-count " apps") "missing")}
        {"name" "authn"
         "ok" auth-ok
         "detail" (if auth-ok "signed in" "not signed in")}])))

;; ── CLI verbs (host edge). Return JSON-ready data or the textual lines a
;;    click.echo would emit. ───────────────────────────────────────────────────
#?(:clj
   (defn yoroshiku
     "Top-level yoroshiku group body (invoke_without_command)."
     ([] (yoroshiku nil false))
     ([workspace-dir json-out]
      (let [ws      (resolve-root workspace-dir)
            checks  (run-readiness ws)
            passing (count (filter #(get % "ok") checks))]
        (if json-out
          {"passing" passing "total" (count checks) "checks" checks}
          (str/join "\n"
                    (cons (str "yoroshiku (よろしく): " passing "/" (count checks) " checks passing")
                          (map (fn [c]
                                 (str "  [" (if (get c "ok") "OK  " "WARN") "] "
                                      (get c "name") "  " (get c "detail")))
                               checks))))))))

#?(:clj
   (defn yoroshiku-check
     ([] (yoroshiku-check nil false))
     ([workspace-dir json-out]
      (let [ws     (resolve-root workspace-dir)
            checks (run-readiness ws)]
        (if json-out
          checks
          (str/join "\n"
                    (map (fn [c]
                           (str "  [" (if (get c "ok") "OK  " "WARN") "] "
                                (get c "name") "  " (get c "detail")))
                         checks)))))))

#?(:clj
   (defn yoroshiku-register
     "Register this workspace with the platform via the XRPC POST. Network edge.
      `http-post` is a (fn [url body-map headers] -> {:status :json}) injected by the host
      CLI (the httpx call); kept as a parameter so the port stays free of an HTTP dependency."
     ([http-post pds workspace-dir json-out]
      (let [ws      (resolve-root workspace-dir)
            pds-url (resolve-pds pds)
            resp    (http-post (str pds-url "/xrpc/com.etzhayyim.yoroshiku.registerWorkspace")
                               {"workspace" (str ws)}
                               (auth-headers))
            status  (:status resp)]
        (when-not (and (number? status) (<= 200 status 299))
          (throw (ex-info (str "XRPC error: HTTP " status) {:status status})))
        (let [data (:json resp)]
          (if json-out
            data
            (str "registered workspace: " (get data "id" ""))))))))
