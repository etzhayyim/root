;; etzhayyim.kotoba.test-pages-store — CARv1 + GitHubPagesBlockStore invariants
;; (ADR-2606242400). Run: bb test:pages-store. Hermetic (no network — the file
;; ranger exercises identical index/slice/verify logic as the HTTP ranger).

(ns etzhayyim.kotoba.test-pages-store
  (:require [clojure.test :refer [deftest is testing run-tests]]
            [clojure.java.io :as io]
            [etzhayyim.kotoba.cid :as cid]
            [etzhayyim.kotoba.car :as car]
            [etzhayyim.kotoba.log :as klog]
            [etzhayyim.kotoba.pages-store :as ps]))

(deftest varint-roundtrip
  (doseq [n [0 1 127 128 300 16384 1000000 (long 4294967296)]]
    (is (= [n (count (car/varint-bytes n))] (car/read-varint (car/varint-bytes n) 0))
        (str "varint " n))))

(deftest cid-bytes-roundtrip-and-framing
  (let [c (cid/cid "hello world")
        frame (vec (cid/cid-str->bytes c))]
    (is (= c (cid/cid-bytes->str (cid/cid-str->bytes c))) "str->bytes->str round-trips")
    (is (= 36 (count frame)) "4 header + 32 sha2-256")
    (is (= [1 0x55 0x12 0x20] (mapv #(bit-and % 0xff) (take 4 frame)))
        "version=1 codec=raw mh=sha2-256 len=32")))

(def ^:private logv
  [["rad:abc" :rad/type :identity 1 :add]
   ["rad:abc" :rad/name "cargo" 1 :add]
   ["rad:abc" :rad/age-recipient "age1xyz" 2 :add]
   ["rad:abc" :rad/evolution "evolve/cargo/x|wire-secret" 3 :add]])

(deftest pack-roots-and-index-slices
  (let [{:keys [root blocks]} (ps/blocks-of-log "cargo" logv)
        {:keys [car index]} (car/pack [root] blocks)]
    (testing "CARv1 header carries the root CID"
      (is (= [root] (car/read-roots car))))
    (testing "every indexed data slice recomputes to its own CID"
      (doseq [[cstr [off len]] index]
        (is (= cstr (cid/cid (car/slice car off len))) (str "block " cstr))))
    (testing "tamper detection: a flipped byte fails verify-block"
      (let [[cstr [off len]] (first index)
            data (car/slice car off len)
            _ (aset-byte data 0 (unchecked-byte (inc (aget data 0))))]
        (is (thrown? Exception (car/verify-block cstr data)))))))

(deftest publish-and-query-roundtrip-file
  (let [dir (str (System/getProperty "java.io.tmpdir") "/etz-pages-test")
        graph "cargo"]
    (io/make-parents (io/file (str dir "/x")))
    (try
      (let [r (ps/publish! dir graph logv)
            index (ps/index-from-file (str dir "/" graph ".car.idx.edn"))
            ranger (ps/file-ranger (str dir "/" graph ".car"))
            back (ps/fetch-log ranger index)]
        (testing "published artifacts exist"
          (is (.exists (io/file (:car r))))
          (is (.exists (io/file (:idx r))))
          (is (.exists (io/file (:head-json r))))
          (is (.exists (io/file (str dir "/.nojekyll")))))
        (testing "root resolves + the log reassembles datom-for-datom"
          (is (= (:root index) (:root r)))
          (is (= logv back) "reconstructed log == original")
          (is (= (klog/head-cid logv) (klog/head-cid back) (:head r))
              "head CID stable across publish->fetch"))
        (testing "get-block CID-verifies; unknown CID is refused"
          (is (thrown? Exception (ps/get-block ranger index "bafkreiunknown")))))
      (finally
        (doseq [f [(str dir "/" graph ".car") (str dir "/" graph ".car.idx.edn")
                   (str dir "/head.json") (str dir "/.nojekyll")]]
          (io/delete-file f true))))))

(deftest manifest-links-all-datoms
  (let [{:keys [root blocks]} (ps/blocks-of-log "cargo" logv)
        man (clojure.edn/read-string (String. (second (first blocks)) "UTF-8"))]
    (is (true? (:kotoba/car-root man)))
    (is (= (count logv) (:count man)))
    (is (= (count logv) (count (:blocks man))) "manifest links every datom block")
    (is (= root (cid/cid (second (first blocks)))) "root == manifest block CID")))

(defn -main [& _]
  (let [{:keys [fail error]} (run-tests 'etzhayyim.kotoba.test-pages-store)]
    (System/exit (if (pos? (+ fail error)) 1 0))))
