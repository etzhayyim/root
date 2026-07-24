(ns etzhayyim.aozora.repo.repo
  "AT Protocol repo layer on the kotoba Datom log (app-aozora-repo).

  A record's canonical form is its **dag-cbor block**; its key is
  `at://<did>/<collection>/<rkey>`. `put-record` lifts atproto `$link` refs to
  dag-cbor CID links, encodes the value to its block, content-addresses it to a
  spec-exact CIDv1(dag-cbor), and stores BOTH:

    * the block            `[<cid> :block/bytes ..]`   (canonical, content-addressed)
    * an EAVT projection   `[<uri> :record/cid <cid>] ..` (datalog-queryable view)

  on the SAME kotoba blockstore — so the Datom log stays first-class canonical
  state (ADR-2605312345) AND records remain queryable.

  `format-commit` builds the unsigned AT Protocol v3 commit object referencing
  the MST data root. The **MST tree** (orders record keys → record CIDs into that
  root) + **signing** + **CAR** + **com.atproto.sync.\\***  are the next increment
  (README §Next) — this layer is the verified block/CID/commit substrate they sit
  on, and it keeps every block on kotoba (never an `@atproto/repo` side store)."
  (:require [etzhayyim.aozora.repo.cid :as cid]
            [etzhayyim.aozora.repo.dag-cbor :as dc]
            [etzhayyim.aozora.repo.mst :as mst]
            [etzhayyim.aozora.repo.commit :as commit]
            [etzhayyim.aozora.repo.blockstore :as bs]))

(defn lift-links
  "Recursively lift atproto JSON CID-link maps `{\"$link\" \"bafy..\"}` to dag-cbor
  CID links (tag 42), so a record's blob/refs hash spec-correctly."
  [v]
  (cond
    (and (map? v) (= 1 (count v))
         (contains? v "$link") (string? (get v "$link")))
    (dc/cid-link (get v "$link"))
    (map? v)        (into (empty v) (map (fn [[k val]] [k (lift-links val)])) v)
    (sequential? v) (mapv lift-links v)
    :else v))

(defn at-uri [did collection rkey]
  (str "at://" did "/" collection "/" rkey))

(defn put-record
  "Store `value` as a content-addressed dag-cbor block on the kotoba blockstore +
  an EAVT projection. Returns {:uri :cid}."
  [store did collection rkey value]
  (let [uri (at-uri did collection rkey)
        {:keys [cid bytes]} (cid/block (lift-links value))]
    (bs/put-block store cid bytes)
    (bs/assert-datoms store [[uri :record/did did]
                             [uri :record/collection collection]
                             [uri :record/rkey rkey]
                             [uri :record/cid cid]])
    {:uri uri :cid cid}))

(defn record-cid
  "The spec CIDv1(dag-cbor) of a record value, without storing it (e.g. to build
  an MST leaf)."
  [value] (cid/cid-of (lift-links value)))

(defn get-record-cid
  "The stored record CID at `uri` (from the EAVT projection), or nil."
  [store did collection rkey]
  (bs/read-attr store (at-uri did collection rkey) :record/cid))

(defn get-block-bytes
  "Raw dag-cbor block bytes for a stored cid, or nil."
  [store cid] (bs/get-block store cid))

;; ── commit object (unsigned AT Protocol v3) ──────────────────────────────────

(defn format-commit
  "The unsigned AT Protocol v3 commit object for `did` with MST data root
  `data-cid` (a CID-link), revision `rev`, and optional previous commit `prev`.
  Returns {:cid :bytes :unsigned <map>}; signing (`:sig`) is the no-server-key
  member-key leg (README §Next), applied over these bytes."
  [{:keys [did data-cid rev prev]}]
  (let [unsigned (cond-> {"did" did
                          "version" 3
                          "data" (dc/cid-link data-cid)
                          "rev" rev}
                   prev (assoc "prev" (dc/cid-link prev))
                   (nil? prev) (assoc "prev" nil))
        {:keys [cid bytes]} (cid/block unsigned)]
    {:cid cid :bytes bytes :unsigned unsigned}))

;; ── full repo build (the entry point the PDS calls; ADR-2606242330 P-wiring) ──

(defn commit-records!
  "Store each record as a block + EAVT projection, build the MST data root, sign
  + store the commit, advance the repo head — all on the kotoba blockstore.

  This is the single entry point `etzhayyim-atproto-pds-clj` calls to materialise
  a signed AT-Proto repo from its first-party records (`records` =
  [{:collection :rkey :value}]). `sign-fn` is the member/operator key seam
  (no-server-key). Returns {:commit :rev :data-root :signed?}."
  [store {:keys [did rev prev sign-fn]} records]
  (let [kvs (mapv (fn [{:keys [collection rkey value]}]
                    (let [{:keys [cid]} (put-record store did collection rkey value)]
                      {:key (str collection "/" rkey) :val cid}))
                  records)
        data-root (mst/data-root! store kvs)
        c (commit/commit! store {:did did :data-cid data-root :rev rev
                                 :prev prev :sign-fn sign-fn})]
    {:commit (:cid c) :rev rev :data-root data-root :signed? (:signed? c)}))
