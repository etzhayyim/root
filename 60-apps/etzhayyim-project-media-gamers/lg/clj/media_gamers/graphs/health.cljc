(ns media-gamers.graphs.health
  "media-gamers `health` graph — clj twin of graphs/health.py.
  NSID: com.etzhayyim.apps.media_gamers.health

  Topology preserved: START → check → audit → END.

  Port deviation (charter-aligned, ADR-2605262130 substrate boundary): the python
  node probed RisingWave/Postgres connectivity via psycopg. RisingWave is a
  PROHIBITED substrate; the clj twin reports a `:store-ok false` placeholder (a
  kotoba-engine reachability probe is the proper replacement, deferred). `:ok`
  stays true regardless, exactly as the python health node always returned ok."
  (:require [clojure.string :as str]
            [media-gamers.audit :as audit]
            #?(:clj [langgraph.graph :as g])))

(defn- getenv [k default]
  #?(:clj (or (System/getenv k) default) :default default))

(defn app-did []
  (getenv "MEDIA_GAMERS_APP_DID" "did:web:media-gamers.etzhayyim.com"))

(defn now-iso []
  #?(:clj (.format (java.time.format.DateTimeFormatter/ofPattern "yyyy-MM-dd'T'HH:mm:ss'Z'")
                   (java.time.ZonedDateTime/now (java.time.ZoneOffset/UTC)))
     :default ""))

(defn node-check
  "Port of `_node_check` (RW probe removed per substrate boundary)."
  [_state]
  (let [store-url (or (not-empty (getenv "RW_URL" "")) (not-empty (getenv "KOTOBA_URL" "")))]
    (cond-> {:service "lg-media-gamers"
             :version "0.1.0"
             :server-now (now-iso)
             :ok true
             :store-ok false}
      (not store-url) identity
      store-url (assoc :store-note "store probe deferred (kotoba; RW prohibited)"))))

(defn node-audit
  "Port of `_node_audit` — fire-and-forget OCEL emit."
  [state]
  #?(:clj (audit/emit-audit-bg
           {:actor (app-did)
            :activity "media_gamers.health.check"
            :object-id (str "health:" (quot (System/currentTimeMillis) 1000))
            :object-type "media_gamers.health"
            :attributes {:ok (get state :ok true)
                         :storeOk (get state :store-ok false)}}))
  {})

#?(:clj
   (defn build []
     (-> (g/state-graph)
         (g/add-node :check node-check)
         (g/add-node :audit node-audit)
         (g/add-edge :check :audit)
         (g/set-entry-point :check)
         (g/set-finish-point :audit)
         (g/compile-graph))))

#?(:clj (def graph (delay (build))))
