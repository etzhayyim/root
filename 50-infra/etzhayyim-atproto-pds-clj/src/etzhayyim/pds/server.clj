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
  "com.atproto.sync.* — getRepo returns a CAR; the rest return JSON."
  [store signing-key nsid params]
  (let [did (or (:did params) cfg/pds-did)]
    (case nsid
      "com.atproto.sync.getRepo"
      (let [records (all-records store did)
            {:keys [car]} (repo/repo-car did records (repo-rev records) signing-key)]
        (car-response car))

      "com.atproto.sync.getLatestCommit"
      (let [records (all-records store did)
            rev (repo-rev records)
            {:keys [commit-cid]} (repo/repo-car did records rev signing-key)]
        (json-response {:status 200 :body {"cid" commit-cid "rev" rev}}))

      "com.atproto.sync.listRepos"
      (json-response {:status 200 :body {"repos" [{"did" cfg/pds-did
                                                   "head" (:commit-cid (repo/repo-car cfg/pds-did (all-records store cfg/pds-did) (repo-rev (all-records store cfg/pds-did)) signing-key))
                                                   "rev" (repo-rev (all-records store cfg/pds-did))}]}})

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

(defn make-handler [store signing-key]
  (fn [req]
    (let [uri (:uri req)
          method (:request-method req)
          qp (parse-query (:query-string req))
          nsid (when (str/starts-with? uri "/xrpc/") (subs uri 6))]
      (cond
        ;; health
        (= uri "/health")
        (json-response {:status 200 :body {"status" "ok" "did" cfg/pds-did}})

        ;; did:web document
        (= uri "/.well-known/did.json")
        (json-response {:status 200 :body (cfg/did-document)})

        (nil? nsid)
        (json-response {:status 404 :body {"error" "NotFound" "message" uri}})

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

(defn start! [store signing-key port]
  (http/run-server (make-handler store signing-key) {:port port :legacy-return-value? false}))

(defn -main [& _]
  (let [store (make-store)
        ;; commit signing key (present-only). Sealed off-platform in production;
        ;; here generated per-process — the did:web doc must publish its public key
        ;; for a relay to verify `sig` (the remaining federation step).
        signing-key (.getPrivate (repo/gen-keypair))]
    (start! store signing-key cfg/port)
    (println (format "[pds] etzhayyim atproto PDS up: %s  did=%s  domains=%s  :%d"
                     cfg/host cfg/pds-did (str/join "," cfg/user-domains) cfg/port))
    (println "[pds] sync surface: com.atproto.sync.{getRepo,getLatestCommit,listRepos}")
    @(promise)))
