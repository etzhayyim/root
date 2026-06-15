#!/usr/bin/env bb
;; Working Clojure port of methods/analyze.py (replaces the failed unit_refactor cljc stub).
(ns kabuto.methods.analyze
  "kabuto 兜 — public-company supply-chain concentration analyzer (ADR-2606022000).

  Reads a kotoba-EDN company graph (:company/* + :supply.edge/* supplier→customer edges) and
  emits an AGGREGATE-FIRST resilience/accountability report + derived :supply/* datoms. Metrics:
  single-source dependencies, per-commodity HHI, jurisdiction/bloc load, supplier-sector
  diversification, supply-betweenness intermediaries, disclosed tier depth, cross-bloc corridors,
  composite resilience score, market-cap concentration.

  CONSTITUTIONAL (G2 + Charter Rider §2(d)): a resilience + corporate-power TRANSPARENCY map,
  NEVER a target-list. Single-source findings exist to be DIVERSIFIED, not exploited; kabuto does
  not adjudicate (G4). Concentration is an observation, never a verdict.

  Run:  bb --classpath 20-actors 20-actors/kabuto/methods/analyze.clj"
  (:require [kabuto.methods.kabuto-edn :as e]
            [clojure.java.io :as io]
            [clojure.set]
            [clojure.string :as str]))

(def ^:private this-file *file*)
(defn- actor-root [] (-> this-file io/file .getAbsoluteFile .getParentFile .getParentFile))
(defn- r2 [x] (/ (Math/round (* (double x) 100.0)) 100.0))
(defn- r3 [x] (/ (Math/round (* (double x) 1000.0)) 1000.0))
(defn- r1 [x] (/ (Math/round (* (double x) 10.0)) 10.0))

(def ^:private bloc-map
  {"JP" "East Asia" "KR" "East Asia" "CN" "East Asia" "TW" "East Asia" "HK" "East Asia" "MO" "East Asia"
   "US" "North America" "CA" "North America" "MX" "North America"
   "NL" "Europe" "DE" "Europe" "FR" "Europe" "CH" "Europe" "GB" "Europe" "IE" "Europe" "ES" "Europe"
   "IT" "Europe" "SE" "Europe" "FI" "Europe" "DK" "Europe" "NO" "Europe" "LU" "Europe" "PL" "Europe"
   "AT" "Europe" "PT" "Europe" "SI" "Europe" "HR" "Europe" "LT" "Europe" "IS" "Europe" "GR" "Europe"
   "CZ" "Europe" "HU" "Europe" "RO" "Europe"
   "IN" "South Asia" "BD" "South Asia" "PK" "South Asia" "LK" "South Asia"
   "SG" "SE Asia" "ID" "SE Asia" "TH" "SE Asia" "MY" "SE Asia" "VN" "SE Asia" "PH" "SE Asia"
   "SA" "Middle East" "AE" "Middle East" "QA" "Middle East" "KW" "Middle East" "BH" "Middle East"
   "OM" "Middle East" "JO" "Middle East" "IL" "Middle East" "TR" "Middle East"
   "BR" "Latin America" "CL" "Latin America" "CO" "Latin America" "AR" "Latin America"
   "PE" "Latin America" "PA" "Latin America"
   "ZA" "Africa" "NG" "Africa" "EG" "Africa" "KE" "Africa" "MA" "Africa" "CI" "Africa" "GH" "Africa"
   "AU" "Oceania" "NZ" "Oceania" "GE" "Eurasia" "KZ" "Eurasia"})
(defn- bloc [country] (get bloc-map country "Other"))

(defn- crit-of [e] (double (or (:supply.edge/criticality e) 0.0)))

(defn- tier-depths [in-deg nodes]
  (let [memo (atom {})]
    (letfn [(depth [node stack]
              (if (contains? @memo node)
                (@memo node)
                (if (stack node)
                  0
                  (let [sups (get in-deg node)]
                    (if (empty? sups)
                      (do (swap! memo assoc node 0) 0)
                      (let [d (inc (apply max (map #(depth % (conj stack node)) sups)))]
                        (swap! memo assoc node d) d))))))]
      (into {} (map (fn [n] [n (depth n #{})]) nodes)))))

(defn analyze [companies edges]
  (let [valid (filter #(and (:supply.edge/from %) (:supply.edge/to %)) edges)
        sec-of (fn [s] (get-in companies [s :company/sector] :unknown))
        ctry-of (fn [s] (get-in companies [s :company/country] "??"))
        in-deg (reduce (fn [m e] (update m (:supply.edge/to e) (fnil conj #{}) (:supply.edge/from e))) {} valid)
        out-deg (reduce (fn [m e] (update m (:supply.edge/from e) (fnil conj #{}) (:supply.edge/to e))) {} valid)
        ccs (reduce (fn [m e] (update m [(:supply.edge/to e) (or (:supply.edge/commodity e) :unknown)]
                                     (fnil conj []) [(:supply.edge/from e) (crit-of e)])) {} valid)
        systemic (reduce (fn [m e] (update m (:supply.edge/from e) (fnil + 0.0) (crit-of e))) {} valid)
        jurisdiction-load (reduce (fn [m e] (update m (ctry-of (:supply.edge/from e)) (fnil + 0.0) (crit-of e))) {} valid)
        bloc-load (reduce (fn [m e] (update m (bloc (ctry-of (:supply.edge/from e))) (fnil + 0.0) (crit-of e))) {} valid)
        ;; single-source
        single-source (->> ccs
                           (keep (fn [[[c commodity] sups]]
                                   (when (= 1 (count sups))
                                     (let [[sup crit] (first sups)]
                                       (when (>= crit 0.7) [c commodity sup crit])))))
                           (sort-by (juxt #(- (nth % 3)) str)))
        ;; diversification
        cust-supplier-sectors (reduce (fn [m e] (update m (:supply.edge/to e) (fnil conj #{}) (sec-of (:supply.edge/from e)))) {} valid)
        cust-in-crit (reduce (fn [m e] (update m (:supply.edge/to e) (fnil + 0.0) (crit-of e))) {} valid)
        diversification (->> cust-in-crit
                             (keep (fn [[c raw]]
                                     (let [load (r2 raw) secs (count (cust-supplier-sectors c))]
                                       (when (>= load 1.0)
                                         [c secs load (if (> load 0) (r3 (/ secs load)) 0.0)]))))
                             (sort-by (juxt #(nth % 3) str)))
        ;; intermediaries (nodes both customer and supplier)
        intermediaries (->> (clojure.set/intersection (set (keys in-deg)) (set (keys out-deg)))
                            (map (fn [n] (let [i (count (in-deg n)) o (count (out-deg n))] [n i o (* i o)])))
                            (sort-by (juxt #(- (nth % 3)) str)))
        ;; tier depth
        td (tier-depths in-deg (clojure.set/union (set (keys in-deg)) (set (keys out-deg))))
        tier-depth (->> td (filter (fn [[_ d]] (> d 0))) (sort-by (juxt #(- (val %)) key)) (mapv (fn [[n d]] [n d])))
        ;; per-commodity HHI
        commodity-supplier-crit (reduce (fn [m e]
                                          (let [crit (crit-of e) s (:supply.edge/from e)]
                                            (if (and s (> crit 0))
                                              (update-in m [(or (:supply.edge/commodity e) :unknown) s] (fnil + 0.0) crit) m)))
                                        {} valid)
        commodity-hhi (->> commodity-supplier-crit
                           (keep (fn [[commodity shares]]
                                   (let [tot (reduce + 0.0 (vals shares))]
                                     (when (> tot 0)
                                       [commodity (count shares) (r3 (reduce + 0.0 (map #(let [sh (/ % tot)] (* sh sh)) (vals shares))))]))))
                           (sort-by (juxt #(- (nth % 2)) str)))
        ;; cross-bloc
        all-total (reduce + 0.0 (map crit-of valid))
        cross (reduce (fn [m e]
                        (let [bs (bloc (ctry-of (:supply.edge/from e)))
                              bc (bloc (ctry-of (:supply.edge/to e)))]
                          (if (not= bs bc) (update m [bs bc] (fnil + 0.0) (crit-of e)) m)))
                      {} valid)
        cross-total (reduce + 0.0 (vals cross))
        cross-corridors (->> cross (map (fn [[[a b] v]] [(str a "→" b) v])) (sort-by (juxt #(- (second %)) first)))
        cross-share (if (> all-total 0) (r1 (* 100 (/ cross-total all-total))) 0.0)
        ;; resilience
        cust-single-cnt (frequencies (map first single-source))
        cust-cross-in (reduce (fn [m e]
                                (if (not= (bloc (ctry-of (:supply.edge/from e))) (bloc (ctry-of (:supply.edge/to e))))
                                  (update m (:supply.edge/to e) (fnil + 0.0) (crit-of e)) m)) {} valid)
        resilience (->> cust-in-crit
                        (keep (fn [[c load]]
                                (when (>= load 1.0)
                                  (let [secs (max 1 (count (cust-supplier-sectors c)))
                                        cross-frac (if (> load 0) (/ (get cust-cross-in c 0.0) load) 0.0)
                                        frag (+ (* (get cust-single-cnt c 0) 2) (/ load secs) cross-frac)
                                        score (r1 (/ 100.0 (+ 1.0 frag)))]
                                    [c score (get cust-single-cnt c 0) (count (cust-supplier-sectors c)) (r2 load) (r2 cross-frac)]))))
                        (sort-by (juxt second str)))
        ;; market-cap
        capped (->> companies
                    (keep (fn [[cid co]]
                            (let [mc (try (double (:company/market-cap-busd co)) (catch Exception _ nil))]
                              (when (and mc (> mc 0)) [cid mc (get co :company/sector :unknown)])))))
        sector-cap (reduce (fn [m [_ mc sec]] (update m sec (fnil + 0.0) mc)) {} capped)
        total-cap (reduce + 0.0 (map second capped))
        cap-hhi (if (> total-cap 0) (r3 (reduce + 0.0 (map #(let [sh (/ % total-cap)] (* sh sh)) (vals sector-cap)))) 0.0)]
    {:in-deg (into {} (map (fn [[k v]] [k (count v)]) in-deg))
     :out-deg (into {} (map (fn [[k v]] [k (count v)]) out-deg))
     :single-source (vec single-source)
     :jurisdiction-load jurisdiction-load
     :systemic systemic
     :bloc-load bloc-load
     :diversification (vec diversification)
     :intermediaries (vec intermediaries)
     :tier-depth tier-depth
     :commodity-hhi (vec commodity-hhi)
     :cross-corridors (vec cross-corridors)
     :cross-share cross-share
     :resilience (vec resilience)
     :sector-cap-rank (vec (sort-by (comp - val) sector-cap))
     :cap-hhi cap-hhi :total-cap (r1 total-cap) :cap-count (count capped)
     :cap-coverage (if (seq companies) (r1 (* 100 (/ (count capped) (count companies)))) 0.0)}))

(defn cname [companies cid] (get-in companies [cid :company/name] cid))

(defn render-report [{:keys [companies edges]} a]
  (str/join
   "\n"
   (concat
    ["# kabuto 兜 — public-company supply-chain concentration report" ""
     (str "> ADR-2606022000 · **aggregate-first** · resilience + accountability map (NOT a "
          "target-list; Charter Rider §2(d)). Single-source findings exist to be DIVERSIFIED, not "
          "exploited. kabuto does not adjudicate (G4). All supplier edges `:representative`.") ""
     (str "- companies: **" (count companies) "**  ·  disclosed supply edges: **" (count edges)
          "**  ·  single-source dependencies: **" (count (:single-source a)) "**  ·  cross-bloc share: **"
          (:cross-share a) "%**") ""
     "## Per-commodity supplier concentration (HHI — 1.0 = monopoly)" ""
     "| commodity | suppliers | HHI |" "|---|---:|---:|"]
    (for [[commodity n hhi] (take 20 (:commodity-hhi a))]
      (str "| " (str/replace (str commodity) #"^:" "") " | " n " | " hhi " |"))
    ["" "## Most brittle customers — supplier-sector diversification (lowest first)" ""
     "| customer | supplier-sectors | inbound-criticality | diversification-index |" "|---|---:|---:|---:|"]
    (for [[c secs load idx] (take 20 (:diversification a))]
      (str "| " (cname companies c) " | " secs " | " load " | " idx " |"))
    ["" "## Single-source dependencies — diversification candidates (never a target-list)" ""
     "| customer | commodity | sole supplier | criticality |" "|---|---|---|---:|"]
    (for [[c commodity sup crit] (take 30 (:single-source a))]
      (str "| " (cname companies c) " | " (str/replace (str commodity) #"^:" "") " | "
           (cname companies sup) " | " crit " |"))
    ["" "---"
     (str "*Generated by `kabuto/methods/analyze.clj`. HONEST: R0 bounded `:representative` seed; "
          "supplier edges disclosed/public, not an exhaustive BOM; criticality a bounded estimate, "
          "never a contract figure. Live GLEIF/EDGAR-universe ingest is G7 Council+operator gated.*") ""])))

(defn- es [s] (str "\"" (str/replace (str/replace (str s) "\\" "\\\\") "\"" "\\\"") "\""))

(defn render-datoms [companies a]
  (str/join
   "\n"
   (concat
    [";; kabuto — DERIVED supply-chain concentration datoms (ADR-2606022000). :derived — NOT fact."
     ";; Recomputed from the seed graph; do not re-ingest as :authoritative." "["]
    (for [[c commodity sup crit] (:single-source a)]
      (format " {:supply/single-source-customer %s :supply/commodity %s :supply/sole-supplier %s :supply/criticality %s :supply/derived true}"
              (es c) (es (str/replace (str commodity) #"^:" "")) (es sup) crit))
    (for [[country load] (sort-by (comp - val) (:jurisdiction-load a))]
      (format " {:supply/jurisdiction %s :supply/jurisdiction-load %s :supply/derived true}" (es country) (r2 load)))
    (for [[sup load] (sort-by (comp - val) (:systemic a))]
      (format " {:supply/systemic-supplier %s :supply/out-degree %d :supply/outward-criticality %s :supply/derived true}"
              (es sup) (get-in a [:out-deg sup] 0) (r2 load)))
    (for [[c secs load idx] (:diversification a)]
      (format " {:supply/diversification-customer %s :supply/supplier-sectors %d :supply/inbound-criticality %s :supply/diversification-index %s :supply/derived true}"
              (es c) secs load idx))
    (for [[n ind outd score] (:intermediaries a)]
      (format " {:supply/intermediary %s :supply/in-degree %d :supply/out-degree %d :supply/betweenness %d :supply/derived true}"
              (es n) ind outd score))
    (for [[n d] (:tier-depth a)]
      (format " {:supply/tier-depth-node %s :supply/tier-depth %d :supply/derived true}" (es n) d))
    (for [[commodity nsup hhi] (:commodity-hhi a)]
      (format " {:supply/commodity %s :supply/commodity-suppliers %d :supply/commodity-hhi %s :supply/derived true}"
              (es (str/replace (str commodity) #"^:" "")) nsup hhi))
    ["]" ""])))

(defn main [& argv]
  (let [args (vec argv)
        out-idx (.indexOf args "--out")
        out-val (when (>= out-idx 0) (nth args (inc out-idx)))
        out (if out-val (io/file out-val) (io/file (actor-root) "out"))
        seed (or (first (remove #(or (str/starts-with? % "--") (= % out-val)) args))
                 (str (io/file (actor-root) "data" "seed-public-companies.kotoba.edn")))
        g (e/classify (e/load-edn seed))
        a (analyze (:companies g) (:edges g))]
    (.mkdirs out)
    (spit (io/file out "intel-report.md") (render-report g a))
    (spit (io/file out "supply-criticality.kotoba.edn") (render-datoms (:companies g) a))
    (println (format "kabuto: %d companies, %d edges; %d single-source, %d commodities (HHI), cross-bloc %s%%"
                     (count (:companies g)) (count (:edges g)) (count (:single-source a))
                     (count (:commodity-hhi a)) (:cross-share a)))))

(when (= *file* (System/getProperty "babashka.file"))
  (require 'clojure.set)
  (apply main *command-line-args*))
