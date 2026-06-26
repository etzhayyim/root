(ns etzhayyim.aozora.repo.car
  "CARv1 export — the wire format for `com.atproto.sync.getRepo` / `getBlocks`.

  CARv1 = varint(len) ‖ dag-cbor header `{roots:[CID], version:1}`, then per block
  varint(len(cidbytes ‖ data)) ‖ cidbytes ‖ data. The block CID is the RAW binary
  CID (version‖codec‖multihash) — no 0x00 multibase prefix (that is only for the
  in-cbor tag-42 link form). Blocks come straight off the kotoba Datom log."
  (:require [etzhayyim.aozora.repo.dag-cbor :as dc])
  (:import [java.io ByteArrayOutputStream]))

(defn- write-varint [^ByteArrayOutputStream o ^long n]
  (loop [n n]
    (if (< n 0x80)
      (.write o (int n))
      (do (.write o (int (bit-or (bit-and n 0x7f) 0x80)))
          (recur (unsigned-bit-shift-right n 7))))))

(defn- frame! [^ByteArrayOutputStream o ^bytes payload]
  (write-varint o (alength payload))
  (.write o payload 0 (alength payload)))

(defn car-bytes
  "CARv1 bytes for `roots` (cid strings) + `blocks` (seq of {:cid :bytes})."
  [roots blocks]
  (let [o (ByteArrayOutputStream.)
        header (dc/encode {"roots" (mapv dc/cid-link roots) "version" 1})]
    (frame! o header)
    (doseq [{:keys [cid ^bytes bytes]} blocks]
      (let [cidbin (dc/cid-str->binary cid)
            buf (ByteArrayOutputStream.)]
        (.write buf cidbin 0 (alength cidbin))
        (.write buf bytes 0 (alength bytes))
        (frame! o (.toByteArray buf))))
    (.toByteArray o)))
