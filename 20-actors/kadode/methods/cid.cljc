(ns kadode.methods.cid
  "hinagata 雛形 — kotoba IPFS content-address (CIDv1, raw, sha2-256, base32).
  1:1 Clojure port of `methods/cid.py` (ADR-2606112238).

  Pure-stdlib re-implementation of the repo-canonical content-address used by the WASM
  loaders (ADR-2605231525 / 2606014500): CIDv1, raw codec (0x55), multihash sha2-256
  (0x12 0x20), multibase base32-lower with the 'b' prefix. This is the SAME CID
  `ipfs add --cid-version=1 --raw-leaves` produces for a single raw block (< 256 KiB), so a
  published template body's content-address is verifiable with or without the `ipfs` daemon
  (G4).

  Single-block only by design: an individual template body / clause text fits one raw block.

  Operates on bytes; callers pass UTF-8 bytes (str → (->bytes s)). sha-256 is host-only behind
  #?(:clj …)."
  (:require [clojure.string :as str]))

(def ^:private b32 "abcdefghijklmnopqrstuvwxyz234567") ; RFC4648 base32 lower, no padding (multibase 'b')

(defn ->bytes
  "UTF-8 encode a string to a byte-array (matches Python str.encode(\"utf-8\")); pass-through a
  byte-array / byte seq unchanged."
  [s]
  (if (string? s)
    #?(:clj (.getBytes ^String s "UTF-8") :default (throw (ex-info "no utf-8 host" {})))
    s))

(defn base32
  "Port of _base32: 5-bit-group base32-lower encode of the bytes (no padding). `data` is a seq
  of bytes (signed Java bytes are masked to 0..255)."
  [data]
  (let [out (StringBuilder.)]
    (loop [bs (seq data), val 0, bits 0]
      (if (empty? bs)
        (do
          (when (pos? bits)
            (.append out (.charAt b32 (bit-and (bit-shift-left val (- 5 bits)) 31))))
          (.toString out))
        (let [b (bit-and (int (first bs)) 0xff)
              val (bit-or (bit-shift-left val 8) b)
              bits (+ bits 8)
              ;; emit every complete 5-bit group; carry the remainder
              [val bits] (loop [val val, bits bits]
                           (if (>= bits 5)
                             (do
                               (.append out (.charAt b32 (bit-and (unsigned-bit-shift-right val (- bits 5)) 31)))
                               (recur val (- bits 5)))
                             [val bits]))]
          (recur (rest bs) val bits))))))

#?(:clj
   (defn- sha256-bytes
     "Raw 32-byte SHA-256 digest of a byte-array (seq of signed Java bytes)."
     [data]
     (let [md (java.security.MessageDigest/getInstance "SHA-256")]
       (.digest md (byte-array (map unchecked-byte data))))))

(defn cidv1-raw
  "CIDv1 / raw (0x55) / sha2-256 — matches `ipfs add --cid-version=1 --raw-leaves`.
  `data` = a byte-array / byte seq (use (->bytes s) for a string)."
  [data]
  #?(:clj
     (let [digest (sha256-bytes data)
           mh (concat [0x12 0x20] (seq digest))   ; sha2-256, 32-byte digest
           cid (concat [0x01 0x55] mh)]           ; CIDv1, raw codec
       (str "b" (base32 cid)))
     :default (throw (ex-info "bind a sha-256 impl on this host" {}))))

(defn sha256-hex
  "0x-prefixed lowercase hex SHA-256 — the esign documentSha256 defense-in-depth hash.
  `data` = a byte-array / byte seq."
  [data]
  #?(:clj
     (str "0x" (apply str (map #(format "%02x" (bit-and % 0xff)) (sha256-bytes data))))
     :default (throw (ex-info "bind a sha-256 impl on this host" {}))))

(def single-block-limit (* 256 1024)) ; ipfs default chunk size; above this the raw CID no longer applies

#?(:clj
   (defn -main
     "CLI: print the CIDv1 + sha256-hex of each file argument (file I/O at this edge)."
     [& argv]
     (doseq [p argv]
       (let [data (#?(:clj (fn [^String f]
                             (with-open [in (clojure.java.io/input-stream f)]
                               (let [baos (java.io.ByteArrayOutputStream.)]
                                 (clojure.java.io/copy in baos)
                                 (.toByteArray baos))))) p)
             warn (if (> (count data) single-block-limit)
                    "  ⚠ >256KiB: dag-pb, not single raw block" "")]
         (println (str (cidv1-raw data) "  " (sha256-hex data) "  " p
                       "  (" (count data) " B)" warn))))
     0))
