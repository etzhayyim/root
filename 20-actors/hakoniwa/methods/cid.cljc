;; ported from 20-actors/hakoniwa/methods/cid.py — real port replacing the unit_refactor
;; stage-0 "TODO: port-failed" stubs (and the wrong root.hakoniwa.* ns). 20-actors is the bb
;; source root, so hakoniwa.methods.cid resolves; the root.* prefix never did.
(ns hakoniwa.methods.cid
  "cid.py — hakoniwa 箱庭 kotoba IPFS content-address (CIDv1 / raw 0x55 / sha2-256 / base32-lower).
  1:1 Clojure port of `methods/cid.py`.

  Produces the SAME CID `ipfs add --cid-version=1 --raw-leaves` produces for a single raw block
  (< 256 KiB). Single-block only by design (hakoniwa ingests a BOUNDED slice → one raw block).

  Self-contained: own sha-256 + base32; no third-party deps. The Python `__main__` demo printer
  is intentionally omitted.")

;; RFC4648 base32 lower, no padding (multibase 'b').
(def ^:private b32 "abcdefghijklmnopqrstuvwxyz234567")

(defn base32
  "Bytes (seq of unsigned ints 0..255) → RFC4648 base32-lower, no padding. Mirrors _base32."
  [data]
  (let [sb (StringBuilder.)]
    (loop [bs (seq data), val 0, bits 0]
      (if bs
        (let [val (bit-or (bit-shift-left val 8) (bit-and (long (first bs)) 0xff))
              bits (+ bits 8)]
          ;; while bits >= 5: emit a 5-bit group
          (let [[val bits] (loop [val val, bits bits]
                             (if (>= bits 5)
                               (do (.append sb (nth b32 (bit-and (bit-shift-right val (- bits 5)) 31)))
                                   (recur val (- bits 5)))
                               [val bits]))]
            (recur (next bs) val bits)))
        (do
          (when (> bits 0)
            (.append sb (nth b32 (bit-and (bit-shift-left val (- 5 bits)) 31))))
          (.toString sb))))))

(defn- sha256-bytes
  "UTF-8 string OR byte-array → vector of unsigned-int sha-256 digest bytes."
  [s]
  (let [^bytes b (if (bytes? s) s (.getBytes ^String s "UTF-8"))
        d (.digest (java.security.MessageDigest/getInstance "SHA-256") b)]
    (mapv #(bit-and % 0xff) d)))

(defn cidv1-raw
  "CIDv1 / raw (0x55) / sha2-256 of the bytes (UTF-8 string OR byte-array) — matches
  `ipfs add --cid-version=1 --raw-leaves`. Returns the multibase-'b' base32 CID string."
  [data]
  (let [digest (sha256-bytes data)                ;; sha2-256, 32-byte digest
        mh     (into [0x12 0x20] digest)          ;; multihash: sha2-256 (0x12), len 32 (0x20)
        cid    (into [0x01 0x55] mh)]             ;; CIDv1 (0x01), raw codec (0x55)
    (str "b" (base32 cid))))

(def single-block-limit (* 256 1024))
