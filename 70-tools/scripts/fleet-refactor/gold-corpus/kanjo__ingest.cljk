;; ported from orgs/etzhayyim/com-etzhayyim-kanjo/methods/ingest.py (parse_edgar_companyfacts) — gold reference (Fable)
;; kanjō 勘定 — ingest cell: PRIMARY-disclosure (SEC EDGAR companyfacts) → kotoba EAVT 決算 facts。
;; us-gaap:* element を canonical concept へ正規化し、annual (fp="FY", form 10-K/20-F) を 1 fact/(concept,fy)。
;; 全 fact は :authoritative (primary disclosure)、非裁定。
;;
;; canonical / concept-stmt は呼び出し側注入 (concept_map の写し)。深いネストの map/filter/transform。
(ns kanjo.methods.ingest
  (:require [clojure.string :as str]))

(defn- annual-point? [p]
  (and (= (get p "fp") "FY")
       (contains? #{"10-K" "20-F"} (get p "form"))))

(defn- filing-of [org-id fy unit form filed accession end]
  (let [fid (str "fil.us.edgar." (last (str/split org-id #"\.")) "." fy)]
    [fid
     {:fin.filing/id fid
      :fin.filing/company org-id
      :fin.filing/source :edgar
      :fin.filing/form (keyword (or form "10-K"))
      :fin.filing/fiscal-year fy
      :fin.filing/period-type :annual
      :fin.filing/period-end end
      :fin.filing/filed-date (or filed "")
      :fin.filing/accession (or accession "")
      :fin.filing/currency (keyword (str/lower-case unit))
      :fin.filing/accounting :usgaap
      :fin.filing/sourcing :authoritative}]))

(defn parse-edgar-companyfacts
  "SEC EDGAR companyfacts JSON → {:facts […] :filings […]} (:authoritative)。
  obj[\"facts\"][\"us-gaap\"][Element][\"units\"][unit][ {end val fy fp form …} ]。
  canonical: (fn [element \"usgaap\"] → canon | nil)。concept-stmt: {canon → :pl/:bs/:cf}。"
  [obj org-id {:keys [canonical concept-stmt want-fy]}]
  (let [gaap (get-in obj ["facts" "us-gaap"] {})
        rows (for [[element body] gaap
                   :let [canon (canonical element "usgaap")]
                   :when canon
                   [unit points] (get body "units" {})
                   p points
                   :when (annual-point? p)
                   :let [fy (get p "fy")]
                   :when (or (nil? want-fy) (= fy want-fy))]
               (let [[fid filing] (filing-of org-id fy unit (get p "form")
                                             (get p "filed") (get p "accn")
                                             (get p "end" ""))]
                 {:filing [fid filing]
                  :fact {:fin.fact/filing fid
                         :fin.fact/concept canon
                         :fin.fact/statement (get concept-stmt canon :pl)
                         :fin.fact/value (get p "val")
                         :fin.fact/period-end (get p "end" "")
                         :fin.fact/sourcing :authoritative}}))]
    {:facts (mapv :fact rows)
     :filings (vec (vals (into {} (map :filing rows))))}))
