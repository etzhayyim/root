;; etzhayyim.kotoba.test-pages-store — CARv1 + GitHubPagesBlockStore invariants
;; (ADR-2606242400). Run: bb test:pages-store. Hermetic (no network — the file
;; ranger exercises identical index/slice/verify logic as the HTTP ranger).

(ns etzhayyim.kotoba.test-pages-store
  (:require [clojure.test :refer [deftest is testing run-tests]]
            [clojure.java.io :as io]
            [clojure.set]
            [etzhayyim.kotoba.cid :as cid]
            [etzhayyim.kotoba.car :as car]
            [etzhayyim.kotoba.log :as klog]
            [etzhayyim.kotoba.prolly :as prolly]
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

;; ── prolly-tree (multi-level Merkle DAG) ─────────────────────────────────────

(def ^:private big-log
  (vec (for [i (range 80)] [(str "e" (format "%03d" i)) :a/v i (inc i) :add])))

(deftest prolly-is-multilevel-deterministic-and-walks
  (let [t (prolly/build big-log :bits 2)
        m (into {} (:blocks t))
        get-fn (fn [c] (get m c))
        back (prolly/walk get-fn (:root t))]
    (testing "content-defined chunking yields a MULTI-level DAG (not a flat list)"
      (is (> (:levels t) 1) (str "levels=" (:levels t)))
      (is (> (:nodes t) 1)))
    (testing "history-independent: shuffled input -> identical root CID"
      (is (= (:root t) (:root (prolly/build (shuffle big-log) :bits 2)))))
    (testing "walk reassembles the full datom set (sorted)"
      (is (= (set big-log) (set back)))
      (is (= back (vec (sort-by prolly/key-str big-log))) "in-order"))))

(deftest prolly-seek-is-logarithmic-locality
  (let [t (prolly/build big-log :bits 2)
        m (into {} (:blocks t))
        get-fn (fn [c] (get m c))
        target (nth big-log 53)
        r (prolly/seek-datom get-fn (:root t) target)]
    (is (:found? r) "target found by descending one spine")
    (is (= (prolly/key-of target) (prolly/key-of (:datom r))))
    (testing "a point seek fetches ~tree-depth nodes, NOT the whole tree"
      (is (<= (:fetched r) (:levels t)))
      (is (< (:fetched r) (:nodes t)) (str "fetched " (:fetched r) " of " (:nodes t))))))

(deftest prolly-path-copy-on-change
  (let [t1 (prolly/build big-log :bits 2)
        t2 (prolly/build (conj big-log ["e999" :a/v 999 999 :add]) :bits 2)
        s1 (set (map first (:blocks t1)))
        s2 (set (map first (:blocks t2)))]
    (is (not= (:root t1) (:root t2)) "root changes with content")
    (testing "most leaf/internal CIDs are SHARED (path-copy, not full rewrite)"
      (is (pos? (count (clojure.set/intersection s1 s2)))))))

(deftest prolly-publish-query-roundtrip-file
  (let [dir (str (System/getProperty "java.io.tmpdir") "/etz-pages-prolly")
        graph "big"]
    (io/make-parents (io/file (str dir "/x")))
    (try
      (let [r (ps/publish! dir graph big-log :layout :prolly :bits 2)
            index (ps/index-from-file (str dir "/" graph ".car.idx.edn"))
            ranger (ps/file-ranger (str dir "/" graph ".car"))]
        (is (= :prolly (:layout index)))
        (is (> (:levels r) 1) "published a multi-level tree")
        (testing "fetch-log over the CAR reassembles the full set, CID-verified"
          (is (= (set big-log) (set (ps/fetch-log ranger index)))))
        (testing "seek over the Pages store finds a datom with O(log n) Range fetches"
          (let [s (ps/seek ranger index (nth big-log 17))]
            (is (:found? s))
            (is (< (:fetched s) (:n-blocks r))))))
      (finally
        (doseq [f [(str dir "/" graph ".car") (str dir "/" graph ".car.idx.edn")
                   (str dir "/head.json") (str dir "/.nojekyll")]]
          (io/delete-file f true))))))

(defn -main [& _]
  (let [{:keys [fail error]} (run-tests 'etzhayyim.kotoba.test-pages-store)]
    (System/exit (if (pos? (+ fail error)) 1 0))))
