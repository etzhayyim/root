(ns etzhayyim.pds.blob
  "Content-addressed blob store for the PDS — opaque bytes (images, video, …)
  addressed by CIDv1 raw / sha2-256, one file per blob under a directory. A blob
  ref in a record is {$type:blob, ref:{$link:<cid>}, mimeType, size}; uploadBlob
  returns that ref, sync.getBlob serves the bytes, sync.listBlobs enumerates them.

  Kept out of the record datom log (blobs are large + opaque); the directory is
  the durable store, the CID is the integrity check."
  (:require [clojure.java.io :as io]
            [clojure.string :as str]
            [etzhayyim.pds.repo :as repo]))

(defn- blob-file [dir cid] (io/file dir (str cid ".blob")))
(defn- mime-file [dir cid] (io/file dir (str cid ".mime")))

(defn put-blob
  "Store bytes content-addressed. Returns {:cid :size :mime} (idempotent by CID)."
  [dir ^bytes data mime]
  (let [cid (repo/cid-str (repo/raw-cid-of-bytes data))]
    (io/make-parents (blob-file dir cid))
    (when-not (.exists (blob-file dir cid))
      (with-open [o (io/output-stream (blob-file dir cid))] (.write o data))
      (spit (mime-file dir cid) (or mime "application/octet-stream")))
    {:cid cid :size (alength data) :mime (or mime "application/octet-stream")}))

(defn get-blob
  "Return {:bytes :mime} for a blob cid, verifying the CID, or nil if absent/corrupt."
  [dir cid]
  (let [f (blob-file dir cid)]
    (when (.exists f)
      (let [data (with-open [in (io/input-stream f)] (.readAllBytes in))]
        (when (= cid (repo/cid-str (repo/raw-cid-of-bytes data)))   ; integrity check
          {:bytes data
           :mime (if (.exists (mime-file dir cid)) (slurp (mime-file dir cid)) "application/octet-stream")})))))

(defn present? [dir cid] (.exists (blob-file dir cid)))

(defn- gv [m k] (or (get m k) (get m (keyword k))))   ; string- or keyword-keyed

(defn blob-refs
  "All blob-ref CIDs referenced in a record value: `{$type:blob, ref:{$link:cid}}`.
  Handles both string- and keyword-keyed maps (incoming JSON vs stored records)."
  [value]
  (cond
    (map? value)
    (let [link (gv (gv value "ref") "$link")]
      (if (and (= "blob" (gv value "$type")) link)
        [link]
        (mapcat blob-refs (vals value))))
    (sequential? value) (mapcat blob-refs value)
    :else []))

(defn missing-refs
  "Blob-ref CIDs in `value` that are NOT present in the store (validation on write)."
  [dir value]
  (vec (remove #(.exists (blob-file dir %)) (blob-refs value))))

(defn list-blobs
  "All blob cids in the store."
  [dir]
  (let [d (io/file dir)]
    (if (.isDirectory d)
      (->> (.list d)
           (filter #(str/ends-with? % ".blob"))
           (map #(subs % 0 (- (count %) 5)))
           sort vec)
      [])))
