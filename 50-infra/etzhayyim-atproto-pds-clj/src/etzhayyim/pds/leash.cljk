(ns etzhayyim.pds.leash
  "Member CACAO leash — the consent-attribution layer for autonomous actor writes.

  Charter (Server-side signing / ADR-2606111400 + 2606072802): an actor may write
  autonomously ONLY when the write is attributed to a CONSENTING HUMAN via a member
  CACAO leash — a scoped, expiring capability the MEMBER signs in their OWN runtime
  (the kaname/ibuki/tsubasa pattern). The actor PRESENTS the opaque leash; it never
  signs it. This module is the PDS-side VERIFIER: it checks the member's Ed25519
  signature, the audience (this PDS), the expiry, and the scope, and returns WHICH
  member authorised the write — so the PDS can attribute the autonomous write to a
  consenting human (accountability by consent, no platform-held key).

  Leash wire form (compact, JWS-like): `<payload-b64url>.<sig-b64url>` where payload
  is JSON `{iss, aud, exp, scope}` and `iss` is the member's did:key (Ed25519, z6Mk…).
  The member's public key is recovered FROM the did:key — no key registry needed.

  Pure JVM/babashka, no external deps (Ed25519 via the bundled SunEC)."
  (:require [cheshire.core :as json]
            [clojure.string :as str])
  (:import [java.security KeyPairGenerator KeyFactory Signature SecureRandom MessageDigest]
           [java.security.spec X509EncodedKeySpec PKCS8EncodedKeySpec]
           [javax.crypto Cipher]
           [javax.crypto.spec GCMParameterSpec SecretKeySpec]
           [java.math BigInteger]
           [java.util Base64]))

;; ── byte / base64url helpers ─────────────────────────────────────────────────
(defn- concat-bytes ^bytes [& arrs]
  (let [total (reduce (fn [acc ^bytes a] (+ acc (alength a))) 0 arrs)
        out   (byte-array total)]
    (loop [pos 0 [a & more] arrs]
      (when a (System/arraycopy a 0 out pos (alength a)) (recur (+ pos (alength a)) more)))
    out))

(def ^:private url-enc (.withoutPadding (Base64/getUrlEncoder)))
(def ^:private url-dec (Base64/getUrlDecoder))
(defn- ->u ^String [^bytes b] (.encodeToString url-enc b))
(defn- <-u ^bytes [^String s] (.decode url-dec s))

;; ── base58btc (Bitcoin alphabet) for did:key z-form ──────────────────────────
(def ^:private b58 "123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz")

(defn- b58-encode ^String [^bytes data]
  (let [zeros (count (take-while zero? data)) sb (StringBuilder.)]
    (loop [n (BigInteger. 1 data)]
      (when (pos? (.signum n))
        (let [^"[Ljava.math.BigInteger;" qr (.divideAndRemainder n (BigInteger/valueOf 58))]
          (.append sb (.charAt b58 (.intValue (aget qr 1)))) (recur (aget qr 0)))))
    (dotimes [_ zeros] (.append sb \1))
    (.toString (.reverse sb))))

(defn- b58-decode ^bytes [^String s]
  (let [ones (count (take-while #(= \1 %) s))
        n (reduce (fn [^BigInteger a c]
                    (let [d (.indexOf b58 (int c))]
                      (when (neg? d) (throw (ex-info "bad base58" {:c c})))
                      (.add (.multiply a (BigInteger/valueOf 58)) (BigInteger/valueOf d))))
                  BigInteger/ZERO s)
        raw (.toByteArray n)
        body (if (and (> (alength raw) 1) (zero? (aget raw 0)))
               (java.util.Arrays/copyOfRange raw 1 (alength raw)) raw)]
    (concat-bytes (byte-array ones) body)))

;; ── Ed25519 did:key ↔ PublicKey ──────────────────────────────────────────────
(def ^:private +ed-multicodec+ (byte-array [(unchecked-byte 0xed) (unchecked-byte 0x01)]))
(def ^:private +ed-spki-prefix+
  (byte-array (mapv unchecked-byte
    [0x30 0x2a 0x30 0x05 0x06 0x03 0x2b 0x65 0x70 0x03 0x21 0x00])))

(defn pubkey->did-key
  "Ed25519 PublicKey → did:key:z… (multicodec 0xed01 + 32-byte raw, base58btc)."
  ^String [pub]
  (let [enc (.getEncoded pub)                     ; 44-byte X.509; raw = last 32
        raw (java.util.Arrays/copyOfRange enc (- (alength enc) 32) (alength enc))]
    (str "did:key:z" (b58-encode (concat-bytes +ed-multicodec+ raw)))))

(defn did-key->pubkey
  "did:key:z… (Ed25519) → a verifiable PublicKey. Throws on a non-Ed25519 / malformed
  did:key (callers in verify-leash treat that as an invalid leash)."
  [^String didkey]
  (when-not (.startsWith didkey "did:key:z") (throw (ex-info "not an ed25519 did:key" {:k didkey})))
  (let [raw (b58-decode (subs didkey (count "did:key:z")))]
    (when-not (and (= (bit-and (aget raw 0) 0xff) 0xed) (= (bit-and (aget raw 1) 0xff) 0x01))
      (throw (ex-info "did:key is not ed25519" {:k didkey})))
    (let [pub32 (java.util.Arrays/copyOfRange raw 2 (alength raw))]
      (.generatePublic (KeyFactory/getInstance "Ed25519")
                       (X509EncodedKeySpec. (concat-bytes +ed-spki-prefix+ pub32))))))

;; ── issue (member runtime / tests) + verify (PDS) ────────────────────────────
(defn gen-member-key
  "Generate a member Ed25519 keypair + its did:key. (A member's OWN runtime does this;
  the platform never holds it. Provided here for the member tool + tests.)"
  []
  (let [kp (.generateKeyPair (KeyPairGenerator/getInstance "Ed25519"))
        pub (.getPublic kp)]
    {:private (.getPrivate kp) :public pub :did (pubkey->did-key pub)}))

(defn gen-jti
  "A unique leash id (token id) — 16 SecureRandom bytes, base64url. Lets a member
  REVOKE a specific leash before its expiry (the charter's 'revocable' property)."
  ^String []
  (->u (let [b (byte-array 16)] (.nextBytes (SecureRandom.) b) b)))

(defn issue-leash
  "The MEMBER signs a scoped/expiring/REVOCABLE capability in their OWN runtime. Returns
  the compact `<payload-b64url>.<sig-b64url>`. `member` = gen-member-key map. opts:
  {:aud <pds-did> :exp <unix-seconds> :scope <str, default \"datom:transact\">
   :jti <str, default a fresh gen-jti>} — the jti is what a revocation list names."
  ^String [member {:keys [aud exp scope jti] :or {scope "datom:transact"}}]
  (let [payload (.getBytes (json/generate-string {"iss" (:did member) "aud" aud
                                                  "exp" exp "scope" scope
                                                  "jti" (or jti (gen-jti))}
                                                 {:sort-keys true}) "UTF-8")
        sg (doto (Signature/getInstance "Ed25519") (.initSign (:private member)) (.update payload))]
    (str (->u payload) "." (->u (.sign sg)))))

(defn jti-of
  "The token id of a leash (for building/inspecting a revocation list), or nil."
  [^String leash]
  (try
    (let [[p64] (str/split (str leash) #"\." 2)]
      (get (json/parse-string (String. (<-u p64) "UTF-8")) "jti"))
    (catch Exception _ nil)))

(defn verify-leash
  "Verify a presented leash for this PDS. Returns
  {:valid? bool :member <did:key or nil> :reason <keyword>}. Checks, in order: shape,
  member Ed25519 signature over the payload, audience == `aud`, scope == `scope`,
  NOT revoked (jti ∉ `revoked`), and not expired (exp > `now` seconds). NEVER throws —
  a malformed/garbage leash is simply {:valid? false} (untrusted actor-presented bytes).
  `revoked` (default #{}) is the member/operator revocation set of jtis — a leaked or
  abused leash is killed BEFORE its expiry (the charter's 'revocable' property)."
  [^String leash {:keys [aud now scope revoked] :or {scope "datom:transact" revoked #{}}}]
  (try
    (let [[p64 s64] (str/split (str leash) #"\." 2)]
      (if (or (nil? p64) (nil? s64))
        {:valid? false :member nil :reason :malformed}
        (let [payload (<-u p64)
              claims  (json/parse-string (String. payload "UTF-8"))
              iss     (get claims "iss")
              pub     (did-key->pubkey iss)
              vr      (doto (Signature/getInstance "Ed25519") (.initVerify pub) (.update payload))
              sig-ok  (.verify vr (<-u s64))]
          (cond
            (not sig-ok)                      {:valid? false :member iss :reason :bad-signature}
            (not= (get claims "aud") aud)     {:valid? false :member iss :reason :wrong-audience}
            (not= (get claims "scope") scope) {:valid? false :member iss :reason :wrong-scope}
            (contains? revoked (get claims "jti")) {:valid? false :member iss :reason :revoked}
            (<= (long (get claims "exp" 0)) (long now)) {:valid? false :member iss :reason :expired}
            :else                             {:valid? true :member iss :reason :ok}))))
    (catch Exception _ {:valid? false :member nil :reason :malformed})))

;; ── member key at-rest sealing (AES-256-GCM) — for the MEMBER's own runtime ────
;; The member generates their key once and seals the Ed25519 PKCS#8 private under a
;; secret THEY hold (never the platform). The sealed blob persists; issuing a leash
;; unseals it in the member's runtime. did is public (it IS the public key), kept in
;; the clear so the public key is recoverable without the secret.
(defn- aes-key ^SecretKeySpec [^String secret]
  (SecretKeySpec. (.digest (MessageDigest/getInstance "SHA-256") (.getBytes secret "UTF-8")) "AES"))

(defn seal-member
  "Seal a member key {:private :did} for at-rest persistence under `secret` (the
  MEMBER's own sealing key — the platform never holds it). Returns a JSON-safe map."
  [member ^String secret]
  (let [iv (let [b (byte-array 12)] (.nextBytes (SecureRandom.) b) b)
        c  (doto (Cipher/getInstance "AES/GCM/NoPadding")
             (.init Cipher/ENCRYPT_MODE (aes-key secret) (GCMParameterSpec. 128 iv)))
        ct (.doFinal c (.getEncoded (:private member)))]   ; Ed25519 PKCS#8
    {:v 1 :did (:did member) :iv (->u iv) :ct (->u ct)}))

(defn unseal-member
  "Reconstitute {:private :did} from `seal-member` output + the member `secret`.
  Sufficient to issue leashes (issue-leash uses only :private + :did)."
  [blob ^String secret]
  (let [iv (<-u (:iv blob))
        c  (doto (Cipher/getInstance "AES/GCM/NoPadding")
             (.init Cipher/DECRYPT_MODE (aes-key secret) (GCMParameterSpec. 128 iv)))
        pkcs8 (.doFinal c (<-u (:ct blob)))
        priv (.generatePrivate (KeyFactory/getInstance "Ed25519") (PKCS8EncodedKeySpec. pkcs8))]
    {:private priv :did (:did blob)}))

(defn leash-author
  "Glue for the write path: given a PRESENTED leash (or nil) + env {:aud :now [:scope]},
  return the consenting member's did to ATTRIBUTE the write to — or nil if no leash is
  presented or it does not verify. The PDS passes this as store/put-record's {:author …}.
  nil leash → nil (the write proceeds unattributed; fail-open, no key, no live posting)."
  [leash env]
  (when leash
    (let [{:keys [valid? member]} (verify-leash leash env)]
      (when valid? member))))
