(ns tanemaki.methods.cid
  "tanemaki 種蒔き — kotoba IPFS content-address (CIDv1, raw, sha2-256, base32).

   Pure re-implementation of the repo-canonical content-address used by the WASM
   loaders (20-actors/*/wasm/verify.mjs, ADR-2605231525 / 2606014500): CIDv1, raw codec
   (0x55), multihash sha2-256 (0x12 0x20), multibase base32-lower with the 'b' prefix. This
   is the SAME CID `ipfs add --cid-version=1 --raw-leaves` produces for a single raw block
   (< 256 KiB), so a published scorecard body's content-address is verifiable with or without
   the `ipfs` daemon — anyone can re-derive the CID of a tanemaki scorecard and confirm the
   bytes they fetched are the bytes the steward published (G4).

   Single-block only by design: an individual scorecard / proposal fits one raw block.
   Artifacts > 256 KiB would chunk into a UnixFS dag-pb tree (root codec 0x70) and need the
   ipfs builder — out of scope for a single scorecard."
  (:import [java.security MessageDigest]))

(def ^:private b32-alphabet "abcdefghijklmnopqrstuvwxyz234567")

(defn ^:private base32-encode
  "RFC4648 base32 lower, no padding (multibase 'b'). Mirrors Python:
   base64.b32encode(bytes).decode().lower().rstrip('=')"
  [^bytes data]
  (let [len (alength data)]
    (loop [i 0
           bits 0
           val 0
           ^StringBuilder out (StringBuilder.)]
      (if (< i len)
        (let [b (bit-and (aget data i) 0xFF)
              val' (bit-or (bit-shift-left val 8) b)
              bits' (+ bits 8)]
          ;; Consume all possible 5-bit groups from current accumulation
          (let [[bits'' val'' ^StringBuilder out']
                (loop [b bits'
                       v val'
                       ^StringBuilder sb out]
                  (if (>= b 5)
                    (let [idx (bit-and (bit-shift-right v (- b 5)) 0x1F)]
                      (recur (- b 5)
                             v
                             (.append sb (.charAt b32-alphabet idx))))
                    [b v sb]))]
            (recur (inc i) bits'' val'' out')))
        ;; Emit final partial 5-bit group if any bits remain
        (let [out' (if (> bits 0)
                     (.append out
                              (.charAt b32-alphabet
                                       (bit-and (bit-shift-left val (- 5 bits)) 0x1F)))
                     out)]
          (.toString out'))))))

(defn cidv1-raw
  "CIDv1 / raw (0x55) / sha2-256 — matches `ipfs add --cid-version=1 --raw-leaves`."
  [^bytes data]
  (let [md (MessageDigest/getInstance "SHA-256")
        digest (.digest md data)
        n (alength digest)]
    (str "b"
         (-> (doto (byte-array (+ 4 n))
               (aset-byte 0 (byte 0x01))
               (aset-byte 1 (byte 0x55))
               (aset-byte 2 (byte 0x12))
               (aset-byte 3 (byte 0x20))
               ((fn [arr] (System/arraycopy digest 0 arr 4 n))))
             base32-encode))))

(defn sha256-hex
  "0x-prefixed lowercase hex SHA-256 — the proposal scorecardSha256 defense-in-depth hash."
  [^bytes data]
  (let [md (MessageDigest/getInstance "SHA-256")
        digest (.digest md data)
        n (alength digest)]
    (loop [i 0
           ^StringBuilder sb (StringBuilder. (+ 2 (* 2 n)))]
      (if (< i n)
        (let [b (bit-and (aget digest i) 0xFF)]
          (recur (inc i)
                 (doto sb
                   (.append (Character/forDigit (bit-shift-right b 4) 16))
                   (.append (Character/forDigit (bit-and b 0x0F) 16)))))
        (str "0x" (.toString sb))))))

(def SINGLE_BLOCK_LIMIT
  "ipfs default chunk size; above this the raw CID no longer applies"
  (* 256 1024))
