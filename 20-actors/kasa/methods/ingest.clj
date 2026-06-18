#!/usr/bin/env bb
;; Working Clojure port of methods/ingest.py.
(ns kasa.methods.ingest
  "kasa 嵩 — ingest cell: PUBLIC compute-capacity data → kotoba EAVT observations (ADR-2606072000).

  Bridges public, redistributable data points into the :compute.series/* + :compute.obs/*
  vocabulary, gating every row through the G1 admissibility layer (sources/admissible?). Two
  shapes are accepted offline (data/ingest/*.json):

    • \"rows\"  : {\"source\": \"src.epoch\", \"publisher\": \"epoch-ai\", \"access\": \"open-dataset\",
                \"rows\": [ {\"series\": \"cap.flops.frontier-training.world\", \"year\": 2025,
                             \"value\": 1.0e26, \"sourcing\": \"estimated\",
                             \"method\": \"Epoch AI largest-model training FLOP\"} ]}
    • \"series\": optional new :compute.series definitions (same file, key \"series\": [ {...} ]).

  NETWORK DISCIPLINE (G7 + ADR-2605262400 §7 passive-only):
    - DEFAULT = OFFLINE. Reads pre-downloaded files from data/ingest/*.json (no network).
    - LIVE fetch requires BOTH KASA_OPERATOR_GATE=1 AND an explicit --fetch-epoch. Even
      then it is a single polite request to the public CC-BY Epoch AI dataset, never a scrape.
    - Real reported rows are :authoritative; the seed stays :representative. Merge keeps the
      more-authoritative source on id collision (authoritative > estimated/representative).

  Run:  bb --classpath 20-actors 20-actors/kasa/methods/ingest.clj
        KASA_OPERATOR_GATE=1 bb --classpath 20-actors 20-actors/kasa/methods/ingest.clj --fetch-epoch"
  (:require [kasa.methods.kasa-edn :as ke]
            [kasa.methods.sources :as src]
            [cheshire.core :as json]
            [clojure.java.io :as io]
            [clojure.string :as str]))

(def ^:private this-file *file*)
(defn- actor-root [] (-> this-file io/file .getAbsoluteFile .getParentFile .getParentFile))

(def ^:private SEED-PATH
  (delay (io/file (actor-root) "data" "seed-compute-capacity.kotoba.edn")))

;; RANK mirrors ingest.py's RANK dict: more-authoritative sources have higher rank.
;; Keys are the string-prefixed-colon form that kasa_edn returns (":representative" etc.)
(def ^:private RANK
  {":representative" 0 ":estimated" 1 ":synthesized" 0 ":authoritative" 2})

(defn rows-to-obs
  "A 'rows' ingest object → list of :compute.obs maps. G1-gated by sources/admissible?.
  Mirrors ingest.py rows_to_obs exactly."
  [obj]
  (let [source    (get obj "source")
        publisher (get obj "publisher" "")
        access    (get obj "access")]
    (when-not (src/admissible? publisher access)
      (throw (ex-info (str "refused (G1): publisher " (pr-str publisher)
                           "/access " (pr-str access)
                           " is not an admissible public source "
                           "(Charter Rider §2(e)+§2(c)). Read the press release, never the terminal.")
                      {:publisher publisher :access access})))
    (vec
     (for [r (get obj "rows" [])]
       (let [sid     (get r "series")
             year    (int (get r "year"))
             raw-src (get r "sourcing" "authoritative")
             sourcing (str ":" (str/replace raw-src #"^:+" ""))]
         {":compute.obs/id"      (str "obs." sid "." year)
          ":compute.obs/series"  sid
          ":compute.obs/year"    year
          ":compute.obs/value"   (double (get r "value"))
          ":compute.obs/source"  source
          ":compute.obs/method"  (get r "method" "")
          ":compute.obs/sourcing" sourcing})))))

(defn offline-ingest
  "Bridge any data/ingest/*.json ('rows'-shaped); collect new series + obs.
  Returns [series obs]. With no ingest files present → [[] []]."
  []
  (let [ingest-dir (io/file (actor-root) "data" "ingest")]
    (if-not (.isDirectory ingest-dir)
      [[] []]
      (reduce
       (fn [[series obs] f]
         (let [obj (json/parse-string (slurp f))
               new-series (get obj "series" [])
               new-obs    (rows-to-obs obj)]
           [(concat series new-series) (concat obs new-obs)]))
       [[] []]
       (sort-by #(.getName %)
                (filter #(str/ends-with? (.getName %) ".json")
                        (.listFiles ingest-dir)))))))

(defn fetch-epoch-gate
  "G7 outward gate: returns refusal string if KASA_OPERATOR_GATE != '1', else nil.
  Pure fn (takes the env value) so the test exercises it without process-env mutation."
  [env-gate]
  (when (not= (str env-gate) "1")
    (str "refused: live fetch requires KASA_OPERATOR_GATE=1 (G7 Council+operator). "
         "Offline mode reads data/ingest/*.json.")))

(defn fetch-epoch
  "LIVE Epoch AI notable-models CSV fetch — G7-gated, single polite request, CC-BY source.
  Returns [[] []] (parse is R1). Exits with error if gate not set."
  []
  (when-let [msg (fetch-epoch-gate (System/getenv "KASA_OPERATOR_GATE"))]
    (println msg)
    (System/exit 2))
  ;; Gate is open — R0: prove the gated path; parse into rows-JSON is R1.
  (let [url "https://epoch.ai/data/notable_ai_models.csv"]
    (println (str "kasa ingest: fetching Epoch AI CC-BY dataset from " url " ..."))
    ;; Would use clojure.java.io/reader with a URL; R0 just proves path:
    (println "kasa ingest: fetch is R1 (parse step). Place a rows-shaped file in data/ingest/ to bridge.")
    [[] []]))

(defn- row-sourcing
  "Extract the sourcing string from a row (checking both :compute.obs/sourcing and
  :compute.series/sourcing), returning nil if not found."
  [row]
  (or (get row ":compute.obs/sourcing")
      (get row ":compute.series/sourcing")))

(defn- row-id
  "Extract the id from a row, checking :compute.series/id, :compute.obs/id, :compute.source/id.
  Mirrors ingest.py merge_with_seed id-key fallback exactly."
  [row]
  (or (get row ":compute.series/id")
      (get row ":compute.obs/id")
      (get row ":compute.source/id")))

(defn merge-with-seed
  "Merge ingested over the :representative/:estimated seed; more-authoritative wins on id.
  Reads seed via ke/read-file. Mirrors ingest.py merge_with_seed exactly."
  [series obs]
  (let [seed   (ke/read-file (str @SEED-PATH))
        ;; start by-id from seed (all rows)
        by-id  (reduce (fn [m row]
                         (let [rid (row-id row)]
                           (if rid (assoc m rid row) m)))
                       {} seed)]
    ;; overlay ingested rows (series + obs) using rank comparison
    (vals
     (reduce
      (fn [m row]
        (let [rid       (row-id row)
              old       (get m rid)
              new-rank  (get RANK (row-sourcing row) 0)
              old-rank  (get RANK (row-sourcing old) -1)]
          (if (or (nil? old) (>= new-rank old-rank))
            (assoc m rid row)
            m)))
      by-id
      (concat series obs)))))

(defn- edn-val
  "Format a value as EDN. Mirrors ingest.py _v."
  [v]
  (cond
    (string? v) (if (str/starts-with? v ":") v (str "\"" (str/replace v "\"" "\\\"") "\""))
    (true? v)   "true"
    (false? v)  "false"
    :else        (pr-str v)))

(defn main [& argv]
  (let [args (vec argv)
        fetch? (some #{"--fetch-epoch"} args)]
    (let [[series obs] (if fetch? (fetch-epoch) (offline-ingest))
          n (count obs)]
      (when-not fetch?
        (println (str "kasa ingest (offline): bridged " (count series)
                      " series · " n " obs from data/ingest/"
                      (when (zero? n) " (none present — seed is the graph; drop rows-JSON in data/ingest/)"))))
      (let [merged (merge-with-seed series obs)
            out    (io/file (actor-root) "data" "capacity.merged.kotoba.edn")]
        (spit out
              (str ";; kasa — merged compute-capacity graph (seed ⊕ ingested; authoritative wins). GENERATED by ingest.clj.\n["
                   (str/join "\n"
                             (map (fn [row]
                                    (str " {" (str/join " " (map (fn [[k v]] (str k " " (edn-val v))) row)) "}"))
                                  merged))
                   "\n]\n"))
        (println (str "  → data/capacity.merged.kotoba.edn (" (count merged) " rows). Run analyze.py on it for growth."))))))

(when (= *file* (System/getProperty "babashka.file"))
  (apply main *command-line-args*))
