(ns hirameki.methods.cid
  "hirameki 閃き — kotoba IPFS content-address (CIDv1, raw 0x55, sha2-256, base32 'b').

  clj port of the repo-canonical content-address (20-actors/rasen/methods/cid.py,
  ADR-2605231525 / 2606014500): the SAME CID `ipfs add --cid-version=1 --raw-leaves`
  produces for a single raw block (< 256 KiB), so a kotoba/DataLad artifact's address is
  verifiable with or without the `ipfs` daemon. Single-block by design — the R0 corpus
  snapshot is a BOUNDED slice (G5/G9); a > 256 KiB artifact chunks into a UnixFS dag-pb
  tree and needs the ipfs builder (out of scope for the bounded R0 snapshot).")

(def ^:private b32 "abcdefghijklmnopqrstuvwxyz234567") ;; RFC4648 base32 lower, no padding (multibase 'b')
(def single-block-limit (* 256 1024))

#?(:clj
   (defn- base32 [^bytes data]
     ;; Eager emit + mask so the bit buffer never exceeds ~13 bits (no JVM long overflow).
     (let [n (alength data) sb (StringBuilder.)]
       (loop [i 0 val 0 bits 0]
         (cond
           (>= bits 5)
           (let [shift (- bits 5)]
             (.append sb (.charAt b32 (bit-and (unsigned-bit-shift-right val shift) 31)))
             (recur i (bit-and val (dec (bit-shift-left 1 shift))) shift))
           (< i n)
           (recur (inc i)
                  (bit-or (bit-shift-left val 8) (long (bit-and (aget data i) 0xff)))
                  (+ bits 8))
           (pos? bits)
           (do (.append sb (.charAt b32 (bit-and (bit-shift-left val (- 5 bits)) 31)))
               (str sb))
           :else (str sb))))))

(defn cidv1-raw
  "CIDv1 / raw (0x55) / sha2-256 — matches `ipfs add --cid-version=1 --raw-leaves`.
  Input is a UTF-8 string (the artifact bytes)."
  [^String s]
  #?(:clj
     (let [digest (.digest (java.security.MessageDigest/getInstance "SHA-256")
                           (.getBytes s "UTF-8"))
           ;; cid = 0x01(v1) 0x55(raw) ++ multihash(0x12 sha2-256, 0x20 len, digest)
           cid-bytes (byte-array (concat [(unchecked-byte 0x01) (unchecked-byte 0x55)
                                          (unchecked-byte 0x12) (unchecked-byte 0x20)]
                                         (seq digest)))]
       (str "b" (base32 cid-bytes)))
     :cljs (throw (ex-info "cidv1-raw is :clj-only" {}))))
