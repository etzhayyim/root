#!/usr/bin/env bb
;; Working Clojure port of methods/ingest.py.
(ns uchiwake.methods.ingest
  "uchiwake 内訳 — product / GTIN / BOM ingestion bridge (offline default; live G7-gated).

  ADR-2606081800. Bridges public product-data sources into the kotoba Datom log as
  :product/:part/:material/:bom.edge/:process.step/:logistics.leg/:design.ref/
  :company.ownership datoms, dedup-merged with the bounded real seed (seed wins on id).

  GATES enforced here:
    G1  public trade items + public-record data only; no confidential recipes/terms.
    G5  every emitted datom carries :*/sourcing; bridged data defaults :representative.
    G7  live full-universe fetch requires UCHIWAKE_OPERATOR_GATE=1 (Council + operator).
        Default is OFFLINE: bridge data/ingest/*.json if present, else just the seed.
    no-server-key: read-only. uchiwake never holds a GS1/GLEIF write credential.

  Imports:
    uchiwake.methods.uchiwake-edn — load-edn, classify, normalize-gtin, gtin-check-digit-ok?
    uchiwake.methods.adapters.openfoodfacts — normalize-dataset (for OFF-shaped JSON files)

  Run:  bb --classpath 20-actors 20-actors/uchiwake/methods/ingest.clj
        UCHIWAKE_OPERATOR_GATE=1 bb --classpath 20-actors 20-actors/uchiwake/methods/ingest.clj --live"
  (:require [uchiwake.methods.uchiwake-edn :as ue]
            [uchiwake.methods.adapters.openfoodfacts :as off]
            [cheshire.core :as json]
            [clojure.java.io :as io]
            [clojure.string :as str]))

(def ^:private this-file *file*)
(defn- actor-root [] (-> this-file io/file .getAbsoluteFile .getParentFile .getParentFile))

;; ── ID-extraction helpers ─────────────────────────────────────────────────────

(def ^:private kw-id-keys
  "The ordered list of uchiwake entity id keys — keyword form (seed rows use real Clojure keywords)."
  [:product/id :part/id :material/id :bom.edge/id
   :process.step/id :logistics.leg/id :design.ref/id :company.ownership/id])

(def ^:private str-id-keys
  "String-keyed variants of the same id keys — used by the OFF adapter which emits string keys."
  (mapv #(str ":" (namespace %) "/" (name %)) kw-id-keys))

(defn- record-id
  "Return the first id-typed value found in a datom map.
  Handles both keyword-keyed maps (seed rows) and string-keyed maps (OFF adapter output)."
  [r]
  (or (some #(get r %) kw-id-keys)
      (some #(get r %) str-id-keys)))

(defn seed-id-set
  "Build the set of all id values present in the seed rows (for dedup seed-wins merge)."
  [rows]
  (reduce (fn [s r]
            (if-not (map? r)
              s
              (if-let [id (record-id r)]
                (conj s id)
                s)))
          #{}
          rows))

;; ── OFF-adapter normalization: string-keyed datom maps → keyword datoms ──────
;;
;; The OFF adapter (openfoodfacts.clj) emits string-keyed maps (":product/id" etc.)
;; so the EDN serialiser can output EDN keyword literals.  We need keyword-keyed maps
;; for the seed dedup merge (the seed loads with real Clojure keywords).  This small
;; shim converts one datom either direction.

(defn- str-keys->kw
  "Convert string-keyed datom {:\":product/id\" \"x\" …} → keyword-keyed {:product/id \"x\" …}.
  Values that are EDN keyword-strings like \":representative\" are keywordified too."
  [m]
  (reduce-kv
   (fn [out k v]
     (let [kw (keyword (str/replace (str k) #"^:" ""))
           vv (if (and (string? v) (str/starts-with? v ":"))
                (keyword (str/replace v #"^:" ""))
                v)]
       (assoc out kw vv)))
   {}
   m))

;; ── Core bridge: offline merge ────────────────────────────────────────────────

(defn bridge-offline
  "Merge any data/ingest/*.json bridged datoms with the seed (seed wins on id).
  Returns [seed-rows bridged-datoms] — same shape as ingest.py bridge_offline()."
  []
  (let [seed-path  (io/file (actor-root) "data" "seed-products.kotoba.edn")
        ingest-dir (io/file (actor-root) "data" "ingest")
        seed-rows  (ue/load-edn seed-path)
        seed-ids   (seed-id-set seed-rows)
        bridged
        (if-not (.isDirectory ingest-dir)
          []
          (reduce
           (fn [acc f]
             (let [fname (.getName f)]
               (cond
                 ;; Open Food Facts files → route through OFF adapter (GTIN-validated)
                 (str/starts-with? fname "openfoodfacts")
                 (let [raw     (json/parse-string (slurp f))
                       recs    (if (map? raw) (get raw "products" []) raw)
                       [datoms stats] (off/normalize-dataset recs)
                       _       (binding [*out* *err*]
                                 (println (format "  OFF adapter %s: %d products, %d materials, %d skipped"
                                                  fname
                                                  (get stats "products_ok")
                                                  (get stats "materials")
                                                  (get stats "skipped_bad_gtin"))))]
                   ;; OFF adapter emits string-keyed maps; convert to keyword-keyed for dedup
                   (into acc
                         (keep (fn [d]
                                 (let [r (str-keys->kw d)
                                       rid (record-id r)]
                                   (when-not (and rid (contains? seed-ids rid))
                                     r)))
                               datoms)))

                 ;; Generic datom-shaped JSON (list of datom maps or {:datoms [...]})
                 (str/ends-with? fname ".json")
                 (let [doc  (json/parse-string (slurp f) true)
                       rows (if (vector? doc) doc (get doc :datoms []))]
                   (into acc
                         (keep (fn [r]
                                 ;; validate GTIN check digit before admitting a product datom (G5 honesty)
                                 (when (or (not (:product/gtin r))
                                           (ue/gtin-check-digit-ok? (str (:product/gtin r))))
                                   (let [rid (record-id r)]
                                     (when-not (and rid (contains? seed-ids rid))
                                       (cond-> r
                                         (and (:product/id r) (not (:product/sourcing r)))
                                         (assoc :product/sourcing :representative))))))
                               rows)))

                 :else acc)))
           []
           (sort-by #(.getName %) (.listFiles ingest-dir))))]
    [seed-rows bridged]))

;; ── G7 gate ───────────────────────────────────────────────────────────────────

(defn live-refusal
  "G7 outward gate: returns the refusal message if --live is requested without the operator gate, else nil."
  [argv env-gate]
  (when (some #{"--live"} argv)
    (if (not= (str env-gate) "1")
      (str "REFUSED (G7): live full-universe GS1/GLEIF ingest requires "
           "UCHIWAKE_OPERATOR_GATE=1 + Council authorization. Running offline instead.")
      (str "G7 gate satisfied — live ingest would run here (GS1 GDSN / GLEIF RR / "
           "Open Product Data). Not wired in R0; falling back to offline bridge."))))

;; ── EDN serialiser ────────────────────────────────────────────────────────────

(defn- val->edn
  "Serialize a single datom value to an EDN literal string."
  [v]
  (cond
    (boolean? v)  (if v "true" "false")
    (keyword? v)  (str v)
    (string? v)   (str "\"" (-> v (str/replace "\\" "\\\\") (str/replace "\"" "\\\"")) "\"")
    :else         (str v)))

(defn emit-bridged-edn
  "Serialize bridged keyword-keyed datom maps to EDN map literals (one per line)."
  [datoms]
  (str/join "\n"
            (concat [" ;; ── bridged datoms (offline adapters; :representative, G5) ──"]
                    (map (fn [d]
                           (str " {" (str/join " " (map (fn [[k v]] (str k " " (val->edn v))) d)) "}"))
                         datoms))))

;; ── main ──────────────────────────────────────────────────────────────────────

(defn main [& argv]
  (let [args (vec argv)]
    ;; G7 gate — print refusal/gate message if --live is present, then continue offline
    (when-let [msg (live-refusal args (System/getenv "UCHIWAKE_OPERATOR_GATE"))]
      (binding [*out* *err*] (println msg)))
    (let [[seed-rows bridged] (bridge-offline)
          g        (ue/classify seed-rows)
          seed-txt (slurp (io/file (actor-root) "data" "seed-products.kotoba.edn"))
          merged-p (io/file (actor-root) "data" "products.merged.kotoba.edn")]
      (println (format "seed: %d products, %d parts, %d materials, %d BOM edges, %d ownership edges"
                       (count (:products g))
                       (count (:parts g))
                       (count (:materials g))
                       (count (:bom g))
                       (count (:ownership g))))
      (println (format "bridged (offline data/ingest/*.json): %d new datoms" (count bridged)))
      (if (seq bridged)
        (let [block (emit-bridged-edn bridged)
              cut   (str/last-index-of (str/trim-newline seed-txt) "]")
              merged (str (subs seed-txt 0 cut) "\n" block "\n]\n")]
          (spit merged-p merged)
          (println (str "→ " (.getPath merged-p) " (seed + " (count bridged) " bridged datoms)")))
        (do
          (spit merged-p seed-txt)
          (println (str "→ " (.getPath merged-p) " (== seed; no external ingest)")))))))

(when (= *file* (System/getProperty "babashka.file"))
  (apply main *command-line-args*))
