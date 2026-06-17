(ns tanemaki.methods.cid
  "tanemaki 種蒔き — kotoba IPFS content-address (CIDv1, raw, sha2-256, base32).
  1:1 Clojure port of `methods/cid.py` (ADR-2606122001).

  Pure re-implementation of the repo-canonical content-address used by the WASM loaders
  (CIDv1, raw codec 0x55, multihash sha2-256 0x12 0x20, multibase base32-lower with the 'b'
  prefix). This is the SAME CID `ipfs add --cid-version=1 --raw-leaves` produces for a single
  raw block (< 256 KiB), so a published scorecard body's content-address is verifiable with or
  without the `ipfs` daemon — anyone can re-derive the CID of a tanemaki scorecard and confirm
  the bytes they fetched are the bytes the steward published (G4).

  Single-block only by design: an individual scorecard / proposal fits one raw block.

  Self-contained: own sha-256 (no sibling provides it). Inputs are BYTE SEQUENCES (vectors/seqs
  of 0..255 ints) — the callers feed (utf8-bytes scorecard-text). Portable .cljc; the host
  sha-256 lives behind #?(:clj …). The __main__ demo is intentionally omitted (file/CLI scope)."
  (:require [clojure.string :as str]))

(def ^:private B32 "abcdefghijklmnopqrstuvwxyz234567") ;; RFC4648 base32 lower, no padding ('b')

(defn utf8-bytes
  "String → seq of unsigned bytes (0..255), mirroring Python `s.encode('utf-8')`."
  [^String s]
  #?(:clj (map #(bit-and % 0xff) (.getBytes s "UTF-8"))
     :default (throw (ex-info "bind a utf-8 encoder on this host" {}))))

(defn- base32
  "Port of _base32: 5-bit RFC4648 base32-lower encode of a byte seq (no padding)."
  [data]
  (let [[out bits val]
        (reduce
         (fn [[out bits val] b]
           (let [val  (bit-or (bit-shift-left val 8) (bit-and b 0xff))
                 bits (+ bits 8)]
             (loop [out out, bits bits]
               (if (>= bits 5)
                 (recur (conj out (nth B32 (bit-and (bit-shift-right val (- bits 5)) 31)))
                        (- bits 5))
                 [out bits val]))))
         [[] 0 0]
         data)
        out (if (> bits 0)
              (conj out (nth B32 (bit-and (bit-shift-left val (- 5 bits)) 31)))
              out)]
    (apply str out)))

(defn- sha256-bytes
  "Byte seq → 32-byte sha-256 digest as a seq of unsigned bytes."
  [data]
  #?(:clj (let [md (java.security.MessageDigest/getInstance "SHA-256")]
            (doseq [b data] (.update md (unchecked-byte (bit-and b 0xff))))
            (map #(bit-and % 0xff) (.digest md)))
     :default (throw (ex-info "bind a sha-256 impl on this host" {}))))

(defn cidv1-raw
  "CIDv1 / raw (0x55) / sha2-256 — matches `ipfs add --cid-version=1 --raw-leaves`.
  `data` is a byte seq (e.g. (utf8-bytes text))."
  [data]
  (let [mh  (concat [0x12 0x20] (sha256-bytes data)) ;; sha2-256, 32-byte digest
        cid (concat [0x01 0x55] mh)]                 ;; CIDv1, raw codec
    (str "b" (base32 cid))))

(defn sha256-hex
  "0x-prefixed lowercase hex SHA-256 — the proposal scorecardSha256 defense-in-depth hash.
  `data` is a byte seq."
  [data]
  (str "0x" (str/join (map #(format "%02x" (bit-and % 0xff)) (sha256-bytes data)))))

(def SINGLE-BLOCK-LIMIT (* 256 1024)) ;; ipfs default chunk size
