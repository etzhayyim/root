(ns etzhayyim.pds.keys
  "actor-sealed signing keys — the per-actor key custody for did:web:etzhayyim.com:actor:*.

  Posture (founder direction, 2026-06-25): the key belongs to the ACTOR, and its
  private contents are known to no one — not the operator, not the platform. This is
  the correct reading of the no-server-key invariant (Charter G7 / ADR-2605231525):
  G7 forbids a *server-held* key the platform could wield to impersonate anyone. An
  actor-sealed key is held by no human and belongs to exactly ONE actor, so the actor
  signs its own atproto repo commits autonomously WITHOUT a member lending identity and
  WITHOUT a platform master key.

  How `contents known to no one` is structural here, not a promise:

    - the private key never leaves this namespace as raw scalar bytes. The public API
      exposes only {public multikey, verificationMethod, sign, verify}. There is no
      `private-scalar` accessor — by construction, not by discipline;
    - at rest the PKCS#8 private material is AES-256-GCM sealed under a per-node sealing
      secret (`MURAKUMO_SEAL_KEY`, the actor's resident murakumo node). On disk the
      operator sees only ciphertext; to sign, the actor process unseals into memory;
    - generation uses the platform SecureRandom; the scalar is never logged, printed,
      committed, or returned.

  Curve: p256 (secp256r1). atproto accepts BOTH p256 and k256 signing keys; p256 is the
  one babashka's bundled SunEC can do with no external dependency (bb's SunEC rejects
  secp256k1 — `Curve not supported`). k256 would need a pure-clj field implementation or
  an off-bb signer; it is a one-line `+curve+` switch + multicodec entry away (see
  `+multicodec+`), deliberately NOT wired so this stays pure-bb. Pure JVM/babashka, no
  external deps — same constraint as util.clj."
  (:require [cheshire.core :as json])
  (:import [java.security KeyPairGenerator KeyFactory Signature SecureRandom MessageDigest]
           [java.security.spec ECGenParameterSpec PKCS8EncodedKeySpec X509EncodedKeySpec]
           [javax.crypto Cipher]
           [javax.crypto.spec SecretKeySpec GCMParameterSpec]
           [java.math BigInteger]
           [java.util Base64]))

;; ── curve parameters ─────────────────────────────────────────────────────────
(def ^:private +curve+ "secp256r1")            ; JCE name for NIST P-256
(def ^:private +jca-key-alg+ "EC")
(def ^:private +jca-sig-alg+ "SHA256withECDSA") ; sha256(msg) then ECDSA — atproto's scheme

;; P-256 group order n, and n/2 for low-S normalisation.
(def ^:private +n+
  (BigInteger. "FFFFFFFF00000000FFFFFFFFFFFFFFFFBCE6FAADA7179E84F3B9CAC2FC632551" 16))
(def ^:private +n-half+ (.shiftRight +n+ 1))

;; P-256 field prime p and curve constant b (a = -3). Used to decompress a public
;; point recovered from a multikey, so a signature can be verified from the PUBLISHED
;; multikey alone — no shared key, exactly what a remote PDS/AppView does.
(def ^:private +p+
  (BigInteger. "FFFFFFFF00000001000000000000000000000000FFFFFFFFFFFFFFFFFFFFFFFF" 16))
(def ^:private +b+
  (BigInteger. "5AC635D8AA3A93E7B3EBBD55769886BC651D06B0CC53B0F63BCE3C3E27D2604B" 16))
(def ^:private +three+ (BigInteger/valueOf 3))
;; Fixed 26-byte X.509 SubjectPublicKeyInfo prefix for a P-256 key; the 65-byte
;; uncompressed point `04 X Y` is appended to rebuild a verifiable PublicKey.
(def ^:private +spki-prefix+
  (byte-array (mapv unchecked-byte
    [0x30 0x59 0x30 0x13 0x06 0x07 0x2a 0x86 0x48 0xce 0x3d 0x02 0x01 0x06 0x08
     0x2a 0x86 0x48 0xce 0x3d 0x03 0x01 0x07 0x03 0x42 0x00])))

;; multicodec prefix for the public key type, varint-encoded. p256-pub = 0x1200 →
;; varint [0x80 0x24]. (k256-pub = 0xe7 → [0xe7 0x01], for the future switch.)
(def ^:private +multicodec+
  {:p256 (byte-array [(unchecked-byte 0x80) (unchecked-byte 0x24)])})

;; ── small byte helpers ───────────────────────────────────────────────────────
(defn- ub [^bytes a ^long i] (bit-and (aget a i) 0xff))

(defn- concat-bytes ^bytes [& arrs]
  (let [total (reduce (fn [acc ^bytes a] (+ acc (alength a))) 0 arrs)
        out   (byte-array total)]
    (loop [pos 0, [a & more] arrs]
      (when a
        (System/arraycopy a 0 out pos (alength a))
        (recur (+ pos (alength a)) more)))
    out))

(defn- bigint->fixed
  "Unsigned big-endian of `bi` in exactly `n` bytes (strips a BigInteger sign byte,
  left-pads with zeros). Never negative input in our use."
  ^bytes [^BigInteger bi ^long n]
  (let [raw (.toByteArray bi)
        len (alength raw)
        ;; drop a leading 0x00 sign byte if present
        start (if (and (> len 1) (zero? (aget raw 0))) 1 0)
        eff (- len start)
        out (byte-array n)]
    (System/arraycopy raw start out (- n eff) eff)
    out))

(def ^:private b64-enc (Base64/getEncoder))
(def ^:private b64-dec (Base64/getDecoder))
(defn- ->b64 ^String [^bytes b] (.encodeToString b64-enc b))
(defn- <-b64 ^bytes [^String s] (.decode b64-dec s))

(defn- sha256 ^bytes [^bytes b] (.digest (MessageDigest/getInstance "SHA-256") b))

;; ── base58btc (Bitcoin alphabet) — for multibase 'z' ─────────────────────────
(def ^:private b58-alphabet
  "123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz")

(defn- base58btc ^String [^bytes data]
  (let [zeros (count (take-while zero? data))
        sb    (StringBuilder.)]
    (loop [n (BigInteger. 1 data)]
      (when (pos? (.signum n))
        (let [^"[Ljava.math.BigInteger;" qr (.divideAndRemainder n (BigInteger/valueOf 58))]
          (.append sb (.charAt b58-alphabet (.intValue (aget qr 1))))
          (recur (aget qr 0)))))
    (dotimes [_ zeros] (.append sb \1))
    (.reverse sb)
    (.toString sb)))

(defn- base58btc-decode ^bytes [^String s]
  (let [ones  (count (take-while #(= \1 %) s))
        n     (reduce (fn [^BigInteger acc c]
                        (let [d (.indexOf b58-alphabet (int c))]
                          (when (neg? d) (throw (ex-info "bad base58 char" {:c c})))
                          (.add (.multiply acc (BigInteger/valueOf 58)) (BigInteger/valueOf d))))
                      BigInteger/ZERO s)
        raw   (.toByteArray n)
        ;; strip a BigInteger sign byte
        body  (if (and (> (alength raw) 1) (zero? (aget raw 0)))
                (java.util.Arrays/copyOfRange raw 1 (alength raw))
                raw)]
    (concat-bytes (byte-array ones) body)))

;; ── EC public-key → compressed point → multikey ──────────────────────────────
(defn- uncompressed-point
  "The 65-byte uncompressed EC point `04 || X || Y`. For a P-256 X.509
  SubjectPublicKeyInfo (fixed 91-byte layout) this is the trailing 65 bytes."
  ^bytes [pub]
  (let [enc ^bytes (.getEncoded pub)
        n   (alength enc)
        pt  (byte-array 65)]
    (System/arraycopy enc (- n 65) pt 0 65)
    (when-not (= 4 (ub pt 0))
      (throw (ex-info "unexpected EC point encoding (not uncompressed 0x04)" {})))
    pt))

(defn- compressed-pubkey
  "33-byte compressed point: `02|03 || X`, parity from Y's low bit."
  ^bytes [pub]
  (let [pt   (uncompressed-point pub)
        x    (byte-array 32)
        ylsb (bit-and (ub pt 64) 1)            ; last byte of Y
        out  (byte-array 33)]
    (System/arraycopy pt 1 x 0 32)
    (aset-byte out 0 (unchecked-byte (if (zero? ylsb) 0x02 0x03)))
    (System/arraycopy x 0 out 1 32)
    out))

(defn multikey
  "did:key-style multibase string for the public key: 'z' + base58btc(multicodec ++
  compressed-pubkey). Goes verbatim into a did:web doc verificationMethod."
  ^String [pub]
  (str "z" (base58btc (concat-bytes (+multicodec+ :p256) (compressed-pubkey pub)))))

(defn verification-method
  "The did:web Multikey verificationMethod entry for `did` signed by `pub`. atproto
  reads the `#atproto` key as the repo's signing key."
  [^String did pub]
  {"id" (str did "#atproto")
   "type" "Multikey"
   "controller" did
   "publicKeyMultibase" (multikey pub)})

;; ── ECDSA DER ↔ compact(64) with low-S ───────────────────────────────────────
(defn- parse-der-int
  "Read one DER INTEGER at offset `off`; returns [BigInteger next-off]."
  [^bytes der ^long off]
  (when-not (= 0x02 (ub der off))
    (throw (ex-info "DER: expected INTEGER" {:off off})))
  (let [len (ub der (inc off))
        start (+ off 2)
        buf (byte-array len)]
    (System/arraycopy der start buf 0 len)
    [(BigInteger. buf) (+ start len)]))

(defn der->compact
  "JCE ECDSA DER signature → atproto 64-byte compact `r||s`, low-S normalised."
  ^bytes [^bytes der]
  (when-not (= 0x30 (ub der 0))
    (throw (ex-info "DER: expected SEQUENCE" {})))
  (let [[r off1] (parse-der-int der 2)
        [s _]    (parse-der-int der off1)
        s*       (if (> s +n-half+) (.subtract +n+ s) s)]
    (concat-bytes (bigint->fixed r 32) (bigint->fixed s* 32))))

(defn- der-int ^bytes [^BigInteger v]
  (let [raw (.toByteArray v)]                  ; already includes a sign byte when needed
    (concat-bytes (byte-array [(unchecked-byte 0x02) (unchecked-byte (alength raw))]) raw)))

(defn compact->der
  "64-byte compact `r||s` → DER SEQUENCE, for handing back to the JCE verifier."
  ^bytes [^bytes sig64]
  (let [r (BigInteger. 1 (java.util.Arrays/copyOfRange sig64 0 32))
        s (BigInteger. 1 (java.util.Arrays/copyOfRange sig64 32 64))
        body (concat-bytes (der-int r) (der-int s))]
    (concat-bytes (byte-array [(unchecked-byte 0x30) (unchecked-byte (alength body))]) body)))

;; ── sign / verify ────────────────────────────────────────────────────────────
(defn sign
  "Sign `msg` (raw bytes) with the actor's sealed private key. Returns a 64-byte
  low-S compact signature (atproto wire form). The private key is used opaquely; its
  scalar is never materialised."
  ^bytes [sealed ^bytes msg]
  (let [sg (doto (Signature/getInstance +jca-sig-alg+)
             (.initSign (:private sealed))
             (.update msg))]
    (der->compact (.sign sg))))

(defn verify
  "Verify a 64-byte compact signature against `pub` (a PublicKey) over `msg`."
  [pub ^bytes msg ^bytes sig64]
  (let [vr (doto (Signature/getInstance +jca-sig-alg+)
             (.initVerify pub)
             (.update msg))]
    (.verify vr (compact->der sig64))))

;; ── multikey → PublicKey (decompress) → verify from the PUBLISHED key alone ───
(defn- mod-sqrt
  "√v mod p for the P-256 prime (p ≡ 3 mod 4 → v^((p+1)/4)). Returns nil if v is a
  non-residue (the compressed point was malformed)."
  [^BigInteger v]
  (let [r (.modPow v (.shiftRight (.add +p+ BigInteger/ONE) 2) +p+)]
    (when (= v (.mod (.multiply r r) +p+)) r)))

(defn- decompress-point
  "33-byte compressed `02|03 || X` → 65-byte uncompressed `04 || X || Y` on P-256."
  ^bytes [^bytes compressed]
  (let [want-odd (= 0x03 (ub compressed 0))
        x   (BigInteger. 1 (java.util.Arrays/copyOfRange compressed 1 33))
        ;; y² = x³ - 3x + b (mod p)
        rhs (.mod (.add (.subtract (.modPow x +three+ +p+) (.multiply +three+ x)) +b+) +p+)
        y0  (or (mod-sqrt rhs) (throw (ex-info "point not on P-256 curve" {})))
        y   (if (= want-odd (.testBit y0 0)) y0 (.subtract +p+ y0))]
    (concat-bytes (byte-array [(unchecked-byte 0x04)]) (bigint->fixed x 32) (bigint->fixed y 32))))

(defn pubkey-from-multikey
  "Reconstruct a verifiable PublicKey from a 'z…' P-256 multikey (the inverse of
  `multikey`). Lets any party verify an actor's signature from its DID doc alone."
  [^String mk]
  (when-not (= \z (first mk)) (throw (ex-info "multikey must be multibase 'z'" {:mk mk})))
  (let [raw  (base58btc-decode (subs mk 1))
        pfx  (+multicodec+ :p256)]
    (when-not (and (= (ub raw 0) (ub pfx 0)) (= (ub raw 1) (ub pfx 1)))
      (throw (ex-info "multikey is not a p256 public key" {:mk mk})))
    (let [compressed (java.util.Arrays/copyOfRange raw 2 (alength raw))
          point      (decompress-point compressed)
          spki       (concat-bytes +spki-prefix+ point)]
      (.generatePublic (KeyFactory/getInstance +jca-key-alg+) (X509EncodedKeySpec. spki)))))

(defn verify-multikey
  "Verify a 64-byte compact signature over `msg` using ONLY the published multikey —
  no access to the actor's key object. This is the remote-verifier path."
  [^String mk ^bytes msg ^bytes sig64]
  (verify (pubkey-from-multikey mk) msg sig64))

;; ── base64 sig convenience (string-friendly, for datoms / JSON) ───────────────
(defn sign-b64
  "Sign `msg` with the actor's sealed key; return the compact signature base64."
  ^String [sealed ^bytes msg]
  (->b64 (sign sealed msg)))

(defn verify-b64
  "Verify a base64 compact signature over `msg` against the published multikey."
  [^String mk ^bytes msg ^String sig-b64]
  (verify-multikey mk msg (<-b64 sig-b64)))

(defn record-signer
  "A crypto-agnostic store signer for an actor's sealed handle: a closure
  `(fn [^bytes payload] -> {:sig <base64> :multikey <str>})`. The PDS store calls
  it to sign each record's content id; the store never sees the key. Anyone
  verifies the result with `verify-b64` + the actor's published multikey."
  [sealed]
  (fn [^bytes payload]
    {:sig (sign-b64 sealed payload) :multikey (:multikey sealed)}))

;; ── generation ───────────────────────────────────────────────────────────────
(defn new-actor-key
  "Generate a fresh actor-sealed keypair. Returns a sealed handle
  {:private <PrivateKey, opaque> :public <PublicKey> :multikey <str> :curve :p256}.
  The private scalar is created from SecureRandom and never leaves this map as bytes."
  []
  (let [kpg (doto (KeyPairGenerator/getInstance +jca-key-alg+)
              (.initialize (ECGenParameterSpec. +curve+) (SecureRandom.)))
        kp  (.generateKeyPair kpg)
        pub (.getPublic kp)]
    {:private (.getPrivate kp) :public pub :multikey (multikey pub) :curve :p256}))

;; ── at-rest sealing (AES-256-GCM under the node sealing secret) ───────────────
(defn- aes-key ^SecretKeySpec [^String secret]
  (SecretKeySpec. (sha256 (.getBytes secret "UTF-8")) "AES"))

(defn seal
  "Seal a handle for at-rest persistence. Returns a JSON-safe map: the multikey and the
  X.509 public key in the clear (both are public), and the PKCS#8 private key AES-GCM
  ciphertext. The operator sees only ciphertext on disk. `secret` is the per-node
  sealing key (e.g. env MURAKUMO_SEAL_KEY); the platform's global config never holds it."
  [sealed ^String secret]
  (let [iv  (let [b (byte-array 12)] (.nextBytes (SecureRandom.) b) b)
        c   (doto (Cipher/getInstance "AES/GCM/NoPadding")
              (.init Cipher/ENCRYPT_MODE (aes-key secret) (GCMParameterSpec. 128 iv)))
        ct  (.doFinal c (.getEncoded (:private sealed)))]
    {:v 1 :curve (name (:curve sealed)) :multikey (:multikey sealed)
     :pub-x509 (->b64 (.getEncoded (:public sealed)))
     :iv (->b64 iv) :ct (->b64 ct)}))

(defn unseal
  "Reconstruct an in-memory sealed handle from `seal` output + the node `secret`.
  Reconstitutes the opaque PrivateKey and the PublicKey; the scalar stays opaque."
  [blob ^String secret]
  (let [kf   (KeyFactory/getInstance +jca-key-alg+)
        pub  (.generatePublic kf (X509EncodedKeySpec. (<-b64 (:pub-x509 blob))))
        iv   (<-b64 (:iv blob))
        c    (doto (Cipher/getInstance "AES/GCM/NoPadding")
               (.init Cipher/DECRYPT_MODE (aes-key secret) (GCMParameterSpec. 128 iv)))
        pkcs8 (.doFinal c (<-b64 (:ct blob)))
        priv (.generatePrivate kf (PKCS8EncodedKeySpec. pkcs8))]
    {:private priv :public pub :multikey (:multikey blob) :curve (keyword (:curve blob))}))

(defn node-secret
  "The per-node sealing secret. From MURAKUMO_SEAL_KEY; absent → nil (callers must
  refuse to seal/unseal without it — the platform holds no fallback)."
  []
  (System/getenv "MURAKUMO_SEAL_KEY"))

(defn seal->json ^String [blob] (json/generate-string blob {:pretty true}))
(defn json->seal [^String s] (json/parse-string s true))
