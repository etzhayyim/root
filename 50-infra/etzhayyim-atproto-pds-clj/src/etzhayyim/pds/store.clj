(ns etzhayyim.pds.store
  "Record persistence for the PDS, modelled as a kotoba Datom log.

  A write appends datoms describing the record; the current repo state is the
  materialization of that append-only log. Two backends implement the same
  `PdsStore` protocol:

    * `->mem-store`     — in-process datom log (single node; local/dev + tests).
    * `->durable-store` — the same datom log, write-through to an append-only file
                          on disk and replayed on boot, so records survive a PDS
                          restart with no external dependency (the PDS owns its own
                          on-disk kotoba Datom log).
    * `->kotoba-store`  — the live kotoba engine over HTTP, so the PDS owns no DB —
                          records land on the canonical Datom log (ADR-2605262130).

  Record identity: an at-uri `at://<did>/<collection>/<rkey>`. Each write emits
  datoms [uri :record/did did] [uri :record/collection coll] [uri :record/rkey
  rkey] [uri :record/cid cid] [uri :record/value <json>] [uri :record/createdAt
  ts]. Deletes append a tombstone [uri :record/deleted true]."
  (:require [cheshire.core :as json]
            [clojure.edn :as edn]
            [clojure.java.io :as io]
            [babashka.http-client :as http]
            [etzhayyim.pds.datom :as d]
            [etzhayyim.pds.util :as util]))

(defn at-uri [did collection rkey]
  (str "at://" did "/" collection "/" rkey))

(defprotocol PdsStore
  (put-record   [_ did collection rkey value]
    "Assert a record. Returns {:uri :cid :value}.")
  (get-record   [_ did collection rkey]
    "Return {:uri :cid :value} or nil if absent/tombstoned.")
  (delete-record [_ did collection rkey]
    "Append a tombstone. Returns true.")
  (list-records [_ did collection opts]
    "Return {:records [{:uri :rkey :cid :value}] :cursor next-rkey-or-nil}. opts:
     {:limit :cursor :reverse :rkey-start :rkey-end}.")
  (describe-repo [_ did]
    "Return {:did :collections [coll ..] :count n}."))

;; ── in-process datom-log backend ─────────────────────────────────────────────
;; State: an atom holding the ordered datom log (vector of [e a v]). Reads fold
;; the log into an EAVT db and project current (non-tombstoned, latest) records.

(defn- read-attr [db uri attr]
  (first (get-in db [:eav uri attr])))

(defn- live-uris [db]
  (let [all (keys (:eav db))
        dead? (fn [uri] (read-attr db uri :record/deleted))]
    (->> all (filter #(read-attr db % :record/did)) (remove dead?))))

(defn- materialize [db uri]
  (when (and (read-attr db uri :record/did)
             (not (read-attr db uri :record/deleted)))
    {:uri uri
     :rkey (read-attr db uri :record/rkey)
     :cid (read-attr db uri :record/cid)
     :value (json/parse-string (read-attr db uri :record/value))}))

(defn repo-summary
  "describeRepo projection from an EAVT `db`: collections + total + per-collection counts."
  [db did]
  (let [uris (filter #(= did (read-attr db % :record/did)) (live-uris db))
        by-coll (frequencies (keep #(read-attr db % :record/collection) uris))]
    {:did did :collections (vec (sort (keys by-coll))) :count (count uris)
     :collection-counts by-coll}))

(defn query-records
  "Project listRecords from an EAVT `db`. opts: {:limit :cursor :reverse :rkey-start
  :rkey-end}. Records are ordered by rkey (ascending; `reverse` → descending); the
  cursor is the last rkey returned. Shared by the mem + durable backends."
  [db did collection {:keys [limit cursor reverse rkey-start rkey-end] :or {limit 50}}]
  (let [recs (->> (live-uris db)
                  (filter #(and (= did (read-attr db % :record/did))
                                (= collection (read-attr db % :record/collection))))
                  (keep #(materialize db %))
                  (sort-by :rkey))
        recs (cond->> recs
               rkey-start (filter #(>= (compare (:rkey %) rkey-start) 0))
               rkey-end   (filter #(<= (compare (:rkey %) rkey-end) 0))
               reverse    (#(clojure.core/reverse %)))
        recs (if cursor
               (if reverse
                 (drop-while #(>= (compare (:rkey %) cursor) 0) recs)
                 (drop-while #(<= (compare (:rkey %) cursor) 0) recs))
               recs)
        page (take limit recs)]
    {:records (vec page)
     :cursor (when (= (count page) limit) (:rkey (last page)))}))

(defrecord MemStore [log]
  PdsStore
  (put-record [_ did collection rkey value]
    (let [uri (at-uri did collection rkey)
          cid (util/content-cid value)
          ts (util/now-iso)]
      (swap! log into [[uri :record/did did]
                       [uri :record/collection collection]
                       [uri :record/rkey rkey]
                       [uri :record/cid cid]
                       [uri :record/value (json/generate-string value)]
                       [uri :record/createdAt ts]])
      {:uri uri :cid cid :value value}))
  (get-record [_ did collection rkey]
    (materialize (d/build-db @log) (at-uri did collection rkey)))
  (delete-record [_ did collection rkey]
    (swap! log conj [(at-uri did collection rkey) :record/deleted true])
    true)
  (list-records [_ did collection opts]
    (query-records (d/build-db @log) did collection opts))
  (describe-repo [_ did]
    (repo-summary (d/build-db @log) did)))

(defn ->mem-store [] (->MemStore (atom [])))

;; ── durable on-disk datom-log backend ────────────────────────────────────────
;; The same append-only EAVT log as MemStore, but every appended datom is also
;; written (write-through) to a newline-delimited EDN file, and the file is
;; replayed into the log on boot. Crash-safe to the last completed write, no
;; external service — the PDS carries its own Datom journal on disk.

(defn- append-datoms! [path datoms]
  (locking path
    (io/make-parents path)
    (with-open [w (io/writer path :append true)]
      (doseq [datom datoms]
        (.write w (pr-str datom))
        (.write w "\n")))))

(defn- replay-log [path]
  (let [f (io/file path)]
    (if (.exists f)
      (with-open [r (io/reader f)]
        (->> (line-seq r)
             (remove #(re-matches #"\s*" %))
             (mapv edn/read-string)))
      [])))

(defrecord DurableStore [path log]
  PdsStore
  (put-record [_ did collection rkey value]
    (let [uri (at-uri did collection rkey)
          cid (util/content-cid value)
          ts (util/now-iso)
          datoms [[uri :record/did did]
                  [uri :record/collection collection]
                  [uri :record/rkey rkey]
                  [uri :record/cid cid]
                  [uri :record/value (json/generate-string value)]
                  [uri :record/createdAt ts]]]
      (append-datoms! path datoms)               ; durable first…
      (swap! log into datoms)                     ; …then in-memory index
      {:uri uri :cid cid :value value}))
  (get-record [_ did collection rkey]
    (materialize (d/build-db @log) (at-uri did collection rkey)))
  (delete-record [_ did collection rkey]
    (let [datoms [[(at-uri did collection rkey) :record/deleted true]]]
      (append-datoms! path datoms)
      (swap! log into datoms)
      true))
  (list-records [_ did collection opts]
    (query-records (d/build-db @log) did collection opts))
  (describe-repo [_ did]
    (repo-summary (d/build-db @log) did)))

(defn ->durable-store
  "Datom-log store persisted to `path` (newline-delimited EDN), replayed on boot."
  [path]
  (->DurableStore path (atom (replay-log path))))

;; ── kotoba engine backend (production) ───────────────────────────────────────
;; Persists each record-tx to the live kotoba Datom log over its XRPC/HTTP
;; surface. The PDS holds no DB of its own. (The wire shape mirrors the kotoba
;; graph ingest/query XRPC; verified against the live engine at cutover — until
;; then KOTOBA_URL being unset keeps the PDS on the mem datom log.)

(defn- kpost [base path body]
  (-> (http/post (str base path)
                 {:headers {"content-type" "application/json"}
                  :body (json/generate-string body)
                  :throw false})
      :body
      (json/parse-string true)))

(defrecord KotobaStore [base graph]
  PdsStore
  (put-record [_ did collection rkey value]
    (let [uri (at-uri did collection rkey)
          cid (util/content-cid value)
          ts (util/now-iso)
          datoms [[uri "record/did" did]
                  [uri "record/collection" collection]
                  [uri "record/rkey" rkey]
                  [uri "record/cid" cid]
                  [uri "record/value" (json/generate-string value)]
                  [uri "record/createdAt" ts]]]
      (kpost base "/xrpc/com.etzhayyim.apps.kotoba.kg.ingest_batch"
             {:graph graph :datoms datoms})
      {:uri uri :cid cid :value value}))
  (get-record [_ did collection rkey]
    (let [uri (at-uri did collection rkey)
          r (kpost base "/xrpc/com.etzhayyim.apps.kotoba.kg.get_entity"
                   {:graph graph :entity uri})]
      (when (and (:record/value r) (not (:record/deleted r)))
        {:uri uri :cid (:record/cid r) :value (json/parse-string (:record/value r))})))
  (delete-record [_ did collection rkey]
    (kpost base "/xrpc/com.etzhayyim.apps.kotoba.kg.ingest_batch"
           {:graph graph :datoms [[(at-uri did collection rkey) "record/deleted" true]]})
    true)
  (list-records [_ did collection {:keys [limit cursor reverse rkey-start rkey-end]}]
    (let [r (kpost base "/xrpc/com.etzhayyim.apps.kotoba.kg.list_records"
                   {:graph graph :did did :collection collection
                    :limit limit :cursor cursor :reverse reverse
                    :rkeyStart rkey-start :rkeyEnd rkey-end})]
      {:records (mapv (fn [m] {:uri (:uri m) :cid (:cid m)
                               :value (json/parse-string (:value m))})
                      (:records r))
       :cursor (:cursor r)}))
  (describe-repo [_ did]
    (kpost base "/xrpc/com.etzhayyim.apps.kotoba.kg.describe_repo"
           {:graph graph :did did})))

(defn ->kotoba-store [base graph] (->KotobaStore base graph))
