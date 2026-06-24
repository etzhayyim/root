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
            [etzhayyim.pds.xrpc :as xrpc]
            [etzhayyim.pds.repo :as pdsrepo]))

(defn- json-response [{:keys [status body]}]
  {:status status
   :headers {"content-type" "application/json; charset=utf-8"
             "access-control-allow-origin" "*"}
   :body (json/generate-string body)})

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

(defn- read-raw-bytes ^bytes [req]
  (when-let [b (:body req)]
    (cond
      (string? b) (.getBytes ^String b "UTF-8")
      (bytes? b)  b
      :else       (.readAllBytes ^java.io.InputStream b))))

(defn make-handler [store]
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

        ;; uploadBlob: raw bytes IN (content-type = the blob mime), JSON ref OUT
        (= nsid "com.atproto.repo.uploadBlob")
        (let [data (try (read-raw-bytes req) (catch Exception _ nil))
              mime (get-in req [:headers "content-type"])
              did  (or (xrpc/resolve-repo (:repo qp)) (:did qp) cfg/pds-did)]
          (json-response (xrpc/upload-blob store did mime data)))

        ;; getBlob: JSON error OR the raw blob bytes (served with its mimeType)
        (= nsid "com.atproto.sync.getBlob")
        (let [resp (xrpc/get-blob store qp)]
          (if-let [b (:blob resp)]
            {:status 200
             :headers {"content-type" (or (:mimeType b) "application/octet-stream")
                       "access-control-allow-origin" "*"}
             :body (java.io.ByteArrayInputStream. (:bytes b))}
            (json-response resp)))

        ;; sync.getRepo / getBlocks: rebuild the repo (app-aozora-repo MST/commit)
        ;; and serve it as a CARv1 (no-server-key → unsigned on read).
        (#{"com.atproto.sync.getRepo" "com.atproto.sync.getBlocks"} nsid)
        (let [did (or (xrpc/resolve-repo (:did qp)) cfg/pds-did)
              ^bytes car (if (= nsid "com.atproto.sync.getRepo")
                           (pdsrepo/get-repo-car store did)
                           (pdsrepo/get-blocks-car store did
                             (some-> (or (:cids qp) (:cid qp)) (str/split #","))))]
          {:status 200
           :headers {"content-type" "application/vnd.ipld.car"
                     "access-control-allow-origin" "*"}
           :body (java.io.ByteArrayInputStream. car)})

        :else
        (let [body (try (read-body req) (catch Exception _ nil))
              params (merge qp body)
              resp (case nsid
                     "com.atproto.server.describeServer" (xrpc/describe-server params)
                     "com.atproto.server.createSession"  (xrpc/create-session params)
                     "com.atproto.server.createAccount"  (xrpc/create-account store params)
                     "com.atproto.server.getSession"     (xrpc/get-session store params)
                     "com.atproto.identity.resolveHandle" (xrpc/resolve-handle params)
                     "com.atproto.repo.createRecord" (xrpc/create-record store params)
                     "com.atproto.repo.putRecord"    (xrpc/put-record store params)
                     "com.atproto.repo.getRecord"    (xrpc/get-record store params)
                     "com.atproto.repo.deleteRecord" (xrpc/delete-record store params)
                     "com.atproto.repo.listRecords"  (xrpc/list-records store params)
                     "com.atproto.repo.describeRepo" (xrpc/describe-repo store params)
                     "com.atproto.sync.getLatestCommit"
                     (let [did (or (xrpc/resolve-repo (:repo params) ) (:did params) cfg/pds-did)]
                       (if-let [lc (pdsrepo/get-latest-commit store did)]
                         {:status 200 :body {"cid" (:cid lc) "rev" (:rev lc)}}
                         {:status 404 :body {"error" "RepoNotFound" "message" "no repo for did"}}))
                     {:status 501 :body {"error" "MethodNotImplemented"
                                         "message" (str nsid " is not implemented by this PDS")}})]
          (json-response resp))))))

(defn make-store []
  (if cfg/kotoba-url
    (do (println "[pds] storage = kotoba engine" cfg/kotoba-url "graph" cfg/kotoba-graph)
        (store/->kotoba-store cfg/kotoba-url cfg/kotoba-graph))
    (do (println "[pds] storage = in-process datom log (KOTOBA_URL unset)")
        (store/->mem-store))))

(defn start! [store port]
  (http/run-server (make-handler store) {:port port :legacy-return-value? false}))

(defn -main [& _]
  (let [store (make-store)]
    (start! store cfg/port)
    (println (format "[pds] etzhayyim atproto PDS up: %s  did=%s  domains=%s  :%d"
                     cfg/host cfg/pds-did (str/join "," cfg/user-domains) cfg/port))
    @(promise)))
