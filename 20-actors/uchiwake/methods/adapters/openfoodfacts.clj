;; openfoodfacts.clj — uchiwake 内訳 Open Food Facts → kotoba datom normalizer.
;;
;; Clojure port of adapters/openfoodfacts.py (ADR-2606081800), Wave 2 of the clj-native migration
;; (ADR-2606142300). The first concrete BULK-INGEST adapter: turns Open Food Facts product records
;; (CC-BY-SA, ~3M+ real food/beverage trade items, each a real GTIN + brand + ingredient list) into
;; uchiwake :product / :material / :bom.edge datoms. The LIVE network fetch of the full OFF dump
;; stays G7/operator-gated; this module operates on a LOCAL file/fixture and is import-safe.
;;
;; HONESTY (G5): OFF is crowd-sourced → every emitted datom is :sourcing :representative (never
;; :authoritative). The GTIN is validated against the GS1 mod-10 check digit; a record with a
;; bad/missing check digit is SKIPPED, not admitted. Ingredient percentages become bounded
;; :bom.edge/qty "%mass" estimates, never a confidential recipe. Reuses the canonical `.cljc`
;; uchiwake.methods.uchiwake-edn GTIN helpers. stdlib + uchiwake-edn only.
(ns uchiwake.methods.adapters.openfoodfacts
  (:require [uchiwake.methods.uchiwake-edn :as ue]
            [clojure.string :as str])
  (:import [java.math BigDecimal RoundingMode]))

;; OFF ingredient id (en:sugar) → canonical uchiwake material id (conservative; unknowns slugify).
(def ^:private mat-alias
  {"en:sugar" "mat.sugar" "en:sucrose" "mat.sugar"
   "en:water" "mat.water"
   "en:cocoa" "mat.cocoa" "en:cocoa-butter" "mat.cocoa" "en:fat-reduced-cocoa" "mat.cocoa"
   "en:hazelnut" "mat.hazelnut" "en:hazelnuts" "mat.hazelnut"
   "en:palm-oil" "mat.palm-oil" "en:palm-fat" "mat.palm-oil"
   "en:skimmed-milk-powder" "mat.milk-powder" "en:milk" "mat.milk-powder"
   "en:carbon-dioxide" "mat.co2"})

(def ^:private mat-name
  {"mat.sugar" "Sugar (sucrose)" "mat.water" "Water" "mat.cocoa" "Cocoa"
   "mat.hazelnut" "Hazelnut" "mat.palm-oil" "Palm oil" "mat.milk-powder" "Skim milk powder"
   "mat.co2" "Carbon dioxide (food grade)"})

(defn- slug [s]
  (let [base    (-> (str s) str/lower-case (str/split #":") last)
        cleaned (-> (str/replace (str base) #"[^a-z0-9]+" "-") (str/replace #"^-+|-+$" ""))]
    (if (str/blank? cleaned) "unknown" cleaned)))

(defn- round2 [x]
  (.doubleValue (.setScale (BigDecimal/valueOf (double x)) 2 RoundingMode/HALF_EVEN)))

(defn material-for
  "Return [material-id material-datom] for an OFF ingredient map."
  [ingredient]
  (let [iid (or (get ingredient "id") "")]
    (if (contains? mat-alias iid)
      (let [mid (mat-alias iid)]
        [mid {":material/id" mid
              ":material/name" (get mat-name mid (or (get ingredient "text") mid))
              ":material/kind" ":agricultural" ":material/sourcing" ":representative"}])
      (let [mid (str "mat." (slug (if (str/blank? iid) (or (get ingredient "text") "unknown") iid)))]
        [mid {":material/id" mid
              ":material/name" (or (get ingredient "text") (slug iid))
              ":material/kind" ":agricultural" ":material/sourcing" ":representative"}]))))

(defn normalize-record
  "One OFF record → vector of datom maps, or [] if the GTIN is invalid (skipped, G5)."
  [rec]
  (let [raw (str/trim (str (or (get rec "code") "")))]
    (if (or (str/blank? raw) (not (ue/gtin-check-digit-ok raw)))
      []
      (let [gtin14  (ue/normalize-gtin raw)
            pid     (str "gtin." gtin14)
            digits  (apply str (filter #(Character/isDigit ^char %) raw))
            fmt     (get {8 ":gtin-8" 12 ":gtin-12" 13 ":gtin-13" 14 ":gtin-14"} (count digits) ":gtin-13")
            brand   (str/trim (first (str/split (str (or (get rec "brands") "")) #",")))
            product {":product/id" pid ":product/gtin" gtin14 ":product/gtin-format" fmt
                     ":product/name" (or (get rec "product_name") pid)
                     ":product/brand" (if (str/blank? brand) "(unknown)" brand)
                     ":product/gs1-prefix" (subs digits 0 (min 3 (count digits)))
                     ":product/sector" ":food-beverage" ":product/sourcing" ":representative"}]
        (loop [ings (or (get rec "ingredients") []) seen #{} out [product]]
          (if (empty? ings)
            out
            (let [ing  (first ings)
                  [mid mdat] (material-for ing)
                  out1 (if (seen mid) out (conj out mdat))
                  pct  (get ing "percent_estimate")
                  edge (cond-> {":bom.edge/id" (str "bom." gtin14 "." (last (str/split mid #"\.")))
                                ":bom.edge/parent" pid ":bom.edge/child" mid ":bom.edge/tier" 1
                                ":bom.edge/criticality" 0.3 ":bom.edge/sourcing" ":representative"}
                         (number? pct) (assoc ":bom.edge/qty" (round2 pct) ":bom.edge/qty-unit" "%mass"))]
              (recur (rest ings) (conj seen mid) (conj out1 edge)))))))))

(defn normalize-dataset
  "Normalize many OFF records; dedup materials by id across the dataset (first wins). Returns
   [datoms stats] with stats {:products-ok :skipped-bad-gtin :materials}."
  [records]
  (loop [recs records out [] mat-ids #{} n-ok 0 n-skip 0]
    (if (empty? recs)
      [out {:products-ok n-ok :skipped-bad-gtin n-skip :materials (count mat-ids)}]
      (let [ds (normalize-record (first recs))]
        (if (empty? ds)
          (recur (rest recs) out mat-ids n-ok (inc n-skip))
          (let [[out2 mat2] (reduce (fn [[o m] d]
                                      (if (contains? d ":material/id")
                                        (if (m (get d ":material/id")) [o m]
                                            [(conj o d) (conj m (get d ":material/id"))])
                                        [(conj o d) m]))
                                    [out mat-ids] ds)]
            (recur (rest recs) out2 mat2 (inc n-ok) n-skip)))))))

(defn to-edn
  "Serialize normalized datoms to an EDN vector literal (1:1 with openfoodfacts.py _to_edn)."
  [datoms]
  (let [val (fn [v] (cond (boolean? v) (if v "true" "false")
                          (and (string? v) (str/starts-with? v ":")) v
                          (string? v) (ue/edn-str v)
                          :else v))]
    (str (str/join "\n"
           (concat [";; uchiwake — datoms normalized from Open Food Facts (CC-BY-SA). :representative (G5)."
                    ";; ADR-2606081800. GTINs validated by GS1 mod-10; LIVE OFF fetch is G7-gated." "["]
                   (map (fn [d] (str " {" (str/join " " (map (fn [[k v]] (str k " " (val v))) d)) "}")) datoms)
                   ["]"]))
         "\n")))
