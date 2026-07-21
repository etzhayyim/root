(ns etzhayyim.aozora.repo.firehose
  "`com.atproto.sync.subscribeRepos` #commit frame encoder + replayable event log.

  A firehose frame = two concatenated dag-cbor objects: a header
  `{op:1, t:'#commit'}` and a body carrying the commit CID + the CARv1 of the new
  blocks + the per-record ops. `mst-projector` consumes this stream. Frames are
  persisted to the kotoba blockstore as a seq-indexed log (`:firehose/*` datoms)
  so subscribeRepos can replay from a cursor — same canonical Datom log, no
  parallel store. (The WebSocket transport is a thin wrapper over `replay`.)"
  (:require [etzhayyim.aozora.repo.dag-cbor :as dc]
            [etzhayyim.aozora.repo.blockstore :as bs])
  (:import [java.io ByteArrayOutputStream]
           [java.util Base64]))

(defn commit-frame
  "Encode a #commit firehose frame (header ‖ body, both dag-cbor). `ev` =
  {:seq :repo :commit :rev :since :car :ops :time}; `:car` is CARv1 bytes, `:ops`
  = [{:action :create|:update|:delete :path \"coll/rkey\" :cid <cid-or-nil>}]."
  ^bytes [{:keys [seq repo commit rev since car ops time]}]
  (let [header (dc/encode {"op" 1 "t" "#commit"})
        body   (dc/encode {"seq" seq
                           "rebase" false
                           "tooBig" false
                           "repo" repo
                           "commit" (dc/cid-link commit)
                           "rev" rev
                           "since" since
                           "blocks" car
                           "ops" (mapv (fn [{:keys [action path cid]}]
                                         {"action" (name action)
                                          "path" path
                                          "cid" (when cid (dc/cid-link cid))})
                                       ops)
                           "blobs" []
                           "time" time})
        o (ByteArrayOutputStream.)]
    (.write o header 0 (alength header))
    (.write o body 0 (alength body))
    (.toByteArray o)))

(defn- b64e [^bytes b] (.encodeToString (Base64/getEncoder) b))
(defn- b64d ^bytes [^String s] (.decode (Base64/getDecoder) s))

(defn append!
  "Persist a #commit frame to the firehose log on `store`. Returns its seq."
  [store ev]
  (let [e (str "fh:" (:seq ev))]
    (bs/assert-datoms store [[e :firehose/seq (:seq ev)]
                             [e :firehose/frame (b64e (commit-frame ev))]])
    (:seq ev)))

(defn replay
  "Frames with seq > `cursor` (nil = from the start), in seq order, as ^bytes."
  [store cursor]
  (->> (bs/datoms store)
       (filter (fn [[_ a _]] (= a :firehose/frame)))
       (map (fn [[e _ v]] [(Long/parseLong (subs e 3)) (b64d v)]))
       (filter (fn [[s _]] (or (nil? cursor) (> s cursor))))
       (sort-by first)
       (mapv second)))
