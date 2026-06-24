(ns etzhayyim.pds.xrpc
  "com.atproto.* XRPC method handlers. Pure functions of (store, params) →
  {:status n :body m}; the HTTP layer (server.clj) handles transport. No vendor
  SDK, no gftd code — the method surface is implemented directly against the
  kotoba Datom-log store."
  (:require [clojure.string :as str]
            [etzhayyim.pds.config :as cfg]
            [etzhayyim.pds.store :as store]
            [etzhayyim.pds.account :as account]
            [etzhayyim.pds.lexicon :as lexicon]
            [etzhayyim.pds.util :as util]))

(defn- ok [body] {:status 200 :body body})
(defn- err [status error message]
  {:status status :body {"error" error "message" message}})

(defn resolve-repo
  "Resolve a `repo` identifier (did or handle) to a did. A handle under a
  configured user-domain resolves to did:web:<handle>; a did passes through; the
  PDS host itself maps to the PDS did."
  [repo]
  (cond
    (nil? repo) nil
    (str/starts-with? repo "did:") repo
    (= repo cfg/host) cfg/pds-did
    (some #(str/ends-with? repo (str "." %)) cfg/user-domains) (str "did:web:" repo)
    (contains? (set cfg/user-domains) repo) (str "did:web:" repo)
    :else repo))

;; ── identity ─────────────────────────────────────────────────────────────────
(defn resolve-handle [{:keys [handle]}]
  (if (str/blank? handle)
    (err 400 "InvalidRequest" "handle is required")
    ;; a registered account's did wins; otherwise fall back to the did:web mapping
    (ok {"did" (or (account/account-did cfg/accounts-file handle) (resolve-repo handle))})))

;; ── server ───────────────────────────────────────────────────────────────────
(defn describe-server [_] (ok (cfg/describe-server)))

(defn create-session [{:keys [identifier]}]
  ;; Minimal: issues a non-cryptographic session bound to the resolved did. Real
  ;; JWT/OAuth issuance is staged (README) — kept deliberately small, not copied.
  (let [did (or (resolve-repo identifier) cfg/pds-did)]
    (ok {"did" did
         "handle" (or identifier cfg/host)
         "accessJwt" (str "etzhayyim-session." (util/content-cid did))
         "refreshJwt" (str "etzhayyim-refresh." (util/content-cid (str did "/r")))})))

;; ── repo ─────────────────────────────────────────────────────────────────────
(declare record-error)

(defn apply-writes
  "com.atproto.repo.applyWrites — a batch of create/update/delete in one call.
  Each write's action is keyed by its `$type` suffix (#create/#update/#delete)."
  [store {:keys [repo writes]}]
  (let [did (resolve-repo repo)
        w-coll #(or (:collection %) (get % "collection"))
        w-val  #(or (:value %) (get % "value"))
        w-del? #(str/ends-with? (str (or (:$type %) (get % "$type"))) "#delete")
        bad-write (some (fn [w] (when-not (w-del? w) (record-error (w-coll w) (w-val w)))) writes)]
    (cond
      (or (str/blank? repo) (nil? did)) (err 400 "InvalidRequest" "repo is required")
      (not (sequential? writes)) (err 400 "InvalidRequest" "writes[] is required")
      bad-write (err 400 "InvalidRequest" bad-write)
      :else
      (ok {"results"
           (vec (for [w writes
                      :let [t (str (or (:$type w) (get w "$type")))
                            collection (or (:collection w) (get w "collection"))
                            rkey (let [k (or (:rkey w) (get w "rkey"))] (if (str/blank? k) (util/tid) k))
                            value (or (:value w) (get w "value"))]]
                  (cond
                    (str/ends-with? t "#delete")
                    (do (store/delete-record store did collection rkey)
                        {"$type" "com.atproto.repo.applyWrites#deleteResult"
                         "uri" (store/at-uri did collection rkey)})
                    :else
                    (let [{:keys [uri cid]} (store/put-record store did collection rkey value)]
                      {"$type" (if (str/ends-with? t "#update")
                                 "com.atproto.repo.applyWrites#updateResult"
                                 "com.atproto.repo.applyWrites#createResult")
                       "uri" uri "cid" cid}))))}))))

(defn record-error
  "Why `record` is not a valid atproto record (must be an object with a $type; and,
  when PDS_VALIDATE_RECORDS is set, must satisfy the known lexicon shape), or nil."
  [collection record]
  (cond
    (nil? record) "record is required"
    (not (map? record)) "record must be an object"
    (str/blank? (str (or (get record "$type") (get record :$type)))) "record must have a $type"
    :else (when cfg/validate-records (lexicon/validate collection record))))

(defn create-record [store {:keys [repo collection record rkey]}]
  (let [did (resolve-repo repo)]
    (cond
      (or (str/blank? repo) (nil? did)) (err 400 "InvalidRequest" "repo is required")
      (str/blank? collection) (err 400 "InvalidRequest" "collection is required")
      (record-error collection record) (err 400 "InvalidRequest" (record-error collection record))
      :else
      (let [rkey (if (str/blank? rkey) (util/tid) rkey)
            {:keys [uri cid]} (store/put-record store did collection rkey record)]
        (ok {"uri" uri "cid" cid})))))

(defn put-record [store {:keys [repo collection rkey record]}]
  (let [did (resolve-repo repo)]
    (cond
      (or (str/blank? repo) (nil? did)) (err 400 "InvalidRequest" "repo is required")
      (str/blank? collection) (err 400 "InvalidRequest" "collection is required")
      (str/blank? rkey) (err 400 "InvalidRequest" "rkey is required")
      (record-error collection record) (err 400 "InvalidRequest" (record-error collection record))
      :else
      (let [{:keys [uri cid]} (store/put-record store did collection rkey record)]
        (ok {"uri" uri "cid" cid})))))

(defn get-record [store {:keys [repo collection rkey]}]
  (let [did (resolve-repo repo)]
    (if-let [r (and did (not (str/blank? collection)) (not (str/blank? rkey))
                    (store/get-record store did collection rkey))]
      (ok {"uri" (:uri r) "cid" (:cid r) "value" (:value r)})
      (err 404 "RecordNotFound" "record not found"))))

(defn delete-record [store {:keys [repo collection rkey]}]
  (let [did (resolve-repo repo)]
    (cond
      (or (str/blank? repo) (nil? did)) (err 400 "InvalidRequest" "repo is required")
      (str/blank? collection) (err 400 "InvalidRequest" "collection is required")
      (str/blank? rkey) (err 400 "InvalidRequest" "rkey is required")
      :else (do (store/delete-record store did collection rkey) (ok {})))))

(defn list-records [store {:keys [repo collection limit cursor reverse rkeyStart rkeyEnd]}]
  (let [did (resolve-repo repo)
        limit (let [n (try (Integer/parseInt (str (or limit "50"))) (catch Exception _ 50))]
                (max 1 (min 100 n)))
        reverse? (contains? #{true "true" "1"} reverse)]
    (if (or (nil? did) (str/blank? collection))
      (err 400 "InvalidRequest" "repo and collection are required")
      (let [{:keys [records cursor]} (store/list-records store did collection
                                                         {:limit limit :cursor cursor :reverse reverse?
                                                          :rkey-start rkeyStart :rkey-end rkeyEnd})]
        (ok (cond-> {"records" (mapv (fn [r] {"uri" (:uri r) "cid" (:cid r) "value" (:value r)}) records)}
              cursor (assoc "cursor" cursor)))))))

(defn describe-repo [store {:keys [repo]}]
  (let [did (resolve-repo repo)]
    (if (nil? did)
      (err 400 "InvalidRequest" "repo is required")
      (let [{:keys [collections count collection-counts]} (store/describe-repo store did)]
        (ok {"did" did
             "handle" repo
             "didDoc" (cfg/did-document)
             "collections" collections
             "handleIsCorrect" true
             "recordCount" count
             "collectionCounts" (or collection-counts {})})))))
