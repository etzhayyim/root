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
            [etzhayyim.ie-flow.metrics :as metrics]
            [etzhayyim.ie-flow.boundary :as boundary]))

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

;; ── the IE-flow LAB: every actor is a BOUNDED system with its OWN dynamics ──
;; lab.kotoba.edn is a FLAT [e a v tx op] datom vector (the snapshot shape the page's parse-kotoba
;; reads). It now carries, PER ACTOR (repo-git + each adopter), that actor's own:
;;   · system BOUNDARY — interior stations + the metered membrane (imports drawn in / exports of
;;     order returned out), namespaced `lab:imp:<a>:*` / `lab:exp:<a>:*` / `lab:a:<a>`
;;   · scalar INDICES (`lab:idx:<a>`) — net-gain / order-index / agent-eff / surprise
;;   · SYSTEM-DYNAMICS params (`lab:sd:<a>`) — init stocks + per-step rates from THAT actor's flow
;; plus the colony ABM (`lab:abm` + `lab:agent:<a>`) coupling the actors. Each actor is its own
;; system-of-systems-dynamics; the colony is a system OF those systems. ADR-2606211200.

(def ^:private sd-steps 12)

(defn- sd-params-from-state
  "Derive system-dynamics init stocks + per-step input rates from an actor's IE-flow state. The
  boundary's import/export aggregates drive the actor's OWN stock dynamics. Pure."
  [st]
  (let [oi (double (:order-index st))
        per (fn [x] (long (Math/round (/ (double x) sd-steps))))]
    {:init {"customers" 0 "trust" 0.30 "data-asset" 0 "model-quality" 0.10 "reserves" 0}
     :in {"acquisition" (per (:throughput st)) "revenue" (per (:total-value st))
          "cost" (per (:total-cost st)) "failures" (per (:total-risk st))
          "good-exp" (long (Math/round (* 100.0 (max 0.0 oi))))
          "spam" (long (Math/round (* 20.0 (max 0.0 (- 1.0 oi)))))
          "churn" (long (Math/round (* 0.05 (double (per (:throughput st))))))}}))

(defn- repo-actor-lab
  "Build repo-git's bounded-system descriptor from its REAL measured flow log (the one actor with a
  live measurement). Its membrane: dev-effort drawn in, code/order exported to each repo layer."
  [log-path]
  (let [st (metrics/flow-state (ledger/read-events (kd/read-log log-path)))
        edges (->> (:edges st) (sort-by :value >) vec)]
    {:id "repo-git" :role "the monorepo's own development metabolism" :representative false
     :inside ["repo" "ledger" "build"]
     :imports [{:kind "dev-effort" :from "developers" :volume (:throughput st) :cost (:total-cost st)}]
     :exports (mapv (fn [e] {:kind "code" :to (:target e) :value (double (:value e 0))})
                    (take 6 edges))
     :state st}))

#?(:clj
   (defn lab-datoms
     "Build the flat [e a v tx op] datom vector for lab.kotoba.edn — one bounded system PER actor
     (repo-git real + adopters representative) + the colony ABM. Pure over the flow log + roles."
     [log-path]
     (let [adopters (boundary/adopters)
           actor-labs (into [(repo-actor-lab log-path)]
                            (map boundary/boundary adopters))
           order (mapv :id actor-labs)
           x0 {"ibuki" 0.60 "tsumugi" 0.45 "shionome" 0.55 "kaname" 0.78 "okaimono" 0.50 "repo-git" 0.65}
           d (fn [e a v] [e a v 1 :add])
           actor-datoms
           (fn [{:keys [id role representative inside imports exports state]}]
             (let [st state oi (double (:order-index st))
                   {:keys [init in]} (sd-params-from-state st)
                   ae (str "lab:a:" id) ie (str "lab:idx:" id) se (str "lab:sd:" id)]
               (concat
                 [(d ae :lab.actor/id id) (d ae :lab.actor/role role)
                  (d ae :lab.actor/representative (boolean representative))
                  (d ae :lab.actor/inside (vec inside))]
                 ;; indices
                 [(d ie :lab.index/net-gain (:net-gain st))
                  (d ie :lab.index/order-index oi)
                  (d ie :lab.index/agent-eff (jnum (:agent-efficiency st)))
                  (d ie :lab.index/throughput (:throughput st))
                  (d ie :lab.index/total-value (:total-value st))
                  (d ie :lab.index/total-cost (:total-cost st))
                  (d ie :lab.index/parasitic (:parasitic? st))
                  (d ie :lab.index/surprise
                     (/ (+ (if (:parasitic? st) 1.0 0.0) (max 0.0 (- 1.0 oi))) 2.0))]
                 ;; membrane: imports (drawn IN)
                 (mapcat (fn [i im]
                           (let [eid (str "lab:imp:" id ":" i)]
                             [(d eid :lab.imp/actor id) (d eid :lab.imp/idx i)
                              (d eid :lab.imp/kind (:kind im)) (d eid :lab.imp/from (:from im))
                              (d eid :lab.imp/volume (double (:volume im 0)))
                              (d eid :lab.imp/cost (double (:cost im 0)))]))
                         (range) imports)
                 ;; membrane: exports (order returned OUT)
                 (mapcat (fn [i ex]
                           (let [eid (str "lab:exp:" id ":" i)]
                             [(d eid :lab.exp/actor id) (d eid :lab.exp/idx i)
                              (d eid :lab.exp/kind (:kind ex)) (d eid :lab.exp/to (:to ex))
                              (d eid :lab.exp/value (double (:value ex 0)))]))
                         (range) exports)
                 ;; the actor's OWN system-dynamics params
                 [(d se :lab.sd/steps sd-steps)]
                 (for [[k v] init] (d se (keyword "lab.sd" (str "init-" k)) v))
                 (for [[k v] in]   (d se (keyword "lab.sd" k) v)))))]
       (vec (concat
              ;; the selector roster (ordered)
              (map-indexed (fn [i a] (d (str "lab:actor:" a) :lab/actor a)) order)
              (map-indexed (fn [i a] (d (str "lab:actor:" a) :lab/order i)) order)
              ;; every actor's bounded system
              (mapcat actor-datoms actor-labs)
              ;; colony ABM (Friedkin-Johnsen coupling the actor systems; kaname = synthesis centre)
              [(d "lab:abm" :lab.abm/lambda 0.5) (d "lab:abm" :lab.abm/steps 16)]
              (mapcat (fn [a] (let [eid (str "lab:agent:" a)]
                                [(d eid :lab.agent/id a) (d eid :lab.agent/x0 (double (get x0 a 0.5)))]))
                      (boundary/adopters)))))))

#?(:clj
   (defn -lab
     "bb task: emit lab.kotoba.edn — every actor as its OWN bounded system (boundary + indices +
     system-dynamics) + the colony ABM. Pure read, no held key. Args: [flow-log-path]."
     [& args]
     (let [log-path (or (first args) default-flow-log)
           datoms (lab-datoms log-path)
           out (str ";; GENERATED kotoba Datom snapshot (etzhayyim.ie-flow.organism/-lab).\n"
                    ";; Per-actor bounded systems (boundary/index/sd) + colony ABM. [e a v tx op].\n"
                    "[\n" (apply str (map #(str (pr-str %) "\n") datoms)) "]\n")]
       (doseq [dir out-dirs]
         (let [p (str dir "/lab.kotoba.edn")] (io/make-parents p) (spit p out)))
       (println (str "lab.kotoba.edn · " (count datoms) " datoms · "
                     (count (boundary/adopters)) " adopters + repo-git, each a bounded system"))
       datoms)))

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
