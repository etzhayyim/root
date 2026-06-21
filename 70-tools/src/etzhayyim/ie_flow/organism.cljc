(ns etzhayyim.ie-flow.organism
  "etzhayyim.ie-flow.organism — project the information-energy flow ledger into the /organism
  page. ADR-2606211200.

  The organism view already renders the colony's STRUCTURE (cells/vitals), live ACTIVITY (pulse),
  情緒 (joucho) and EVOLUTION (trajectory). This adds the fifth layer the IE-flow lifecycle measures:
  the *information-energy flow itself* — did the metabolism PAY FOR ITSELF (net-gain), and did it
  RECTIFY scattered free-energy into low-entropy structure returned to society (order-index /
  負エントロピー輸出)? It is a pure fold of the committed flow snapshot
  (`80-data/ie-flow/<source>/flow.kotoba.edn`) through `etzhayyim.ie-flow.{ledger,metrics}`,
  emitting `ieflow.json` into every served organism dir.

  clj/bb, deterministic (logical time = the snapshot's as-of), no network I/O, no held key — the
  same substrate discipline as vitals/pulse/joucho."
  (:require [clojure.java.io :as io]
            [clojure.edn :as edn]
            [cheshire.core :as json]
            [kotoba.datom :as kd]
            [etzhayyim.ie-flow.ledger :as ledger]
            [etzhayyim.ie-flow.metrics :as metrics]))

(def ^:private out-dirs
  ["60-apps/etzhayyim-project-organism/public"
   "50-infra/etzhayyim-did-web/public/organism"])

(def ^:private default-flow-log "80-data/ie-flow/repo-git/flow.kotoba.edn")
(def ^:private registry-path "80-data/ie-flow/registry.edn")
(def ^:private data-root "80-data/ie-flow")

(defn- jnum
  "JSON-safe number: ##Inf / ##-Inf / NaN → a display string (cheshire can't encode them)."
  [x]
  (let [d (double x)]
    (cond (Double/isInfinite d) (if (pos? d) "∞" "-∞")
          (Double/isNaN d) "—"
          :else d)))

(defn- nodes-of
  "Derive flow stations from the aggregated edges: each source/target with its in/out value &
  volume, and a kind (source = only emits, sink = only receives, hub = both)."
  [edges]
  (let [acc (reduce
              (fn [m {:keys [source target value volume]}]
                (-> m
                    (update-in [source :out-value]  (fnil + 0.0) (double value))
                    (update-in [source :out-volume] (fnil + 0.0) (double volume))
                    (update-in [target :in-value]   (fnil + 0.0) (double value))
                    (update-in [target :in-volume]  (fnil + 0.0) (double volume))))
              {} edges)]
    (->> acc
         (map (fn [[id m]]
                (let [in?  (or (:in-value m) (:in-volume m))
                      out? (or (:out-value m) (:out-volume m))]
                  {:id id
                   :kind (cond (and in? out?) "hub" out? "source" :else "sink")
                   :inValue   (double (:in-value m 0.0))
                   :outValue  (double (:out-value m 0.0))
                   :inVolume  (double (:in-volume m 0.0))
                   :outVolume (double (:out-volume m 0.0))})))
         (sort-by (juxt #(case (:kind %) "source" 0 "hub" 1 "sink" 2)
                        #(- (+ (:inValue %) (:outValue %)))))
         vec)))

(defn project
  "Read a flow log, compute its IE-flow state, and return the organism viz projection map. Pure."
  [log-path]
  (let [txs    (kd/read-log log-path)
        events (ledger/read-events txs)
        st     (metrics/flow-state events)
        as-of  (some-> txs peek :tx/as-of str)
        edges  (->> (:edges st)
                    (map (fn [e]
                           {:source (:source e) :target (:target e) :type (:type e)
                            :volume (double (:volume e 0)) :value (double (:value e 0))
                            :cost (double (:cost e 0)) :risk (double (:risk e 0))
                            :count (:count e) :net (metrics/net-gain e)}))
                    (sort-by :value >)
                    vec)]
    {:source          "repo-git"
     :asOf            as-of
     :generatedAt     (str "ie-flow · as-of " (when as-of (subs as-of 0 (min 12 (count as-of)))))
     :events          (count events)
     :flowsN          (:flows-n st)
     :netGain         (jnum (:net-gain st))
     :orderIndex      (jnum (:order-index st))
     :agentEfficiency (jnum (:agent-efficiency st))
     :throughput      (jnum (:throughput st))
     :totalValue      (jnum (:total-value st))
     :totalCost       (jnum (:total-cost st))
     :totalRisk       (jnum (:total-risk st))
     :parasitic       (:parasitic? st)
     :summary         (metrics/summary-line st)
     :edges           edges
     :nodes           (nodes-of edges)}))

;; ── system-of-systems graph: every actor embeds the SAME unforkable substrate ──
;; The IE-flow lifecycle is ONE shared library (kotoba Datom ledger + organism react-loop +
;; co-scientist) that each actor embeds (3 lines) — so the colony is a SYSTEM OF SYSTEMS, not 80
;; forks. sos.json is the node-link graph of that topology: the shared substrate core, the measured
;; sources feeding it, the adopters embedding it, and kaname synthesizing across the multiplex.

(def ^:private subsystems
  [{:id "sub:ledger"     :label "kotoba Datom ledger" :kind "core" :ja "不変台帳"}
   {:id "sub:loop"       :label "organism react-loop" :kind "core" :ja "代謝ループ"}
   {:id "sub:coscientist" :label "co-scientist"        :kind "core" :ja "共同科学者"}])

#?(:clj
   (defn- read-registry []
     (try (edn/read-string (slurp registry-path)) (catch Exception _ {}))))

#?(:clj
   (defn- measure-actor
     "Fold an actor's own flow ledger if it has one; nil when the actor is registered but unmeasured."
     [actor]
     (let [p (str data-root "/" actor "/flow.kotoba.edn")]
       (when (.exists (io/file p))
         (let [st (metrics/flow-state (ledger/read-events (kd/read-log p)))]
           {:netGain (jnum (:net-gain st)) :orderIndex (jnum (:order-index st))
            :flowsN (:flows-n st) :parasitic (:parasitic? st)})))))

#?(:clj
   (defn sos-project
     "Build the system-of-systems node-link graph from the registry + per-actor measurement. Pure-ish
     (reads committed ledgers only)."
     []
     (let [reg (read-registry)
           adopters (:adopted reg)
           sources  (:measured-sources reg)
           actor-nodes (mapv (fn [{:keys [actor note]}]
                               (let [m (measure-actor actor)]
                                 (cond-> {:id (str "actor:" actor) :label actor :kind "actor"
                                          :note note :measured (boolean m)}
                                   m (merge m))))
                             adopters)
           source-nodes (mapv (fn [{:keys [name note]}]
                                (let [m (measure-actor name)]
                                  (cond-> {:id (str "src:" name) :label name :kind "source" :note note}
                                    m (merge m))))
                              sources)
           ;; core triangle (the loop) + each measured source → ledger
           core-edges [{:from "sub:ledger" :to "sub:loop" :type "core"}
                       {:from "sub:loop" :to "sub:coscientist" :type "core"}
                       {:from "sub:coscientist" :to "sub:ledger" :type "core"}]
           src-edges (mapv (fn [s] {:from (:id s) :to "sub:ledger" :type "measures"}) source-nodes)
           ;; each adopter embeds the substrate: record!→ledger, beat!→loop
           embed-edges (vec (mapcat (fn [a] [{:from (:id a) :to "sub:ledger" :type "embeds"}
                                             {:from (:id a) :to "sub:loop" :type "embeds"}])
                                    actor-nodes))
           ;; kaname is the SoS synthesizer over the multiplex — it links the other adopters
           others (remove #(= "actor:kaname" (:id %)) actor-nodes)
           synth-edges (when (some #(= "actor:kaname" (:id %)) actor-nodes)
                         (mapv (fn [a] {:from "actor:kaname" :to (:id a) :type "synthesizes"}) others))]
       {:generatedAt (str "sos · " (count actor-nodes) " adopters / "
                          (count (filter :measured actor-nodes)) " measured")
        :nodes (vec (concat subsystems source-nodes actor-nodes))
        :edges (vec (concat core-edges src-edges embed-edges synth-edges))})))

#?(:clj
   (defn -sos
     "bb task: emit sos.json — the actor system-of-systems graph — into every served organism dir."
     [& _]
     (let [g (sos-project)
           out (json/generate-string g {:pretty true})]
       (doseq [d out-dirs]
         (let [p (str d "/sos.json")] (io/make-parents p) (spit p out)))
       (println (str "sos.json · " (count (:nodes g)) " nodes / " (count (:edges g)) " edges · "
                     (:generatedAt g)))
       g)))

#?(:clj
   (defn -report
     "bb task: project the IE-flow ledger → ieflow.json in every served organism dir.
     Args: [flow-log-path] (default 80-data/ie-flow/repo-git/flow.kotoba.edn)."
     [& args]
     (let [log-path (or (first args) default-flow-log)
           proj (project log-path)
           out (json/generate-string proj {:pretty true})]
       (doseq [d out-dirs]
         (let [p (str d "/ieflow.json")]
           (io/make-parents p)
           (spit p out)))
       (println (str "ieflow.json ← " log-path " · " (:summary proj)
                     " · parasitic=" (:parasitic proj)))
       proj)))
