;; etzhayyim.authz — Authorization pure helpers (cljc port, wave 5a).
;;
;; Port of 70-tools/etzhayyim-py/src/etzhayyim/authz.py
;;
;; TRIAGE RESULT: authz.py is almost entirely IO.
;;
;; Every command (create-api-key / list-api-keys / revoke-api-key / dids / switch)
;; makes an httpx call or writes to the auth file.  The only non-IO logic is:
;;
;;   controlled-dids   — deduplicate + prepend primary DID to the controlled list
;;                       (pure list-building; mirrors authz_dids command body)
;;   format-key-row    — format a single API-key entry as a display string
;;                       (mirrors the for-loop in authz_list_api_keys)
;;
;; IO LEGS DEFERRED (not ported — httpx XRPC / auth-file read-write):
;;   _token / _headers    — reads auth file + calls resolve_pds → bb leg
;;   authz_create_api_key — httpx POST createApiKey → bb leg
;;   authz_list_api_keys  — httpx GET listApiKeys → bb leg
;;   authz_revoke_api_key — httpx POST revokeApiKey → bb leg
;;   authz_dids           — reads auth file + displays → bb leg (list IO)
;;   authz_switch         — writes auth file → bb leg
;;
;; bb usage (classpath 70-tools/src):
;;   (require '[etzhayyim.authz :as authz])
;;   (authz/controlled-dids {"did" "did:plc:abc" "controlledDids" ["did:plc:xyz"]})
;;   ;=> ["did:plc:abc" "did:plc:xyz"]
;;   (authz/format-key-row {"id" "k1" "label" "main" "scopes" "read,write"})
;;   ;=> "  k1  main  read,write"

(ns etzhayyim.authz
  (:require [clojure.string :as str]))

;; ── pure helpers ─────────────────────────────────────────────────────────────

(defn controlled-dids
  "Return a deduplicated list of DIDs controlled by the current auth identity.
   Primary DID is prepended if not already present.
   Mirrors Python: dids = auth.get('controlledDids') or []; prepend primary.

   auth-map — string-keyed auth.json map."
  [auth-map]
  (let [dids    (vec (or (get auth-map "controlledDids") []))
        primary (str/trim (or (get auth-map "did" "") ""))]
    (if (and (not-empty primary) (not (some #{primary} dids)))
      (into [primary] dids)
      dids)))

(defn format-key-row
  "Format a single API-key entry as a display string.
   Mirrors Python: for k in keys: echo(f'  {id}  {label}  {scopes}').

   key-map — string-keyed map with 'id', 'label', 'scopes'."
  [key-map]
  (str "  "
       (or (get key-map "id") "")
       "  "
       (or (get key-map "label") "")
       "  "
       (or (get key-map "scopes") "")))

(defn format-did-row
  "Format a single DID entry as a display string, marking the active DID.
   Mirrors Python: for d in dids: echo(f'  {d}{ (active) if d == primary else }').

   did      — the DID string
   primary  — the active DID (or nil/'')"
  [did primary]
  (str "  " did
       (when (= did primary) " (active)")))

;; ── CLI entrypoint (JVM/bb only) ──────────────────────────────────────────────
;; Mirrors the Python click group `authz` (authz.py). Read-only `dids` runs for
;; real off ~/.etzhayyim/auth.json via controlled-dids/format-did-row. Network
;; commands (create-api-key / list-api-keys / revoke-api-key = XRPC) and the
;; file-writing `switch` are GUARDED no-ops here.

#?(:clj
   (do
     (require '[cheshire.core :as json])

     (def ^:private auth-file
       (str (System/getProperty "user.home") "/.etzhayyim/auth.json"))

     (defn- load-auth []
       (try (json/parse-string (slurp auth-file)) (catch Exception _ {})))

     (defn- parse-opts [args bool-flags]
       (loop [a args pos [] opts {}]
         (if (empty? a)
           [pos opts]
           (let [t (first a)]
             (cond
               (contains? bool-flags t) (recur (rest a) pos (assoc opts t true))
               (str/starts-with? t "-") (recur (drop 2 a) pos (assoc opts t (second a)))
               :else                    (recur (rest a) (conj pos t) opts))))))

     (def ^:private bool-flags #{"--json" "--test" "-q"})

     (defn- usage []
       (println "usage: authz <create-api-key|list-api-keys|revoke-api-key|dids|switch> [args] [--opts]")
       (println "  read-only: dids [--json]")
       (println "  network (guarded): create-api-key, list-api-keys, revoke-api-key <id>")
       (println "  file-write (guarded): switch <did>"))

     (defn -main [& args]
       (let [[pos opts] (parse-opts (rest args) bool-flags)
             sub (first args)
             auth (load-auth)]
         (case sub
           nil  (usage)
           "dids" (if (empty? auth)
                    (binding [*out* *err*] (println "not signed in — run: authn signin"))
                    (let [dids (controlled-dids auth)
                          primary (get auth "did" "")]
                      (if (get opts "--json")
                        (println (json/generate-string {"dids" dids} {:pretty true}))
                        (doseq [d dids] (println (format-did-row d primary))))))
           "create-api-key"
                (println (str "authz create-api-key (guarded, no-op): would POST "
                              "com.etzhayyim.auth.createApiKey (name="
                              (get opts "--name" "default") " scopes="
                              (get opts "--scopes" "read,write")
                              (when (get opts "--test") " test=true")
                              "). Live issue = run the Python CLI."))
           "list-api-keys"
                (println "authz list-api-keys (guarded, no-op): would GET com.etzhayyim.authz.listApiKeys. Live = run the Python CLI.")
           "revoke-api-key"
                (let [kid (first pos)]
                  (if kid
                    (println (str "authz revoke-api-key (guarded, no-op): would POST "
                                  "com.etzhayyim.authz.revokeApiKey id=" kid ". Live = run the Python CLI."))
                    (binding [*out* *err*] (println "authz revoke-api-key: missing KEY_ID argument"))))
           "switch"
                (let [did (first pos)]
                  (if did
                    (println (str "authz switch (guarded, no-op): would set active did=" did
                                  " in " auth-file ". Live = run the Python CLI."))
                    (binding [*out* *err*] (println "authz switch: missing DID argument"))))
           (binding [*out* *err*] (println (str "authz: unknown subcommand: " sub)) (usage)))))))
