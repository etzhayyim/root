;; ported from 20-actors/hotaru/cells/commons_readiness/state_machine.py (unit_refactor stage 0)
;; Phase state machine for the hotaru commons_readiness (蛍) cell.
(ns hotaru.cells.commons-readiness.state-machine
  (:require [clojure.string] [clojure.set] [clojure.edn]))

(declare substrate-stages readiness-phase readiness-state state norm transition-to-assessed transition-to-reported)

(def substrate-stages ["synthesis" "bulk-growth" "wafering" "surface-prep"])
(def stage-weight {"open-mature" 1.0 "open-emerging" 0.5 "gap" 0.0 "absent" 0.0})
(def forbidden-keys ["fabricationOpened" "fabricationPermitted" "gateDecided" "gateOpened"])

(def readiness-phase
  #{;; INIT, ASSESSED, REPORTED are the values of the enum
   :init "init"
   :assessed "assessed"
   :reported "reported"})

(def readiness-state-initial-value {:phase "ReadinessPhase.INIT.value"})

(defn readiness-state [this]
  (let [phase (:phase this)
        per-stage (:per-stage this)
        epitaxy-open-mature (:epitaxy-open-mature this)
        stages-covered (:stages-covered this)
        substrate-commons-ready (:substrate-commons-ready this)
        r4-gate-satisfiable (:r4-gate-satisfiable this)
        maturity-score (:maturity-score this)
        conflict-flagged (:conflict-flagged this)
        sourcing (:sourcing this)
        payload (:payload this)]
    (assoc this :phase phase
           :per-stage per-stage
           :epitaxy-open-mature epitaxy-open-mature
           :stages-covered stages-covered
           :substrate-commons-ready substrate-commons-ready
           :r4-gate-satisfiable r4-gate-satisfiable
           :maturity-score maturity-score
           :conflict-flagged conflict-flagged
           :sourcing sourcing
           :payload payload)))

(defn readiness-state-new [initial-values]
  (let [default-state (assoc initial-values :phase "ReadinessPhase.INIT.value")]
    (readiness-state default-state)))

(defn _state [d]
  (let [cell-state (get d "cell_state")]
    (if cell-state
      cell-state ; Assuming ReadinessState is a constructor that accepts the map directly or we return the map as the state representation.
      nil)))

(defn _norm [v]
  (if (nil? v) "" (str/trim-leading ":" v)))

;; TODO: port-failed unit transition_to_assessed (/var/folders/px/b63lssbx5056kq_1t6pvc1f80000gn/T/tmpr9rxbgnm/scratch.clj:2:1: er)
;; def transition_to_assessed(state: dict[str, Any]) -> dict[str, Any]:
;;     """Compute coverage + maturity score. G3: reject any adjudicating input key."""
;;     cs = _state(state)
;; 
;;     for k in FORBIDDEN_KEYS:
;;         if k in state:
;;             raise ValueError(
;;                 f"G3 violation: commons_readiness is non-adjudicating; it cannot carry "
;;                 f"{k!r}. Opening the ADR-2605265500 §2 R4+ gate is Council Lv7+ only — "
;;                 f"this cell reports the commons, it never decides fabrication."
;;             )
;; 
;;     # per_stage maps each substrate stage to its best maturity string (default 'absent')
;;     raw = state.get("per_stage", cs.per_stage) or {}
;;     cs.per_stage = {_norm(k): _norm(v) for k, v in raw.items()}
;;     cs.epitaxy_open_mature = bool(state.get("epitaxy_open_mature", cs.epitaxy_open_mature))
;;     cs.conflict_flagged = int(state.get("conflict_flagged", cs.conflict_flagged))
;; 
;;     covered = 0
;;     score_sum = 0.0
;;     for st in SUBSTRATE_STAGES:
;;         m = cs.per_stage.get(st, "absent")
;;         if m not in _STAGE_WEIGHT:
;;             raise ValueError(f"unknown maturity {m!r} for stage {st!r}")
;;         score_sum += _STAGE_WEIGHT[m]
;;         if m == "open-mature":
;;             covered += 1
;;     cs.stages_covered = covered
;;     cs.maturity_score = round(score_sum / len(SUBSTRATE_STAGES), 4)
;;     cs.substrate_commons_ready = covered == len(SUBSTRATE_STAGES)
;;     # R4+ gate is satisfiable from the commons only if the WHOLE chain incl. epitaxy is
;;     # open-mature. Reported, NOT decided (G3).
;;     cs.r4_gate_satisfiable = cs.substrate_commons_ready and cs.epitaxy_open_mature
;;     cs.phase = ReadinessPhase.ASSESSED.value
;;     return {"cell_state": cs.__dict__}
(defn transition-to-assessed [& _]
  (throw (ex-info "TODO: port-failed" {:from "transition_to_assessed"})))

;; TODO: port-failed unit transition_to_reported (assembled-lint error)
;; def transition_to_reported(state: dict[str, Any]) -> dict[str, Any]:
;;     """Materialize the commonsReadinessReport record (non-adjudicating, G3)."""
;;     cs = _state(state)
;;     if cs.phase != ReadinessPhase.ASSESSED.value:
;;         raise ValueError("report requires an assessment first")
;;     cs.payload = {
;;         "stagesCovered": cs.stages_covered,
;;         "stagesTotal": len(SUBSTRATE_STAGES),
;;         "substrateCommonsReady": cs.substrate_commons_ready,
;;         "epitaxyOpenMature": cs.epitaxy_open_mature,
;;         "r4GateSatisfiable": cs.r4_gate_satisfiable,
;;         "maturityScore": cs.maturity_score,
;;         "conflictFlagged": cs.conflict_flagged,
;;         "fabricationProhibited": True,  # G3 — invariant, this report never opens fabrication
;;         "sourcing": "derived",
;;     }
;;     cs.phase = ReadinessPhase.REPORTED.value
;;     return {"cell_state": cs.__dict__}
(defn transition-to-reported [& _]
  (throw (ex-info "TODO: port-failed" {:from "transition_to_reported"})))

