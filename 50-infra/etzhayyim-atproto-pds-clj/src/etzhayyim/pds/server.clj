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
            [etzhayyim.pds.account :as account]
            [etzhayyim.pds.actorkeys :as actorkeys]
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
                (let [{:keys [records cursor]} (store/list-records store did coll {:limit 100 :cursor cursor})
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

(def ^:private write-methods
  #{"com.atproto.repo.createRecord" "com.atproto.repo.putRecord"
    "com.atproto.repo.deleteRecord" "com.atproto.repo.applyWrites"
    "com.atproto.repo.uploadBlob" "com.atproto.repo.importRepo"})

(def ^:private repo-write-methods
  #{"com.atproto.repo.createRecord" "com.atproto.repo.putRecord"
    "com.atproto.repo.deleteRecord" "com.atproto.repo.applyWrites"})

(defn- write-values [nsid params]
  (if (= nsid "com.atproto.repo.applyWrites")
    (keep #(or (:value %) (get % "value")) (:writes params))
    (remove nil? [(or (:record params) (:value params))])))

(defn make-handler [store signing-key signing-multibase jwt-secret]
  (fn [req]
    (let [uri (:uri req)
          qp (parse-query (:query-string req))
          nsid (when (str/starts-with? uri "/xrpc/") (subs uri 6))
          binary? (#{"com.atproto.repo.uploadBlob" "com.atproto.repo.importRepo"} nsid)
          ws? (= nsid "com.atproto.sync.subscribeRepos")
          ;; read the JSON body ONCE (binary + ws bodies are read raw by their handlers)
          jbody (when (and nsid (not binary?) (not ws?)) (try (read-body req) (catch Exception _ nil)))
          params (merge qp jbody)
          auth-sub (account/verify-jwt jwt-secret (get-in req [:headers "authorization"]))
          ;; every blob ref in a write must already resolve in the blob store
          blob-missing (when (repo-write-methods nsid)
                         (mapcat #(blob/missing-refs cfg/blob-dir %) (write-values nsid params)))]
      (cond
        ;; health
        (= uri "/health")
        (json-response {:status 200 :body {"status" "ok" "did" cfg/pds-did}})

        ;; did:web document — publishes the atproto signing key (relay verifies sig)
        (= uri "/.well-known/did.json")
        (json-response {:status 200 :body (cfg/did-document signing-multibase)})

        ;; registry index (Path B) — enumerate the PDS's actors + their published
        ;; keys so a relay/worker can discover + verify them. Public (no secret read).
        (= uri "/actors.json")
        (json-response {:status 200 :body (actorkeys/actors-index cfg/actor-keys-dir)})

        ;; per-actor did:web doc (Path B) — published from the actor-keys registry
        ;; when configured (PDS_ACTOR_KEYS_DIR + MURAKUMO_SEAL_KEY). Each actor's doc
        ;; carries its own #atproto Multikey so a verifier checks the actor's record
        ;; signatures from the resolved doc alone. Unconfigured → falls through to 404.
        (re-matches #"/actor/[^/]+/did\.json" uri)
        (if-let [resp (actorkeys/serve-actor-did
                       cfg/actor-keys-dir cfg/actor-seal-secret
                       (second (re-matches #"/actor/([^/]+)/did\.json" uri)))]
          (json-response resp)
          (json-response {:status 404 :body {"error" "NotFound" "message" uri}}))

        (nil? nsid)
        (json-response {:status 404 :body {"error" "NotFound" "message" uri}})

        ;; opt-in write auth (PDS_REQUIRE_AUTH): a valid session is required…
        (and cfg/require-auth (contains? write-methods nsid) (nil? auth-sub))
        (json-response {:status 401 :body {"error" "AuthRequired" "message" "valid session Bearer required"}})

        ;; …and for a repo write, the session `sub` must own the target repo
        (and cfg/require-auth (repo-write-methods nsid)
             (when-let [rd (xrpc/resolve-repo (:repo params))] (not= auth-sub rd)))
        (json-response {:status 403 :body {"error" "Forbidden" "message" "session does not own this repo"}})

        ;; blob-ref integrity: a record may not reference an absent blob
        (seq blob-missing)
        (json-response {:status 400 :body {"error" "BlobNotFound"
                                           "message" (str "unresolved blob refs: " (str/join "," blob-missing))}})

        ;; account + session
        (= nsid "com.atproto.server.createAccount")
        (let [{:keys [handle password did]} params]
          (try
            (let [a (account/create-account cfg/accounts-file {:handle handle :password password :did did})]
              (json-response {:status 200 :body {"did" (:did a) "handle" (:handle a)
                                                 "accessJwt" (account/make-jwt jwt-secret (:did a))}}))
            (catch Exception e (json-response {:status 400 :body {"error" "InvalidRequest" "message" (.getMessage e)}}))))

        (= nsid "com.atproto.server.createSession")
        (let [{:keys [identifier password]} params]
          (if-let [did (and password (account/verify-password cfg/accounts-file identifier password))]
            (json-response {:status 200 :body {"did" did "handle" identifier
                                               "accessJwt" (account/make-jwt jwt-secret did)
                                               "refreshJwt" (account/make-jwt jwt-secret did)}})
            (json-response (xrpc/create-session (merge qp {:identifier identifier})))))

        (= nsid "com.atproto.server.getSession")
        (if auth-sub
          (json-response {:status 200 :body {"did" auth-sub "handle" auth-sub "active" true}})
          (json-response {:status 401 :body {"error" "AuthRequired" "message" "valid session Bearer required"}}))

        ;; rotate the access/refresh JWTs from a valid (refresh) Bearer
        (= nsid "com.atproto.server.refreshSession")
        (if auth-sub
          (json-response {:status 200 :body {"did" auth-sub "handle" auth-sub
                                             "accessJwt" (account/make-jwt jwt-secret auth-sub)
                                             "refreshJwt" (account/make-jwt jwt-secret auth-sub)}})
          (json-response {:status 401 :body {"error" "AuthRequired" "message" "valid refresh Bearer required"}}))

        ;; stateless sessions: the client discards the token (no server-side revocation list)
        (= nsid "com.atproto.server.deleteSession")
        (json-response {:status 200 :body {}})

        ;; repo import (binary CAR body → walk MST → ingest records)
        (= nsid "com.atproto.repo.importRepo")
        (let [{:keys [did records]} (repo/import-records (read-bytes req))]
          (doseq [[collection rkey value] records]
            (store/put-record store did collection rkey value))
          (json-response {:status 200 :body {"imported" (count records) "did" did}}))

        ;; blob upload (binary body, content-addressed)
        (= nsid "com.atproto.repo.uploadBlob")
        (let [data (read-bytes req)
              {:keys [cid size mime]} (blob/put-blob cfg/blob-dir data
                                                     (get-in req [:headers "content-type"]))]
          (json-response {:status 200 :body {"blob" {"$type" "blob"
                                                     "ref" {"$link" cid}
                                                     "mimeType" mime "size" size}}}))

        ;; blobs the repo references but has not uploaded
        (= nsid "com.atproto.repo.listMissingBlobs")
        (let [did (xrpc/resolve-repo (or (:repo params) cfg/pds-did))
              refs (distinct (mapcat #(blob/blob-refs (:value %)) (all-records store did)))
              missing (remove #(blob/present? cfg/blob-dir %) refs)]
          (json-response {:status 200 :body {"blobs" (mapv (fn [c] {"cid" c}) missing)}}))

        ;; federation firehose: com.atproto.sync.subscribeRepos (websocket)
        (= nsid "com.atproto.sync.subscribeRepos")
        (subscribe-handler req store signing-key)

        ;; federation: com.atproto.sync.* (getRepo → CAR; rest → JSON)
        (str/starts-with? nsid "com.atproto.sync.")
        (sync-response store signing-key nsid qp)

        :else
        (let [resp (case nsid
                     "com.atproto.server.describeServer" (xrpc/describe-server params)
                     "com.atproto.server.createSession"  (xrpc/create-session params)
                     "com.atproto.identity.resolveHandle" (xrpc/resolve-handle params)
                     "com.atproto.repo.createRecord" (xrpc/create-record store params)
                     "com.atproto.repo.applyWrites"  (xrpc/apply-writes store params)
                     "com.atproto.repo.putRecord"    (xrpc/put-record store params)
                     "com.atproto.repo.getRecord"    (xrpc/get-record store params)
                     "com.atproto.repo.deleteRecord" (xrpc/delete-record store params)
                     "com.atproto.repo.listRecords"  (xrpc/list-records store params)
                     "com.atproto.repo.describeRepo" (xrpc/describe-repo store params)
                     ;; AppView read rendering from the local kotoba log (Method A)
                     "app.bsky.feed.getAuthorFeed"   (xrpc/get-author-feed store params)
                     "app.bsky.actor.getProfile"     (xrpc/get-profile store params)
                     {:status 501 :body {"error" "MethodNotImplemented"
                                         "message" (str nsid " is not implemented by this PDS")}})]
          (json-response resp))))))

(defn make-store []
  ;; When the actor-keys registry is configured, every write is signed by ITS OWN
  ;; actor's sealed key (multi-actor; Path B). Otherwise writes are unsigned.
  (let [signer (when (and cfg/actor-keys-dir (not (str/blank? (str cfg/actor-seal-secret))))
                 (do (println "[pds] writes signed per-actor from registry" cfg/actor-keys-dir)
                     (actorkeys/registry-signer cfg/actor-keys-dir cfg/actor-seal-secret)))]
    (cond
      cfg/kotoba-url
      (do (println "[pds] storage = kotoba engine" cfg/kotoba-url "graph" cfg/kotoba-graph)
          (store/->kotoba-store cfg/kotoba-url cfg/kotoba-graph signer))
      cfg/store-path
      (do (println "[pds] storage = durable on-disk datom log" cfg/store-path)
          (store/->durable-store cfg/store-path signer))
      :else
      (do (println "[pds] storage = in-process datom log (ephemeral; set PDS_STORE_PATH or KOTOBA_URL)")
          (store/->mem-store signer)))))

(defn start! [store signing-key signing-multibase jwt-secret port]
  (http/run-server (make-handler store signing-key signing-multibase jwt-secret)
                   {:port port :legacy-return-value? false}))

(defn -main [& _]
  (let [store (make-store)
        ;; stable commit signing key (present-only, persisted at PDS_SIGNING_KEY_FILE).
        kp (repo/load-or-create-keypair cfg/signing-key-file)
        multibase (repo/pubkey-multibase (:public kp))
        jwt-secret (account/secret-from-key (.getEncoded (:private kp)))]
    (start! store (:private kp) multibase jwt-secret cfg/port)
    (println (format "[pds] etzhayyim atproto PDS up: %s  did=%s  domains=%s  :%d"
                     cfg/host cfg/pds-did (str/join "," cfg/user-domains) cfg/port))
    (println "[pds] sync surface: com.atproto.sync.{getRepo,getRecord,getBlocks,getLatestCommit,getRepoStatus,listRepos,subscribeRepos,getBlob,listBlobs} + repo.{uploadBlob,importRepo,applyWrites}")
    (println "[pds] auth: createAccount/createSession/getSession (HS256); write-auth" (if cfg/require-auth "ENFORCED" "open"))
    (println "[pds] signing key published in did.json: #atproto" multibase)
    @(promise)))
