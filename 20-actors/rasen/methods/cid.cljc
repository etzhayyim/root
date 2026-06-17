(ns rasen.methods.cid
  "rasen 螺旋 — kotoba IPFS content-address (CIDv1, raw, sha2-256, base32).
  1:1 Clojure port of `methods/cid.py` (ADR-2606101000).

  Pure re-implementation of the repo-canonical content-address used by the WASM loaders
  (CIDv1, raw codec 0x55, multihash sha2-256 0x12 0x20, multibase base32-lower with the 'b'
  prefix). This is the SAME CID `ipfs add --cid-version=1 --raw-leaves` produces for a single
  raw block (< 256 KiB), so a kotoba artifact's content-address is verifiable with or without
  the `ipfs` daemon. Verified byte-identical against `ipfs` 0.41.0.

  Single-block only by design: rasen ingests a BOUNDED public-reference slice (G5/G7), so the
  EDN/Datom artifacts fit one raw block. Artifacts > 256 KiB would chunk into a UnixFS dag-pb
  tree (root codec 0x70) and need the ipfs builder — out of scope for the bounded slice.

  House style: pure fns; sha2-256 behind #?(:clj …) (java.security.MessageDigest)."
  (:require [clojure.string :as str]))

;; RFC4648 base32 lower, no padding (multibase 'b')
(def ^:private b32 "abcdefghijklmnopqrstuvwxyz234567")

(defn- ->unsigned
  "Coerce a (possibly signed) byte to an int in [0,255]."
  [b]
  (bit-and (int b) 0xff))

(defn- drain
  "Emit all complete 5-bit groups from (val,bits); returns [bits val] with bits < 5."
  [^StringBuilder out bits val]
  (if (>= bits 5)
    (do (.append out (nth b32 (bit-and (bit-shift-right val (- bits 5)) 31)))
        (recur out (- bits 5) val))
    [bits val]))

(defn base32
  "RFC4648 base32-lower, no padding. `data` = seq of byte/int values. Mirrors cid.py `_base32`."
  [data]
  (let [out (StringBuilder.)]
    (loop [data (seq data), bits 0, val 0]
      (if (empty? data)
        (do
          (when (pos? bits)
            (.append out (nth b32 (bit-and (bit-shift-left val (- 5 bits)) 31))))
          (.toString out))
        (let [val (bit-or (bit-shift-left val 8) (->unsigned (first data)))
              [bits val] (drain out (+ bits 8) val)]
          (recur (rest data) bits val))))))

(defn- sha256-bytes
  "Raw 32-byte sha2-256 digest of a byte-array, as a vector of unsigned ints [0,255]."
  [^bytes data]
  #?(:clj
     (let [d (.digest (java.security.MessageDigest/getInstance "SHA-256") data)]
       (mapv ->unsigned d))
     :cljs
     (throw (js/Error. "sha256 not available in cljs runtime"))))

(defn cidv1-raw
  "CIDv1 / raw (0x55) / sha2-256 — matches `ipfs add --cid-version=1 --raw-leaves`.
  Accepts a byte-array (or a String, encoded UTF-8). Returns the multibase-'b' base32 CID."
  [data]
  (let [^bytes ba #?(:clj (if (string? data) (.getBytes ^String data "UTF-8") data)
                     :cljs (throw (js/Error. "cidv1-raw not available in cljs runtime")))
        mh (concat [0x12 0x20] (sha256-bytes ba))   ;; sha2-256, 32-byte digest
        cid (concat [0x01 0x55] mh)]                ;; CIDv1, raw codec
    (str "b" (base32 cid))))

;; ipfs default chunk size; above this the raw CID no longer applies
(def single-block-limit (* 256 1024))

;; NOTE: the original cid.py `__main__` CLI demo (prints CID per file arg) is omitted.
