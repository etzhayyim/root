;; etzhayyim.kotoba.ingest — load an actor's seed into the kotoba Datom log.
;;
;; The generic, validated replacement for per-actor Python `datom_emit.py`: any
;; 🟡 R0 actor's orgs/etzhayyim/com-etzhayyim-<a>/data/seed-*.kotoba.edn (entity-map or nested-graph
;; form) is ingested into a content-addressed append-only log, optionally
;; type/enum/unique-validated against its 00-contracts schema, and materialized
;; to a canonical .kotoba.edn snapshot — all root-side, never the kotoba subrepo.
;;
;; CLI:  bb kotoba:ingest <schema.kotoba.edn> <seed.kotoba.edn> [out.kotoba.edn] [--validate]

(ns etzhayyim.kotoba.ingest
  (:require [clojure.edn :as edn]
            [clojure.string :as str]
            [etzhayyim.kotoba.cid :as cid]
            [etzhayyim.kotoba.schema :as schema]
            [etzhayyim.kotoba.engine :as kt]))

(defn- with-db-id [m]
  (if-let [idk (some #(when (= "id" (name %)) %) (keys m))]
    (assoc m :db/id (get m idk))
    ;; id-less maps (e.g. asobi/keizu edge maps) get a deterministic
    ;; content-addressed id so edges are first-class entities.
    (assoc m :db/id (str "e:" (subs (cid/cid-of-edn (into (sorted-map) m)) 1 25)))))

(defn- seed->rows [raw sections]
  (let [ms (if sections
             (mapcat raw sections)
             (cond (vector? raw) (filter map? raw)
                   (map? raw) (mapcat (fn [[_ v]] (when (and (sequential? v) (every? map? v)) v)) raw)
                   :else nil))]
    {:ms ms :rows (map with-db-id ms)}))

(defn ingest-actor
  "Ingest a seed into a (fresh) kotoba log + return a maturity report. opts:
     :schema     path to the 00-contracts vocabulary (optional but recommended)
     :seed       path to the actor seed (required)
     :sections   section keys to flatten for nested-graph seeds (optional)
     :journal    journal path (required; under 80-data, never the subrepo)
     :out        snapshot .kotoba.edn path (optional)
     :validate?  reject type/enum/unique violations at transact time
   Report: {:entities :datoms :head :undeclared :value-violations :snapshot}."
  [{:keys [schema seed sections journal out validate?]}]
  (let [raw (edn/read-string (slurp seed))
        {:keys [ms rows]} (seed->rows raw sections)
        vocab (when schema (schema/load-vocabulary schema))
        registry (when schema (schema/load-registry schema))
        conn (kt/connect (cond-> {:journal journal}
                           schema (assoc :schemas [schema])
                           validate? (assoc :validate? true)))]
    (kt/transact conn rows)
    {:entities (count ms)
     :datoms (count (:live (kt/db conn)))
     :head (kt/head-cid conn)
     :undeclared (when vocab (vec (sort (schema/undeclared-attrs vocab ms))))
     :value-violations (when registry (count (schema/value-violations registry ms)))
     :snapshot (when out (kt/snapshot! conn out))}))

(defn -main
  "CLI entry. Args: <schema> <seed> [out] [--validate]"
  [& args]
  (let [[schema seed] args
        rest-args (drop 2 args)
        validate? (some #{"--validate"} rest-args)
        out (first (remove #(str/starts-with? % "--") rest-args))
        journal (str (or out seed) ".ingest-journal.edn")]
    (when (or (nil? schema) (nil? seed))
      (println "usage: bb kotoba:ingest <schema.kotoba.edn> <seed.kotoba.edn> [out.kotoba.edn] [--validate]")
      (System/exit 2))
    (let [r (ingest-actor {:schema schema :seed seed :journal journal
                           :out out :validate? (boolean validate?)})]
      (println (format "ingested %d entities → %d live datoms" (:entities r) (:datoms r)))
      (println "head CID:" (:head r))
      (when (:undeclared r)
        (println "undeclared attrs:" (if (seq (:undeclared r)) (:undeclared r) "none ✓")))
      (when (:value-violations r)
        (println "value violations:" (:value-violations r)))
      (when (:snapshot r)
        (println "snapshot:" (get-in r [:snapshot :out]) "(" (get-in r [:snapshot :rows]) "rows)")))))
