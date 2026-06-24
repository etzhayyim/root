(ns etzhayyim.aozora.repo.dag-cbor
  "Deterministic IPLD **dag-cbor** encoder — the subset AT Protocol repos use:
  null / bool / int / text / bytes / array / map + CID links (tag 42).

  This is the byte layer beneath the repo block addresses (cid.clj): a record's
  canonical form is its dag-cbor bytes, and its CIDv1(dag-cbor) is the hash of
  exactly these bytes. Determinism rules (so every node computes the same CID):

    * map keys sorted **length-first, then bytewise** (RFC 7049 canonical — what
      dag-cbor mandates; VERIFIED against `ipfs dag put`, not RFC 8949 bytewise);
    * integers in shortest form (major 0 unsigned / 1 negative);
    * floats are REJECTED (AT Protocol lexicons disallow them in records);
    * CID links encode as tag 42 → byte string `0x00 ‖ <binary CID>`.

  No external deps — pure JVM/babashka. Output bytes are verified byte-identical
  to go-ipfs `dag put` (see repo_test.clj golden vectors)."
  (:require [clojure.string :as str])
  (:import [java.io ByteArrayOutputStream]))

;; ── CID link marker ──────────────────────────────────────────────────────────
;; A value the encoder writes as a CBOR tag-42 link (vs an ordinary map). The
;; repo/MST layers wrap child + value CIDs in this; record JSON `{$link cid}` is
;; lifted to it by the repo layer.
(defrecord CidLink [^String cid])
(defn cid-link [cid-str] (->CidLink cid-str))
(defn cid-link? [x] (instance? CidLink x))

;; ── base32 decode (RFC4648 lower, no pad) — to recover binary CID bytes ──────
(def ^:private b32-alphabet "abcdefghijklmnopqrstuvwxyz234567")
(def ^:private b32-rev
  (into {} (map-indexed (fn [i c] [c i]) b32-alphabet)))

(defn base32-decode ^bytes [^String s]
  (let [out (ByteArrayOutputStream.)]
    (loop [i 0 buf 0 bits 0]
      (if (< i (count s))
        (let [v (b32-rev (Character/toLowerCase (.charAt s i)))]
          (when (nil? v) (throw (ex-info "bad base32 char" {:s s})))
          (let [buf (bit-or (bit-shift-left buf 5) (int v))
                bits (+ bits 5)]
            (if (>= bits 8)
              (let [bits (- bits 8)]
                (.write out (int (bit-and (unsigned-bit-shift-right buf bits) 0xff)))
                (recur (inc i) buf bits))
              (recur (inc i) buf bits))))
        (.toByteArray out)))))

(defn cid-str->binary
  "Decode a `b`-prefixed base32 multibase CIDv1 string to its binary CID bytes
  (version ‖ codec ‖ multihash). Only the base32 multibase ('b') is supported —
  the form this repo emits."
  ^bytes [^String cid]
  (when-not (str/starts-with? cid "b")
    (throw (ex-info "only base32 ('b') multibase CIDs are supported" {:cid cid})))
  (base32-decode (subs cid 1)))

;; ── CBOR writer ──────────────────────────────────────────────────────────────
(defn- w! [^ByteArrayOutputStream o b] (.write o (int (bit-and b 0xff))))

(defn- head!
  "Write a CBOR head: major type `mt` (0..7) + unsigned argument `n`, shortest."
  [^ByteArrayOutputStream o mt ^long n]
  (let [hb (bit-shift-left mt 5)]
    (cond
      (< n 24)            (w! o (bit-or hb n))
      (< n 0x100)         (do (w! o (bit-or hb 24)) (w! o n))
      (< n 0x10000)       (do (w! o (bit-or hb 25))
                              (w! o (unsigned-bit-shift-right n 8)) (w! o n))
      (< n 0x100000000)   (do (w! o (bit-or hb 26))
                              (dotimes [i 4] (w! o (unsigned-bit-shift-right n (* 8 (- 3 i))))))
      :else               (do (w! o (bit-or hb 27))
                              (dotimes [i 8] (w! o (unsigned-bit-shift-right n (* 8 (- 7 i))))))) ))

(defn- key->str [k]
  (cond (string? k) k
        (keyword? k) (name k)
        :else (throw (ex-info "map key must be string/keyword" {:k k}))))

(defn- key-bytes ^bytes [k] (.getBytes ^String (key->str k) "UTF-8"))

(defn- cmp-key-bytes [^bytes a ^bytes b]
  ;; length-first, then unsigned bytewise (dag-cbor canonical map ordering)
  (let [la (alength a) lb (alength b)]
    (if (not= la lb)
      (Integer/compare la lb)
      (loop [i 0]
        (if (= i la) 0
            (let [d (Integer/compare (bit-and (aget a i) 0xff) (bit-and (aget b i) 0xff))]
              (if (zero? d) (recur (inc i)) d)))))))

(declare encode!)

(defn- encode-int! [^ByteArrayOutputStream o ^long n]
  (if (>= n 0) (head! o 0 n) (head! o 1 (- (- n) 1))))

(defn- encode-link! [^ByteArrayOutputStream o ^CidLink link]
  (let [bin (cid-str->binary (.cid link))
        framed (byte-array (inc (alength bin)))]
    (aset-byte framed 0 (byte 0))            ;; 0x00 multibase-identity prefix
    (System/arraycopy bin 0 framed 1 (alength bin))
    (w! o 0xd8) (w! o 0x2a)                   ;; tag 42
    (head! o 2 (alength framed))             ;; byte string
    (.write o framed 0 (alength framed))))

(defn- encode! [^ByteArrayOutputStream o v]
  (cond
    (cid-link? v) (encode-link! o v)
    (nil? v)      (w! o 0xf6)
    (true? v)     (w! o 0xf5)
    (false? v)    (w! o 0xf4)
    (integer? v)  (encode-int! o (long v))
    (float? v)    (throw (ex-info "dag-cbor: floats are disallowed in AT Proto records" {:v v}))
    (string? v)   (let [bs (.getBytes ^String v "UTF-8")] (head! o 3 (alength bs)) (.write o bs 0 (alength bs)))
    (bytes? v)    (do (head! o 2 (alength ^bytes v)) (.write o ^bytes v 0 (alength ^bytes v)))
    (keyword? v)  (let [bs (.getBytes (name v) "UTF-8")] (head! o 3 (alength bs)) (.write o bs 0 (alength bs)))
    (map? v)      (let [entries (->> v (map (fn [[k val]] [(key-bytes k) (key->str k) val]))
                                     (sort-by first cmp-key-bytes))]
                    (head! o 5 (count entries))
                    (doseq [[kb _ val] entries]
                      (head! o 3 (alength ^bytes kb)) (.write o ^bytes kb 0 (alength ^bytes kb))
                      (encode! o val)))
    (sequential? v) (do (head! o 4 (count v)) (doseq [x v] (encode! o x)))
    :else (throw (ex-info "dag-cbor: unencodable value" {:type (type v) :v v}))))

(defn encode
  "Encode a Clojure value to deterministic dag-cbor bytes."
  ^bytes [v]
  (let [o (ByteArrayOutputStream.)] (encode! o v) (.toByteArray o)))
