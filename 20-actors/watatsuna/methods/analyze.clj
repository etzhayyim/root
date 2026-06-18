#!/usr/bin/env bb
;; Working Clojure port of methods/analyze.py (replaces the failed unit_refactor cljc stub).
(ns watatsuna.methods.analyze
  "watatsuna 綿津綱 — submarine-cable network resilience analyzer (ADR-2606012600).

  Reads a kotoba-EDN cable graph (:cable/* systems, :station/* landing stations, :cable.link/*
  incidence, :cable.seg/* chokepoint-traversing segments, :cable.fault/* observed bulletins)
  and emits an AGGREGATE-FIRST resilience report + derived :resilience/* datoms (flagged
  :derived, never re-ingested as authoritative fact).

  CONSTITUTIONAL (watatsumi N8 + Charter Rider §2(d)): a RESILIENCE map, NEVER a target-list.
  Chokepoints are ranked by fragility so the network can be made MORE robust (diverse routes,
  pre-staged repair) — it does NOT identify where to cut. Sabotage intent is never asserted;
  fault :kind mirrors only the public bulletin's own classification (the Python tokenizer is
  replaced by clojure.edn — keywords read natively).

  Run:  bb --classpath 20-actors 20-actors/watatsuna/methods/analyze.clj"
  (:require [clojure.java.io :as io]
            [clojure.edn :as edn]
            [clojure.string :as str]))

(def ^:private this-file *file*)
(defn- actor-root [] (-> this-file io/file .getAbsoluteFile .getParentFile .getParentFile))
(defn- round2 [x] (/ (Math/round (* (double x) 100.0)) 100.0))

(defn load-edn [path] (edn/read-string (slurp (io/file path))))

(defn classify
  "Bucket a flat datom vector into cable/station/link/seg/fault entities."
  [rows]
  (reduce
   (fn [out r]
     (if-not (map? r)
       out
       (cond
         (:cable/id r)       (assoc-in out [:cables (:cable/id r)] r)
         (:station/id r)     (assoc-in out [:stations (:station/id r)] r)
         (:cable.link/id r)  (update out :links conj r)
         (:cable.seg/id r)   (update out :segs conj r)
         (:cable.fault/id r) (update out :faults conj r)
         :else out)))
   {:cables {} :stations {} :links [] :segs [] :faults []}
   rows))

(defn analyze [{:keys [cables stations links segs]}]
  (let [cap (into {} (map (fn [[id c]] [id (or (:cable/design-capacity-tbps c) 0.0)]) cables))
        ;; per-station: which cables land here
        station-cables (reduce (fn [m lk]
                                 (update m (:cable.link/station lk) (fnil conj #{}) (:cable.link/cable lk)))
                               {} links)
        sc (fn [s] (get station-cables s #{}))
        station-degree (into {} (map (fn [s] [s (count (sc s))]) (keys stations)))
        station-capacity (into {} (map (fn [s] [s (round2 (reduce + 0.0 (map #(get cap % 0.0) (sc s))))])
                                       (keys stations)))
        ;; per-chokepoint: distinct cables traversing it (via segments) + via station tags
        choke-cables (as-> {} m
                       (reduce (fn [m sg]
                                 (reduce (fn [m cp] (update m cp (fnil conj #{}) (:cable.seg/cable sg)))
                                         m (or (:cable.seg/traverses sg) [])))
                               m segs)
                       (reduce (fn [m [s meta]]
                                 (reduce (fn [m cp]
                                           (reduce (fn [m c] (update m cp (fnil conj #{}) c))
                                                   m (sc s)))
                                         m (or (:station/chokepoint meta) [])))
                               m stations))
        choke-load (into {} (map (fn [[cp cs]] [cp (round2 (reduce + 0.0 (map #(get cap % 0.0) cs)))]) choke-cables))
        choke-count (into {} (map (fn [[cp cs]] [cp (count cs)]) choke-cables))
        ;; per-cable diversity: # distinct chokepoints it depends on (lower = more brittle)
        cable-chokes (reduce (fn [m [cp cs]] (reduce (fn [m c] (update m c (fnil conj #{}) cp)) m cs))
                             {} choke-cables)
        cable-diversity (into {} (map (fn [c] [c (count (get cable-chokes c #{}))]) (keys cables)))
        redundancy-gap (sort (filter #(<= (station-degree %) 1) (keys stations)))]
    {:cap cap :station-cables station-cables :station-degree station-degree
     :station-capacity station-capacity :choke-cables choke-cables :choke-load choke-load
     :choke-count choke-count :cable-diversity cable-diversity :redundancy-gap redundancy-gap}))

(defn render-report [{:keys [cables stations links segs faults]} a]
  (let [P (fn [& xs] (apply str xs))
        total-design (round2 (reduce + 0.0 (vals (:cap a))))]
    (str/join
     "\n"
     (concat
      ["# watatsuna 綿津綱 — submarine-cable network resilience report"
       ""
       (str "> ADR-2606012600 · **aggregate-first** · RESILIENCE map (NOT a target-list; "
            "watatsumi N8 + Charter Rider §2(d)). Sabotage intent never asserted. "
            "All sourcing `:representative` — bounded illustrative seed, not exhaustive coverage.")
       ""
       (P "- cable systems: **" (count cables) "**  ·  landing stations: **" (count stations)
          "**  ·  cable↔station links: **" (count links) "**  ·  chokepoint segments: **"
          (count segs) "**  ·  observed faults: **" (count faults) "**")
       (P "- total seeded design capacity: **" total-design " Tbps**")
       ""
       "## Chokepoint concentration — single-point-of-failure surface"
       ""
       (str "Capacity (Σ design Tbps of distinct cables) that depends on each maritime "
            "chokepoint. Higher = more of the world's traffic shares one geographic fate. "
            "**Routed to redundancy + pre-staged repair, never to interdiction.**")
       ""
       "| chokepoint | cables | dependent capacity (Tbps) |"
       "|---|---:|---:|"]
      (for [cp (sort-by (juxt #(- (get-in a [:choke-load %])) str) (keys (:choke-load a)))]
        (P "| `" cp "` | " (get-in a [:choke-count cp]) " | " (get-in a [:choke-load cp]) " |"))
      ["" "## Landing-station hubs — convergence points" ""
       "| station | country | cables | landed capacity (Tbps) |"
       "|---|---|---:|---:|"]
      (for [s (sort-by (juxt #(- (get-in a [:station-degree %]))
                             #(- (get-in a [:station-capacity %])) str) (keys stations))
            :when (pos? (get-in a [:station-degree s]))]
        (P "| " (get-in stations [s :station/name] s) " | " (get-in stations [s :station/country] "?")
           " | " (get-in a [:station-degree s]) " | " (get-in a [:station-capacity s]) " |"))
      ["" "## Most brittle systems — low chokepoint diversity" ""
       (str "Cables depending on the fewest distinct chokepoints carry the highest "
            "correlated-failure risk; candidates for diverse-route augmentation.")
       ""
       "| cable | chokepoints depended on | design (Tbps) | RFS |"
       "|---|---:|---:|---:|"]
      (for [c (sort-by (juxt #(get-in a [:cable-diversity %]) #(- (get-in a [:cap %])) str) (keys cables))
            :when (pos? (get-in a [:cable-diversity c]))]
        (P "| " (get-in cables [c :cable/name] c) " | " (get-in a [:cable-diversity c]) " | "
           (get-in a [:cap c]) " | " (get-in cables [c :cable/rfs-year] "?") " |"))
      ["" "## Redundancy gaps — single-cable landing stations" ""]
      (if (seq (:redundancy-gap a))
        (for [s (:redundancy-gap a)]
          (P "- " (get-in stations [s :station/name] s) " ("
             (get-in stations [s :station/country] "?") ") — routed to redundancy"))
        ["- (none in seed)"])
      ["" "## Observed fault bulletins (Datom as-of history; 非終末論 — appended, never overwritten)" ""
       "| fault | cable | kind (bulletin's own) | detected | restored |"
       "|---|---|---|---|---|"]
      (for [f faults]
        (P "| `" (:cable.fault/id f) "` | "
           (get-in cables [(:cable.fault/cable f) :cable/name] (:cable.fault/cable f))
           " | `" (:cable.fault/kind f) "` | " (or (:cable.fault/detected-at f) "?")
           " | " (or (:cable.fault/restored-at f) "open") " |"))
      ["" "---"
       (str "*Generated by `watatsuna/methods/analyze.clj`. HONEST: R0 bounded seed; coordinates "
            "rounded to landing town; capacities are public design figures; chokepoint dependency "
            "is charted only for seeded segments. Live planet-scale ingest is G7 Council+operator gated.*")
       ""]))))

(defn render-datoms [{:keys [cables stations]} a]
  (str/join
   "\n"
   (concat
    [";; watatsuna — DERIVED resilience datoms (ADR-2606012600). :derived — NOT authoritative fact."
     ";; Recomputed from the seed graph; do not re-ingest as :authoritative."
     "["]
    (for [cp (sort-by (juxt #(- (get-in a [:choke-load %])) str) (keys (:choke-load a)))]
      (format " {:resilience/chokepoint %s :resilience/chokepoint-load %s :resilience/cable-count %d :resilience/derived true}"
              (pr-str cp) (get-in a [:choke-load cp]) (get-in a [:choke-count cp])))
    (for [s (sort-by (juxt #(- (get-in a [:station-degree %])) str) (keys stations))
          :when (pos? (get-in a [:station-degree s]))]
      (format " {:resilience/station %s :resilience/station-degree %d :resilience/station-capacity-tbps %s :resilience/derived true}"
              (pr-str s) (get-in a [:station-degree s]) (get-in a [:station-capacity s])))
    (for [c (sort-by (juxt #(get-in a [:cable-diversity %]) str) (keys cables))]
      (format " {:resilience/cable %s :resilience/cable-diversity %d :resilience/derived true}"
              (pr-str c) (get-in a [:cable-diversity c])))
    ["]" ""])))

(defn main [& argv]
  (let [args (vec argv)
        out-idx (.indexOf args "--out")
        out-val (when (>= out-idx 0) (nth args (inc out-idx)))
        out (if out-val (io/file out-val) (io/file (actor-root) "out"))
        seed (or (first (remove #(or (str/starts-with? % "--") (= % out-val)) args))
                 (str (io/file (actor-root) "data" "seed-cable-graph.kotoba.edn")))
        g (classify (load-edn seed))
        a (analyze g)]
    (.mkdirs out)
    (spit (io/file out "intel-report.md") (render-report g a))
    (spit (io/file out "cable-criticality.kotoba.edn") (render-datoms g a))
    (println (format "watatsuna: %d cables, %d stations, %d links, %d segments, %d faults"
                     (count (:cables g)) (count (:stations g)) (count (:links g))
                     (count (:segs g)) (count (:faults g))))
    (let [top (take 3 (sort-by (comp - val) (:choke-load a)))]
      (println (str "top chokepoints by dependent capacity: "
                    (str/join ", " (map (fn [[cp l]] (str cp " " l "Tbps")) top)))))))

(when (= *file* (System/getProperty "babashka.file"))
  (apply main *command-line-args*))
