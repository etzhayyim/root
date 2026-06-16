(ns jinushi.methods.cid
  "jinushi 地主 — content-addressing (R1): CIDv1 (raw codec / sha2-256) for acquisition snapshots.

  A snapshot's CIDv1 is its self-certifying identity on the kotoba/IPFS substrate
  (ADR-2605241500 + ADR-2605262130): the same bytes always hash to the same CID, so a snapshot
  recorded in `ingest-provenance.json` is tamper-evident and fetch-verifiable from any IPFS
  gateway by content.

  Scope (honest): this is the **raw single-block** CIDv1 — `multibase(base32, 0x01 0x55 0x12 0x20
  <sha2-256>)` — the content hash of the file bytes. It is NOT the dag-pb/UnixFS CID that
  `ipfs add` (default, chunked) produces for large files; UnixFS parity is a later leg. A
  raw-codec CIDv1/sha2-256 always renders with the `bafkrei…` prefix."
  (:require [clojure.string :as str]
            #?(:clj [clojure.java.io :as io])))

(def ^:private b32 "abcdefghijklmnopqrstuvwxyz234567") ;; RFC4648 base32 lower, multibase 'b'

(defn sha256-bytes [^bytes data]
  #?(:clj (.digest (java.security.MessageDigest/getInstance "SHA-256") data)
     :cljs (throw (ex-info "cid: :clj only" {}))))

(defn base32-nopad
  "RFC4648 base32 (lower, no padding) of a byte array — multibase base32 body."
  [^bytes data]
  (let [bits (mapcat (fn [b] (let [u (bit-and (long b) 0xff)]
                               (map #(bit-and (unsigned-bit-shift-right u %) 1) [7 6 5 4 3 2 1 0])))
                     data)]
    (apply str (map (fn [g] (let [g (concat g (repeat (- 5 (count g)) 0))
                                  v (reduce (fn [a x] (+ (* 2 a) x)) 0 g)]
                              (.charAt b32 (int v))))
                    (partition-all 5 bits)))))

(defn cidv1-raw
  "CIDv1 (raw 0x55 / sha2-256) string for content bytes → \"bafkrei…\"."
  [^bytes content]
  (let [digest (sha256-bytes content)
        prefix (byte-array [0x01 0x55 0x12 0x20])          ;; cidv1 · raw · sha2-256 · len 32
        cid-bytes (byte-array (concat (seq prefix) (seq digest)))]
    (str "b" (base32-nopad cid-bytes))))

(defn string->cidv1 [^String s]
  #?(:clj (cidv1-raw (.getBytes s "UTF-8")) :cljs (throw (ex-info "cid: :clj only" {}))))

#?(:clj
   (defn file->cidv1 [f] (cidv1-raw (java.nio.file.Files/readAllBytes (.toPath (io/file f))))))

#?(:clj
   (defn -main [& argv]
     (let [here (or (some-> (when (and *file* (not= *file* "NO_SOURCE_PATH")) (io/file *file*))
                            .getParentFile .getParentFile)
                    (io/file "20-actors/jinushi"))
           root (or (some-> here .getParentFile .getParentFile) (io/file "."))
           dir (io/file root "80-data" "jinushi-land")
           files (if (seq argv) (map io/file argv)
                     (filter #(str/ends-with? (.getName %) ".kotoba.edn") (.listFiles dir)))]
       (doseq [f (sort-by #(.getName %) files)]
         (println (file->cidv1 f) " " (.getName f)))
       0)))
