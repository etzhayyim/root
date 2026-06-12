;; ported from 20-actors/tedai/cells/intent_plan/state_machine.py (unit_refactor stage 0)
;; Phase state machine for the tedai intent_plan (手代) cell.
(ns tedai.cells.intent-plan.state-machine
  (:require [clojure.string] [clojure.set] [clojure.edn]))

(declare methods plan-phase plan-state state transition-parse-brief transition-prohibition-scan transition-emit-plan)

;; TODO: port-failed unit _METHODS (/var/folders/px/b63lssbx5056kq_1t6pvc1f80000gn/T/tmptrkb9938/scratch.clj:2:1: er)
;; _METHODS = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "methods"))
;; PROHIBITED_INTENTS: tuple[str, ...] = (
;;     "keylog", "keylogger", "spy", "surveil", "monitor my employee", "watch my kid",
;;     "track my partner", "record their screen", "their camera", "their microphone",
;;     "bypass anti-cheat", "bypass anticheat", "bypass drm", "evade detection",
;;     "without them knowing", "someone else's computer",
;; )
;; OUTCOME_PROHIBITED = "refused-prohibited-intent"
(def methods nil) ;; TODO: port-failed const

{:init "init"
 :parsed "parsed"
 :scanned "scanned"
 :planned "planned"
 :refused "refused"}

(def plan-state
  {:phase "PlanPhase.INIT"
   :brief ""
   :command-lines []
   :payload {}})

(defn state [d]
  (let [cell-state (get d "cell_state")]
    (if cell-state
      {:plan-state (apply :keys cell-state) :values cell-state} ; Simplified representation of PlanState(**kwargs)
      nil)))

;; TODO: port-failed unit transition_parse_brief (assembled-lint error)
;; def transition_parse_brief(state: dict[str, Any]) -> dict[str, Any]:
;;     """Collect the brief text + literal command lines (R0; NL→command is the R1 Murakumo leg, G4)."""
;;     cs = _state(state)
;;     cs.brief = state.get("brief", cs.brief)
;;     cs.command_lines = list(state.get("command_lines", cs.command_lines))
;;     if not cs.command_lines:
;;         raise ValueError("intent_plan: no command lines supplied (R0 takes literal `tedai …` lines)")
;;     cs.phase = PlanPhase.PARSED.value
;;     return {"cell_state": cs.__dict__, "next_node": "prohibition_scan"}
(defn transition-parse-brief [& _]
  (throw (ex-info "TODO: port-failed" {:from "transition_parse_brief"})))

;; TODO: port-failed unit transition_prohibition_scan (/var/folders/px/b63lssbx5056kq_1t6pvc1f80000gn/T/tmpjrgad8cc/scratch.clj:4:15: w)
;; def transition_prohibition_scan(state: dict[str, Any]) -> dict[str, Any]:
;;     """G8/G2: refuse a brief that asks for surveillance or detection-evasion in intent."""
;;     cs = _state(state)
;;     text = " ".join([cs.brief, *cs.command_lines]).lower()
;;     hits = [marker for marker in PROHIBITED_INTENTS if marker in text]
;;     if hits:
;;         cs.phase = PlanPhase.REFUSED.value
;;         cs.payload["outcome"] = OUTCOME_PROHIBITED
;;         cs.payload["markers"] = hits
;;         return {"cell_state": cs.__dict__, "next_node": "end"}
;;     cs.phase = PlanPhase.SCANNED.value
;;     return {"cell_state": cs.__dict__, "next_node": "emit_plan"}
(defn transition-prohibition-scan [& _]
  (throw (ex-info "TODO: port-failed" {:from "transition_prohibition_scan"})))

;; TODO: port-failed unit transition_emit_plan (/var/folders/px/b63lssbx5056kq_1t6pvc1f80000gn/T/tmpzinkm0gs/scratch.clj::: erro)
;; def transition_emit_plan(state: dict[str, Any]) -> dict[str, Any]:
;;     """G5/G6: plan each command line into a gated, dry-run DesktopOp."""
;;     cs = _state(state)
;;     if cs.phase != PlanPhase.SCANNED.value:
;;         raise ValueError("intent_plan: emit_plan reached without a clean prohibition scan")
;;     ops = [plan_op(line) for line in cs.command_lines]
;;     cs.payload["ops"] = [op.__dict__ for op in ops]
;;     cs.payload["dryRun"] = True                     # G6 invariant
;;     cs.payload["mutatingCount"] = sum(1 for op in ops if op.safety != "read")
;;     cs.phase = PlanPhase.PLANNED.value
;;     return {"cell_state": cs.__dict__, "next_node": "end"}
(defn transition-emit-plan [& _]
  (throw (ex-info "TODO: port-failed" {:from "transition_emit_plan"})))

