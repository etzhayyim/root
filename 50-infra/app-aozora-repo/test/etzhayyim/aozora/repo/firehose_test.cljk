(ns etzhayyim.aozora.repo.firehose-test
  "subscribeRepos #commit frame + replay log. Frame spec-correctness (header ‖
  body dag-cbor + embedded CARv1) is cross-checked with @ipld/dag-cbor + @ipld/car
  in the PR; here we cover framing + cursor replay."
  (:require [clojure.test :refer [deftest is testing]]
            [etzhayyim.aozora.repo.repo :as repo]
            [etzhayyim.aozora.repo.sync :as sync]
            [etzhayyim.aozora.repo.firehose :as fh]
            [etzhayyim.aozora.repo.blockstore :as bs]))

(def did "did:web:alice.etzhayyim.com")

(defn- evt [store seq]
  (let [res (repo/commit-records!
             store {:did did :rev (str "r" seq) :prev nil :sign-fn (fn [_] (byte-array 64))}
             [{:collection "app.bsky.feed.post" :rkey (str "3a" seq) :value {"text" (str "n" seq)}}])]
    {:seq seq :repo did :commit (:commit res) :rev (str "r" seq) :since nil
     :car (sync/get-repo store did)
     :ops [{:action :create :path (str "app.bsky.feed.post/3a" seq) :cid (:data-root res)}]
     :time "2026-06-24T00:00:00Z"}))

(deftest frame-and-replay
  (let [store (bs/->mem-blockstore)
        f (fh/commit-frame (evt store 1))]
    (testing "commit-frame is non-empty (header ‖ body dag-cbor)"
      (is (pos? (alength ^bytes f))))
    (fh/append! store (evt store 2))
    (fh/append! store (evt store 3))
    (fh/append! store (evt store 4))
    (testing "replay from the start returns every appended frame"
      (is (= 3 (count (fh/replay store nil)))))
    (testing "replay from a cursor returns only later-seq frames"
      (is (= 1 (count (fh/replay store 3))))
      (is (zero? (count (fh/replay store 4)))))
    (testing "frames are persisted as :firehose/* datoms on the kotoba log"
      (is (= 3 (count (filter (fn [[_ a _]] (= a :firehose/frame)) (bs/datoms store))))))))
