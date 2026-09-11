(ns etzhayyim.aozora.repo.mst-test
  "MST conformance: root CIDs are byte-identical to the official @atproto/repo
  `MST.create(storage).add(key, cid).getPointer()` (go/ts gold). Vectors were
  produced by a node harness against @atproto/repo + multiformats."
  (:require [clojure.test :refer [deftest is testing]]
            [etzhayyim.aozora.repo.mst :as mst]
            [etzhayyim.aozora.repo.blockstore :as bs]))

(def V "bafyreigbtj4x7ip5legnfznufuopl4sg4knzc2cof6duas4b3q2fy6swua")

(defn root [keys]
  (mst/data-root! (bs/->mem-blockstore) (mapv (fn [k] {:key k :val V}) keys)))

;; same construction as the node harness: i.toString(36) for i in 0..29
(def kn (mapv (fn [i] (str "app.bsky.feed.post/3k" (Integer/toString i 36) "aaaa" i)) (range 30)))

(deftest mst-root-matches-atproto-repo
  (testing "empty / 1 / 3 / 30-entry roots == @atproto/repo MST.getPointer()"
    (is (= "bafyreie5737gdxlw5i64vzichcalba3z2v5n6icifvx5xytvske7mr3hpm" (root [])))
    (is (= "bafyreigu2zbenu4lfkd5qfihjb3al7czhhmu6lfo72i7xabmylkn3hv7de"
           (root ["app.bsky.feed.post/3jzfcijpj2z2a"])))
    (is (= "bafyreifmacex4vprajkrkafdg6qe2abvr5bbutovf6bc754otvinr2yoiy"
           (root ["app.bsky.feed.post/3jzfcijpj2z2a"
                  "app.bsky.feed.like/3jzfcijpj2z2b"
                  "app.bsky.actor.profile/self"])))
    (is (= "bafyreigulcytdvlgo6o2pxsnmaxh2ta2jg4orhrxjc4z46cpjfsrp2xsei" (root kn)))))

(deftest mst-order-independent
  (testing "root is determined by the key SET, not insert order"
    (is (= (root kn) (root (reverse kn))))
    (is (= (root kn) (root (shuffle kn))))))

(deftest mst-blocks-on-kotoba
  (testing "every MST node is a content-addressed block Datom on the kotoba log"
    (let [store (bs/->mem-blockstore)]
      (mst/data-root! store (mapv (fn [k] {:key k :val V}) kn))
      (is (pos? (bs/block-count store)))
      (is (seq (filter (fn [[_ a _]] (= a :block/bytes)) (bs/datoms store)))))))

(deftest leading-zeros-matches
  (testing "leadingZerosOnHash matches the node harness samples"
    (is (= 0 (mst/leading-zeros "app.bsky.feed.post/3jzfcijpj2z2a")))
    (is (= 0 (mst/leading-zeros "abc")))))
