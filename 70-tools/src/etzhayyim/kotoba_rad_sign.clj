;; etzhayyim.kotoba-rad-sign — Ed25519 signing seam for kotoba-rad (ADR-2606231200).
;;
;; no-server-key: this is the MEMBER/operator key leg. kotoba-rad core never
;; signs; this namespace builds a `:sign-fn` from a key the member holds (macOS
;; Keychain / 1Password), so signatures are produced only with an explicit key
;; present, never by a platform-held secret.
;;
;; Signature convention is BYTE-IDENTICAL to the in-repo verifier
;; `50-infra/etzhayyim-did-web/cljs/src/did_web/kotoba.cljs` `verify-root-sig`:
;;   did = did:key:z<hex(raw 32B pubkey)>
;;   message signed = base32-DECODE(headCid[1:])   ; the raw CID bytes, NOT utf-8
;;   sig = hex(64B Ed25519)
;;
;; Ed25519 runs on bb's JDK via the standard JCA "Ed25519" provider. bb's
;; GraalVM image does not expose the EdEC interface classes, so the raw public
;; key is taken as the last 32 bytes of the X.509 SubjectPublicKeyInfo encoding
;; (fixed 44-byte structure for Ed25519) — verified equivalent in tests.

(ns etzhayyim.kotoba-rad-sign
  (:require [clojure.string :as str]
            [babashka.process :as p]
            [etzhayyim.kotoba-rad :as rad])
  (:import (java.security KeyPairGenerator Signature KeyFactory)
           (java.security.spec PKCS8EncodedKeySpec X509EncodedKeySpec)
           (java.util Base64)))

;; ── hex / base32 (RFC4648 lower, no pad — inverse of cid.cljc's base32) ──────

(defn hexify ^String [^bytes b]
  (apply str (map #(format "%02x" (bit-and % 0xff)) b)))

(defn unhex ^bytes [^String s]
  (byte-array (map (fn [[a b]] (unchecked-byte (Integer/parseInt (str a b) 16)))
                   (partition 2 s))))

(def ^:private b32 "abcdefghijklmnopqrstuvwxyz234567")
(def ^:private b32-idx (into {} (map-indexed (fn [i c] [c i]) b32)))

(defn base32-decode
  "RFC4648 base32 lower (no pad) -> byte-array. Inverse of cid.cljc base32."
  ^bytes [^String s]
  (let [out (java.io.ByteArrayOutputStream.)]
    (loop [cs (seq s) buf 0 bits 0]
      (if (empty? cs)
        (.toByteArray out)
        (let [v (b32-idx (first cs))
              buf (bit-or (bit-shift-left buf 5) (int v))
              bits (+ bits 5)]
          (if (>= bits 8)
            (do (.write out (bit-and (unsigned-bit-shift-right buf (- bits 8)) 0xff))
                (recur (rest cs) buf (- bits 8)))
            (recur (rest cs) buf bits)))))))

(defn cid->bytes
  "Raw bytes a CIDv1 string addresses — base32-decode after the 'b' multibase.
   This is exactly what kotoba.cljs verifies the signature over."
  ^bytes [^String cid]
  (when-not (str/starts-with? cid "b")
    (throw (ex-info "expected base32 'b' multibase CID" {:cid cid})))
  (base32-decode (subs cid 1)))

;; ── key material ─────────────────────────────────────────────────────────────

(defn- pub->raw-hex [pub]
  ;; last 32 bytes of the 44-byte X.509 SPKI = the raw Ed25519 public key
  (hexify (byte-array (take-last 32 (seq (.getEncoded pub))))))

(defn gen-keypair
  "Fresh Ed25519 keypair -> {:priv-b64 <PKCS8 base64> :pub-hex <raw32 hex>
   :did-key did:key:z<hex>}. The member stores :priv-b64 in Keychain/1Password."
  []
  (let [kp (.generateKeyPair (KeyPairGenerator/getInstance "Ed25519"))
        pub-hex (pub->raw-hex (.getPublic kp))]
    {:priv-b64 (.encodeToString (Base64/getEncoder) (.getEncoded (.getPrivate kp)))
     :pub-hex pub-hex
     :did-key (rad/did-key pub-hex)}))

(defn- load-priv [^String priv-b64]
  (.generatePrivate (KeyFactory/getInstance "Ed25519")
                    (PKCS8EncodedKeySpec. (.decode (Base64/getDecoder) priv-b64))))

(defn sign-bytes ^bytes [^String priv-b64 ^bytes msg]
  (let [s (Signature/getInstance "Ed25519")]
    (.initSign s (load-priv priv-b64))
    (.update s msg)
    (.sign s)))

(defn verify-bytes
  "Verify a signature with a raw-hex Ed25519 public key (for tests / parity)."
  [^String pub-hex ^bytes msg ^bytes sig]
  (let [spki (byte-array (concat (unhex "302a300506032b6570032100") (unhex pub-hex)))
        pub (.generatePublic (KeyFactory/getInstance "Ed25519") (X509EncodedKeySpec. spki))
        v (Signature/getInstance "Ed25519")]
    (.initVerify v pub) (.update v msg) (.verify v sig)))

;; ── sign-fn seam (the value kotoba-rad/publish-identity! consumes) ───────────

(defn make-sign-fn
  "Build the (fn [head-cid] -> {:by did-key :sig hex}) seam from key material.
   Signs the base32-decoded CID bytes, kotoba.cljs-compatible."
  [{:keys [priv-b64 pub-hex]}]
  (fn [head-cid]
    {:by (rad/did-key pub-hex)
     :sig (hexify (sign-bytes priv-b64 (cid->bytes head-cid)))}))

;; ── Keychain integration (member key store) ─────────────────────────────────

(def keychain-service "etzhayyim.kotoba-rad")

(defn keychain-read
  "Read the member's PKCS8 base64 priv key for an actor from macOS Keychain,
   or nil if absent. account = the actor name."
  [actor]
  (let [{:keys [exit out]} (p/sh "security" "find-generic-password"
                                 "-s" keychain-service "-a" actor "-w")]
    (when (zero? exit) (str/trim (str out)))))

(defn keychain-store!
  "Store :priv-b64 under (keychain-service, actor). -U updates if present."
  [actor priv-b64]
  (p/sh "security" "add-generic-password" "-U"
        "-s" keychain-service "-a" actor
        "-l" (str "etzhayyim kotoba-rad Ed25519 priv (" actor ")")
        "-w" priv-b64))

(defn sign-fn-for-actor
  "If the actor's key is in Keychain, return a ready sign-fn; else nil.
   pub-hex is recovered by signing+self-derive is not possible from PKCS8 alone
   without the EdEC API, so the caller passes the known pub-hex (from did.json /
   --pubkey). Here we accept it explicitly."
  [actor pub-hex]
  (when-let [priv-b64 (keychain-read actor)]
    (make-sign-fn {:priv-b64 priv-b64 :pub-hex pub-hex})))

;; ── CLI: actor:keygen ───────────────────────────────────────────────────────

(defn -keygen
  "Generate an Ed25519 keypair for an actor. Prints pub-hex + did:key. With
   --apply, stores the private key in macOS Keychain (member key, no-server-key)."
  [& args]
  (let [actor (first (remove #(str/starts-with? % "--") args))
        apply? (contains? (set args) "--apply")
        {:keys [priv-b64 pub-hex did-key]} (gen-keypair)]
    (when-not actor
      (println "usage: bb actor:keygen <name> [--apply]") (System/exit 2))
    (println "actor   " actor)
    (println "pub-hex " pub-hex)
    (println "did:key " did-key)
    (if apply?
      (do (keychain-store! actor priv-b64)
          (println "stored  priv in Keychain:" keychain-service "/" actor)
          (println "next    bb actor:publish" actor "--apply --pubkey=" pub-hex))
      (do (println "priv-b64 (DRY-RUN, NOT stored — pass --apply to store in Keychain):")
          (println priv-b64)))))

;; ── CLI: actor:delegate-add ─────────────────────────────────────────────────

(defn -delegate-add
  "Register a member did:key as a :rad/delegate of an EXISTING actor identity,
   RID-stable (ADR-2606251200 A-2 §Remaining — operationalizes sovereign git push
   for the delegate-less pilot journals). Sources the key two ways:
     --keygen          generate a fresh Ed25519 member key (with --apply, store
                       the priv in Keychain), then add its did:key as a delegate.
     --pubkey=<hex>    add an already-held member key (priv expected in Keychain
                       under (etzhayyim.kotoba-rad, <actor>) so the new delegate's
                       sigref can be member-signed).
   DRY-RUN by default; --apply writes the journal (+ Keychain on --keygen).
   no-server-key: the signature is the MEMBER's, via the Keychain sign-fn seam."
  [& args]
  (let [flags  (set (filter #(str/starts-with? % "--") args))
        apply? (contains? flags "--apply")
        keygen? (contains? flags "--keygen")
        actor  (first (remove #(str/starts-with? % "--") args))
        pubkey-arg (some->> args (filter #(str/starts-with? % "--pubkey="))
                            first (drop 9) (apply str) not-empty)]
    (when-not actor
      (println "usage: bb actor:delegate-add <name> (--keygen | --pubkey=<hex>) [--apply]")
      (System/exit 2))
    (let [{:keys [pub-hex]}
          (cond keygen?    (let [kp (gen-keypair)]
                             (when apply? (keychain-store! actor (:priv-b64 kp))
                                          (println "stored  priv in Keychain:"
                                                   keychain-service "/" actor))
                             kp)
                pubkey-arg {:pub-hex pubkey-arg}
                :else      (do (println "error: pass --keygen or --pubkey=<hex>")
                               (System/exit 2)))
          sign-fn (when apply? (sign-fn-for-actor actor pub-hex))]
      (println "actor   " actor)
      (println "did:key " (rad/did-key pub-hex))
      (when (and apply? (not sign-fn))
        (println "WARN    no member key in Keychain for" actor
                 "— the delegate's sigref will be UNSIGNED"))
      (if apply?
        (let [res (rad/add-delegate! actor pub-hex {:sign-fn sign-fn})]
          (println "rid     " (:rid res))
          (println "added?  " (:added? res) " signed?" (:signed? res)
                   " head" (:head res)))
        (println "DRY-RUN — would append :rad/delegate" (rad/did-key pub-hex)
                 "to the journal of" actor "(pass --apply to write)")))))
