;; crosscheck.clj — uchiwake 内訳 ⇄ kabuto coverage-linkage crosscheck.
;;
;; Clojure port of crosscheck.py (ADR-2606081800), Wave 2 of the clj-native migration
;; (ADR-2606142300) — the first uchiwake method ported beyond the already-`.cljc` uchiwake-edn /
;; analyze. Reuses the canonical `uchiwake.methods.uchiwake-edn` (load-edn + classify); this is a
;; clj-side data tool (reads disk seeds), so it is `.clj` rather than `.cljc`.
;;
;; uchiwake's product graph references companies by kabuto :company/id in the shared org.corp.*
;; space. This MEASURES — does not claim — how much of that graph wires into kabuto's ingested
;; company universe, and surfaces the gap honestly (an unresolved ref = "not yet ingested in
;; kabuto", NOT "does not exist"; G5). It also reports the 子会社 OWNERSHIP-ROLLUP effect (a
;; brand-owner subsidiary not itself in kabuto but whose ULTIMATE parent is) and the REVERSE
;; coverage (what fraction of kabuto's supply-chain companies have product-level BOM detail) +
;; a prioritized ingest worklist. stdlib + uchiwake-edn only.
(ns uchiwake.methods.crosscheck
  (:require [uchiwake.methods.uchiwake-edn :as ue]
            [clojure.set :as set]
            [clojure.java.io :as io])
  (:import [java.math BigDecimal RoundingMode]))

(def default-seed "20-actors/uchiwake/data/seed-products.kotoba.edn")
(def default-kabuto-seed "20-actors/kabuto/data/seed-public-companies.kotoba.edn")

(defn- round-n [x scale]
  (.doubleValue (.setScale (BigDecimal/valueOf (double x)) (int scale) RoundingMode/HALF_EVEN)))

(defn load-kabuto
  "Return [company-ids out-degree] or [nil nil] if the kabuto seed is absent. A :company/id row is
   a company; a :supply.edge/from row contributes an out-edge (supplier centrality)."
  [path]
  (if-not (.isFile (io/file path))
    [nil nil]
    (reduce (fn [[ids od] r]
              (cond
                (not (map? r))                  [ids od]
                (contains? r ":company/id")     [(conj ids (get r ":company/id")) od]
                (contains? r ":supply.edge/from") [ids (update od (get r ":supply.edge/from") (fnil inc 0))]
                :else                           [ids od]))
            [#{} {}]
            (ue/load-edn path))))

(defn uchiwake-covered-companies
  "Set of kabuto company ids that have ANY product-level detail in uchiwake."
  [g]
  (into #{}
        (concat (keep #(get % ":product/brand-owner") (vals (:products g)))
                (keep #(get % ":bom.edge/supplier") (:bom g))
                (keep #(get % ":process.step/operator") (:process g))
                (keep #(get % ":logistics.leg/carrier") (:logistics g)))))

(defn collect-company-refs
  "Ordered [[kind [[ref-id holder-id] …]] …] for every company reference in the graph (kind order
   mirrors crosscheck.py: brand-owner → bom-supplier → process-operator → logistics-carrier →
   ownership-child → ownership-parent)."
  [g]
  [["brand-owner"       (vec (keep (fn [[pid p]] (when-let [bo (get p ":product/brand-owner")] [bo pid])) (:products g)))]
   ["bom-supplier"      (vec (keep (fn [e] (when-let [s (get e ":bom.edge/supplier")] [s (get e ":bom.edge/id")])) (:bom g)))]
   ["process-operator"  (vec (keep (fn [s] (when-let [op (get s ":process.step/operator")] [op (get s ":process.step/id")])) (:process g)))]
   ["logistics-carrier" (vec (keep (fn [l] (when-let [c (get l ":logistics.leg/carrier")] [c (get l ":logistics.leg/id")])) (:logistics g)))]
   ["ownership-child"   (vec (map (fn [o] [(get o ":company.ownership/child") (get o ":company.ownership/id")]) (:ownership g)))]
   ["ownership-parent"  (vec (map (fn [o] [(get o ":company.ownership/parent") (get o ":company.ownership/id")]) (:ownership g)))]])

(defn- ultimate
  "Follow ownership child→parent edges to the topmost parent (cycle/depth guarded)."
  [own-index cid]
  (loop [c cid d 0]
    (let [nxt (get own-index c)]
      (if (or (nil? nxt) (= nxt c) (> d 16)) c (recur nxt (inc d))))))

(defn crosscheck
  "Measure uchiwake⇄kabuto linkage + reverse coverage. Returns the summary map."
  ([] (crosscheck default-seed default-kabuto-seed))
  ([seed-path kabuto-path]
   (let [g          (ue/classify (ue/load-edn seed-path))
         [kabuto-ids out-degree] (load-kabuto kabuto-path)
         refs       (collect-company-refs g)
         own-index  (into {} (map (fn [o] [(get o ":company.ownership/child") (get o ":company.ownership/parent")]) (:ownership g)))
         all-refs   (into #{} (mapcat (fn [[_ items]] (map first items)) refs))
         resolved   (if kabuto-ids (set/intersection all-refs kabuto-ids) #{})
         by-kind    (into {} (for [[kind items] refs]
                               [kind {:total (count items)
                                      :resolved (count (filter (fn [[r _]] (and kabuto-ids (kabuto-ids r))) items))}]))
         rollup     (vec (for [[kind items] refs
                               [ref-id _]   items
                               :when        (and kabuto-ids (not (kabuto-ids ref-id)))
                               :let         [up (ultimate own-index ref-id)]
                               :when        (and (not= up ref-id) (kabuto-ids up))]
                           {:ref ref-id :ultimate up :kind kind}))
         base       {:kabuto-available (some? kabuto-ids)
                     :kabuto-company-count (if kabuto-ids (count kabuto-ids) 0)
                     :by-kind by-kind
                     :rollup-recovered rollup
                     :distinct-company-refs (count all-refs)
                     :distinct-resolved (count resolved)
                     :linkage-pct (round-n (/ (* 100.0 (count resolved)) (max 1 (count all-refs))) 1)
                     :unresolved (vec (sort (set/difference all-refs resolved)))}]
     (if (nil? kabuto-ids)
       base
       (let [covered        (set/intersection (uchiwake-covered-companies g) kabuto-ids)
             supply-cos     (set (keys out-degree))
             covered-supply (set/intersection covered supply-cos)]
         (assoc base :reverse
                {:kabuto-supply-companies (count supply-cos)
                 :with-product-detail (count covered-supply)
                 :reverse-pct (round-n (/ (* 100.0 (count covered-supply)) (max 1 (count supply-cos))) 3)
                 :all-company-coverage-pct (round-n (/ (* 100.0 (count covered)) (max 1 (count kabuto-ids))) 3)
                 :worklist (->> out-degree
                                (sort-by val >)
                                (remove (fn [[c _]] (covered c)))
                                (take 15)
                                (mapv (fn [[c d]] {:company c :supply-out-degree d})))}))))))
