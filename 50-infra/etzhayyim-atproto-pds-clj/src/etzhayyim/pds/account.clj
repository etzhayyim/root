(ns etzhayyim.pds.account
  "Account store + session auth for the PDS. Accounts (handle → did + PBKDF2 password
  hash) live in a small EDN file; sessions are HS256 JWTs signed with a PDS secret.
  Write methods can be auth-scoped (a Bearer whose `sub` did matches the repo) when
  PDS_REQUIRE_AUTH is set — otherwise writes stay open (operator-gated at the network)."
  (:require [cheshire.core :as json]
            [clojure.java.io :as io]
            [clojure.edn :as edn]
            [clojure.string :as str])
  (:import [javax.crypto Mac SecretKeyFactory]
           [javax.crypto.spec PBEKeySpec SecretKeySpec]
           [java.security MessageDigest SecureRandom]
           [java.util Base64]))

;; ── base64url ────────────────────────────────────────────────────────────────

(defn- b64url [^bytes b] (-> (.encodeToString (Base64/getUrlEncoder) b) (str/replace "=" "")))
(defn- b64url-dec ^bytes [^String s]
  (.decode (Base64/getUrlDecoder) (str s (apply str (repeat (mod (- 4 (mod (count s) 4)) 4) "=")))))

;; ── password hashing (PBKDF2-HMAC-SHA256) ────────────────────────────────────

(defn- pbkdf2 ^bytes [^String password ^bytes salt]
  (.getEncoded (.generateSecret (SecretKeyFactory/getInstance "PBKDF2WithHmacSHA256")
                                (PBEKeySpec. (.toCharArray password) salt 100000 256))))

(defn- load-accounts [path] (if (.exists (io/file path)) (edn/read-string (slurp path)) {}))
(defn- save-accounts [path m] (io/make-parents (io/file path)) (spit path (pr-str m)))

(defn create-account
  "Register handle → did with a salted PBKDF2 password hash. Returns {:did :handle}."
  [path {:keys [handle password did]}]
  (let [accounts (load-accounts path)
        salt (let [b (byte-array 16)] (.nextBytes (SecureRandom.) b) b)
        did (or did (str "did:web:" handle))]
    (when (get accounts handle) (throw (ex-info "handle taken" {:handle handle})))
    (save-accounts path (assoc accounts handle {:did did :salt (b64url salt) :hash (b64url (pbkdf2 password salt))}))
    {:did did :handle handle}))

(defn verify-password
  "Return the did if (handle, password) is valid, else nil."
  [path handle password]
  (when-let [a (get (load-accounts path) handle)]
    (when (= (:hash a) (b64url (pbkdf2 password (b64url-dec (:salt a))))) (:did a))))

(defn account-did [path handle] (:did (get (load-accounts path) handle)))

;; ── session JWT (HS256) ──────────────────────────────────────────────────────

(defn- hmac ^bytes [^bytes secret ^bytes msg]
  (let [m (Mac/getInstance "HmacSHA256")] (.init m (SecretKeySpec. secret "HmacSHA256")) (.doFinal m msg)))

(defn- now-s [] (quot (System/currentTimeMillis) 1000))

(defn make-jwt
  "Issue an HS256 session JWT for `did`, expiring in `ttl` seconds (default 24h)."
  ([^bytes secret did] (make-jwt secret did 86400))
  ([^bytes secret did ttl]
   (let [now (now-s)
         h (b64url (.getBytes "{\"alg\":\"HS256\",\"typ\":\"JWT\"}" "UTF-8"))
         p (b64url (.getBytes (json/generate-string {:sub did :iss "etzhayyim-pds" :iat now :exp (+ now ttl)}) "UTF-8"))
         sig (b64url (hmac secret (.getBytes (str h "." p) "UTF-8")))]
     (str h "." p "." sig))))

(defn verify-jwt
  "Return the `sub` did if the token's HS256 signature checks out AND it is not
  expired, else nil. Accepts an optional `Bearer ` prefix."
  [^bytes secret token]
  (when token
    (let [token (str/replace token #"^Bearer +" "")
          parts (str/split token #"\.")]
      (when (= 3 (count parts))
        (let [[h p sig] parts]
          (when (= sig (b64url (hmac secret (.getBytes (str h "." p) "UTF-8"))))
            (let [claims (json/parse-string (String. (b64url-dec p) "UTF-8") true)]
              (when (or (nil? (:exp claims)) (> (:exp claims) (now-s)))
                (:sub claims)))))))))

(defn secret-from-key
  "Derive a stable HMAC secret from the persisted signing key's bytes."
  ^bytes [^bytes key-encoded]
  (.digest (MessageDigest/getInstance "SHA-256") key-encoded))
