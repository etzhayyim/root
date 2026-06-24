(ns etzhayyim.pds.util
  "atproto identifier primitives: TID record keys + content addressing.

  Independent of any vendor SDK — pure JVM/babashka."
  (:require [cheshire.core :as json])
  (:import [java.security MessageDigest]))

;; ── base32 (RFC 4648 lower-case, no padding) — the atproto alphabet ──────────
(def ^:private b32-alphabet "234567abcdefghijklmnopqrstuvwxyz")

(defn- long->b32
  "Encode a non-negative long as sortable base32 of fixed `width` chars."
  [^long n ^long width]
  (loop [n n, acc '()]
    (if (>= (count acc) width)
      (apply str acc)
      (recur (unsigned-bit-shift-right n 5)
             (cons (.charAt b32-alphabet (int (bit-and n 0x1f))) acc)))))

(defn- bytes->b32 [^bytes bs]
  (let [sb (StringBuilder.)]
    (loop [buf 0, bits 0, i 0]
      (cond
        ;; enough accumulated bits to emit a 5-bit group (the top 5)
        (>= bits 5)
        (let [bits (- bits 5)]
          (.append sb (.charAt b32-alphabet (int (bit-and (unsigned-bit-shift-right buf bits) 0x1f))))
          (recur buf bits i))
        ;; pull in the next byte
        (< i (alength bs))
        (recur (bit-or (bit-shift-left buf 8) (bit-and (aget bs i) 0xff)) (+ bits 8) (inc i))
        ;; flush trailing bits (left-pad to a final group)
        (pos? bits)
        (do (.append sb (.charAt b32-alphabet (int (bit-and (bit-shift-left buf (- 5 bits)) 0x1f))))
            (str sb))
        :else (str sb)))))

;; ── TID (timestamp identifier) — 13-char sortable rkey ───────────────────────
(def ^:private clockid (long (rand-int 1024)))
(def ^:private last-ts (atom 0))

(defn tid
  "Generate a monotonic atproto TID rkey (microsecond clock + 10-bit clockid)."
  []
  (let [now-us (* (System/currentTimeMillis) 1000)
        ts (swap! last-ts (fn [prev] (if (<= now-us prev) (inc prev) now-us)))]
    (str (long->b32 ts 11) (long->b32 clockid 2))))

;; ── content addressing ───────────────────────────────────────────────────────
(defn sha256-bytes ^bytes [^bytes bs]
  (.digest (MessageDigest/getInstance "SHA-256") bs))

(defn- sha256 ^bytes [^String s]
  (sha256-bytes (.getBytes s "UTF-8")))

(defn content-cid
  "Deterministic content identifier for a record value (stable JSON → sha-256 →
  base32). Prefixed `b` per multibase base32. NOTE: this is a content hash for
  intra-PDS addressing; a spec-exact CIDv1 dag-cbor multihash is a follow-up for
  cross-PDS federation (tracked in README)."
  [value]
  (let [canonical (json/generate-string value {:sort-keys true})]
    (str "b" (bytes->b32 (sha256 canonical)))))

(defn blob-cid
  "Content identifier for a raw blob (sha-256 of the bytes → base32, `b`-prefixed).
  Same intra-PDS addressing family as `content-cid`; spec-exact CIDv1 raw (0x55)
  multihash is the same staged follow-up as record CIDs (README)."
  [^bytes bs]
  (str "b" (bytes->b32 (sha256-bytes bs))))

;; ── base64 (blob payload at rest on the datom log) ───────────────────────────
(defn b64-encode ^String [^bytes bs]
  (.encodeToString (java.util.Base64/getEncoder) bs))

(defn b64-decode ^bytes [^String s]
  (.decode (java.util.Base64/getDecoder) s))

(defn now-iso []
  (str (java.time.Instant/now)))
