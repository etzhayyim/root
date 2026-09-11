(ns etzhayyim.aozora.repo.blockstore
  "Content-addressed block store **backed by the kotoba Datom log**.

  This is THE design invariant of app-aozora-repo (ADR-2606242330 addendum):
  the repo's dag-cbor blocks and commit head are content-addressed **Datoms on
  the canonical kotoba log** — NOT a parallel `@atproto/repo` MemoryBlockstore /
  SQLite. So `kotoba Datom log = first-class canonical state` (ADR-2605312345)
  holds for the repo layer too: blocks materialize from the log, the MST is the
  interop wire over them, IPFS is the block backend tier.

    block        →  [<cid> :block/bytes <base64>]
    repo head    →  [<did> :repo/head  <commit-cid>]

  `MemBlockstore` folds an in-process atom of [e a v] datoms (single-node / dev /
  tests); a kotoba-engine backend mirrors the same datoms over the live engine
  (parity with `etzhayyim.pds.store/->kotoba-store`, wired at P2 cutover)."
  (:import [java.util Base64]))

(defprotocol BlockStore
  (put-block  [_ cid data] "Persist block bytes under `cid`. Returns cid.")
  (get-block  [_ cid]      "Return the block bytes for `cid`, or nil.")
  (has-block? [_ cid]      "True iff `cid` is present.")
  (get-head   [_ did]      "Return the repo head commit cid for `did`, or nil.")
  (set-head!  [_ did cid]  "Set the repo head commit cid for `did`. Returns cid.")
  (assert-datoms [_ ds]    "Append arbitrary [e a v] datoms (e.g. the record EAVT
                            projection) to the SAME canonical log as the blocks.")
  (read-attr  [_ e a]      "Latest value of attribute `a` on entity `e`, or nil.")
  (block-count [_]         "Number of distinct blocks held."))

(defn- b64e [^bytes b] (.encodeToString (Base64/getEncoder) b))
(defn- b64d ^bytes [^String s] (.decode (Base64/getDecoder) s))

(defn- latest-v
  "Latest value of attribute `a` on entity `e` in the append-only log."
  [log e a]
  (reduce (fn [acc [e* a* v]] (if (and (= e* e) (= a* a)) v acc)) nil log))

(defrecord MemBlockstore [log]
  BlockStore
  (put-block  [_ cid data] (swap! log conj [cid :block/bytes (b64e data)]) cid)
  (get-block  [_ cid] (when-let [s (latest-v @log cid :block/bytes)] (b64d s)))
  (has-block? [_ cid] (some? (latest-v @log cid :block/bytes)))
  (get-head   [_ did] (latest-v @log did :repo/head))
  (set-head!  [_ did cid] (swap! log conj [did :repo/head cid]) cid)
  (assert-datoms [_ ds] (swap! log into ds) nil)
  (read-attr  [_ e a] (latest-v @log e a))
  (block-count [_] (->> @log (filter (fn [[_ a _]] (= a :block/bytes)))
                        (map first) distinct count)))

(defn ->mem-blockstore [] (->MemBlockstore (atom [])))

(defn datoms
  "The raw append-only datom log (for inspection / handoff to the kotoba engine)."
  [^MemBlockstore bs] @(:log bs))
