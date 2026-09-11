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

;; ── base32 encode + binary→CID (inverse of cid-str->binary, for the decoder) ─
(defn- base32-encode [^bytes data]
  (let [n (alength data) sb (StringBuilder.)]
    (loop [i 0 buf 0 bits 0]
      (cond
        (>= bits 5) (let [idx (bit-and (unsigned-bit-shift-right buf (- bits 5)) 0x1f)]
                      (.append sb (.charAt b32-alphabet idx)) (recur i buf (- bits 5)))
        (< i n)     (recur (inc i) (bit-or (bit-shift-left buf 8) (bit-and (aget data i) 0xff)) (+ bits 8))
        (pos? bits) (let [idx (bit-and (bit-shift-left buf (- 5 bits)) 0x1f)]
                      (.append sb (.charAt b32-alphabet idx)) (recur i 0 0))
        :else       (.toString sb)))))

(defn binary->cid-str
  "Encode binary CID bytes (version‖codec‖multihash) to a `b`-prefixed base32 string."
  [^bytes bin]
  (str "b" (base32-encode bin)))

;; ── dag-cbor decoder (round-trips encode; CID links → CidLink) ───────────────
(defn- uint-from ^long [^bytes b ^long i ^long n]
  (loop [k 0 acc 0] (if (= k n) acc (recur (inc k) (bit-or (bit-shift-left acc 8)
                                                           (bit-and (aget b (int (+ i k))) 0xff))))))

(defn- read-head
  "Return [major arg next-index] for the CBOR head at `i`."
  [^bytes b ^long i]
  (let [b0 (bit-and (aget b (int i)) 0xff)
        major (bit-shift-right b0 5)
        info (bit-and b0 0x1f)]
    (cond
      (< info 24) [major info (inc i)]
      (= info 24) [major (bit-and (aget b (int (inc i))) 0xff) (+ i 2)]
      (= info 25) [major (uint-from b (inc i) 2) (+ i 3)]
      (= info 26) [major (uint-from b (inc i) 4) (+ i 5)]
      (= info 27) [major (uint-from b (inc i) 8) (+ i 9)]
      :else (throw (ex-info "dag-cbor: bad head info" {:info info})))))

(defn- decode-at [^bytes b ^long i]
  (let [[major arg j] (read-head b i)]
    (case (int major)
      0 [arg j]
      1 [(- (- arg) 1) j]
      2 [(java.util.Arrays/copyOfRange b (int j) (int (+ j arg))) (+ j arg)]
      3 [(String. b (int j) (int arg) "UTF-8") (+ j arg)]
      4 (loop [k 0 idx j acc []]
          (if (= k arg) [acc idx]
              (let [[v ni] (decode-at b idx)] (recur (inc k) ni (conj acc v)))))
      5 (loop [k 0 idx j acc {}]
          (if (= k arg) [acc idx]
              (let [[kk ni] (decode-at b idx) [vv n2] (decode-at b ni)]
                (recur (inc k) n2 (assoc acc kk vv)))))
      6 (if (= arg 42)
          (let [[bs ni] (decode-at b j)]   ;; byte string = 0x00 ‖ binary CID
            [(->CidLink (binary->cid-str (java.util.Arrays/copyOfRange ^bytes bs 1 (alength ^bytes bs)))) ni])
          (throw (ex-info "dag-cbor: unsupported tag" {:tag arg})))
      7 (case (int arg) 20 [false j] 21 [true j] 22 [nil j]
              (throw (ex-info "dag-cbor: unsupported simple/float" {:arg arg})))
      (throw (ex-info "dag-cbor: bad major" {:major major})))))

(defn decode
  "Decode dag-cbor bytes to a Clojure value (round-trips `encode`; maps have
  string keys, CID links become `CidLink`, byte strings become byte-arrays)."
  [^bytes b]
  (first (decode-at b 0)))
