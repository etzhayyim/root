(ns etzhayyim.registry.agent
  "Agent identity primitives for Holochain-iso registration: an agent IS its
   ed25519 key. We mint a keypair, encode the public key as a W3C `did:key`
   (self-certifying, no CA / no TLS anchor — ADR-2606015600), and sign / verify
   genesis content-addresses with it.

   JDK Ed25519 (java 15+). Raw 32-byte public key = the last 32 bytes of the
   X.509 SubjectPublicKeyInfo (fixed 12-byte Ed25519 prefix). did:key multicodec
   = 0xed 0x01 ++ rawpub, multibase base58btc ('z' prefix)."
  (:require [clojure.string :as str])
  (:import [java.security KeyPairGenerator Signature KeyFactory]
           [java.security.spec X509EncodedKeySpec]
           [java.util Base64]))

;; ── base58btc (Bitcoin alphabet) ────────────────────────────────────────────
(def ^:private B58 "123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz")

(defn base58-encode ^String [^bytes data]
  (let [zeros (count (take-while zero? (seq data)))
        fifty8 (java.math.BigInteger/valueOf 58)
        sb (StringBuilder.)]
    (loop [n (java.math.BigInteger. 1 data)]
      (when (pos? (.signum n))
        (let [qr (.divideAndRemainder n fifty8)]
          (.append sb (.charAt B58 (.intValue (aget qr 1))))
          (recur (aget qr 0)))))
    (dotimes [_ zeros] (.append sb \1))
    (str/reverse (.toString sb))))

(defn base58-decode ^bytes [^String s]
  (let [fifty8 (java.math.BigInteger/valueOf 58)
        ;; String.indexOf returns -1 (not an exception) for a character
        ;; outside B58, and BigInteger/valueOf happily accepts -1 as a
        ;; valid digit -- an invalid character in an untrusted did:key
        ;; string used to silently decode to wrong-but-plausible key
        ;; bytes instead of raising. The cljs sibling
        ;; (etzhayyim.explorer.chain.agent/base58-decode) already guards
        ;; this; this JVM copy had drifted out of sync.
        n (reduce (fn [acc c]
                    (let [d (.indexOf B58 (int c))]
                      (when (neg? d)
                        (throw (ex-info "bad base58 character" {:char c})))
                      (.add (.multiply acc fifty8) (java.math.BigInteger/valueOf d))))
                  java.math.BigInteger/ZERO (seq s))
        bs (.toByteArray n)
        ;; strip a possible sign byte
        bs (if (and (> (count bs) 1) (zero? (aget bs 0))) (java.util.Arrays/copyOfRange bs 1 (count bs)) bs)
        zeros (count (take-while #(= \1 %) s))]
    (byte-array (concat (repeat zeros (byte 0)) bs))))

;; ── ed25519 keys ────────────────────────────────────────────────────────────
(defn gen-keypair []
  (.generateKeyPair (KeyPairGenerator/getInstance "Ed25519")))

(defn raw-pubkey ^bytes [kp-or-pub]
  (let [pub (if (instance? java.security.KeyPair kp-or-pub) (.getPublic kp-or-pub) kp-or-pub)
        spki (.getEncoded pub)]                 ; 44 bytes: 12 prefix + 32 raw
    (java.util.Arrays/copyOfRange spki 12 (count spki))))

(def ^:private ED25519-MULTICODEC (byte-array [(unchecked-byte 0xed) (unchecked-byte 0x01)]))

(defn did-key
  "did:key for an ed25519 keypair/public key."
  [kp-or-pub]
  (let [raw (raw-pubkey kp-or-pub)
        prefixed (byte-array (concat (seq ED25519-MULTICODEC) (seq raw)))]
    (str "did:key:z" (base58-encode prefixed))))

(defn did-key->raw-pub
  "did:key → raw 32-byte ed25519 public key (the inverse, for verifiers)."
  ^bytes [did]
  (let [mb (subs did (count "did:key:z"))       ; drop 'z' multibase prefix too
        decoded (base58-decode mb)]
    (java.util.Arrays/copyOfRange decoded 2 (count decoded))))   ; drop 0xed01

(defn raw-pub->public-key
  "Rebuild a java PublicKey from raw 32 bytes (wrap in the Ed25519 SPKI prefix)."
  [^bytes raw]
  (let [prefix (byte-array (map unchecked-byte [0x30 0x2a 0x30 0x05 0x06 0x03 0x2b 0x65 0x70 0x03 0x21 0x00]))
        spki (byte-array (concat (seq prefix) (seq raw)))]
    (.generatePublic (KeyFactory/getInstance "Ed25519")
                     (X509EncodedKeySpec. spki))))

;; ── sign / verify (over the genesis content-address string) ─────────────────
(defn sign
  "Sign a message string with the agent's private key → base64 signature."
  [kp ^String msg]
  (let [s (doto (Signature/getInstance "Ed25519")
            (.initSign (.getPrivate kp))
            (.update (.getBytes msg "UTF-8")))]
    (.encodeToString (Base64/getEncoder) (.sign s))))

(defn verify
  "Verify a base64 signature over `msg` against a did:key. → boolean."
  [did ^String msg ^String sig-b64]
  (try
    (let [pub (raw-pub->public-key (did-key->raw-pub did))
          s (doto (Signature/getInstance "Ed25519")
              (.initVerify pub)
              (.update (.getBytes msg "UTF-8")))]
      (.verify s (.decode (Base64/getDecoder) sig-b64)))
    (catch Exception _ false)))
