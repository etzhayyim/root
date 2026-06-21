#!/usr/bin/env bb
;; busshi 物資 — ie-flow embedding (the SoS scoring leg).
(ns busshi.methods.ie-flow
  "ie_flow.cljc — busshi 物資 embeds the information-energy flow lifecycle
  (etzhayyim.ie-flow, ADR-2606211200 + score ADR-2606212200). busshi is an
  INFORMATION-CONTROL ACTOR in the system + energy flow: the scattered §2(l)
  multi-generational RISK borne across many commodities is high-entropy disorder;
  busshi's observation is a RECTIFIER (整流) that folds that risk onto RESILIENCE
  routes — concentrating realised order onto the commodities whose concentration
  (:de-monopolization) or footprint (:restoration) most needs routing, leaving the
  diffuse low-risk ones at baseline (:resilience).

  This namespace is PURE measurement; it embeds the SHARED ie-flow metrics (NOT a
  fork). busshi is OBSERVATION-ONLY — it never trades and never mines; it moves
  INFORMATION-energy (a resilience map), never physical commodity. The flow ledger
  is the per-actor ie-flow record (80-data/ie-flow/busshi/, gitignored). The map is
  routed to RESILIENCE, NEVER a target-list."
  (:require [busshi.methods.busshi-edn :as be]
            [busshi.methods.analyze :as an]
            [etzhayyim.ie-flow.metrics :as iem]
            #?(:clj [etzhayyim.ie-flow.embed :as embed])
            [clojure.string :as str]
            #?(:clj [clojure.edn :as edn])))

(def ^:private value-scale 100.0)
(def ^:private assess-cost 2.0)   ;; busshi's per-commodity observation compute (cheap — it only observes)

(defn- route-factor
  "Fraction of a commodity's multi-gen risk that this resilience route rectifies into
  realised order. A clear monopoly chokepoint (:de-monopolization) or a clear footprint
  (:restoration) is high-value order (a route-around / stewardship target identified);
  diffuse baseline (:resilience) is low. busshi never punishes — every route is order
  routed to RESILIENCE, never a target-list."
  [route]
  (case route
    :de-monopolization 0.8    ;; a clear chokepoint → route-around (high order rectified)
    :restoration       0.7    ;; a clear multi-gen footprint → stewardship
    :resilience        0.3    ;; diffuse baseline resilience map
    0.3))

(defn flow-events
  "Project busshi's §2(l) commodity observation into ie-flow EVENT maps (the SoS
  measurement the shared metrics fold over). source = the commodity, target = the
  resilience route, volume = multigen-risk (the scattered risk busshi rectifies), value =
  risk·route-factor·scale (the resilience order rectified onto a route), cost = flat
  observation compute, risk = 0 (observation-only — busshi never trades/mines)."
  [commodities]
  (let [rows (get (an/analyze commodities) "commodities")]
    (mapv
     (fn [r]
       (let [route (get r "route")
             mg (double (get r "multigen_risk"))]
         {:id (str "busshi-" (get r "id"))
          :actor "busshi"
          :source (str "commodity:" (get r "id"))
          :target (str "route:" (name route))
          :type (name route)
          :volume mg
          :value (* mg (route-factor route) value-scale)
          :cost assess-cost
          :risk 0.0
          :agent? true}))
     rows)))

(defn flow-state
  "Fold busshi's measured events through the SHARED ie-flow metrics → the order calculus
  (net-gain / order-index / agent-efficiency / parasitic?). Embeds etzhayyim.ie-flow.metrics
  — NOT a fork."
  [commodities]
  (iem/flow-state (flow-events commodities)))

#?(:clj
   (defn record-flow!
     "Record busshi's measured ie-flow EVENTS to the shared per-actor ie-flow ledger
     (80-data/ie-flow/busshi/flow.kotoba.edn) via etzhayyim.ie-flow.embed — so busshi's SoS
     scoreboard entry is tool/heartbeat-produced. Deterministic (caller supplies tx-id +
     as-of), no-server-key, gitignored. Returns {:flow-log :events :order-index}."
     ([commodities] (record-flow! commodities {}))
     ([commodities {:keys [tx-id as-of]}]
      (let [evs (flow-events commodities)]
        (embed/record! "busshi" evs {:tx-id (or tx-id "busshi-ie-flow") :as-of (or as-of "beat")})
        {:flow-log (embed/flow-log "busshi")
         :events (count evs)
         :order-index (get (embed/measure "busshi") :order-index)}))))

#?(:clj
   (defn -main [& args]
     (let [flags (set (filter #(str/starts-with? % "--") args))
           seed (or (first (remove #(str/starts-with? % "--") args)) "20-actors/busshi/kotoba/seed.edn")
           commodities (be/commodities seed)
           st (flow-state commodities)]
       (println (iem/summary-line st))
       (when (contains? flags "--record")
         (let [r (record-flow! commodities {:tx-id "busshi-ie-flow" :as-of "beat"})]
           (println (str "recorded " (:events r) " ie-flow events → " (:flow-log r))))))))

#?(:clj
   (when (= *file* (System/getProperty "babashka.file"))
     (apply -main *command-line-args*)))
