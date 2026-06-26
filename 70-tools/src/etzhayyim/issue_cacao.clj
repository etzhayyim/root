;; etzhayyim.issue-cacao — MEMBER-side CACAO leash issuer (clj/bb).
;;
;; The Clojure port of `20-actors/ibuki/tools/issue_delegation.py`, per the
;; repo-wide rule "operational tooling SHOULD be clj/bb, not py" (root CLAUDE.md).
;; A MEMBER runs this on their OWN machine, with their OWN key, to mint a scoped +
;; expiring + revocable CACAO capability the autonomous actor (ibuki / kaname /
;; tsubasa / …) then PRESENTS — present-only, the actor never signs (no-server-key,
;; ADR-2605231525 §委任 / ADR-2606111400). Revoke by letting `exp` pass.
;;
;; It produces, byte-compatible on the wire with `kotoba-auth::{cacao,delegation}`:
;;   - a CAIP-122 / SIWE CACAO {h:{t:eip4361}, p:{iss,aud,iat,exp,nonce,domain,
;;     version,resources}, s:{t:EdDSA,s}} → definite-length CBOR → base64 = cacao_b64;
;;   - signed with the member's Ed25519 key over the exact `siwe-message` plaintext
;;     the node reconstructs (did:key issuer ⇒ Chain ID 1, address = the z6Mk… seg);
;;   - `aud` = the NODE's operator DID (kotoba checks `cacao.p.aud == operator_did`);
;;   - `resources` = ["kotoba://can/datom:transact", "kotoba://graph/<graph-cid>"];
;;   - write_author resolves to the member (`iss`) — the on-record human principal.
;;
;; ── Deliberate divergence from the .py (a bb/GraalVM constraint, not a choice) ──
;; The .py takes a raw 32-byte Ed25519 seed and derives the pubkey via the
;; `cryptography` lib. bb's GraalVM image exposes the JCA "Ed25519" Signature
;; provider but NOT the EdEC interface classes, and BouncyCastle is absent — so
;; pubkey-FROM-seed derivation is unavailable here (same limitation documented in
;; `kotoba_rad_sign.clj`). This tool therefore GENERATES the member keypair and
;; carries BOTH legs (PKCS8 private + raw public), exactly as `kotoba_rad_sign`
;; does. The wire format + signature validity (what kotoba verifies) are identical;
;; only the key-input interface differs (PKCS8 base64, not raw-seed hex).
;;
;; Usage (bb task `issue-cacao`, or `bb 70-tools/src/etzhayyim/issue_cacao.clj …`):
;;   ;; generate a throwaway member key + a 30-day leash on graph 'ibuki':
;;   bb issue-cacao --node-did did:key:zNODE --graph ibuki \
;;       --exp 2026-07-11T00:00:00Z --out data/ibuki-delegation.json --gen-key
;;   ;; re-issue from a member key this tool previously generated:
;;   bb issue-cacao --node-did did:key:zNODE --graph ibuki \
;;       --exp 2026-07-11T00:00:00Z --member-priv-b64 <pkcs8-b64> \
;;       --member-pub-hex <64hex> --out data/ibuki-delegation.json
;;
;; The private leg is the MEMBER's secret — never commit it, never hand it to the
;; actor. The actor only ever sees `cacao_b64` (opaque) + the sidecar metadata.

(ns etzhayyim.issue-cacao
  (:require [clojure.string :as str])
  (:import (java.security KeyPairGenerator KeyFactory Signature MessageDigest)
           (java.security.spec PKCS8EncodedKeySpec)
           (java.time ZonedDateTime)
           (java.util Base64)))

(def ^:const capability "datom:transact")
(def ^:const default-domain "kotoba.etzhayyim.com")

;; ── encodings ───────────────────────────────────────────────────────────────

(defn- b64 ^String [^bytes b] (.encodeToString (Base64/getEncoder) b))
(defn- unb64 ^bytes [^String s] (.decode (Base64/getDecoder) s))

(defn hexify ^String [^bytes b]
  (apply str (map #(format "%02x" (bit-and (int %) 0xff)) b)))

(defn unhex ^bytes [^String s]
  (let [s (str/replace s #"\s" "")]
    (byte-array (map (fn [[a b]] (unchecked-byte (Integer/parseInt (str a b) 16)))
                     (partition 2 s)))))

(def ^:private b58-alphabet
  "123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz")

(defn b58 ^String [^bytes b]
  ;; base58btc (Bitcoin alphabet) — leading zero bytes → leading '1's.
  (let [n (BigInteger. 1 b)
        fifty8 (BigInteger/valueOf 58)]
    (loop [n n acc ""]
      (if (pos? (.signum n))
        (let [[q r] [(.divide n fifty8) (.intValue (.mod n fifty8))]]
          (recur q (str (.charAt b58-alphabet r) acc)))
        (let [lead (count (take-while zero? (seq b)))]
          (str (apply str (repeat lead \1)) acc))))))

(def ^:private b32-alphabet "abcdefghijklmnopqrstuvwxyz234567") ; RFC4648 lower

(defn b32-lower ^String [^bytes b]
  ;; RFC4648 base32, lowercase, no padding — inverse of cid.cljc's base32-decode.
  (let [bits (mapcat (fn [byte] (let [v (bit-and (int byte) 0xff)]
                                  (map #(bit-and (bit-shift-right v %) 1) [7 6 5 4 3 2 1 0])))
                     (seq b))]
    (->> bits
         (partition 5 5 nil)
         (map (fn [chunk]
                (let [padded (concat chunk (repeat (- 5 (count chunk)) 0))
                      idx (reduce (fn [a bit] (+ (* a 2) bit)) 0 padded)]
                  (.charAt b32-alphabet idx))))
         (apply str))))

;; ── DID + graph CID (must match KotobaCid::from_bytes + did:key spec) ─────────

(defn did-key-from-pub ^String [^bytes pub]
  ;; raw 32-byte Ed25519 pubkey → did:key:z6Mk… (multicodec 0xed01 + base58btc).
  (str "did:key:z" (b58 (byte-array (concat [(unchecked-byte 0xed) (unchecked-byte 0x01)]
                                            (seq pub))))))

(defn graph-cid ^String [^String name]
  ;; KotobaCid::from_bytes(name) — CIDv1 dag-cbor sha2-256, base32lower, 'b' prefix.
  (let [digest (.digest (MessageDigest/getInstance "SHA-256") (.getBytes name "UTF-8"))
        raw (byte-array (concat [(unchecked-byte 0x01) (unchecked-byte 0x71)
                                 (unchecked-byte 0x12) (unchecked-byte 0x20)]
                                (seq digest)))]
    (str "b" (b32-lower raw))))

;; ── SIWE (EIP-4361) plaintext — exactly what kotoba_auth::Cacao::siwe_message signs ──

(defn siwe-message ^String [p]
  (let [addr (last (str/split (:iss p) #":"))
        lines (cond-> [(str (:domain p) " wants you to sign in with your Ethereum account:")
                       addr ""]
                (:statement p) (conj (:statement p) "")
                :always (into [(str "URI: " (:aud p))
                               (str "Version: " (:version p))
                               "Chain ID: 1"
                               (str "Nonce: " (:nonce p))
                               (str "Issued At: " (:iat p))])
                (:exp p) (conj (str "Expiration Time: " (:exp p)))
                (:resources p) (conj "Resources:")
                (:resources p) (into (map #(str "- " %) (:resources p))))]
    (str/join "\n" lines)))

;; ── minimal definite-length CBOR (small text-string maps/arrays) ─────────────
;; Maps are built from ORDERED [k v-bytes] pairs (not Clojure maps) so the byte
;; layout is deterministic and matches the .py dict-insertion order.

(defn- cbor-str ^bytes [^String s]
  (let [b (.getBytes s "UTF-8") n (count b)
        head (cond (< n 24)  (byte-array [(unchecked-byte (bit-or 0x60 n))])
                   (< n 256) (byte-array [(unchecked-byte 0x78) (unchecked-byte n)])
                   :else     (byte-array [(unchecked-byte 0x79)
                                          (unchecked-byte (bit-shift-right n 8))
                                          (unchecked-byte (bit-and n 0xff))]))]
    (byte-array (concat (seq head) (seq b)))))

(defn- cbor-arr ^bytes [items]
  (byte-array (concat [(unchecked-byte (bit-or 0x80 (count items)))]
                      (mapcat seq items))))

(defn- cbor-map ^bytes [pairs]
  ;; pairs = ordered seq of [key-string value-bytes]
  (byte-array (concat [(unchecked-byte (bit-or 0xA0 (count pairs)))]
                      (mapcat (fn [[k v]] (concat (seq (cbor-str k)) (seq v))) pairs))))

(defn build-cacao ^bytes [payload ^String sig-b64]
  (let [p [["iss" (cbor-str (:iss payload))]
           ["aud" (cbor-str (:aud payload))]
           ["iat" (cbor-str (:iat payload))]
           ["exp" (cbor-str (:exp payload))]
           ["nonce" (cbor-str (:nonce payload))]
           ["domain" (cbor-str (:domain payload))]
           ["version" (cbor-str (:version payload))]
           ["resources" (cbor-arr (map cbor-str (:resources payload)))]]]
    (cbor-map [["h" (cbor-map [["t" (cbor-str "eip4361")]])]
               ["p" (cbor-map p)]
               ["s" (cbor-map [["t" (cbor-str "EdDSA")] ["s" (cbor-str sig-b64)]])]])))

;; ── Ed25519 keys (JCA "Ed25519"; raw pub = last 32B of X.509 SPKI, per kotoba_rad_sign) ──

(defn gen-keypair []
  (let [kp (.generateKeyPair (KeyPairGenerator/getInstance "Ed25519"))
        priv-pkcs8 (.getEncoded (.getPrivate kp))
        spki (.getEncoded (.getPublic kp))
        pub (byte-array (take-last 32 (seq spki)))]
    {:priv-b64 (b64 priv-pkcs8) :pub pub :pub-hex (hexify pub)}))

(defn- load-priv [^String priv-b64]
  (.generatePrivate (KeyFactory/getInstance "Ed25519")
                    (PKCS8EncodedKeySpec. (unb64 priv-b64))))

(defn sign-bytes ^bytes [^String priv-b64 ^bytes msg]
  (let [sig (Signature/getInstance "Ed25519")]
    (.initSign sig (load-priv priv-b64))
    (.update sig msg)
    (.sign sig)))

(def ^:private spki-ed25519-prefix
  ;; fixed 12-byte X.509 SubjectPublicKeyInfo header for an Ed25519 public key.
  (byte-array (map unchecked-byte [0x30 0x2a 0x30 0x05 0x06 0x03 0x2b 0x65 0x70 0x03 0x21 0x00])))

(defn- pub-from-raw [^bytes raw-pub]
  (.generatePublic (KeyFactory/getInstance "Ed25519")
                   (java.security.spec.X509EncodedKeySpec.
                    (byte-array (concat (seq spki-ed25519-prefix) (seq raw-pub))))))

(defn verify-bytes ^Boolean [^String pub-hex ^bytes msg ^bytes sig-bytes]
  (let [sig (Signature/getInstance "Ed25519")]
    (.initVerify sig (pub-from-raw (unhex pub-hex)))
    (.update sig msg)
    (.verify sig sig-bytes)))

(defn iso->epoch ^long [^String iso]
  (.getEpochSecond (.toInstant (ZonedDateTime/parse iso))))

;; ── issue ────────────────────────────────────────────────────────────────────

(defn issue
  "Mint the delegation bundle. `key` = {:priv-b64 … :pub-hex …} (the member's key).
   Returns the {cacao_b64, aud, capability, graph, exp(epoch), exp_iso, nonce, …}
   sidecar the actor's delegation loader consumes."
  [{:keys [node-did graph iat exp nonce domain key]
    :or {domain default-domain}}]
  (let [member-did (did-key-from-pub (unhex (:pub-hex key)))
        gcid (graph-cid graph)
        payload {:iss member-did :aud node-did :iat iat :exp exp :nonce nonce
                 :domain domain :version "1"
                 :resources [(str "kotoba://can/" capability)
                             (str "kotoba://graph/" gcid)]}
        sig (sign-bytes (:priv-b64 key) (.getBytes (siwe-message payload) "UTF-8"))
        cacao (build-cacao payload (b64 sig))]
    {:cacao_b64 (b64 cacao)
     :aud node-did :capability capability :graph graph
     :exp (iso->epoch exp) :exp_iso exp :nonce nonce :_issuer member-did
     :_note "member-signed; the actor presents this, never signs. Revoke by letting exp pass."}))

;; ── tiny JSON emit (sidecar; avoids a runtime dep — values are flat strings/longs) ──

(defn- json-escape ^String [^String s]
  (str/escape s {\" "\\\"" \\ "\\\\" \newline "\\n" \tab "\\t" \return "\\r"}))

(defn- ->json ^String [m]
  (str "{\n"
       (str/join ",\n"
                 (map (fn [[k v]]
                        (str "  \"" (name k) "\": "
                             (if (number? v) (str v) (str "\"" (json-escape (str v)) "\""))))
                      m))
       "\n}\n"))

;; ── CLI ────────────────────────────────────────────────────────────────────

(defn- parse-args [args]
  (loop [a args m {}]
    (if-let [[k & r] (seq a)]
      (cond
        (= k "--gen-key") (recur r (assoc m :gen-key true))
        (str/starts-with? k "--") (recur (rest r) (assoc m (keyword (subs k 2)) (first r)))
        :else (recur r m))
      m)))

(defn -main [& args]
  (let [{:keys [node-did graph exp nonce iat out gen-key member-priv-b64 member-pub-hex]
         :or {graph "ibuki" nonce "leash0001" iat "2026-06-11T00:00:00Z"}} (parse-args args)]
    (when-not (and node-did exp out)
      (binding [*out* *err*]
        (println "usage: issue-cacao --node-did <did> --exp <ISO-8601> --out <path>"
                 "[--graph <name>] [--nonce <s>] [--iat <ISO>]"
                 "(--gen-key | --member-priv-b64 <b64> --member-pub-hex <hex>)"))
      (System/exit 2))
    (let [key (cond
                gen-key (let [kp (gen-keypair)]
                          (binding [*out* *err*]
                            (println (str "# generated member key (SECRET — store safely, never commit):"))
                            (println (str "#   --member-priv-b64 " (:priv-b64 kp)))
                            (println (str "#   --member-pub-hex  " (:pub-hex kp))))
                          kp)
                (and member-priv-b64 member-pub-hex) {:priv-b64 member-priv-b64 :pub-hex member-pub-hex}
                :else (binding [*out* *err*]
                        (println "need --gen-key OR (--member-priv-b64 + --member-pub-hex)")
                        (System/exit 2)))
          bundle (issue {:node-did node-did :graph graph :iat iat :exp exp :nonce nonce :key key})]
      (spit out (->json bundle))
      (println (str "wrote leash → " out "  (issuer " (subs (:_issuer bundle) 0 30)
                    "…, graph " graph ", exp " exp ")")))))
