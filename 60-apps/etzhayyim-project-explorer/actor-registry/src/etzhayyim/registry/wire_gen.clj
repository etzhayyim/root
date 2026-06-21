(ns etzhayyim.registry.wire-gen
  "Generate a kotoba Datom QUERY RESPONSE on the Transit wire (transit+json) —
   the form a kotoba node returns to a browser, the Datomic-client wire standard.

   Reads the canonical vitals EAVT snapshot (EDN on disk — the content-addressed
   state), runs the living-cells query, and encodes the RESULT as transit+json so
   the browser can decode it with transit-cljs. Keywords stay keywords on the
   wire (`:vitals.actor/cells`, `:class :alive`) — the whole point of Transit vs
   plain JSON, and what makes repeated attribute keys cache-compress."
  (:require [clojure.edn :as edn]
            [cognitect.transit :as t])
  (:import [java.io ByteArrayOutputStream]))

(def vitals-path "../public/organism/vitals.kotoba.edn")
(def out-path "../public/kotoba/wire/cells.transit.json")

(defn- ->transit-json [data]
  (let [out (ByteArrayOutputStream.)]
    (t/write (t/writer out :json) data)
    (.toString out "UTF-8")))

(defn- materialize [datoms]
  (reduce (fn [acc [e a v _tx op]]
            (if (= op :add) (assoc-in acc [e a] v) (update acc e dissoc a)))
          {} datoms))

(defn- green? [r] (= "green" (some-> r name)))

(defn- classify [{:keys [reflex integrates bsky port-ratio]}]
  (cond
    (and (green? reflex) (pos? (or integrates 0)) bsky) :alive
    (or (green? reflex) (pos? (or port-ratio 0)))       :dormant
    :else                                               :stub))

(defn -main [& _]
  (let [datoms (edn/read-string (slurp vitals-path))
        eavt (materialize datoms)
        cells (->> (vals eavt)
                   (filter :vitals.actor/name)
                   (mapv (fn [a]
                           ;; keyword attrs + a keyword :class value — Transit
                           ;; preserves both across the wire (JSON could not)
                           {:cell/id (:vitals.actor/name a)
                            :cell/cells (or (:vitals.actor/cells a) 0)
                            :cell/in-degree (or (:vitals.actor/in-degree a) 0)
                            :cell/integrates (or (:vitals.actor/integrates a) 0)
                            :cell/reflex (keyword (some-> (:vitals.clj/reflex a) name))
                            :cell/class (classify {:reflex (:vitals.clj/reflex a)
                                                   :integrates (:vitals.actor/integrates a)
                                                   :bsky (:vitals.atproto/bsky-post a)
                                                   :port-ratio (:vitals.clj/port-ratio a)})})))
        response {:wire/format "transit+json"
                  :wire/note "Datomic-client wire standard; keywords preserved + key-cached"
                  :query/find '[?e :cell/* :where [?e :vitals.actor/name]]
                  :result/count (count cells)
                  :result/cells cells}
        json (->transit-json response)]
    (clojure.java.io/make-parents out-path)
    (spit out-path json)
    (println (format "wrote %d-cell Datom query response as transit+json (%d bytes) → %s"
                     (count cells) (count json) out-path))
    (println "sample (first 180 bytes):" (subs json 0 (min 180 (count json))))))
