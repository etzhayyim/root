#!/usr/bin/env bb
;; Working Clojure port of methods/crosscheck.py (the uchiwake⇄kabuto supply-chain linkage measure).
(ns uchiwake.methods.crosscheck
  "uchiwake 内訳 — kabuto coverage-linkage crosscheck (ADR-2606081800).

  uchiwake's product graph references companies (brand-owner, BOM supplier, process operator,
  logistics carrier, ownership parent/child) by kabuto :company/id in the shared org.corp.* space.
  This tool MEASURES — does not claim — how much of that product graph actually WIRES INTO kabuto's
  ingested company universe, and surfaces the gap honestly (an unresolved reference = 'not yet
  ingested in kabuto', NOT 'does not exist'; G5). It also reports the 子会社 ownership-rollup effect
  + the REVERSE coverage (what fraction of kabuto's supply-chain companies carry product-BOM
  detail) + a prioritized ingest worklist. The measured supply-chain integration % across actors.

  Run:  bb --classpath 20-actors 20-actors/uchiwake/methods/crosscheck.clj [--json]"
  (:require [uchiwake.methods.uchiwake-edn :as e]
            [clojure.java.io :as io]
            [clojure.set]
            [clojure.string :as str]))

(def ^:private this-file *file*)
(defn- actor-root [] (-> this-file io/file .getAbsoluteFile .getParentFile .getParentFile))
(defn- seed-path [] (io/file (actor-root) "data" "seed-products.kotoba.edn"))
(defn- kabuto-seed [] (io/file (actor-root) ".." "kabuto" "data" "seed-public-companies.kotoba.edn"))

(defn load-kabuto
  "Return [company-ids out-degree] or [nil nil] if the kabuto seed is absent."
  []
  (let [f (kabuto-seed)]
    (if-not (.isFile f)
      [nil nil]
      (reduce (fn [[ids od] r]
                (cond
                  (not (map? r)) [ids od]
                  (:company/id r) [(conj ids (:company/id r)) od]
                  (:supply.edge/from r) [ids (update od (:supply.edge/from r) (fnil inc 0))]
                  :else [ids od]))
              [#{} {}] (e/load-edn f)))))

(defn uchiwake-covered-companies
  "Set of kabuto company ids that have ANY product-level detail in uchiwake."
  [g]
  (-> #{}
      (into (keep :product/brand-owner (vals (:products g))))
      (into (keep :bom.edge/supplier (:bom g)))
      (into (keep :process.step/operator (:process g)))
      (into (keep :logistics.leg/carrier (:logistics g)))))

(defn collect-company-refs
  "Return {kind [[ref-id holder-id] …]} for every company reference in the graph."
  [g]
  (reduce
   (fn [refs [k v]] (if (seq v) (assoc refs k (vec v)) refs))
   {}
   {"brand-owner"      (for [[pid p] (:products g) :let [bo (:product/brand-owner p)] :when bo] [bo pid])
    "bom-supplier"     (for [edge (:bom g) :let [s (:bom.edge/supplier edge)] :when s] [s (:bom.edge/id edge)])
    "process-operator" (for [s (:process g) :let [op (:process.step/operator s)] :when op] [op (:process.step/id s)])
    "logistics-carrier" (for [lg (:logistics g) :let [c (:logistics.leg/carrier lg)] :when c] [c (:logistics.leg/id lg)])
    "ownership-child"  (for [o (:ownership g)] [(:company.ownership/child o) (:company.ownership/id o)])
    "ownership-parent" (for [o (:ownership g)] [(:company.ownership/parent o) (:company.ownership/id o)])}))

(defn- pct [num den d] (let [p (* 100.0 (/ num (double (max 1 den))))]
                         (/ (Math/round (* p (Math/pow 10 d))) (Math/pow 10 d))))

(defn crosscheck []
  (let [g (e/classify (e/load-edn (seed-path)))
        [kabuto-ids out-degree] (load-kabuto)
        refs (collect-company-refs g)
        own-idx (into {} (map (juxt :company.ownership/child :company.ownership/parent) (:ownership g)))
        ultimate (fn ultimate [cid d]
                   (if (or (nil? cid) (> d 16)) cid
                       (let [nxt (own-idx cid)] (if (or (nil? nxt) (= nxt cid)) cid (ultimate nxt (inc d))))))
        ;; per-kind resolution + rollup recovery
        init {:by-kind {} :all-refs #{} :resolved #{} :rollup []}
        acc (reduce
             (fn [a [kind items]]
               (let [a (reduce
                        (fn [a [ref-id _holder]]
                          (let [a (update a :all-refs conj ref-id)]
                            (cond
                              (and kabuto-ids (contains? kabuto-ids ref-id))
                              (update a :resolved conj ref-id)
                              kabuto-ids
                              (let [up (ultimate ref-id 0)]
                                (if (and (not= up ref-id) (contains? kabuto-ids up))
                                  (update a :rollup conj {:ref ref-id :ultimate up :kind kind})
                                  a))
                              :else a)))
                        a items)
                     resolved-here (count (filter #(and kabuto-ids (contains? kabuto-ids (first %))) items))]
                 (assoc-in a [:by-kind kind] {:total (count items) :resolved resolved-here})))
             init refs)
        distinct-refs (count (:all-refs acc))
        resolved-n (count (:resolved acc))
        base {:kabuto-available (some? kabuto-ids)
              :kabuto-company-count (if kabuto-ids (count kabuto-ids) 0)
              :by-kind (:by-kind acc) :rollup-recovered (:rollup acc)
              :distinct-company-refs distinct-refs :distinct-resolved resolved-n
              :linkage-pct (pct resolved-n distinct-refs 1)
              :unresolved (sort (clojure.set/difference (:all-refs acc) (:resolved acc)))}]
    (if (nil? kabuto-ids)
      base
      (let [covered (clojure.set/intersection (uchiwake-covered-companies g) kabuto-ids)
            supply (set (keys out-degree))
            covered-supply (clojure.set/intersection covered supply)]
        (assoc base :reverse
               {:kabuto-supply-companies (count supply)
                :with-product-detail (count covered-supply)
                :reverse-pct (pct (count covered-supply) (count supply) 3)
                :all-company-coverage-pct (pct (count covered) (count kabuto-ids) 3)
                :worklist (vec (take 15 (for [[c d] (sort-by (juxt (comp - val) key) out-degree)
                                              :when (not (covered c))]
                                          {:company c :supply-out-degree d})))})))))

(defn render [s]
  (if-not (:kabuto-available s)
    "# uchiwake ⇄ kabuto crosscheck\n\nkabuto seed not found — cannot crosscheck.\n"
    (str/join
     "\n"
     (concat
      ["# uchiwake ⇄ kabuto coverage-linkage crosscheck" ""
       "> Measured (not claimed) integration of the uchiwake product graph into kabuto's ingested"
       "> company universe. Unresolved = \"not yet ingested in kabuto\", not \"nonexistent\" (G5)." ""
       (str "- kabuto ingested companies: **" (:kabuto-company-count s) "**")
       (str "- distinct company refs in uchiwake: **" (:distinct-company-refs s) "**")
       (str "- resolved into kabuto: **" (:distinct-resolved s) "** (**" (:linkage-pct s) "%** linkage)" )
       "" "| reference kind | total | resolved |" "|---|---:|---:|"]
      (for [[kind v] (sort-by key (:by-kind s))]
        (str "| " kind " | " (:total v) " | " (:resolved v) " |"))
      (when-let [rev (:reverse s)]
        (concat
         ["" "## Reverse coverage — how much of kabuto has product-level BOM detail (情報取得割合)" ""
          (str "- kabuto supply-chain companies: **" (:kabuto-supply-companies rev) "**")
          (str "- of those, with ANY uchiwake product detail: **" (:with-product-detail rev)
               "** (**" (:reverse-pct rev) "%**)")
          (str "- across ALL " (:kabuto-company-count s) " kabuto companies: **"
               (:all-company-coverage-pct rev) "%** have product detail")]))
      [""]))))

(defn main [& argv]
  (let [s (crosscheck)]
    (if (some #{"--json"} argv)
      (println (pr-str s))
      (println (render s)))))

(when (= *file* (System/getProperty "babashka.file"))
  (require 'clojure.set)
  (apply main *command-line-args*))
