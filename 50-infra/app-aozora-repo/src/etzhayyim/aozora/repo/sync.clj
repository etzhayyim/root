(ns etzhayyim.aozora.repo.sync
  "`com.atproto.sync.*` read methods over the kotoba blockstore — the federation
  egress that feeds `mst-projector` + any AT client.

    getLatestCommit  → {:cid <head> :rev <rev>}
    getBlocks        → CARv1 of the requested cids
    getRepo          → CARv1 of the whole repo (root = head commit)

  All blocks come straight off the canonical kotoba Datom log; no parallel store."
  (:require [etzhayyim.aozora.repo.car :as car]
            [etzhayyim.aozora.repo.blockstore :as bs]))

(defn- block-cids [store]
  (->> (bs/datoms store)
       (filter (fn [[_ a _]] (= a :block/bytes)))
       (map first) distinct))

(defn- blocks-for [store cids]
  (keep (fn [c] (when-let [b (bs/get-block store c)] {:cid c :bytes b})) cids))

(defn get-latest-commit
  "Head commit cid + rev for `did`, or nil. `rev` is read from the `:repo/rev`
  datom set by `commit/commit!` (no dag-cbor decoder needed on the read path)."
  [store did]
  (when-let [head (bs/get-head store did)]
    {:cid head :rev (bs/read-attr store did :repo/rev)}))

(defn get-blocks
  "CARv1 (no roots) of the requested `cids` that are present."
  [store cids]
  (car/car-bytes [] (blocks-for store cids)))

(defn get-repo
  "CARv1 of the entire repo for `did` (root = head commit, all blocks)."
  [store did]
  (let [head (bs/get-head store did)]
    (car/car-bytes (if head [head] []) (blocks-for store (block-cids store)))))
