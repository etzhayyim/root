(ns hinagata.methods.cid
  "hinagata 雛形 — kotoba IPFS content-address (CIDv1, raw, sha2-256, base32).
  1:1 Clojure port of `methods/cid.py` (ADR-2606111954).

  Pure-stdlib re-implementation of the repo-canonical content-address used by the WASM
  loaders: CIDv1, raw codec (0x55), multihash sha2-256 (0x12 0x20), multibase base32-lower
  with the 'b' prefix. This is the SAME CID `ipfs add --cid-version=1 --raw-leaves` produces
  for a single raw block (< 256 KiB), so a published template body's content-address is
  verifiable with or without the `ipfs` daemon (G4).

  Single-block only by design: an individual template body / clause text fits one raw block.

  House style: pure fns; the byte-oriented entry points take a byte-array (or seq of ints).
  `bytes-of` is the string→UTF-8 bytes edge. The Python `__main__` file demo is omitted.
  Self-contained (own sha-256 via java.security.MessageDigest); no sibling require."
  (:require [clojure.string :as str]))

(def ^:private B32 "abcdefghijklmnopqrstuvwxyz234567") ;; RFC4648 base32 lower, no padding (multibase 'b')

(defn bytes-of
  "UTF-8 bytes of a string (the encode('utf-8') edge in the Python callers)."
  ^bytes [^String s]
  (.getBytes s "UTF-8"))

(defn- ->ints
  "Coerce a byte-array (signed) into a seq of unsigned ints [0,255], matching Python's
  iteration over `bytes`."
  [data]
  (if (bytes? data)
    (map #(bit-and (int %) 0xff) data)
    (map #(bit-and (int %) 0xff) data)))

(defn base32
  "Port of _base32(data) — RFC4648 base32 lower, no padding (multibase 'b' body)."
  [data]
  (let [sb (StringBuilder.)]
    (loop [bs (->ints data), val 0, bits 0]
      (if (seq bs)
        (let [val (bit-or (bit-shift-left val 8) (first bs))
              bits (+ bits 8)]
          ;; while bits >= 5: emit a 5-bit group
          (let [[val bits]
                (loop [val val, bits bits]
                  (if (>= bits 5)
                    (do (.append sb (.charAt B32 (bit-and (bit-shift-right val (- bits 5)) 31)))
                        (recur val (- bits 5)))
                    [val bits]))]
            (recur (rest bs) val bits)))
        ;; flush the trailing partial group
        (do
          (when (> bits 0)
            (.append sb (.charAt B32 (bit-and (bit-shift-left val (- 5 bits)) 31))))
          (.toString sb))))))

(defn- sha256-digest
  "Raw sha-256 digest bytes of a byte-array (UTF-8 already applied by the caller)."
  ^bytes [data]
  (let [^bytes ba (if (bytes? data) data (byte-array (map unchecked-byte (->ints data))))]
    (.digest (java.security.MessageDigest/getInstance "SHA-256") ba)))

(defn cidv1-raw
  "CIDv1 / raw (0x55) / sha2-256 — matches `ipfs add --cid-version=1 --raw-leaves`.
  `data` is a byte-array (or seq of ints)."
  [data]
  (let [digest (sha256-digest data)
        ;; mh = [0x12 0x20] + digest ; cid = [0x01 0x55] + mh
        cid (concat [0x01 0x55 0x12 0x20] (map #(bit-and (int %) 0xff) digest))]
    (str "b" (base32 cid))))

(defn sha256-hex
  "0x-prefixed lowercase hex SHA-256 — the esign documentSha256 defense-in-depth hash.
  `data` is a byte-array (or seq of ints)."
  [data]
  (str "0x" (apply str (map #(format "%02x" (bit-and (int %) 0xff)) (sha256-digest data)))))

(def SINGLE-BLOCK-LIMIT (* 256 1024)) ;; ipfs default chunk size; above this the raw CID no longer applies
