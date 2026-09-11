;; etzhayyim.kotoba.car — CARv1 (Content-Addressable aRchive) writer + index.
;;
;; ADR-2606242400. A CAR bundles content-addressed blocks into one file so the
;; whole graph travels as a single static asset (committable to git, servable by
;; GitHub Pages). The companion `.car.idx.edn` maps each CID to the [offset len]
;; of its block DATA inside the CAR, so a reader can HTTP **Range**-fetch ONE
;; block without downloading the bundle — the "query a static site by CID" path
;; (etzhayyim.kotoba.pages-store).
;;
;; CARv1 layout (https://ipld.io/specs/transport/car/carv1/):
;;   <varint headerLen> <dag-cbor header: {roots:[cid…], version:1}>
;;   then, repeated:  <varint sectionLen> <cid-bytes> <block-data>
;;     sectionLen = len(cid-bytes) + len(block-data)
;;
;; We index the DATA region directly (offset past the cid-bytes), so a Range GET
;; over [offset, offset+len) returns exactly the block bytes — recompute its CID
;; to verify. CIDv1 raw/sha2-256 framing is etzhayyim.kotoba.cid's (the
;; ipfs-parity address); the header `roots` carry the binary CID form.
;;
;; clj/bb; pure byte ops (no IO) — the store layer owns files/HTTP.

(ns etzhayyim.kotoba.car
  (:require [etzhayyim.kotoba.cid :as cid]
            [etzhayyim.kotoba.cbor :as cbor])
  (:import (java.io ByteArrayOutputStream)))

;; ── unsigned LEB128 varint (CARv1 length prefixes) ───────────────────────────

(defn write-varint [^ByteArrayOutputStream o n]
  (loop [n (long n)]
    (if (< n 0x80)
      (.write o (int n))
      (do (.write o (int (bit-or (bit-and n 0x7f) 0x80)))
          (recur (unsigned-bit-shift-right n 7))))))

(defn varint-bytes ^bytes [n]
  (let [o (ByteArrayOutputStream.)] (write-varint o n) (.toByteArray o)))

(defn read-varint
  "Decode an unsigned LEB128 varint from `^bytes b` at `i`. -> [value next-index]."
  [^bytes b i]
  (loop [i i shift 0 acc 0]
    (let [byte (bit-and (aget b i) 0xff)
          acc (bit-or acc (bit-shift-left (long (bit-and byte 0x7f)) shift))]
      (if (zero? (bit-and byte 0x80))
        [acc (inc i)]
        (recur (inc i) (+ shift 7) acc)))))

;; ── header ───────────────────────────────────────────────────────────────────

(defn- header-bytes ^bytes [root-cids]
  ;; dag-cbor {"roots" [<cid-bytes…>] "version" 1}. Our cbor encodes byte-arrays
  ;; as CBOR byte strings (major 2) — sufficient for round-tripping roots here.
  (cbor/encode {:roots (mapv cid/cid-str->bytes root-cids) :version 1}))

;; ── pack ─────────────────────────────────────────────────────────────────────

(defn pack
  "Build a CARv1 from `roots` (seq of CID strings) and `blocks`
   (ordered seq of [cid-string ^bytes data]). Returns
   {:car ^bytes :index {cid-string [data-offset data-len]} :roots roots}.
   The index points at the DATA region so a Range GET returns just the block."
  [roots blocks]
  (let [o (ByteArrayOutputStream.)
        hdr (header-bytes roots)
        _ (write-varint o (alength hdr))
        _ (.write o hdr)
        index (reduce
               (fn [idx [cstr ^bytes data]]
                 (let [cb (cid/cid-str->bytes cstr)
                       section-len (+ (alength cb) (alength data))]
                   (write-varint o section-len)
                   (.write o cb)
                   ;; record the DATA offset = current size (after writing cid bytes)
                   (let [off (.size o)]
                     (.write o data)
                     (assoc idx cstr [off (alength data)]))))
               {} blocks)]
    {:car (.toByteArray o) :index index :roots (vec roots)}))

;; ── read ─────────────────────────────────────────────────────────────────────

(defn read-roots
  "Parse the CAR header and return its root CID strings."
  [^bytes car]
  (let [[hlen i] (read-varint car 0)
        hdr (cbor/decode (java.util.Arrays/copyOfRange car i (+ i hlen)))]
    (mapv (fn [cb] (cid/cid-bytes->str cb)) (:roots hdr))))

(defn slice
  "Extract `len` bytes at `offset` from `^bytes car` (the Range-fetch analogue)."
  ^bytes [^bytes car offset len]
  (java.util.Arrays/copyOfRange car offset (+ offset len)))

(defn verify-block
  "Recompute the CIDv1 of `data` and assert it equals `cid-str`. Returns data."
  ^bytes [cid-str ^bytes data]
  (let [actual (cid/cid data)]
    (when-not (= actual cid-str)
      (throw (ex-info "CAR block CID mismatch (tamper/corruption)"
                      {:expected cid-str :actual actual})))
    data))
