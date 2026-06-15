#!/usr/bin/env bb
;; Working Clojure port of methods/analyze.py (replaces the failed unit_refactor cljc stub).
(ns watari.methods.analyze
  "watari 渡り — live moving-craft (ship + aircraft) situational analyzer (ADR-2606041827).

  Reads a kotoba-EDN moving-craft graph (:craft/* identities, :craft.fix/* append-only position
  fixes, :craft.leg/* voyages/flights, :lane/* density units) and emits an AGGREGATE-FIRST
  situational report + derived :movement/* datoms. The canonical 'current position' of a craft
  is the LATEST :craft.fix (max observed-at; ISO-8601 sorts lexically). The fix set IS the
  trajectory (非終末論 — appended, never overwritten).

  CONSTITUTIONAL (Charter Rider §2(a) force-separation + §2(d); mirrors watatsuna G2): a
  SITUATIONAL-AWARENESS map, NEVER a person-surveillance feed and NEVER a targeting feed. Lanes/
  chokepoints are ranked by live concentration so traffic is made SAFER + more resilient — it does
  NOT follow a named individual, build pattern-of-life, or identify where to intercept. A craft is
  a craft, not a person (G4). The chokepoint-transit output composes with watatsuna's STATIC
  cable-load over the SAME chokepoint keywords (静↔動).

  Run:  bb --classpath 20-actors 20-actors/watari/methods/analyze.clj"
  (:require [clojure.java.io :as io]
            [clojure.edn :as edn]
            [clojure.string :as str]))

(def ^:private this-file *file*)
(defn- actor-root [] (-> this-file io/file .getAbsoluteFile .getParentFile .getParentFile))

(defn load-edn [path] (edn/read-string (slurp (io/file path))))

(defn classify [rows]
  (reduce
   (fn [out r]
     (if-not (map? r)
       out
       (cond
         (:craft/id r)     (assoc-in out [:craft (:craft/id r)] r)
         (:craft.fix/id r) (update out :fixes conj r)
         (:craft.leg/id r) (update out :legs conj r)
         (:lane/id r)      (assoc-in out [:lanes (:lane/id r)] r)
         :else out)))
   {:craft {} :fixes [] :legs [] :lanes {}}
   rows))

(defn analyze [{:keys [craft fixes legs lanes]}]
  (let [ts-of (fn [fx] (or (:craft.fix/observed-at fx) ""))
        latest (reduce (fn [m fx]
                         (let [c (:craft.fix/craft fx)]
                           (if (or (not (contains? m c)) (pos? (compare (ts-of fx) (ts-of (m c)))))
                             (assoc m c fx) m)))
                       {} fixes)
        dataset-latest (reduce (fn [mx fx] (if (pos? (compare (ts-of fx) mx)) (ts-of fx) mx)) "" fixes)
        kind-of (into {} (map (fn [[c m]] [c (:craft/kind m)]) craft))
        lane-craft (reduce (fn [m [c fx]]
                             (if-let [ln (:craft.fix/lane fx)] (update m ln (fnil conj #{}) c) m))
                           {} latest)
        lane-kind (reduce (fn [m [c fx]]
                            (if-let [ln (:craft.fix/lane fx)]
                              (update-in m [ln (get kind-of c :unknown)] (fnil conj #{}) c) m))
                          {} latest)
        lane-load (into {} (map (fn [[ln cs]] [ln (count cs)]) lane-craft))
        choke-transit (reduce (fn [m [ln meta]]
                                (let [cp (:lane/chokepoint meta)]
                                  (if (and cp (lane-craft ln))
                                    (update m cp (fnil + 0) (count (lane-craft ln))) m)))
                              {} lanes)
        approach (into {} (for [[ln meta] lanes
                                :when (and (= (:lane/kind meta) :approach) (lane-load ln))]
                            [ln (lane-load ln)]))
        trail (frequencies (map :craft.fix/craft fixes))
        stale (sort (for [[c fx] latest :when (neg? (compare (ts-of fx) dataset-latest))] c))
        kind-count (frequencies (map #(get kind-of % :unknown) (keys craft)))]
    {:latest latest :dataset-latest dataset-latest :kind-of kind-of
     :lane-craft lane-craft :lane-kind lane-kind :lane-load lane-load
     :choke-transit choke-transit :approach approach :trail trail
     :stale stale :kind-count kind-count}))

(defn render-report [{:keys [craft fixes legs lanes]} a]
  (let [P str
        nv (get-in a [:kind-count :vessel] 0)
        na (get-in a [:kind-count :aircraft] 0)]
    (str/join
     "\n"
     (concat
      ["# watari 渡り — live moving-craft (ship + aircraft) situational report" ""
       (str "> ADR-2606041827 · **aggregate-first** · SITUATIONAL-AWARENESS map (NOT a "
            "person-surveillance feed, NOT a target-list; Charter Rider §2(a) force-separation "
            "+ §2(d); mirrors watatsuna G2). A craft is a craft, never a person (G4). "
            "All sourcing `:representative` — bounded illustrative seed, NOT live coverage.") ""
       (P "- craft: **" (count craft) "** (" nv " vessels · " na " aircraft)  ·  position fixes: **"
          (count fixes) "**  ·  lanes: **" (count lanes) "**  ·  legs: **" (count legs) "**")
       (P "- dataset latest observation: **" (:dataset-latest a) "**  ·  craft current as-of this "
          "instant: **" (- (count (:latest a)) (count (:stale a))) "** / " (count (:latest a))
          " (freshness tail: " (count (:stale a)) ")") ""
       "## Chokepoint transit — live vessel/craft concentration" ""
       (str "Distinct craft whose LATEST fix transits each maritime chokepoint. Composes with "
            "watatsuna's STATIC submarine-cable chokepoint load over the same keywords "
            "(ADR-2606012600). **Routed to safety + redundancy, never to interdiction.**") ""
       "| chokepoint | craft transiting now |" "|---|---:|"]
      (for [cp (sort-by (juxt #(- (get-in a [:choke-transit %])) str) (keys (:choke-transit a)))]
        (P "| `" cp "` | " (get-in a [:choke-transit cp]) " |"))
      ["" "## Lane / corridor load — live concentration" ""
       "| lane | kind | craft | vessels | aircraft |" "|---|---|---:|---:|---:|"]
      (for [ln (sort-by (juxt #(- (get-in a [:lane-load %])) str) (keys (:lane-load a)))]
        (let [meta (get lanes ln {})
              vk (count (get-in a [:lane-kind ln :vessel] #{}))
              ak (count (get-in a [:lane-kind ln :aircraft] #{}))]
          (P "| " (get meta :lane/name ln) " | `" (get meta :lane/kind "?") "` | "
             (get-in a [:lane-load ln]) " | " vk " | " ak " |")))
      ["" "## Port / airport approach congestion" ""
       "Craft holding in an approach lane — routed to congestion-easing + safety. NEVER a targeting output." ""]
      (if (seq (:approach a))
        (concat ["| approach | craft holding |" "|---|---:|"]
                (for [ln (sort-by (juxt #(- (get-in a [:approach %])) str) (keys (:approach a)))]
                  (P "| " (get-in lanes [ln :lane/name] ln) " | " (get-in a [:approach ln]) " |")))
        ["- (none in seed)"])
      ["" "## Freshness tail — craft NOT seen in the latest wave (honest gaps)" ""
       (str "Live coverage is never complete. These craft's latest fix predates the dataset latest; "
            "their position is stale, not current. No fabricated live coverage (G5).") ""]
      (if (seq (:stale a))
        (for [c (:stale a)]
          (let [fx (get-in a [:latest c]) cm (get craft c {})
                label (or (:craft/name cm) (:craft/callsign cm) c)]
            (P "- " label " — last seen " (or (:craft.fix/observed-at fx) "?")
               " (dataset latest " (:dataset-latest a) ")")))
        ["- (all craft current in seed)"])
      ["" "---"
       (str "*Generated by `watari/methods/analyze.clj`. HONEST: R0 bounded `:representative` seed; "
            "coordinates rounded to ~0.1°; timestamps illustrative, NOT a live capture. Live AIS + "
            "ADS-B ingest is G7 Council+operator gated. Public transponder broadcasts only; no "
            "person-tracking (G4).*") ""]))))

(defn render-datoms [{:keys [craft lanes]} a]
  (str/join
   "\n"
   (concat
    [";; watari — DERIVED movement-situation datoms (ADR-2606041827). :derived — NOT fact."
     ";; Recomputed from the seed graph; do not re-ingest as :authoritative." "["]
    (for [cp (sort-by (juxt #(- (get-in a [:choke-transit %])) str) (keys (:choke-transit a)))]
      (format " {:movement/chokepoint %s :movement/chokepoint-transit %d :movement/derived true}"
              (pr-str cp) (get-in a [:choke-transit cp])))
    (for [ln (sort-by (juxt #(- (get-in a [:lane-load %])) str) (keys (:lane-load a)))]
      (format " {:movement/lane %s :movement/lane-load %d :movement/vessels %d :movement/aircraft %d :movement/derived true}"
              (pr-str ln) (get-in a [:lane-load ln])
              (count (get-in a [:lane-kind ln :vessel] #{})) (count (get-in a [:lane-kind ln :aircraft] #{}))))
    (for [c (sort (:stale a))]
      (format " {:movement/craft %s :movement/stale true :movement/last-seen %s :movement/derived true}"
              (pr-str c) (pr-str (or (:craft.fix/observed-at (get-in a [:latest c])) ""))))
    ["]" ""])))

(defn main [& argv]
  (let [args (vec argv)
        out-idx (.indexOf args "--out")
        out-val (when (>= out-idx 0) (nth args (inc out-idx)))
        out (if out-val (io/file out-val) (io/file (actor-root) "out"))
        seed (or (first (remove #(or (str/starts-with? % "--") (= % out-val)) args))
                 (str (io/file (actor-root) "data" "seed-craft-graph.kotoba.edn")))
        g (classify (load-edn seed))
        a (analyze g)]
    (.mkdirs out)
    (spit (io/file out "intel-report.md") (render-report g a))
    (spit (io/file out "movement-situation.kotoba.edn") (render-datoms g a))
    (println (format "watari: %d craft (%d vessels, %d aircraft), %d fixes, %d lanes; latest %s"
                     (count (:craft g)) (get-in a [:kind-count :vessel] 0)
                     (get-in a [:kind-count :aircraft] 0) (count (:fixes g)) (count (:lanes g))
                     (:dataset-latest a)))
    (let [top (take 3 (sort-by (comp - val) (:choke-transit a)))]
      (when (seq top)
        (println (str "top chokepoint transit: "
                      (str/join ", " (map (fn [[cp n]] (str cp " " n)) top))))))
    (println (format "freshness tail: %d craft stale" (count (:stale a))))))

(when (= *file* (System/getProperty "babashka.file"))
  (apply main *command-line-args*))
