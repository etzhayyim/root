(ns etzhayyim.pds.blob-test
  "PDS blob-store invariants: content-addressed put/get (CID = raw-cid of the bytes),
  the integrity check on read (a corrupted blob fails to resolve), and the blob-ref
  validation that gates a write — a record referencing a blob not yet uploaded is
  rejected via missing-refs (handles both string- and keyword-keyed records)."
  (:require [clojure.test :refer [deftest is testing run-tests]]
            [clojure.java.io :as io]
            [etzhayyim.pds.blob :as blob]
            [etzhayyim.pds.repo :as repo]))

(defn- tmp-dir [] (str (System/getProperty "java.io.tmpdir") "/pds-blob-" (System/nanoTime)))
(defn- rm-rf [dir]
  (let [d (io/file dir)]
    (when (.exists d) (doseq [f (.listFiles d)] (.delete f)) (.delete d))))
(defn- bytes->vec [^bytes b] (vec b))

(deftest put-get-round-trips-and-is-content-addressed
  (let [dir (tmp-dir)]
    (try
      (let [data (.getBytes "hello blob" "UTF-8")
            {:keys [cid size mime]} (blob/put-blob dir data "image/png")]
        (testing "the CID is the raw content-id of the bytes (content-addressed)"
          (is (= cid (repo/cid-str (repo/raw-cid-of-bytes data))))
          (is (= (alength data) size))
          (is (= "image/png" mime)))
        (testing "get-blob returns the exact bytes + mime back"
          (let [got (blob/get-blob dir cid)]
            (is (= (bytes->vec data) (bytes->vec (:bytes got))))
            (is (= "image/png" (:mime got)))))
        (testing "present? + list-blobs see the stored blob"
          (is (true? (blob/present? dir cid)))
          (is (= [cid] (blob/list-blobs dir))))
        (testing "put-blob is idempotent by CID (same bytes → same cid, no error)"
          (is (= cid (:cid (blob/put-blob dir data "image/png"))))
          (is (= [cid] (blob/list-blobs dir)))))
      (finally (rm-rf dir)))))

(deftest get-blob-absent-or-corrupt-returns-nil
  (let [dir (tmp-dir)]
    (try
      (testing "an unknown cid resolves to nil"
        (is (nil? (blob/get-blob dir "bafkrei-nope"))))
      (testing "a corrupted blob (bytes no longer hash to the CID) fails the integrity check"
        (let [{:keys [cid]} (blob/put-blob dir (.getBytes "original" "UTF-8") nil)]
          (is (some? (blob/get-blob dir cid)))
          ;; overwrite the on-disk blob with different bytes under the same cid name
          (with-open [o (io/output-stream (io/file dir (str cid ".blob")))]
            (.write o (.getBytes "TAMPERED" "UTF-8")))
          (is (nil? (blob/get-blob dir cid)) "cid mismatch → nil, never serves corrupted bytes")))
      (finally (rm-rf dir)))))

(deftest blob-refs-and-missing-refs-gate-the-write
  (let [dir (tmp-dir)]
    (try
      (let [{:keys [cid]} (blob/put-blob dir (.getBytes "the avatar" "UTF-8") "image/jpeg")
            absent "bafkrei-absent-blob"
            ;; a stored record (string keys) embedding a blob ref + an absent one nested in a list
            rec {"$type" "app.bsky.actor.profile"
                 "avatar" {"$type" "blob" "ref" {"$link" cid} "mimeType" "image/jpeg" "size" 9}
                 "gallery" [{"$type" "blob" "ref" {"$link" absent} "mimeType" "image/png" "size" 3}]}]
        (testing "blob-refs extracts every blob CID, however nested (string-keyed)"
          (is (= #{cid absent} (set (blob/blob-refs rec)))))
        (testing "blob-refs also handles keyword-keyed records (incoming JSON path)"
          (is (= [cid] (blob/blob-refs {:$type "blob" :ref {:$link cid}}))))
        (testing "a record with no blobs yields no refs"
          (is (empty? (blob/blob-refs {"text" "no blobs here" "n" 1}))))
        (testing "missing-refs flags ONLY the not-yet-uploaded blob (write-gate)"
          (is (= [absent] (blob/missing-refs dir rec))))
        (testing "once every referenced blob is present, missing-refs is empty"
          (blob/put-blob dir (.getBytes "now uploaded" "UTF-8") nil)  ; a different blob; absent still missing
          (is (= [absent] (blob/missing-refs dir rec)))
          (is (empty? (blob/missing-refs dir {"a" {"$type" "blob" "ref" {"$link" cid}}})))))
      (finally (rm-rf dir)))))

(defn -main [& _]
  (let [{:keys [fail error]} (run-tests 'etzhayyim.pds.blob-test)]
    (System/exit (if (pos? (+ fail error)) 1 0))))
