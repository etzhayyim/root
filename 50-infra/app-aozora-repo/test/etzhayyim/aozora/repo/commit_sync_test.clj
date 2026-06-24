(ns etzhayyim.aozora.repo.commit-sync-test
  "Commit signing (no-server-key seam) + CARv1 export + com.atproto.sync.* over
  the kotoba blockstore. End-to-end: records → MST → signed commit → CAR."
  (:require [clojure.test :refer [deftest is testing]]
            [etzhayyim.aozora.repo.repo :as repo]
            [etzhayyim.aozora.repo.mst :as mst]
            [etzhayyim.aozora.repo.commit :as commit]
            [etzhayyim.aozora.repo.sync :as sync]
            [etzhayyim.aozora.repo.blockstore :as bs]))

(def did "did:web:alice.etzhayyim.com")

(defn- build-repo []
  (let [store (bs/->mem-blockstore)
        recs [["app.bsky.feed.post" "3a" {"text" "one"}]
              ["app.bsky.feed.post" "3b" {"text" "two"}]
              ["app.bsky.actor.profile" "self" {"displayName" "alice"}]]
        kvs (mapv (fn [[c r v]]
                    (let [{:keys [cid]} (repo/put-record store did c r v)]
                      {:key (str c "/" r) :val cid})) recs)
        data-root (mst/data-root! store kvs)
        ;; deterministic dummy signer (real one = member Ed25519, no-server-key)
        sign-fn (fn [^bytes _] (byte-array 64))
        c (commit/commit! store {:did did :data-cid data-root :rev "3kaaaa"
                                 :prev nil :sign-fn sign-fn})]
    {:store store :commit c :data-root data-root}))

(deftest commit-signing
  (let [{:keys [store commit]} (build-repo)]
    (testing "commit! advances head + rev on the kotoba log"
      (is (= (:cid commit) (bs/get-head store did)))
      (is (= "3kaaaa" (bs/read-attr store did :repo/rev)))
      (is (true? (:signed? commit))))
    (testing "unsigned commit omits sig; signing is deterministic for a given key"
      (let [u (commit/unsigned-commit {:did did :data-cid "bafyreigbtj4x7ip5legnfznufuopl4sg4knzc2cof6duas4b3q2fy6swua" :rev "x" :prev nil})]
        (is (not (contains? u "sig")))
        (is (= (:cid (commit/sign-commit u (fn [_] (byte-array 64))))
               (:cid (commit/sign-commit u (fn [_] (byte-array 64))))))))))

;; ── CARv1 frame scanner (self-consistency, no external dep) ──────────────────
(defn- read-varint [^bytes b i]
  (loop [i i shift 0 acc 0]
    (let [byte (bit-and (aget b i) 0xff)
          acc (bit-or acc (bit-shift-left (bit-and byte 0x7f) shift))]
      (if (zero? (bit-and byte 0x80)) [acc (inc i)] (recur (inc i) (+ shift 7) acc)))))

(defn- frame-count [^bytes car]
  (loop [i 0 n 0]
    (if (>= i (alength car))
      n
      (let [[len j] (read-varint car i)] (recur (+ j len) (inc n))))))

(deftest car-and-sync
  (let [{:keys [store commit]} (build-repo)
        car (sync/get-repo store did)
        nblocks (bs/block-count store)]
    (testing "getRepo CARv1 frames = 1 header + every block (self-consistent)"
      (is (pos? (alength car)))
      (is (= (inc nblocks) (frame-count car))))
    (testing "getLatestCommit returns head + rev"
      (let [lc (sync/get-latest-commit store did)]
        (is (= (:cid commit) (:cid lc)))
        (is (= "3kaaaa" (:rev lc)))))
    (testing "getBlocks CARv1 for a subset has no header roots but the blocks"
      (let [head (bs/get-head store did)
            c (sync/get-blocks store [head])]
        (is (= 2 (frame-count c)))))))  ;; 1 header + 1 requested block

(deftest commit-records-entrypoint
  (testing "repo/commit-records! is the single PDS entry point (records → repo)"
    (let [store (bs/->mem-blockstore)
          res (repo/commit-records!
               store {:did did :rev "3kbbbb" :prev nil :sign-fn (fn [_] (byte-array 64))}
               [{:collection "app.bsky.feed.post" :rkey "3a" :value {"text" "hi"}}
                {:collection "app.bsky.actor.profile" :rkey "self" :value {"displayName" "a"}}])]
      (is (= (:commit res) (bs/get-head store did)))
      (is (true? (:signed? res)))
      (is (string? (:data-root res)))
      (is (= (:commit res) (:cid (sync/get-latest-commit store did))))
      (is (pos? (alength (sync/get-repo store did)))))))
