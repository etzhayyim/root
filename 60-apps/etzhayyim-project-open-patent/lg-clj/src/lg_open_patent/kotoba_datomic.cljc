(ns lg-open-patent.kotoba-datomic
  "kotoba datomic XRPC client — the substrate-clean persistence target for the
  open-patent clj twin (ADR-2606280030).

  SUBSTRATE BOUNDARY: the Python runtime persists to RisingWave PG :4566 (psycopg
  + `_RwAsyncPostgresSaver`). The clj twin does NOT speak RisingWave — the
  substrate boundary forbids it. Persistence here goes to the kotoba Datom log via
  the canonical `ai.etzhayyim.apps.kotoba.datomic.{transact,q,pull}` XRPC surface
  (trimmed port of lg-docs.kotoba-datomic; httpx -> babashka.http-client).

  Read-only `q`/`pull` carry no server key by default (no-server-key, read-only,
  ADR-2606072802); a write `transact` needs the operator/member bearer."
  (:require [clojure.string :as str]
            #?(:clj [cheshire.core :as json])
            #?(:clj [babashka.http-client :as http])))

(defn- env [k default] #?(:clj (or (System/getenv k) default) :cljs default))

(def kotoba-xrpc
  (str/replace
   (or (env "KOTOBA_XRPC_URL" nil)
       (env "KOTOBA_URL" nil)
       "http://kotoba.kotoba.svc.cluster.local:8080")
   #"/+$" ""))

(def kotoba-bearer (env "KOTOBA_BEARER" ""))
(def default-graph (env "KOTOBA_GRAPH" "open-patent-v1"))

(defn- headers []
  (if (seq kotoba-bearer) {"Authorization" (str "Bearer " kotoba-bearer)} {}))

#?(:clj
   (defn- post-json [url body]
     (http/post url {:headers (merge {"Content-Type" "application/json"} (headers))
                     :body (json/generate-string body)
                     :throw false})))

(defrecord KotobaDatomic [graph])

(defn ->client
  ([] (->KotobaDatomic default-graph))
  ([graph] (->KotobaDatomic graph)))

(defn transact
  "Append tx-ops to the kotoba Datom log (graph `open-patent-v1`)."
  [dm tx-edn]
  #?(:clj
     (let [resp (post-json (str kotoba-xrpc "/xrpc/ai.etzhayyim.apps.kotoba.datomic.transact")
                           {:graph (:graph dm) :tx_edn tx-edn})]
       (when (>= (:status resp) 400)
         (throw (ex-info "kotoba transact failed" {:status (:status resp) :body (:body resp)})))
       (json/parse-string (:body resp) true))
     :cljs (throw (ex-info "transact not implemented for cljs" {}))))

(defn q
  "Datalog query against the kotoba Datom log → seq of result rows (EDN strings)."
  [dm query-edn]
  #?(:clj
     (let [resp (post-json (str kotoba-xrpc "/xrpc/ai.etzhayyim.apps.kotoba.datomic.q")
                           {:graph (:graph dm) :query_edn query-edn})]
       (when (>= (:status resp) 400)
         (throw (ex-info "kotoba q failed" {:status (:status resp) :body (:body resp)})))
       (or (get (json/parse-string (:body resp) true) :rows_edn) []))
     :cljs (throw (ex-info "q not implemented for cljs" {}))))
