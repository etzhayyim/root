(ns lg-open-patent.store
  "Patent corpus persistence seam — clj port of the open-patent RisingWave layer
  (ADR-2606280030).

  SUBSTRATE BOUNDARY: the Python graphs read/write `vertex_open_patent_*` tables
  on RisingWave PG :4566 (psycopg). The substrate boundary forbids RisingWave in
  the clj twin, so persistence is an INJECTABLE seam: `PatentStore`.

  Two implementations:
    - `->fake-patent-store`  — in-memory atom; default + used by tests so the
      graph logic verifies deterministically offline (no pod, no network).
    - `->kotoba-patent-store` — production, backed by the kotoba Datom log via
      lg-open-patent.kotoba-datomic (substrate-clean target).

  Graphs reference the store through the `*store*` dynamic var (rebound in tests)."
  (:require [clojure.string :as str]
            [lg-open-patent.kotoba-datomic :as kd]))

(defprotocol PatentStore
  (tech-trends [this]
    "Derive technology domains from the patent corpus -> seq of
     {:domain <str> :count <int>} (gather_tech_trends node).")
  (search-patents [this query]
    "TEXT search vertex_open_patent_patent by title substring ->
     seq of patent maps (search_prior_art node).")
  (put-patents! [this patents]
    "Persist ingested patents (seq of maps) -> count written.")
  (put-citations! [this citations]
    "Persist ingested citations (seq of maps) -> count written.")
  (put-seed! [this seed]
    "Persist a generated invention seed -> {:seed_uri <id>}.")
  (put-novelty! [this report]
    "Persist a novelty report -> {:novelty_uri <id>}."))

;; ── in-memory fake (default + tests) ──────────────────────────────────────────

(defn- domain-of [patent]
  (or (:tech_domain patent)
      (some-> (or (:title patent) "") (str/split #"\s+") first str/lower-case)
      "unknown"))

(defrecord FakePatentStore [db]
  PatentStore
  (tech-trends [_]
    (->> (:patents @db)
         (map domain-of)
         frequencies
         (map (fn [[d n]] {:domain d :count n}))
         (sort-by (comp - :count))
         vec))
  (search-patents [_ query]
    (let [q (str/lower-case (str query))]
      (->> (:patents @db)
           (filter (fn [p] (str/includes? (str/lower-case (str (:title p))) q)))
           vec)))
  (put-patents! [_ patents]
    (swap! db update :patents (fnil into []) patents)
    (count patents))
  (put-citations! [_ citations]
    (swap! db update :citations (fnil into []) citations)
    (count citations))
  (put-seed! [_ seed]
    (swap! db update :seeds (fnil conj []) seed)
    {:seed_uri (str "mem://seed/" (or (:seedId seed) (:seed_id seed) (count (:seeds @db))))})
  (put-novelty! [_ report]
    (swap! db update :novelty (fnil conj []) report)
    {:novelty_uri (str "mem://novelty/" (or (:reportId report) (count (:novelty @db))))}))

(defn ->fake-patent-store
  ([] (->fake-patent-store {}))
  ([seed-db] (->FakePatentStore (atom (merge {:patents [] :citations [] :seeds [] :novelty []}
                                             seed-db)))))

;; ── kotoba Datom-log backed store (production substrate target) ────────────────

(defn- edn-str [x] (pr-str x))

(defrecord KotobaPatentStore [dm]
  PatentStore
  (tech-trends [_]
    ;; Distinct tech domains from the corpus (datalog → rows of [?domain]).
    (let [rows (kd/q dm "[:find ?d :where [?e :patent/tech-domain ?d]]")]
      (->> rows (map first) frequencies
           (map (fn [[d n]] {:domain d :count n})) vec)))
  (search-patents [_ query]
    (kd/q dm (str "[:find (pull ?e [*]) :where [?e :patent/title ?t] "
                  "[(clojure.string/includes? ?t " (edn-str (str query)) ")]]")))
  (put-patents! [_ patents]
    (kd/transact dm (edn-str (mapv (fn [p] (assoc p :doc/type "Patent")) patents)))
    (count patents))
  (put-citations! [_ citations]
    (kd/transact dm (edn-str (mapv (fn [c] (assoc c :doc/type "Citation")) citations)))
    (count citations))
  (put-seed! [_ seed]
    (kd/transact dm (edn-str [(assoc seed :doc/type "InventionSeed")]))
    {:seed_uri (str "kotoba://seed/" (or (:seedId seed) (:seed_id seed)))})
  (put-novelty! [_ report]
    (kd/transact dm (edn-str [(assoc report :doc/type "NoveltyReport")]))
    {:novelty_uri (str "kotoba://novelty/" (:reportId report))}))

(defn ->kotoba-patent-store
  ([] (->KotobaPatentStore (kd/->client)))
  ([dm] (->KotobaPatentStore dm)))

;; Default store: empty in-memory fake (offline-safe). Graphs rebind in prod.
(def ^:dynamic *store* (->fake-patent-store))
