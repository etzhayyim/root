(ns rasen.methods.cid
  "rasen 螺旋 — kotoba IPFS content-address (CIDv1, raw, sha2-256, base32).

   Pure re-implementation of the repo-canonical content-address used by the WASM
   loaders (20-actors/*/wasm/verify.mjs, ADR-2605231525 / 2606014500): CIDv1, raw codec
   (0x55), multihash sha2-256 (0x12 0x20), multibase base32-lower with the 'b' prefix. This
   is the SAME CID `ipfs add --cid-version=1 --raw-leaves` produces for a single raw block
   (< 256 KiB), so a kotoba artifact's content-address is verifiable with or without the
   `ipfs` daemon. Verified byte-identical against `ipfs` 0.41.0.

   Single-block only by design: rasen ingests a BOUNDED public-reference slice (G5/G7), so the
   EDN/Datom artifacts fit one raw block. Artifacts > 256 KiB would chunk into a UnixFS dag-pb
   tree (root codec 0x70) and need the ipfs builder — out of scope for the bounded slice."
  (:import [java.security MessageDigest]))

(def ^:private B32 "abcdefghijklmnopqrstuvwxyz234567")

(defn- base32
  "RFC4648 base32 lower, no padding (multibase 'b')."
  [^bytes data]
  (let [n (alength data)
        sb (StringBuilder.)]
    (loop [i 0
           bits 0
           val 0]
      (if (< i n)
        (let [b (bit-and (long (aget data i)) 0xFF)
              val' (bit-or (bit-shift-left val 8) b)
              bits' (+ bits 8)]
          (let [[v b']
                (loop [v val'
                       b bits']
                  (if (>= b 5)
                    (let [idx (bit-and (unsigned-bit-shift-right v (- b 5)) 31)]
                      (.append sb (nth B32 idx))
                      (recur v (- b 5)))
                    [v b]))]
            (recur (inc i) b' v)))
        (do
          (when (> bits 0)
            (let [idx (bit-and (bit-shift-left val (- 5 bits)) 31)]
              (.append sb (nth B32 idx))))
          (.toString sb))))))

(defn- sha256-digest
  [^bytes data]
  (.digest (doto (MessageDigest/getInstance "SHA-256")
             (.update data))))

(defn cidv1-raw
  "CIDv1 / raw (0x55) / sha2-256 — matches `ipfs add --cid-version=1 --raw-leaves`."
  [^bytes data]
  (let [digest (sha256-digest data)
        digest-len (alength digest)
        cid-len (+ 4 digest-len)
        cid (byte-array cid-len)]
    (aset-byte cid 0 (byte 0x01))
    (aset-byte cid 1 (byte 0x55))
    (aset-byte cid 2 (byte 0x12))
    (aset-byte cid 3 (byte 0x20))
    (System/arraycopy digest 0 cid 4 digest-len)
    (str "b" (base32 cid))))

(def SINGLE_BLOCK_LIMIT (* 256 1024))
