(ns hakoniwa.methods.cid
  "kotoba IPFS content-address (CIDv1, raw, sha2-256, base32).

   Pure re-implementation of the repo-canonical content-address used by the WASM loaders
   (20-actors/*/wasm/verify.mjs, ADR-2605231525 / 2606014500) and by rasen's ingest:
   CIDv1, raw codec (0x55), multihash sha2-256 (0x12 0x20), multibase base32-lower
   with 'b' prefix.  This is the SAME CID `ipfs add --cid-version=1 --raw-leaves`
   produces for a single raw block (< 256 KiB), so an ingested box's content-address
   is verifiable with or without the `ipfs` daemon.

   Single-block only by design: hakoniwa ingests a BOUNDED public-entity slice (G6/G8),
   so the EDN artifact fits one raw block.")

(def ^:private b32 "abcdefghijklmnopqrstuvwxyz234567")

(defn- base32
  "RFC4648 base32 lower, no padding (multibase 'b'). Flushes ALL complete 5-bit groups as each
  byte is consumed (the leftover after the final byte is always <5 bits), then emits one final
  partial group — matches Python base64.b32encode(...).lower().rstrip('=')."
  [^bytes data]
  (let [n (alength data)
        sb (StringBuilder.)]
    (loop [i 0 bits 0 val 0]
      (if (< i n)
        (let [b (bit-and (long (aget data i)) 0xFF)
              v (bit-or (bit-shift-left val 8) b)
              [v' b'] (loop [v v bb (+ bits 8)]
                        (if (>= bb 5)
                          (do (.append sb (.charAt b32 (bit-and (unsigned-bit-shift-right v (- bb 5)) 0x1F)))
                              (recur v (- bb 5)))
                          [v bb]))]
          (recur (inc i) b' v'))
        (do (when (> bits 0)
              (.append sb (.charAt b32 (bit-and (bit-shift-left val (- 5 bits)) 0x1F))))
            (.toString sb))))))

(defn cidv1-raw
  "CIDv1 / raw (0x55) / sha2-256 — matches `ipfs add --cid-version=1 --raw-leaves`."
  [^bytes data]
  (let [md (java.security.MessageDigest/getInstance "SHA-256")
        _ (.update md data)
        digest (.digest md)
        mh (byte-array (concat [0x12 0x20] (seq digest)))
        cid (byte-array (concat [0x01 0x55] (seq mh)))]
    (str "b" (base32 cid))))

(def SINGLE-BLOCK-LIMIT (* 256 1024))
