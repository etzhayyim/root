#!/usr/bin/env bb
;; Working Clojure port of methods/analyze.py (replaces the failed unit_refactor stub).
(ns uchiwake.methods.analyze
  "uchiwake 内訳 — global product bill-of-materials concentration analyzer (ADR-2606081800).

  Reads a kotoba-EDN product graph (:product/* GTIN trade items, :part/*, :material/*,
  :bom.edge/* parent→child edges, :process.step/*, :logistics.leg/*, :company.ownership/*
  子会社→parent) and emits an AGGREGATE-FIRST resilience report + derived concentration datoms
  (flagged :concentration/derived true — a uchiwake OBSERVATION, never re-ingested as fact).

  CONSTITUTIONAL (G2/G4): a supply-chain RESILIENCE + corporate-power TRANSPARENCY map, NEVER
  a target-list and NEVER a clone/counterfeit recipe. Concentration is ranked so makers can
  DIVERSIFY and the public can hold concentration accountable. uchiwake does not adjudicate.

  Run:  bb --classpath 20-actors 20-actors/uchiwake/methods/analyze.clj
        -> out/intel-report.md + out/product-criticality.kotoba.edn"
  (:require [uchiwake.methods.uchiwake-edn :as e]
            [clojure.java.io :as io]
            [clojure.string :as str]))

(def ^:private this-file *file*)
(defn- actor-root [] (-> this-file io/file .getAbsoluteFile .getParentFile .getParentFile))

(defn resolve-ultimate-parent
  "Follow ownership edges up to the topmost parent. Cycle/depth guarded."
  ([company-id ownership-index] (resolve-ultimate-parent company-id ownership-index 0))
  ([company-id ownership-index depth]
   (if (or (nil? company-id) (> depth 16))
     company-id
     (let [parent (get ownership-index company-id)]
       (if (or (nil? parent) (= parent company-id))
         company-id
         (recur parent ownership-index (inc depth)))))))

(defn- bom-children-index [bom]
  (group-by :bom.edge/parent bom))

(defn all-materials-reachable
  "Recursively collect every mat.* id reachable from a product/part via BOM edges."
  ([node-id child-idx] (all-materials-reachable node-id child-idx #{} 0))
  ([node-id child-idx seen depth]
   (if (or (contains? seen node-id) (> depth 24))
     #{}
     (let [seen (conj seen node-id)]
       (reduce
        (fn [mats edge]
          (let [child (:bom.edge/child edge)]
            (cond
              (nil? child) mats
              (str/starts-with? child "mat.") (conj mats child)
              :else (into mats (all-materials-reachable child child-idx seen (inc depth))))))
        #{}
        (get child-idx node-id []))))))

(defn- pct [x] (format "%.0f%%" (* (double x) 100.0)))
(defn- round4 [x] (/ (Math/round (* (double x) 10000.0)) 10000.0))

(defn analyze
  "Return {:report-md str :derived [datom-maps]} for a seed graph path."
  [seed-path]
  (let [g (e/classify (e/load-edn seed-path))
        {:keys [products parts materials bom process logistics ownership]} g
        child-idx (bom-children-index bom)
        ownership-index (into {} (map (juxt :company.ownership/child :company.ownership/parent) ownership))
        with-gtin (filter :product/gtin (vals products))
        n-prod (max 1 (count products))
        ;; 1. material dependence
        mat->products (reduce (fn [m pid]
                                (reduce (fn [m mat] (update m mat (fnil conj #{}) pid))
                                        m (all-materials-reachable pid child-idx)))
                              {} (keys products))
        ;; 2. process-country load
        country-steps (frequencies (keep :process.step/country process))
        n-steps (max 1 (reduce + (vals country-steps)))
        ;; 3. ultimate-parent rollup
        parent-products (reduce (fn [m [pid p]]
                                  (if-let [bo (:product/brand-owner p)]
                                    (update m (resolve-ultimate-parent bo ownership-index)
                                            (fnil conj #{}) pid)
                                    m))
                                {} products)
        parent-denom (max 1 (if (seq with-gtin) (count with-gtin) (count products)))
        ;; 4. high-criticality edges
        hot (->> bom (filter #(>= (or (:bom.edge/criticality %) 0) 0.8))
                 (sort-by #(- (or (:bom.edge/criticality %) 0))))
        derived (atom [])
        emit! (fn [m] (swap! derived conj m))
        R (atom [])
        add (fn [& xs] (swap! R into xs))]
    (add "# uchiwake 内訳 — product bill-of-materials resilience report\n"
         (str "> ADR-2606081800. Aggregate-first RESILIENCE map, never a target-list (G2). "
              "BOM decompositions are :representative public estimates, not authoritative recipes (G5).\n")
         (format "- products (trade items): **%d**" (count products))
         (format "- parts / sub-assemblies: **%d**" (count parts))
         (format "- raw materials: **%d**" (count materials))
         (format "- BOM edges: **%d**" (count bom))
         (format "- process steps: **%d**" (count process))
         (format "- logistics legs: **%d**" (count logistics))
         (format "- ownership (子会社→parent) edges: **%d**\n" (count ownership))
         (format "## GTIN coverage\n\n%d/%d products carry a GTIN. Full coverage target = the GS1 GDSN universe (G7-gated).\n"
                 (count with-gtin) (count products))
         "## Material dependence (how many products trace down to each raw material)\n"
         "| material | products depending | share |" "|---|---:|---:|")
    (doseq [[mat pids] (sort-by (juxt (comp - count val)
                                      (fn [[m _]] (get-in materials [m :material/name] m)))
                                mat->products)]
      (let [share (/ (count pids) (double n-prod))
            name (get-in materials [mat :material/name] mat)]
        (add (format "| %s | %d | %s |" name (count pids) (pct share)))
        (emit! {:concentration/id (str "conc.mat." mat) :concentration/dimension :material
                :concentration/key mat :concentration/share (round4 share)
                :concentration/count (count pids) :concentration/derived true})))
    (add "\n## Processing-jurisdiction load (where production steps cluster)\n"
         "| country | process steps | share |" "|---|---:|---:|")
    (doseq [[c n] (sort-by (juxt (comp - val) key) country-steps)]
      (let [share (/ n (double n-steps))]
        (add (format "| %s | %d | %s |" c n (pct share)))
        (emit! {:concentration/id (str "conc.procctry." c) :concentration/dimension :process-country
                :concentration/key c :concentration/share (round4 share)
                :concentration/count n :concentration/derived true})))
    (add "\n## Brand-owner concentration (subsidiaries rolled up to ultimate parent — 子会社)\n"
         "| ultimate parent | products | rolled-up from subsidiary? |" "|---|---:|:--:|")
    (doseq [[parent pids] (sort-by (juxt (comp - count val) key) parent-products)]
      (let [rolled (boolean (some #(not= (resolve-ultimate-parent
                                          (:product/brand-owner (products %)) ownership-index)
                                         (:product/brand-owner (products %))) pids))]
        (add (format "| %s | %d | %s |" parent (count pids) (if rolled "yes" "no")))
        (emit! {:concentration/id (str "conc.parent." parent) :concentration/dimension :ultimate-parent
                :concentration/key parent :concentration/share (round4 (/ (count pids) (double parent-denom)))
                :concentration/count (count pids) :concentration/derived true})))
    (add "\n## High-criticality (single-source-risk) BOM edges — diversification candidates\n"
         "| parent | child | criticality | disclosed supplier |" "|---|---|---:|---|")
    (doseq [edge hot]
      (add (format "| %s | %s | %.2f | %s |"
                   (:bom.edge/parent edge) (:bom.edge/child edge)
                   (double (or (:bom.edge/criticality edge) 0)) (or (:bom.edge/supplier edge) "—"))))
    {:report-md (str (str/join "\n" @R) "\n") :derived @derived}))

(defn derived->edn [derived]
  (str/join
   "\n"
   (concat
    [";; uchiwake 内訳 — DERIVED concentration datoms. ADR-2606081800."
     ";; :concentration/derived true — a uchiwake OBSERVATION, never re-ingested as fact." "["]
    (map #(str " " (pr-str %)) derived)
    ["]" ""])))

(defn main [& argv]
  (let [args (vec argv)
        out-idx (.indexOf args "--out")
        out-val (when (>= out-idx 0) (nth args (inc out-idx)))
        out (if out-val (io/file out-val) (io/file (actor-root) "out"))
        positionals (remove #(or (str/starts-with? % "--") (= % out-val)) args)
        seed (or (first positionals)
                 (str (io/file (actor-root) "data" "seed-products.kotoba.edn")))
        {:keys [report-md derived]} (analyze seed)]
    (.mkdirs out)
    (spit (io/file out "intel-report.md") report-md)
    (spit (io/file out "product-criticality.kotoba.edn") (derived->edn derived))
    (println (format "uchiwake: → out/intel-report.md + out/product-criticality.kotoba.edn (%d derived datoms)"
                     (count derived)))))

(when (= *file* (System/getProperty "babashka.file"))
  (apply main *command-line-args*))
