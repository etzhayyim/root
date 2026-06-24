(ns etzhayyim.pds.server
  "HTTP transport for the independent etzhayyim atproto PDS.

  babashka + http-kit (both built in) — no external server dependency. Routes
  /.well-known/did.json and /xrpc/com.atproto.* to the handlers in xrpc.clj over
  the kotoba Datom-log store. Entry point: `-main`."
  (:require [clojure.string :as str]
            [cheshire.core :as json]
            [org.httpkit.server :as http]
            [etzhayyim.pds.config :as cfg]
            [etzhayyim.pds.store :as store]
            [etzhayyim.pds.repo :as repo]
            [etzhayyim.pds.blob :as blob]
            [etzhayyim.pds.xrpc :as xrpc]))

(defn- json-response [{:keys [status body]}]
  {:status status
   :headers {"content-type" "application/json; charset=utf-8"
             "access-control-allow-origin" "*"}
   :body (json/generate-string body)})

(defn- car-response [^bytes car]
  {:status 200
   :headers {"content-type" "application/vnd.ipld.car"
             "access-control-allow-origin" "*"}
   :body (java.io.ByteArrayInputStream. car)})

(defn- bytes-response [^bytes data mime]
  {:status 200
   :headers {"content-type" (or mime "application/octet-stream")
             "access-control-allow-origin" "*"}
   :body (java.io.ByteArrayInputStream. data)})

(defn- read-bytes ^bytes [req]
  (when-let [b (:body req)]
    (if (bytes? b) b (with-open [in (clojure.java.io/input-stream b)] (.readAllBytes in)))))

(defn- all-records
  "Every live record of a repo, across its collections (folds list-records)."
  [store did]
  (let [{:keys [collections]} (store/describe-repo store did)]
    (mapcat (fn [coll]
              (loop [cursor nil acc []]
                (let [{:keys [records cursor]} (store/list-records store did coll 100 cursor)
                      acc (into acc records)]
                  (if cursor (recur cursor acc) acc))))
            collections)))

(defn- repo-rev
  "A monotonic repo revision = the highest record rkey (TID-sortable), or a base."
  [records]
  (or (some->> records (map #(last (str/split (:uri %) #"/"))) sort last) "3zzzzzzzzzzzz"))

(defn- sync-response
  "com.atproto.sync.* — getRepo/getRecord/getBlocks return CARs; the rest JSON."
  [store signing-key nsid params]
  (let [did (or (:did params) cfg/pds-did)
        repo* (delay (repo/build-repo did (all-records store did)
                                      (repo-rev (all-records store did)) signing-key))]
    (case nsid
      "com.atproto.sync.getRepo"
      (car-response (repo/blocks-car @repo* nil))

      "com.atproto.sync.getLatestCommit"
      (json-response {:status 200 :body {"cid" (:commit-cid @repo*) "rev" (:rev @repo*)}})

      "com.atproto.sync.getRepoStatus"
      (json-response {:status 200 :body {"did" did "active" true "rev" (:rev @repo*)}})

      "com.atproto.sync.listRepos"
      (json-response {:status 200 :body {"repos" [{"did" cfg/pds-did
                                                   "head" (:commit-cid @repo*)
                                                   "rev" (:rev @repo*)
                                                   "active" true}]}})

      "com.atproto.sync.getRecord"
      (let [{:keys [collection rkey]} params
            key (str collection "/" rkey)
            cid (get-in @repo* [:record-cids key])]
        (if cid
          (car-response (repo/blocks-car @repo* #{cid (:commit-cid @repo*) (:root @repo*)}))
          (json-response {:status 404 :body {"error" "RecordNotFound" "message" key}})))

      "com.atproto.sync.getBlocks"
      (let [want (some-> (:cids params) (str/split #",") set)]
        (car-response (repo/blocks-car @repo* (when want (conj want (:commit-cid @repo*))))))

      "com.atproto.sync.getBlob"
      (if-let [{:keys [bytes mime]} (blob/get-blob cfg/blob-dir (:cid params))]
        (bytes-response bytes mime)
        (json-response {:status 404 :body {"error" "BlobNotFound" "message" (:cid params)}}))

      "com.atproto.sync.listBlobs"
      (json-response {:status 200 :body {"cids" (blob/list-blobs cfg/blob-dir)}})

      (json-response {:status 501 :body {"error" "MethodNotImplemented" "message" nsid}}))))

(defn- parse-query [qs]
  (if (str/blank? qs)
    {}
    (into {}
          (for [pair (str/split qs #"&")
                :let [[k v] (str/split pair #"=" 2)]]
            [(keyword (java.net.URLDecoder/decode k "UTF-8"))
             (some-> v (java.net.URLDecoder/decode "UTF-8"))]))))

(defn- read-body [req]
  (when-let [b (:body req)]
    (let [s (if (string? b) b (slurp b))]
      (when-not (str/blank? s)
        (json/parse-string s true)))))

(defn- iso-now [] (str (java.time.Instant/now)))

(defn- subscribe-handler
  "com.atproto.sync.subscribeRepos — a websocket firehose. On connect, emit a
  #commit frame carrying the current head (CAR + create ops) so a relay can
  bootstrap; the connection stays open for future commit events."
  [req store signing-key]
  (http/as-channel req
    {:on-open
     (fn [ch]
       (try
         (let [records (all-records store cfg/pds-did)
               build (repo/build-repo cfg/pds-did records (repo-rev records) signing-key)
               ops (for [{:keys [uri]} records
                         :let [path (->> (str/split uri #"/") (drop 3) (str/join "/"))
                               cs (get-in build [:record-cids path])]]
                     {:action "create" :path path :cid-bytes (get-in build [:blocks cs :cid])})
               frame (repo/commit-frame 1 cfg/pds-did build (vec ops) (iso-now))]
           (http/send! ch frame))
         (catch Exception e (binding [*out* *err*] (println "[pds] subscribeRepos:" (.getMessage e))))))}))

(defn make-handler [store signing-key signing-multibase]
  (fn [req]
    (let [uri (:uri req)
          method (:request-method req)
          qp (parse-query (:query-string req))
          nsid (when (str/starts-with? uri "/xrpc/") (subs uri 6))]
      (cond
        ;; health
        (= uri "/health")
        (json-response {:status 200 :body {"status" "ok" "did" cfg/pds-did}})

        ;; did:web document — publishes the atproto signing key (relay verifies sig)
        (= uri "/.well-known/did.json")
        (json-response {:status 200 :body (cfg/did-document signing-multibase)})

        (nil? nsid)
        (json-response {:status 404 :body {"error" "NotFound" "message" uri}})

        ;; blob upload (binary body, content-addressed)
        (= nsid "com.atproto.repo.uploadBlob")
        (let [data (read-bytes req)
              {:keys [cid size mime]} (blob/put-blob cfg/blob-dir data
                                                     (get-in req [:headers "content-type"]))]
          (json-response {:status 200 :body {"blob" {"$type" "blob"
                                                     "ref" {"$link" cid}
                                                     "mimeType" mime "size" size}}}))

        ;; federation firehose: com.atproto.sync.subscribeRepos (websocket)
        (= nsid "com.atproto.sync.subscribeRepos")
        (subscribe-handler req store signing-key)

        ;; federation: com.atproto.sync.* (getRepo → CAR; rest → JSON)
        (str/starts-with? nsid "com.atproto.sync.")
        (sync-response store signing-key nsid qp)

        :else
        (let [body (try (read-body req) (catch Exception _ nil))
              params (merge qp body)
              resp (case nsid
                     "com.atproto.server.describeServer" (xrpc/describe-server params)
                     "com.atproto.server.createSession"  (xrpc/create-session params)
                     "com.atproto.identity.resolveHandle" (xrpc/resolve-handle params)
                     "com.atproto.repo.createRecord" (xrpc/create-record store params)
                     "com.atproto.repo.putRecord"    (xrpc/put-record store params)
                     "com.atproto.repo.getRecord"    (xrpc/get-record store params)
                     "com.atproto.repo.deleteRecord" (xrpc/delete-record store params)
                     "com.atproto.repo.listRecords"  (xrpc/list-records store params)
                     "com.atproto.repo.describeRepo" (xrpc/describe-repo store params)
                     {:status 501 :body {"error" "MethodNotImplemented"
                                         "message" (str nsid " is not implemented by this PDS")}})]
          (json-response resp))))))

(defn make-store []
  (cond
    cfg/kotoba-url
    (do (println "[pds] storage = kotoba engine" cfg/kotoba-url "graph" cfg/kotoba-graph)
        (store/->kotoba-store cfg/kotoba-url cfg/kotoba-graph))
    cfg/store-path
    (do (println "[pds] storage = durable on-disk datom log" cfg/store-path)
        (store/->durable-store cfg/store-path))
    :else
    (do (println "[pds] storage = in-process datom log (ephemeral; set PDS_STORE_PATH or KOTOBA_URL)")
        (store/->mem-store))))

(defn start! [store signing-key signing-multibase port]
  (http/run-server (make-handler store signing-key signing-multibase)
                   {:port port :legacy-return-value? false}))

(defn -main [& _]
  (let [store (make-store)
        ;; stable commit signing key (present-only, persisted at PDS_SIGNING_KEY_FILE).
        kp (repo/load-or-create-keypair cfg/signing-key-file)
        multibase (repo/pubkey-multibase (:public kp))]
    (start! store (:private kp) multibase cfg/port)
    (println (format "[pds] etzhayyim atproto PDS up: %s  did=%s  domains=%s  :%d"
                     cfg/host cfg/pds-did (str/join "," cfg/user-domains) cfg/port))
    (println "[pds] sync surface: com.atproto.sync.{getRepo,getRecord,getBlocks,getLatestCommit,getRepoStatus,listRepos,subscribeRepos,getBlob,listBlobs} + repo.uploadBlob")
    (println "[pds] signing key published in did.json: #atproto" multibase)
    @(promise)))
