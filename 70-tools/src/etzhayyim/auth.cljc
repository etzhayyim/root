;; etzhayyim.auth — Auth helpers: token resolution, header construction (cljc port, wave 5a).
;;
;; Port of 70-tools/etzhayyim-py/src/etzhayyim/auth.py
;;
;; PURE LOGIC PORTED:
;;   default-pds            — constant default PDS URL
;;   service-auth-nsid      — constant for scoped JWT bootstrap NSID
;;   scoped-jwt-ttl         — constant TTL (seconds)
;;   scoped-jwt-skew        — constant clock-skew guard (seconds)
;;   scoped-cache-key       — SHA-256 prefix + nsid → stable cache key string
;;   scoped-auth-enabled?   — parse etzhayyim_SCOPED_AUTH env var → boolean
;;   resolve-pds            — read etzhayyim_PDS_URL env var, strip trailing slash
;;   resolve-org-hint       — env + DID prefix logic → org hint string or nil
;;   auth-headers           — assemble Authorization/X-Active-DID/X-etzhayyim-Org-Id map
;;                            from token/did/org strings (pure — no I/O at call site)
;;   audience-from-pds-url  — extract did:web:<hostname> from a PDS URL string
;;   scoped-jwt-ttl-cache   — cache-eligible? expiry check (token,exp,now → bool)
;;   build-token-request    — build the XRPC POST payload map for getServiceAuth
;;
;; IO LEGS DEFERRED (not ported — keychain subprocess / httpx / threading):
;;   _read_keychain         — macOS security subprocess → bb leg (future)
;;   _load_auth_file        — reads ~/.etzhayyim/auth.json → babashka.fs leg
;;   resolve_token          — env > keychain > auth file → bb leg
;;   resolve_active_did     — reads auth file → bb leg
;;   mint_scoped_jwt        — httpx POST + cache (threading.Lock) → bb leg
;;   scoped_auth_headers    — calls mint_scoped_jwt → deferred
;;
;; NOTE: scoped-cache-key uses java.security.MessageDigest (available in bb/JVM).
;;       In SCI/WASM contexts use a pure implementation or skip this fn.
;;
;; bb usage (classpath 70-tools/src):
;;   (require '[etzhayyim.auth :as auth])
;;   (auth/scoped-cache-key "mytoken" "com.atproto.server.getServiceAuth")
;;   ;=> "a1b2c3d4e5f60011:com.atproto.server.getServiceAuth"
;;   (auth/auth-headers "mytoken" "did:plc:abc" "did:plc:abc")
;;   ;=> {"Authorization" "Bearer mytoken" "X-Active-DID" "did:plc:abc" ...}

(ns etzhayyim.auth
  (:require [clojure.string :as str]))

;; ── constants ─────────────────────────────────────────────────────────────────

(def default-pds
  "Default PDS base URL."
  "https://atproto.etzhayyim.com")

(def service-auth-nsid
  "Bootstrap NSID for com.atproto.server.getServiceAuth — skip-looping guard."
  "com.atproto.server.getServiceAuth")

(def scoped-jwt-ttl
  "Short-lived scoped JWT lifetime in seconds."
  300)

(def scoped-jwt-skew
  "Clock-skew guard subtracted from TTL for cache expiry."
  10)

;; ── pure helpers ──────────────────────────────────────────────────────────────

(defn scoped-cache-key
  "Stable cache key for (base-token, nsid) pair.
   Uses first 16 hex chars of SHA-256(base-token) + ':' + nsid.
   Matches Python: hashlib.sha256(base_token.encode()).hexdigest()[:16] + ':' + nsid.
   Falls back to first 16 chars of base-token if MessageDigest unavailable."
  [base-token nsid]
  (let [prefix (try
                 #?(:clj  (let [md  (java.security.MessageDigest/getInstance "SHA-256")
                                bts (.digest md (.getBytes ^String base-token "UTF-8"))
                                hex (apply str (map #(format "%02x" (bit-and % 0xff)) bts))]
                             (subs hex 0 16))
                    :cljs (subs base-token 0 (min 16 (count base-token))))
                 (catch #?(:clj Exception :cljs :default) _
                   (subs (or base-token "") 0 (min 16 (count (or base-token ""))))))]
    (str prefix ":" nsid)))

(defn scoped-auth-enabled?
  "Returns true if etzhayyim_SCOPED_AUTH env var is not 'off', '0', or 'false'.
   Python: v not in ('off', '0', 'false') — case-insensitive.
   Accepts an env-value string (or nil = enabled)."
  [env-value]
  (let [v (str/lower-case (str/trim (or env-value "")))]
    (not (contains? #{"off" "0" "false"} v))))

(defn resolve-pds
  "Return PDS base URL from env-value (etzhayyim_PDS_URL), stripping trailing slashes.
   Falls back to default-pds.
   Pure: call with (System/getenv \"etzhayyim_PDS_URL\") from bb."
  [env-value]
  (str/replace (or (some-> env-value str/trim not-empty) default-pds)
               #"/+$" ""))

(defn resolve-org-hint
  "Return org hint string or nil.
   Logic: if org-env non-empty → return it;
          else if active-did starts with 'did:plc:' → return active-did;
          else nil.
   Mirrors Python: resolve_org_hint()."
  [org-env active-did]
  (let [org (some-> org-env str/trim not-empty)]
    (or org
        (when (and active-did (str/starts-with? active-did "did:plc:"))
          active-did))))

(defn auth-headers
  "Assemble auth header map from resolved token, active DID, and org hint.
   All three args are strings or nil.
   Pure — no I/O. Mirrors Python: auth_headers()."
  [token active-did org-hint]
  (cond-> {}
    (some-> token str/trim not-empty) (assoc "Authorization" (str "Bearer " (str/trim token)))
    (some-> active-did str/trim not-empty) (assoc "X-Active-DID" (str/trim active-did))
    (some-> org-hint str/trim not-empty)   (assoc "X-etzhayyim-Org-Id" (str/trim org-hint))))

(defn audience-from-pds-url
  "Extract 'did:web:<hostname>' from a PDS URL string.
   Returns '' when no hostname can be parsed.
   Mirrors Python: urlparse(pds_url).hostname → 'did:web:<hostname>'."
  [pds-url]
  (if-let [host (second (re-find #"^https?://([^/:?#]+)" (or pds-url "")))]
    (str "did:web:" host)
    ""))

(defn cache-hit?
  "Return true if a cached (token, expiry-unix) pair is still valid.
   now-unix = current epoch seconds (float or int).
   Matches Python: if now < exp: return token."
  [exp-unix now-unix]
  (< now-unix exp-unix))

(defn build-token-request
  "Build the POST payload map for com.atproto.server.getServiceAuth.
   audience = 'did:web:<pds-host>'; lxm = NSID; exp = epoch-seconds int.
   Mirrors Python: payload = {'lxm': nsid, 'exp': exp_unix}."
  [audience lxm exp-unix]
  (cond-> {"lxm" lxm "exp" exp-unix}
    (not-empty audience) (assoc "aud" audience)))
