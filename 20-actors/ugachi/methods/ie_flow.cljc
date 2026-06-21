#!/usr/bin/env bb
;; ugachi 穿ち — ie-flow embedding (the SoS scoring leg).
(ns ugachi.methods.ie-flow
  "ie_flow.cljc — ugachi 穿ち embeds the information-energy flow lifecycle
  (etzhayyim.ie-flow, ADR-2606211200 + score ADR-2606212200). ugachi is an
  INFORMATION-CONTROL ACTOR in the system + energy flow: the scattered
  multi-generational extraction RISK across many proposed projects is
  high-entropy disorder; ugachi's §2(l) gate is a RECTIFIER (整流) that folds
  that risk onto stewardship VERDICTS — concentrating realised stewardship order
  onto the projects it can permit-design (:propose-r0) or route to recovery
  (:route-to-recovery → kanayama), while REFUSING the catastrophic/monopolistic
  ones (protective order: disorder prevented).

  This namespace is PURE measurement; it embeds the SHARED ie-flow metrics (NOT a
  fork). Like kafun, ugachi moves INFORMATION-energy (a stewardship gate), never
  physical extraction — it never digs (G1). The flow ledger is the per-actor
  ie-flow record (80-data/ie-flow/ugachi/, gitignored)."
  (:require [ugachi.methods.ugachi-edn :as ue]
            [ugachi.methods.gate :as gate]
            [etzhayyim.ie-flow.metrics :as iem]
            #?(:clj [etzhayyim.ie-flow.embed :as embed])
            [clojure.string :as str]
            #?(:clj [clojure.edn :as edn])))

(def ^:private value-scale 100.0)
(def ^:private assess-cost 2.0)   ;; ugachi's per-project assessment compute (cheap — it only assesses)

(defn- route-factor
  "Fraction of a project's multi-gen risk that this verdict rectifies into realised
  STEWARDSHIP order. :propose-r0 delivers the most (a permitted, designed, low-risk,
  consented, Transparent-Force project); :route-to-recovery routes to kanayama
  (recovery-first); :refuse exports PROTECTIVE order only (a catastrophic/monopolistic
  project rejected — disorder prevented, shown structurally, not stewardship-energy);
  :insufficient-evidence awaits."
  [verdict]
  (case verdict
    :propose-r0            0.8    ;; realised stewardship (design-only, but the order is real)
    :route-to-recovery     0.5    ;; routed to kanayama urban-mining (recovery-first)
    :refuse                0.0    ;; PROTECTIVE only — no stewardship-energy this cycle
    :insufficient-evidence 0.1    ;; await more evidence
    0.1))

(defn flow-events
  "Project ugachi's §2(l) assessment into ie-flow EVENT maps (the SoS measurement the
  shared metrics fold over). source = the project, target = the verdict route, volume =
  multigen-risk (the scattered risk ugachi rectifies), value = risk·route-factor·scale
  (the stewardship order rectified onto a verdict), cost = flat assessment compute, risk = 0
  (assessment-only — ugachi never digs)."
  [projects]
  (let [rows (get (gate/assess projects) "projects")]
    (mapv
     (fn [r]
       (let [verdict (get r "verdict")
             mg (double (get r "multigen_risk"))]
         {:id (str "ugachi-" (get r "id"))
          :actor "ugachi"
          :source (str "project:" (get r "id"))
          :target (str "route:" (name verdict))
          :type (name verdict)
          :volume mg
          :value (* mg (route-factor verdict) value-scale)
          :cost assess-cost
          :risk 0.0
          :agent? true}))
     rows)))

(defn flow-state
  "Fold ugachi's measured events through the SHARED ie-flow metrics → the order calculus
  (net-gain / order-index / agent-efficiency / parasitic?). Embeds etzhayyim.ie-flow.metrics
  — NOT a fork."
  [projects]
  (iem/flow-state (flow-events projects)))

#?(:clj
   (defn record-flow!
     "Record ugachi's measured ie-flow EVENTS to the shared per-actor ie-flow ledger
     (80-data/ie-flow/ugachi/flow.kotoba.edn) via etzhayyim.ie-flow.embed — so ugachi's SoS
     scoreboard entry is tool/heartbeat-produced. Deterministic (caller supplies tx-id +
     as-of), no-server-key, gitignored. Returns {:flow-log :events :order-index}."
     ([projects] (record-flow! projects {}))
     ([projects {:keys [tx-id as-of]}]
      (let [evs (flow-events projects)]
        (embed/record! "ugachi" evs {:tx-id (or tx-id "ugachi-ie-flow") :as-of (or as-of "beat")})
        {:flow-log (embed/flow-log "ugachi")
         :events (count evs)
         :order-index (get (embed/measure "ugachi") :order-index)}))))

#?(:clj
   (defn -main [& args]
     (let [flags (set (filter #(str/starts-with? % "--") args))
           seed (or (first (remove #(str/starts-with? % "--") args)) "20-actors/ugachi/kotoba/seed.edn")
           projects (ue/projects seed)
           st (flow-state projects)]
       (println (iem/summary-line st))
       (when (contains? flags "--record")
         (let [r (record-flow! projects {:tx-id "ugachi-ie-flow" :as-of "beat"})]
           (println (str "recorded " (:events r) " ie-flow events → " (:flow-log r))))))))

#?(:clj
   (when (= *file* (System/getProperty "babashka.file"))
     (apply -main *command-line-args*)))
