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
