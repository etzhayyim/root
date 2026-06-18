#!/usr/bin/env bb
;; Working Clojure port of methods/plan.py (composes the clj analyze core).
(ns watatsuna.methods.plan
  "watatsuna 綿津綱 — resilience → watatsumi cable-laying mission planner (ADR-2606012600).

  The 'watatsuna knows → watatsumi acts' link. Reads the cable graph, computes resilience
  (via analyze), and emits a watatsumi cable-laying MISSION PLAN tasking robot classes to make
  the network MORE robust:

    :lay-diverse-route  for single-cable landing stations (redundancy gaps)
    :pre-stage-repair   for high chokepoint-load straits (fast restoration)
    :monitor            for brittle systems (single charted chokepoint) — passive DAS

  CONSTITUTIONAL (G2 + watatsumi N8): every recommendation is REDUNDANCY or REPAIR or MONITOR.
  There is NO interdiction/cut output by construction — the plan can only ADD resilience.

  Run:  bb --classpath 20-actors 20-actors/watatsuna/methods/plan.clj"
  (:require [watatsuna.methods.analyze :as a]
            [clojure.java.io :as io]
            [clojure.string :as str]))

(def ^:private this-file *file*)
(defn- actor-root [] (-> this-file io/file .getAbsoluteFile .getParentFile .getParentFile))

;; watatsumi cable-laying fleet (N8-bound)
(def lay-route ["watatsumi.hibiki.survey" "watatsumi.tsuna-suki" "watatsumi.horinuki"
                "watatsumi.tsugite" "watatsumi.funamori.cable-ship"])
(def pre-stage ["watatsumi.tedori" "watatsumi.tsugite" "watatsumi.funamori.cable-ship"])
(def monitor-fleet ["watatsumi.kikimimi"])
(def TOP-CHOKES 4)

(defn- last-seg [s] (last (str/split (str s) #"\.")))

(defn build-plan
  "Returns the vector of :plan/* recommendation maps (resilience-only by construction)."
  [{:keys [cables stations]} an]
  (let [lay (for [s (sort-by (juxt #(- (get-in an [:station-capacity %])) str) (:redundancy-gap an))]
              (let [st (get stations s)]
                {:plan/id (str "plan.lay." (last-seg s))
                 :plan/kind :lay-diverse-route
                 :plan/target-station s
                 :plan/priority (get-in an [:station-capacity s])
                 :plan/rationale (str (get st :station/name s) " is served by a single cable — one "
                                      "fault isolates " (get-in an [:station-capacity s]) " Tbps. Lay a "
                                      "geographically diverse second landing.")
                 :plan/robots lay-route
                 :plan/n8-note "ADD a route; never remove one (N8)."}))
        top (take TOP-CHOKES (sort-by (juxt #(- (get-in an [:choke-load %])) str) (keys (:choke-load an))))
        repair (for [cp top]
                 {:plan/id (str "plan.repair." (name cp))
                  :plan/kind :pre-stage-repair
                  :plan/target-chokepoint (name cp)
                  :plan/priority (get-in an [:choke-load cp])
                  :plan/rationale (str (get-in an [:choke-load cp]) " Tbps across "
                                       (get-in an [:choke-count cp]) " cables depend on " (name cp)
                                       ". Pre-stage repair capability for fast restoration; route new "
                                       "builds diversely around it (cf. Bifrost avoiding the South China Sea).")
                  :plan/robots pre-stage
                  :plan/n8-note "REPAIR-ONLY staging; Tedori recovers faulted cable under logged G4 quorum."})
        monitor (for [c (sort-by (juxt #(get-in an [:cable-diversity %]) str) (keys cables))
                      :when (= (get-in an [:cable-diversity c]) 1)]
                  (let [cb (get cables c)]
                    {:plan/id (str "plan.monitor." (last-seg c))
                     :plan/kind :monitor
                     :plan/target-cable c
                     :plan/priority (or (:cable/design-capacity-tbps cb) 0.0)
                     :plan/rationale (str (get cb :cable/name c) " depends on a single charted "
                                          "chokepoint (brittle). Passive DAS watch on its own fibre "
                                          "for early warning.")
                     :plan/robots monitor-fleet
                     :plan/n8-note "Monitoring only; no location export beyond the cable's own route (G1)."}))]
    (vec (concat lay repair monitor))))

(defn render-md [recs]
  (str/join
   "\n"
   (concat
    ["# watatsuna 綿津綱 → watatsumi 綿津見 — resilience fleet plan" ""
     (str "> ADR-2606012600 · **redundancy + repair + monitor ONLY** (G2 + watatsumi N8). "
          "No interdiction output by construction. watatsuna knows; watatsumi acts.") ""
     (str "- recommendations: **" (count recs) "**") ""]
    (mapcat
     (fn [[kind title]]
       (let [group (filter #(= (:plan/kind %) kind) recs)]
         (when (seq group)
           (concat
            [(str "## " title) ""]
            (mapcat
             (fn [r]
               (let [tgt (or (:plan/target-station r) (:plan/target-chokepoint r) (:plan/target-cable r))
                     robots (str/join ", " (map last-seg (:plan/robots r)))]
                 [(str "- **" tgt "** _(priority " (:plan/priority r) ")_ — " (:plan/rationale r))
                  (str "  - fleet: `" robots "` · " (:plan/n8-note r))]))
             (sort-by (juxt #(- (:plan/priority %)) :plan/id) group))
            [""]))))
     [[:lay-diverse-route "Lay diverse route (close redundancy gaps)"]
      [:pre-stage-repair "Pre-stage repair (high chokepoint-load)"]
      [:monitor "Monitor brittle systems (DAS)"]])
    ["---"
     (str "*Generated by `watatsuna/methods/plan.clj`. HONEST: R0/R2 design-only — recommendations "
          "over a bounded `:representative` seed; no live tasking; real deployment is Council + "
          "operator gated. Fleet acts lay/bury/splice/repair/monitor only.*")
     ""])))

(defn render-edn [recs]
  (str/join
   "\n"
   (concat
    [";; watatsuna → watatsumi resilience fleet plan (GENERATED). :plan/* recommendations."
     ";; G2/N8: redundancy + repair + monitor ONLY. ADR-2606012600. DO NOT hand-edit."
     "["]
    (map #(str " " (pr-str %)) recs)
    ["]" ""])))

(defn main [& argv]
  (let [args (vec argv)
        out-idx (.indexOf args "--out")
        out-val (when (>= out-idx 0) (nth args (inc out-idx)))
        out (if out-val (io/file out-val) (io/file (actor-root) "out"))
        merged (io/file (actor-root) "data" "cable-graph.merged.kotoba.edn")
        graph (or (first (remove #(or (str/starts-with? % "--") (= % out-val)) args))
                  (if (.exists merged) (str merged)
                      (str (io/file (actor-root) "data" "seed-cable-graph.kotoba.edn"))))
        g (a/classify (a/load-edn graph))
        an (a/analyze g)
        recs (build-plan g an)
        by (fn [k] (count (filter #(= (:plan/kind %) k) recs)))]
    (.mkdirs out)
    (spit (io/file out "resilience-plan.md") (render-md recs))
    (spit (io/file out "resilience-plan.kotoba.edn") (render-edn recs))
    (println (format "watatsuna plan: %d recommendations (%d lay-route · %d pre-stage-repair · %d monitor)"
                     (count recs) (by :lay-diverse-route) (by :pre-stage-repair) (by :monitor)))))

(when (= *file* (System/getProperty "babashka.file"))
  (apply main *command-line-args*))
