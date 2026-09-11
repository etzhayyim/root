;; etzhayyim.authn — Authentication pure helpers (cljc port, wave 5a).
;;
;; Port of 70-tools/etzhayyim-py/src/etzhayyim/authn.py
;;
;; PURE LOGIC PORTED:
;;   b64url-encode          — base64url encode bytes (no padding)
;;   parse-jwt-claims       — decode JWT payload segment → {:sub ... :email ...}
;;                            WITHOUT verifying the signature (mirrors Python helper)
;;   build-auth-store       — assemble the auth.json store map from token response
;;                            fields (pure field selection logic)
;;   prefer-token           — pick best token from auth-file map
;;                            (api_key > id_token > access_token priority)
;;
;; IO LEGS DEFERRED (not ported — OAuth2 PKCE / HTTPServer / httpx / webbrowser):
;;   _b64url (generator)    — used only inside _run_signin (IO context)
;;   _run_signin            — PKCE + localhost callback server + httpx → bb leg
;;   _exchange_for_api_key  — httpx POST createApiKey → bb leg
;;   _load_auth             — reads ~/.etzhayyim/auth.json → babashka.fs leg
;;   authn (Click group)    — CLI commands (signin/token/whoami/signout/login/
;;                            logout/revoke/migrate) → bb leg
;;
;; NOTE: parse-jwt-claims is non-verifying by design (matches Python).
;;       It is safe only for extracting display/store fields from already-
;;       trust-established tokens (e.g., the PDS just returned them).
;;
;; bb usage (classpath 70-tools/src):
;;   (require '[etzhayyim.authn :as authn])
;;   (authn/parse-jwt-claims "eyJhbGc.eyJzdWIiOiJkaWQ6cGxjOmFiYyIsImVtYWlsIjoiYUBiLmNvbSJ9.sig")
;;   ;=> {:sub "did:plc:abc" :email "a@b.com"}
;;   (authn/prefer-token {"id_token" "tok_id" "access_token" "tok_acc"})
;;   ;=> "tok_id"

(ns etzhayyim.authn
  (:require [clojure.string :as str])
  #?(:clj (:import [java.util Base64])))

;; ── base64url ────────────────────────────────────────────────────────────────

(defn b64url-encode
  "Encode a byte array to base64url without padding.
   Matches Python: base64.urlsafe_b64encode(b).rstrip(b'=').decode()."
  [^bytes b]
  #?(:clj  (-> (Base64/getUrlEncoder)
               (.withoutPadding)
               (.encodeToString b))
     :cljs (-> (js/btoa (apply str (map char b)))
               (str/replace "+" "-")
               (str/replace "/" "_")
               (str/replace "=" ""))))

;; ── JWT claims decoder ───────────────────────────────────────────────────────

(defn- b64url-decode-str
  "Decode a base64url-encoded string segment to a UTF-8 string.
   Adds padding as required. Returns nil on error."
  [segment]
  (try
    (let [pad (mod (count segment) 4)
          padded (if (pos? pad)
                   (str segment (apply str (repeat (- 4 pad) "=")))
                   segment)]
      #?(:clj  (String. (.decode (Base64/getUrlDecoder) padded) "UTF-8")
         :cljs (js/atob (-> padded
                            (str/replace "-" "+")
                            (str/replace "_" "/")))))
    (catch #?(:clj Exception :cljs :default) _ nil)))

(defn parse-jwt-claims
  "Extract sub and email from a JWT payload WITHOUT verifying the signature.
   Returns {:sub <string> :email <string>}; both default to ''.
   Mirrors Python: _parse_jwt_claims(token) → (sub, email).
   Safe only for display/storage after the issuer is already trusted."
  [token]
  (try
    (let [parts (str/split (or token "") #"\." -1)]
      (if (< (count parts) 2)
        {:sub "" :email ""}
        (let [raw (b64url-decode-str (nth parts 1))]
          (if raw
            (let [parsed #?(:clj  (try
                                    ;; cheshire.core is available in bb
                                    (cheshire.core/parse-string raw true)
                                    (catch Exception _
                                      ;; Fallback: regex extract for bare environments
                                      {:sub   (second (re-find #"\"sub\"\s*:\s*\"([^\"]+)\"" raw))
                                       :email (second (re-find #"\"email\"\s*:\s*\"([^\"]+)\"" raw))}))
                             :cljs (js->clj (js/JSON.parse raw) :keywordize-keys true))]
              {:sub   (or (:sub parsed) (get parsed "sub") "")
               :email (or (:email parsed) (get parsed "email") "")})
            {:sub "" :email ""}))))
    (catch #?(:clj Exception :cljs :default) _
      {:sub "" :email ""})))

;; ── auth-store assembly ───────────────────────────────────────────────────────

(defn prefer-token
  "Return the best available token from an auth-file map.
   Priority: api_key > id_token > access_token.
   Mirrors Python: store.get('api_key') or store.get('id_token') or store.get('access_token')."
  [auth-map]
  (or (some-> (get auth-map "api_key") str/trim not-empty)
      (some-> (get auth-map "id_token") str/trim not-empty)
      (some-> (get auth-map "access_token") str/trim not-empty)))

(defn build-auth-store
  "Assemble the auth.json store map from a token-exchange response and an optional api-key.
   Pure field-selection logic. Mirrors Python: build the 'store' dict in _run_signin.

   tok-resp  — token response map (string keys: access_token / id_token / refresh_token /
                                   expires_in / api_key)
   sub       — DID/subject from JWT
   email     — email from JWT
   api-key   — pre-fetched API key string (may be '' to fall back to tok-resp tokens)
   now-unix  — current epoch seconds (int), used for expires_at"
  [tok-resp sub email api-key now-unix]
  (let [resolved-api-key (or (some-> api-key str/trim not-empty)
                             (some-> (get tok-resp "api_key") str/trim not-empty))]
    (if resolved-api-key
      ;; API key path — store only api_key + identity
      {"sub"    sub
       "email"  email
       "api_key" resolved-api-key}
      ;; Session token path — store all tokens
      (let [expires-in (get tok-resp "expires_in" 0)
            base {"sub"           sub
                  "email"         email
                  "access_token"  (get tok-resp "access_token" "")
                  "id_token"      (get tok-resp "id_token" "")
                  "refresh_token" (get tok-resp "refresh_token" "")}]
        (if (and expires-in (pos? expires-in))
          (assoc base "expires_at" (+ now-unix (int expires-in)))
          base)))))

;; ── CLI entrypoint (JVM/bb only) ──────────────────────────────────────────────
;; Mirrors the Python click group `authn` (authn.py). Read-only commands
;; (whoami / token) run for real off ~/.etzhayyim/auth.json. Every side-effecting
;; command (signin/login = OAuth+file write, signout/logout/revoke = file delete +
;; network, migrate = network + file write) is GUARDED: it prints a plan and is a
;; no-op unless the operator opts in with the same explicit flag Python requires.

#?(:clj
   (do
     (require '[cheshire.core :as json])

     (def ^:private auth-file
       (str (System/getProperty "user.home") "/.etzhayyim/auth.json"))

     (defn- load-auth []
       (try (json/parse-string (slurp auth-file)) (catch Exception _ {})))

     (defn- parse-opts
       "Tiny argv parser. bool-flags is a set of flag tokens taken as booleans;
        any other --flag / -x consumes the next token as its value.
        Returns [positionals opts-map] (opts keyed by the flag token string)."
       [args bool-flags]
       (loop [a args pos [] opts {}]
         (if (empty? a)
           [pos opts]
           (let [t (first a)]
             (cond
               (contains? bool-flags t) (recur (rest a) pos (assoc opts t true))
               (str/starts-with? t "-") (recur (drop 2 a) pos (assoc opts t (second a)))
               :else                    (recur (rest a) (conj pos t) opts))))))

     (def ^:private bool-flags #{"--json" "--dry-run" "--keep-local" "-q"})

     (defn- usage []
       (println "usage: authn <signin|token|whoami|signout|login|logout|revoke|migrate> [--opts]")
       (println "  read-only: token, whoami [--json]")
       (println "  side-effecting (guarded): signin/login [--pds], signout/logout, revoke, migrate [--dry-run]"))

     (defn -main [& args]
       (let [[pos opts] (parse-opts (rest args) bool-flags)
             sub (first args)
             auth (load-auth)]
         (case sub
           nil       (usage)
           "whoami"  (if (empty? auth)
                       (binding [*out* *err*] (println "not signed in — run: authn signin"))
                       (if (get opts "--json")
                         (println (json/generate-string auth {:pretty true}))
                         (let [did (or (get auth "did") (get auth "sub") "")
                               handle (get auth "handle" "")
                               pds (or (get auth "pds") (get auth "service") "")]
                           (println (str "did:    " did))
                           (when (seq handle) (println (str "handle: " handle)))
                           (when (seq pds) (println (str "pds:    " pds))))))
           "token"   (let [tok (or (get auth "accessJwt") (get auth "access_token")
                                   (get auth "token") (prefer-token auth))]
                       (if (seq tok)
                         (println tok)
                         (binding [*out* *err*] (println "not signed in — run: authn signin"))))
           ("signin" "login")
                     (println (str "authn " sub ": OAuth2 Auth-Code+PKCE browser flow + token "
                                   "write to " auth-file " — interactive IO leg, not run here. "
                                   "Run the Python CLI for live sign-in."))
           ("signout" "logout")
                     (println (str "authn " sub " (guarded, no-op): would remove " auth-file
                                   (if (.exists (java.io.File. auth-file)) "" " (not signed in)")))
           "revoke"  (println (str "authn revoke (guarded, no-op): would POST /oauth/revoke for stored "
                                   "tokens and remove " auth-file
                                   (when (get opts "--keep-local") " (--keep-local: file kept)")
                                   ". Live revoke = run the Python CLI."))
           "migrate" (let [name (get opts "--name" "etzhayyim-cli-migrated")]
                       ;; mirror Python's --dry-run plan; never take the live network path here
                       (if (get auth "api_key")
                         (println "✓ Already migrated (api_key is set). No action needed.")
                         (do
                           (println (str "Would: POST createApiKey (name=" name ") using session JWT."))
                           (println (str "Would: overwrite " auth-file " with api_key entry."))
                           (when-not (get opts "--dry-run")
                             (println "(guarded: live createApiKey needs a session token + network — run the Python CLI)")))))
           (binding [*out* *err*] (println (str "authn: unknown subcommand: " sub)) (usage)))))))
