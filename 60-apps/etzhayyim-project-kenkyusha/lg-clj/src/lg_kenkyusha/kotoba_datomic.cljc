(ns lg-kenkyusha.kotoba-datomic
  "kotoba datomic XRPC client — clj/bb port of the read surface lg_kenkyusha
  used via asyncpg/RisingWave (ADR-2606280030 langgraph-python -> langgraph-clj).

  SUBSTRATE DEVIATION (load-bearing): server.py reads frontier/hypothesis/evidence
  rows from RisingWave (`graphar.vertex_kenkyusha_*`) over asyncpg. The substrate
  boundary FORBIDS RisingWave for the clj actor twin, so this client targets the
  kotoba Datom log instead — `ai.etzhayyim.apps.kotoba.datomic.{q,pull}` — the same
  canonical read surface used by the lg-docs twin. httpx -> babashka.http-client.

  Read-only `q`/`pull` carry no server key by default (no-server-key, read-only,
  ADR-2606072802 / ADR-2605215000). Endpoint resolution honors
  `KOTOBA_XRPC_URL`/`KOTOBA_URL`; auth (when present) = Bearer JWT (`KOTOBA_BEARER`)."
  (:require [clojure.string :as str]
            #?(:clj [cheshire.core :as json])
            #?(:clj [babashka.http-client :as http])))

(defn- env [k default]
  #?(:clj (or (System/getenv k) default) :cljs default))

(def kotoba-xrpc
  (str/replace
   (or (env "KOTOBA_XRPC_URL" nil)
       (env "KOTOBA_URL" nil)
       "http://kotoba.kotoba.svc.cluster.local:8080")
   #"/+$" ""))

(def kotoba-bearer (env "KOTOBA_BEARER" ""))
(def default-graph (env "KOTOBA_GRAPH" "kenkyusha-v1"))

(defn- headers []
  (if (seq kotoba-bearer)
    {"Authorization" (str "Bearer " kotoba-bearer)}
    {}))

(defrecord KotobaDatomic [graph])

(defn ->client
  ([] (->KotobaDatomic default-graph))
  ([graph] (->KotobaDatomic graph)))

#?(:clj
   (defn- post-json [url body]
     (http/post url {:headers (merge {"Content-Type" "application/json"} (headers))
                     :body (json/generate-string body)
                     :throw false})))

(defn q
  "Datalog query over the kotoba graph. Returns a vector of result rows."
  ([dm query-edn] (q dm query-edn nil))
  ([dm query-edn inputs-edn]
   #?(:clj
      (let [body (cond-> {:graph (:graph dm) :query_edn query-edn}
                   (seq inputs-edn) (assoc :inputs_edn inputs-edn))
            resp (post-json (str kotoba-xrpc "/xrpc/ai.etzhayyim.apps.kotoba.datomic.q") body)]
        (when (>= (:status resp) 400)
          (throw (ex-info "kotoba q failed" {:status (:status resp) :body (:body resp)})))
        (or (get (json/parse-string (:body resp) true) :rows) []))
      :cljs (throw (ex-info "q not implemented for cljs" {})))))

(defn pull
  "Pull an entity's attribute map (or nil if absent)."
  [dm entity]
  #?(:clj
     (let [body {:graph (:graph dm) :entity entity}
           resp (post-json (str kotoba-xrpc "/xrpc/ai.etzhayyim.apps.kotoba.datomic.pull") body)]
       (cond
         (= 404 (:status resp)) nil
         (>= (:status resp) 400) (throw (ex-info "kotoba pull failed" {:status (:status resp)}))
         :else (get (json/parse-string (:body resp) true) :entity)))
     :cljs (throw (ex-info "pull not implemented for cljs" {}))))
