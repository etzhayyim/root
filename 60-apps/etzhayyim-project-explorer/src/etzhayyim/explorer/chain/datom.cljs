(ns etzhayyim.explorer.chain.datom
  "REAL kotoba Datom-log reader, in the browser (ADR-2606201610 + ADR-2605312345).

   This is NOT a stub: it requires the canonical portable codec
   `kotoba.datom` (orgs/kotoba-lang/kotodama/src/kotoba/datom.cljc) and uses it to
   VERIFY a content-addressed append-only commit-DAG client-side — recomputing
   every `:tx/cid` from its datoms + the previous CID and checking the chain,
   exactly as the clj `verify-chain` does on the server. A tamper of any earlier
   tx breaks every later CID; the browser detects it with no server in the loop.

   The codec's only host seam is `*sha256-hex*`; we bind it to a synchronous
   SHA-256 (js-sha256) so `tx-cid` stays byte-compatible with the Python/JVM
   writers (CID = \"b\" + sha256-hex over canonical JSON {prev,datoms})."
  (:require [kotoba.datom :as kd]
            [cljs.reader :as edn]
            [clojure.string :as str]
            ["js-sha256" :as jssha]))

;; Bind the host sha-256 seam once, at namespace load. js-sha256's `sha256`
;; returns lowercase hex — exactly what kotoba.datom/tx-cid expects.
(set! kd/*sha256-hex* (fn [^string s] (jssha/sha256 s)))

(defn parse-log
  "Parse a kotoba Datom log (the `tx->edn-line` text format: one tx map per
   line, ';'-comment + blank lines skipped). Returns txs oldest-first with
   datoms normalized to \":…\" strings (same as the clj read-log)."
  [text]
  (->> (str/split-lines (or text ""))
       (map str/trim)
       (remove #(or (str/blank? %) (str/starts-with? % ";")))
       (map edn/read-string)
       (map #(update % :tx/datoms kd/normalize-datoms))
       vec))

(defn verify-chain
  "Recompute every CID from (datoms, prev) using the REAL kotoba.datom/tx-cid.
   → {:ok bool :length n :broken-at i :head <cid>}. Pure cljs; mirrors the
   clj verify-chain (which is :clj-only because it reads files)."
  [txs]
  (loop [i 0 prev ""]
    (if (= i (count txs))
      {:ok true :length (count txs) :broken-at -1 :head prev}
      (let [tx (nth txs i)
            recomputed (kd/tx-cid (:tx/datoms tx) prev)]
        (if (or (not= (:tx/cid tx) recomputed)
                (not= (:tx/prev tx) prev))
          {:ok false :length (count txs) :broken-at i
           :expected recomputed :actual (:tx/cid tx)}
          (recur (inc i) (:tx/cid tx)))))))

(defn all-datoms
  "Flatten every tx's datoms into [tx-seq [op e a v]] rows, newest tx's last."
  [txs]
  (vec (mapcat (fn [tx] (map #(vector (:tx/id tx) %) (:tx/datoms tx))) txs)))

(defn materialize-eavt
  "Fold the :db/add datoms into an entity map {entity {attr value-or-values}}.
   Repeated (e,a) accumulates into a vector (EAVT is multi-valued; we keep all
   assertions rather than last-write-wins so the view is faithful)."
  [txs]
  (reduce
   (fn [acc [_op e a v]]
     (update-in acc [e a]
                (fn [cur] (cond (nil? cur) v
                                (vector? cur) (conj cur v)
                                :else [cur v]))))
   {}
   (map second (all-datoms txs))))

(defn entities
  "Sorted entity ids from a materialized EAVT map."
  [eavt] (sort (keys eavt)))

(defn query
  "A small but REAL Datalog-shaped query over the materialized datoms:
   given an attribute (\":foo/bar\") and optional value, return matching
   [entity value] pairs. This is the cljs cold-path until kotoba-wasm's kqe
   (EAVT/AEVT/AVET/VAET arrangements) is wired for the full grammar."
  [txs {:keys [attr value]}]
  (let [rows (map second (all-datoms txs))]
    (->> rows
         (filter (fn [[_op _e a v]]
                   (and (= a attr)
                        (or (nil? value) (= (str v) value)))))
         (map (fn [[_op e _a v]] [e v]))
         distinct
         vec)))

(defn attributes
  "Distinct attribute names present in the log (for the query picker)."
  [txs]
  (->> (all-datoms txs) (map (fn [[_ d]] (nth d 2))) distinct sort vec))

;; ── EAVT snapshot form ([e a v tx op] flat vector, e.g. vitals.kotoba.edn) ──
;; The organism heartbeat exports its canonical EAVT state as a flat 5-tuple
;; datom vector (ADR-2605312345), distinct from the tx->edn-line commit log
;; above. This is a materialized kotoba Datom snapshot; we query it client-side.
(defn materialize-snapshot
  "Fold a [[e a v tx op] …] EAVT snapshot into {entity {attr value}}, honouring
   :add / :retract op in tx order. Returns the as-of entity map."
  [datoms]
  (reduce
   (fn [acc [e a v _tx op]]
     (case op
       (:add "add" :db/add) (assoc-in acc [e a] v)
       (:retract "retract" :db/retract) (update acc e dissoc a)
       (assoc-in acc [e a] v)))
   {}
   (sort-by #(nth % 3) datoms)))                ; by tx

(defn entities-where
  "Query a materialized snapshot: entities whose attribute `attr` is present
   (optionally = `value`). Returns [[entity attrs-map] …]."
  ([eavt attr] (entities-where eavt attr ::any))
  ([eavt attr value]
   (->> eavt
        (filter (fn [[_ attrs]]
                  (and (contains? attrs attr)
                       (or (= value ::any) (= (get attrs attr) value)))))
        vec)))
