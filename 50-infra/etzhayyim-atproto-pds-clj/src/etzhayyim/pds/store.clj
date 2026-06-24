(ns etzhayyim.pds.store
  "Record persistence for the PDS, modelled as a kotoba Datom log.

  A write appends datoms describing the record; the current repo state is the
  materialization of that append-only log. Two backends implement the same
  `PdsStore` protocol:

    * `->mem-store`    — in-process datom log (single node; local/dev + tests).
    * `->kotoba-store` — the live kotoba engine over HTTP (production), so the
                         PDS owns no separate DB — records land on the canonical
                         content-addressed Datom log (ADR-2605262130).

  Record identity: an at-uri `at://<did>/<collection>/<rkey>`. Each write emits
  datoms [uri :record/did did] [uri :record/collection coll] [uri :record/rkey
  rkey] [uri :record/cid cid] [uri :record/value <json>] [uri :record/createdAt
  ts]. Deletes append a tombstone [uri :record/deleted true]."
  (:require [cheshire.core :as json]
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
  (list-records [_ did collection limit cursor]
    "Return {:records [{:uri :cid :value}] :cursor next-rkey-or-nil}, rkey-desc.")
  (describe-repo [_ did]
    "Return {:did :collections [coll ..] :count n}.")
  ;; ── account lifecycle (ADR-2606242330 P1) ──────────────────────────────────
  (create-account [_ did handle email]
    "Register an account (handle->did). Returns {:did :handle :createdAt} or
     {:error ...} if the did/handle is already taken.")
  (get-account [_ identifier]
    "Resolve an account by did OR handle. Returns {:did :handle :createdAt} or nil.")
  (put-blob [_ did mime ^bytes data]
    "Store a blob for `did`. Returns {:cid :mimeType :size}.")
  (get-blob [_ cid]
    "Return {:bytes :mimeType :size} for a stored blob, or nil."))

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
     :cid (read-attr db uri :record/cid)
     :value (json/parse-string (read-attr db uri :record/value))}))

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
  (list-records [_ did collection limit cursor]
    (let [db (d/build-db @log)
          recs (->> (live-uris db)
                    (filter #(and (= did (read-attr db % :record/did))
                                  (= collection (read-attr db % :record/collection))))
                    (keep #(materialize db %))
                    (sort-by :uri)
                    reverse)
          recs (if cursor (drop-while #(>= (compare (:uri %) cursor) 0) recs) recs)
          page (take limit recs)]
      {:records (vec page)
       :cursor (when (= (count page) limit) (:uri (last page)))}))
  (describe-repo [_ did]
    (let [db (d/build-db @log)
          uris (filter #(= did (read-attr db % :record/did)) (live-uris db))
          colls (->> uris (keep #(read-attr db % :record/collection)) distinct sort vec)]
      {:did did :collections colls :count (count uris)}))
  (create-account [_ did handle email]
    (let [db (d/build-db @log)
          taken (first (get-in db [:ave :account/handle handle]))]
      (cond
        (read-attr db did :account/createdAt) {:error "did already registered"}
        (and taken (not= taken did))           {:error "handle already taken"}
        :else
        (let [ts (util/now-iso)]
          (swap! log into (cond-> [[did :account/handle handle]
                                   [did :account/createdAt ts]
                                   [did :account/active true]]
                            email (conj [did :account/email email])))
          {:did did :handle handle :createdAt ts}))))
  (get-account [_ identifier]
    (let [db (d/build-db @log)
          did (if (read-attr db identifier :account/createdAt)
                identifier
                (first (get-in db [:ave :account/handle identifier])))]
      (when (and did (read-attr db did :account/createdAt))
        {:did did
         :handle (read-attr db did :account/handle)
         :createdAt (read-attr db did :account/createdAt)})))
  (put-blob [_ did mime data]
    (let [cid (util/blob-cid data)
          mime (or mime "application/octet-stream")
          size (alength ^bytes data)]
      (swap! log into [[cid :blob/did did]
                       [cid :blob/mimeType mime]
                       [cid :blob/size size]
                       [cid :blob/data (util/b64-encode data)]
                       [cid :blob/createdAt (util/now-iso)]])
      {:cid cid :mimeType mime :size size}))
  (get-blob [_ cid]
    (let [db (d/build-db @log)]
      (when-let [b64 (read-attr db cid :blob/data)]
        {:bytes (util/b64-decode b64)
         :mimeType (read-attr db cid :blob/mimeType)
         :size (read-attr db cid :blob/size)}))))

(defn ->mem-store [] (->MemStore (atom [])))

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
  (list-records [_ did collection limit cursor]
    (let [r (kpost base "/xrpc/com.etzhayyim.apps.kotoba.kg.list_records"
                   {:graph graph :did did :collection collection
                    :limit limit :cursor cursor})]
      {:records (mapv (fn [m] {:uri (:uri m) :cid (:cid m)
                               :value (json/parse-string (:value m))})
                      (:records r))
       :cursor (:cursor r)}))
  (describe-repo [_ did]
    (kpost base "/xrpc/com.etzhayyim.apps.kotoba.kg.describe_repo"
           {:graph graph :did did}))
  (create-account [_ did handle email]
    (let [ts (util/now-iso)]
      (kpost base "/xrpc/com.etzhayyim.apps.kotoba.kg.ingest_batch"
             {:graph graph :datoms (cond-> [[did "account/handle" handle]
                                            [did "account/createdAt" ts]
                                            [did "account/active" true]]
                                     email (conj [did "account/email" email]))})
      {:did did :handle handle :createdAt ts}))
  (get-account [_ identifier]
    ;; did lookup only at this phase; handle->did resolution needs a kotoba
    ;; query endpoint (verified at cutover, README staged item 5).
    (let [r (kpost base "/xrpc/com.etzhayyim.apps.kotoba.kg.get_entity"
                   {:graph graph :entity identifier})]
      (when (:account/createdAt r)
        {:did identifier :handle (:account/handle r) :createdAt (:account/createdAt r)})))
  (put-blob [_ did mime data]
    (let [cid (util/blob-cid data)
          mime (or mime "application/octet-stream")
          size (alength ^bytes data)]
      (kpost base "/xrpc/com.etzhayyim.apps.kotoba.kg.ingest_batch"
             {:graph graph :datoms [[cid "blob/did" did]
                                    [cid "blob/mimeType" mime]
                                    [cid "blob/size" size]
                                    [cid "blob/data" (util/b64-encode data)]
                                    [cid "blob/createdAt" (util/now-iso)]]})
      {:cid cid :mimeType mime :size size}))
  (get-blob [_ cid]
    (let [r (kpost base "/xrpc/com.etzhayyim.apps.kotoba.kg.get_entity"
                   {:graph graph :entity cid})]
      (when (:blob/data r)
        {:bytes (util/b64-decode (:blob/data r))
         :mimeType (:blob/mimeType r)
         :size (:blob/size r)}))))

(defn ->kotoba-store [base graph] (->KotobaStore base graph))
