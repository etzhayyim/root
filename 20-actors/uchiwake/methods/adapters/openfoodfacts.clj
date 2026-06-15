#!/usr/bin/env bb
;; uchiwake 内訳 — Open Food Facts → kotoba datom normalizer (babashka port). ADR-2606081800.
;;
;; Turns Open Food Facts product records (CC-BY-SA open dataset) into uchiwake
;; :product / :material / :bom.edge datoms. HONESTY (G5): every emitted datom is
;; :sourcing :representative (crowd-sourced data). GTIN validated against GS1 mod-10;
;; bad/missing check digit records are SKIPPED. Ingredient percentages → bounded
;; :bom.edge/qty "%mass" estimates (never a manufacturer's confidential recipe).
;;
;; Usage:
;;   bb --classpath 20-actors 20-actors/uchiwake/methods/adapters/openfoodfacts.clj [file.json] [--out merged.edn]
;;   # default input: ../../data/ingest/openfoodfacts.sample.json (relative to adapter)
(ns uchiwake.methods.adapters.openfoodfacts
  (:require [uchiwake.methods.uchiwake-edn :as ue]
            [cheshire.core :as json]
            [clojure.java.io :as io]
            [clojure.string :as str]))

(def ^:private this-file *file*)

(defn- actor-root
  "20-actors/uchiwake dir (two levels up from adapters/)."
  []
  (-> this-file io/file .getAbsoluteFile .getParentFile .getParentFile .getParentFile))

(defn- default-in []
  (io/file (actor-root) "data" "ingest" "openfoodfacts.sample.json"))

;; ── material alias map (OFF ingredient id → canonical uchiwake material id) ──
(def ^:private mat-alias
  {"en:sugar"               "mat.sugar"
   "en:sucrose"             "mat.sugar"
   "en:water"               "mat.water"
   "en:cocoa"               "mat.cocoa"
   "en:cocoa-butter"        "mat.cocoa"
   "en:fat-reduced-cocoa"   "mat.cocoa"
   "en:hazelnut"            "mat.hazelnut"
   "en:hazelnuts"           "mat.hazelnut"
   "en:palm-oil"            "mat.palm-oil"
   "en:palm-fat"            "mat.palm-oil"
   "en:skimmed-milk-powder" "mat.milk-powder"
   "en:milk"                "mat.milk-powder"
   "en:carbon-dioxide"      "mat.co2"})

(def ^:private mat-name
  {"mat.sugar"       "Sugar (sucrose)"
   "mat.water"       "Water"
   "mat.cocoa"       "Cocoa"
   "mat.hazelnut"    "Hazelnut"
   "mat.palm-oil"    "Palm oil"
   "mat.milk-powder" "Skim milk powder"
   "mat.co2"         "Carbon dioxide (food grade)"})

;; ── helpers ───────────────────────────────────────────────────────────────────
(defn- slug
  "Slugify: take the part after the last ':', lowercase, replace non-alphanum with '-'."
  [s]
  (let [tail (last (str/split (str/lower-case (str s)) #":"))
        clean (str/replace tail #"[^a-z0-9]+" "-")
        trimmed (str/replace clean #"^-+|-+$" "")]
    (if (seq trimmed) trimmed "unknown")))

(defn- round2
  "Round to 2 decimal places (mirrors Python round(x, 2))."
  [x]
  (/ (Math/round (* (double x) (Math/pow 10 2))) (Math/pow 10 2)))

(defn material-for
  "Return [material-id material-datom] for an OFF ingredient map (string keys)."
  [ing]
  (let [iid  (str (get ing "id" ""))
        mid  (if (contains? mat-alias iid)
               (mat-alias iid)
               (str "mat." (slug (if (seq iid) iid (get ing "text" "unknown")))))
        name (if (contains? mat-alias iid)
               (get mat-name mid (get ing "text" mid))
               (or (get ing "text") (slug iid)))]
    [mid {":material/id"       mid
          ":material/name"     name
          ":material/kind"     ":agricultural"
          ":material/sourcing" ":representative"}]))

(defn normalize-record
  "One OFF record (string-keyed map) → list of datom maps, or [] if GTIN is invalid."
  [rec]
  (let [raw (str/trim (str (get rec "code" "")))]
    (if (or (str/blank? raw) (not (ue/gtin-check-digit-ok? raw)))
      []
      (let [gtin14  (ue/normalize-gtin raw)
            pid     (str "gtin." gtin14)
            digits  (apply str (filter #(Character/isDigit ^char %) raw))
            fmt     (get {8 ":gtin-8" 12 ":gtin-12" 13 ":gtin-13" 14 ":gtin-14"}
                         (count digits) ":gtin-13")
            brand   (str/trim (first (str/split (str (get rec "brands" "")) #",")))
            product {":product/id"          pid
                     ":product/gtin"        gtin14
                     ":product/gtin-format" fmt
                     ":product/name"        (or (get rec "product_name") pid)
                     ":product/brand"       (if (seq brand) brand "(unknown)")
                     ":product/gs1-prefix"  (subs digits 0 3)
                     ":product/sector"      ":food-beverage"
                     ":product/sourcing"    ":representative"}
            ings    (get rec "ingredients" [])
            ;; collect material datoms + bom edges, deduping mat ids
            [mat-datoms edge-datoms]
            (reduce (fn [[mats edges seen-mat] ing]
                      (let [[mid mdat] (material-for ing)
                            mats'  (if (contains? seen-mat mid) mats (conj mats mdat))
                            seen'  (conj seen-mat mid)
                            pct    (get ing "percent_estimate")
                            edge   (cond-> {":bom.edge/id"          (str "bom." gtin14 "." (last (str/split mid #"\.")))
                                            ":bom.edge/parent"      pid
                                            ":bom.edge/child"       mid
                                            ":bom.edge/tier"        1
                                            ":bom.edge/criticality" 0.3
                                            ":bom.edge/sourcing"    ":representative"}
                                     (number? pct)
                                     (assoc ":bom.edge/qty"      (round2 (double pct))
                                            ":bom.edge/qty-unit" "%mass"))]
                        [mats' (conj edges edge) seen']))
                    [[] [] #{}]
                    ings)]
        (concat [product] mat-datoms edge-datoms)))))

(defn normalize-dataset
  "Normalize many OFF records; dedup materials by id (first wins).
  Returns [datom-list stats-map]."
  [records]
  (let [[out mat-ids n-ok n-skip]
        (reduce (fn [[out mat-ids n-ok n-skip] rec]
                  (let [ds (normalize-record rec)]
                    (if (empty? ds)
                      [out mat-ids n-ok (inc n-skip)]
                      (let [[out' mat-ids']
                            (reduce (fn [[acc mids] d]
                                      (if (contains? d ":material/id")
                                        (if (contains? mids (get d ":material/id"))
                                          [acc mids]
                                          [(conj acc d) (conj mids (get d ":material/id"))])
                                        [(conj acc d) mids]))
                                    [out mat-ids]
                                    ds)]
                        [out' mat-ids' (inc n-ok) n-skip]))))
                [[] #{} 0 0]
                records)]
    [out {"products_ok"       n-ok
          "skipped_bad_gtin"  n-skip
          "materials"         (count mat-ids)}]))

;; ── EDN serialiser ────────────────────────────────────────────────────────────
(defn- edn-str
  "EDN-escape a string into a quoted EDN string literal."
  [s]
  (str "\"" (-> (str s) (str/replace "\\" "\\\\") (str/replace "\"" "\\\"")) "\""))

(defn- val->edn [v]
  (cond
    (boolean? v)                 (if v "true" "false")
    (and (string? v)
         (str/starts-with? v ":")) v
    (string? v)                  (edn-str v)
    :else                        (str v)))

(defn to-edn
  "Serialise datom list to an EDN string."
  [datoms]
  (let [header [";; uchiwake — datoms normalized from Open Food Facts (CC-BY-SA). :representative (G5)."
                ";; ADR-2606081800. GTINs validated by GS1 mod-10; LIVE OFF fetch is G7-gated."
                "["]
        rows   (map (fn [d]
                      (str " {" (str/join " " (map (fn [[k v]] (str k " " (val->edn v))) d)) "}"))
                    datoms)
        footer ["]" ""]]
    (str/join "\n" (concat header rows footer))))

;; ── main ──────────────────────────────────────────────────────────────────────
(defn main [& argv]
  (let [args       (vec argv)
        positional (remove #(str/starts-with? % "--") args)
        inp        (if (seq positional)
                     (io/file (first positional))
                     (default-in))
        raw        (json/parse-string (slurp inp))
        records    (if (map? raw) (get raw "products" []) raw)
        [datoms stats] (normalize-dataset records)
        _          (binding [*out* *err*]
                     (println (format "OFF normalize: %d products, %d materials, %d skipped (bad/missing GTIN)"
                                      (get stats "products_ok")
                                      (get stats "materials")
                                      (get stats "skipped_bad_gtin"))))
        edn        (to-edn datoms)
        out-idx    (.indexOf args "--out")]
    (if (>= out-idx 0)
      (spit (io/file (nth args (inc out-idx))) edn)
      (print edn))))

(when (= *file* (System/getProperty "babashka.file"))
  (apply main *command-line-args*))
