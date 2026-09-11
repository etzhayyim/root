;; ported from 20-actors/hakoniwa/methods/cid.py — gold reference (Fable)
;; kotoba IPFS content-address (CIDv1, raw 0x55, sha2-256 0x12 0x20, multibase base32-lower 'b').
;; `ipfs add --cid-version=1 --raw-leaves` が単一 raw ブロック (<256 KiB) に対して出すのと同一 CID。
(ns hakoniwa.methods.cid
  (:import [java.security MessageDigest]))

(def ^:private b32-alphabet "abcdefghijklmnopqrstuvwxyz234567") ; RFC4648 base32 lower, no padding

(def single-block-limit (* 256 1024))

(defn- base32
  "multibase 'b' base32-lower (パディングなし) でバイト列を符号化する。"
  [^bytes data]
  (let [sb (StringBuilder.)]
    (loop [i 0, val 0, bits 0]
      (if (< i (alength data))
        (let [val (bit-or (bit-shift-left val 8)
                          (bit-and (aget data i) 0xff))
              bits (+ bits 8)]
          ;; bits>=5 の間、5bit ずつ取り出して文字に
          (let [val+bits (loop [val val, bits bits]
                           (if (>= bits 5)
                             (do (.append sb (.charAt b32-alphabet
                                                      (bit-and (unsigned-bit-shift-right val (- bits 5)) 31)))
                                 (recur val (- bits 5)))
                             [val bits]))]
            (recur (inc i) (first val+bits) (second val+bits))))
        (do
          (when (pos? bits)
            (.append sb (.charAt b32-alphabet
                                 (bit-and (bit-shift-left val (- 5 bits)) 31))))
          (.toString sb))))))

(defn- sha256 ^bytes [^bytes data]
  (.digest (MessageDigest/getInstance "SHA-256") data))

(defn cidv1-raw
  "CIDv1 / raw (0x55) / sha2-256 — `ipfs add --cid-version=1 --raw-leaves` と一致。"
  [^bytes data]
  (let [digest (sha256 data)
        out (byte-array (+ 4 (alength digest)))]
    (aset-byte out 0 0x01)   ; CIDv1
    (aset-byte out 1 0x55)   ; raw codec
    (aset-byte out 2 0x12)   ; sha2-256
    (aset-byte out 3 0x20)   ; 32-byte digest
    (System/arraycopy digest 0 out 4 (alength digest))
    (str "b" (base32 out))))
