(ns etzhayyim.pds.repo-conformance-test
  "Pins the PDS repo layer to the official @atproto/repo golden vectors — guarding against a
  regression that would reintroduce a divergent in-house MST. The PDS delegates its repo
  data-structure layer to the golden-verified app-aozora-repo lib; these
  assertions are the same MST.getPointer() vectors the lib pins, asserted through the PDS's
  PUBLIC repo API (so the delegation, and the {::cid bytes}↔CidLink bridge, stay honest)."
  (:require [clojure.test :refer [deftest is testing run-tests]]
            [etzhayyim.pds.repo :as repo]
            [etzhayyim.aozora.repo.dag-cbor :as dc]
            [etzhayyim.aozora.repo.cid :as acid]
            [etzhayyim.aozora.repo.mst :as amst]
            [etzhayyim.aozora.repo.blockstore :as abs]))

;; the @atproto/repo golden record-CID used in the lib's MST vectors
(def V "bafyreigbtj4x7ip5legnfznufuopl4sg4knzc2cof6duas4b3q2fy6swua")
(def Vbytes (dc/cid-str->binary V))

(defn- b-root [keys]
  (repo/cid-str (first (repo/build-mst (mapv (fn [k] [k Vbytes]) keys)))))

;; same construction as the node harness: i.toString(36) for i in 0..29
(def kn (mapv (fn [i] (str "app.bsky.feed.post/3k" (Integer/toString i 36) "aaaa" i)) (range 30)))

(deftest mst-root-matches-atproto-golden
  (testing "PDS build-mst roots == official @atproto/repo MST.getPointer() golden vectors"
    (is (= "bafyreie5737gdxlw5i64vzichcalba3z2v5n6icifvx5xytvske7mr3hpm" (b-root [])))
    (is (= "bafyreigu2zbenu4lfkd5qfihjb3al7czhhmu6lfo72i7xabmylkn3hv7de"
           (b-root ["app.bsky.feed.post/3jzfcijpj2z2a"])))
    (is (= "bafyreifmacex4vprajkrkafdg6qe2abvr5bbutovf6bc754otvinr2yoiy"
           (b-root ["app.bsky.feed.post/3jzfcijpj2z2a"
                    "app.bsky.feed.like/3jzfcijpj2z2b"
                    "app.bsky.actor.profile/self"])))
    (is (= "bafyreigulcytdvlgo6o2pxsnmaxh2ta2jg4orhrxjc4z46cpjfsrp2xsei" (b-root kn)))))

(deftest dag-cbor-and-cid-delegate-byte-for-byte
  (testing "PDS dag-cbor / CID are the lib's bytes"
    (let [r {"$type" "app.bsky.feed.post" "text" "hello 物差し" "n" 7 "f" true "z" nil}]
      (is (java.util.Arrays/equals ^bytes (repo/dag-cbor r) ^bytes (dc/encode r)))
      (is (= (acid/cid-of r) (repo/cid-str (repo/block-cid r)))))))

(deftest build-mst-equals-lib-data-root
  (testing "PDS build-mst root == lib data-root! over the same kv set"
    (let [keys ["app.bsky.feed.post/a" "app.bsky.feed.like/b" "app.bsky.actor.profile/self"]]
      (is (= (amst/data-root! (abs/->mem-blockstore) (mapv (fn [k] {:key k :val V}) keys))
             (b-root keys))))))

(defn -main [& _]
  (let [{:keys [fail error]} (run-tests 'etzhayyim.pds.repo-conformance-test)]
    (System/exit (if (pos? (+ fail error)) 1 0))))
