(ns etzhayyim.aozora.repo.cid
  "CIDv1 **dag-cbor** (codec 0x71) content addresses for repo blocks.

  Framing (CIDv1 = <multibase> <version> <codec> <multihash>):
    multibase 'b' (base32 lower, RFC4648 no pad) · version 0x01 ·
    codec 0x71 (dag-cbor) · multihash = <0x12 sha2-256> <0x20 len=32> <digest>.

  Same proven framing as `etzhayyim.kotoba.cid` (CIDv1/raw, byte-identical to
  `ipfs add --cid-version=1`), specialised to the dag-cbor codec for repo
  records/MST nodes. VERIFIED byte-identical to `ipfs dag put --store-codec
  dag-cbor` — see repo_test.clj golden vectors."
  (:require [etzhayyim.aozora.repo.dag-cbor :as dc])
  (:import [java.security MessageDigest]))

(def ^:private b32-alphabet "abcdefghijklmnopqrstuvwxyz234567")

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

(defn- sha2-256 ^bytes [^bytes b]
  (.digest (MessageDigest/getInstance "SHA-256") b))

(defn cid-of-cbor
  "CIDv1(dag-cbor, sha2-256) base32 string for already-encoded dag-cbor bytes."
  [^bytes cbor]
  (let [digest (sha2-256 cbor)
        framed (byte-array (+ 4 (alength digest)))]
    (aset-byte framed 0 (byte 0x01))   ;; version 1
    (aset-byte framed 1 (byte 0x71))   ;; codec dag-cbor
    (aset-byte framed 2 (byte 0x12))   ;; multihash sha2-256
    (aset-byte framed 3 (byte 0x20))   ;; digest length 32
    (System/arraycopy digest 0 framed 4 (alength digest))
    (str "b" (base32-encode framed))))

(defn cid-of
  "CIDv1(dag-cbor) of a Clojure value."
  [v] (cid-of-cbor (dc/encode v)))

(defn block
  "Encode a value to its repo block: {:cid <cidv1 dag-cbor> :bytes <dag-cbor>}."
  [v]
  (let [cbor (dc/encode v)]
    {:cid (cid-of-cbor cbor) :bytes cbor}))
