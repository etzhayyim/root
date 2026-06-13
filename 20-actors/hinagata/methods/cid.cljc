(ns hinagata.methods.cid
  "hinagata 雛形 — kotoba IPFS content-address (CIDv1, raw, sha2-256, base32).
  1:1 Clojure port of `methods/cid.py` (ADR-2606111954).

  Pure-stdlib re-implementation of the repo-canonical content-address used by the WASM
  loaders (20-actors/*/wasm/verify.mjs, ADR-2605231525 / 2606014500): CIDv1, raw codec
  (0x55), multihash sha2-256 (0x12 0x20), multibase base32-lower with the 'b' prefix. This
  is the SAME CID `ipfs add --cid-version=1 --raw-leaves` produces for a single raw block
  (< 256 KiB), so a published template body's content-address is verifiable with or without
  the `ipfs` daemon — anyone can re-derive the CID of a hinagata template and confirm the
  bytes they fetched are the bytes the commons published (G4).

  Single-block only by design: an individual template body / clause text fits one raw block.
  Artifacts > 256 KiB would chunk into a UnixFS dag-pb tree (root codec 0x70) and need the
  ipfs builder — out of scope for a single document.

  House style: pure fns; the SHA-256 primitive is taken at the #?(:clj) edge from
  java.security.MessageDigest \"SHA-256\" (NOT blake2b — unlike shomei.methods.blake2b)."
  (:require [clojure.string :as str]))

(def ^:private B32 "abcdefghijklmnopqrstuvwxyz234567") ;; RFC4648 base32 lower, no padding (multibase 'b')

(defn- ->ints
  "Normalise a byte/int seq to a vector of 0..255 ints (mirrors iterating Python `bytes`)."
  [data]
  (mapv #(bit-and (long %) 0xff) data))

(defn base32
  "RFC4648 base32 lower, no padding — mirrors cid.py `_base32` byte-for-byte."
  [data]
  (let [out (transient [])]
    (loop [bs (->ints data), val 0, bits 0]
      (if (seq bs)
        ;; ingest one byte, then drain every complete 5-bit group
        (let [val (bit-or (bit-shift-left val 8) (long (first bs)))
              [val bits] (loop [val val, bits (+ bits 8)]
                           (if (>= bits 5)
                             (do (conj! out (nth B32 (bit-and (unsigned-bit-shift-right val (- bits 5)) 31)))
                                 (recur val (- bits 5)))
                             [val bits]))]
          (recur (rest bs) val bits))
        ;; flush a trailing partial group (left-padded with zero bits)
        (do
          (when (> bits 0)
            (conj! out (nth B32 (bit-and (bit-shift-left val (- 5 bits)) 31))))
          (apply str (persistent! out)))))))

#?(:clj
   (defn sha256-bytes
     "SHA-256 digest of a byte-array (file I/O-free crypto primitive at the :clj edge)."
     ^bytes [^bytes data]
     (.digest (java.security.MessageDigest/getInstance "SHA-256") data)))

#?(:clj
   (defn cidv1-raw
     "CIDv1 / raw (0x55) / sha2-256 — matches `ipfs add --cid-version=1 --raw-leaves`.
     `data` is a byte-array (host UTF-8 bytes of the body)."
     [^bytes data]
     (let [digest (sha256-bytes data)
           mh (byte-array (concat [0x12 0x20] (seq digest)))     ;; sha2-256, 32-byte digest
           cid (byte-array (concat [0x01 0x55] (seq mh)))]       ;; CIDv1, raw codec
       (str "b" (base32 cid)))))

#?(:clj
   (defn- byte->hex [b]
     (let [v (bit-and (long b) 0xff)
           s (Integer/toString v 16)]
       (if (< v 16) (str "0" s) s))))

#?(:clj
   (defn sha256-hex
     "0x-prefixed lowercase hex SHA-256 — the esign documentSha256 defense-in-depth hash."
     [^bytes data]
     (str "0x" (str/join (map byte->hex (sha256-bytes data))))))

(def single-block-limit (* 256 1024)) ;; ipfs default chunk size; above this the raw CID no longer applies

#?(:clj
   (defn utf8-bytes
     "UTF-8 bytes of a string — the bytes a body content-addresses over."
     ^bytes [^String s]
     (.getBytes s "UTF-8")))
