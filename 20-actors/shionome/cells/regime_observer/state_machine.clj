;; ported from 20-actors/shionome/cells/regime_observer/state_machine.py (unit_refactor stage 0)
;; Phase state machine for the 潮目 (shionome) regime_observer cell.
(ns shionome.cells.regime-observer.state-machine
  (:require [clojure.string] [clojure.set] [clojure.edn]))

(declare regime-phase regime-state transition-to-observed)

;; TODO: port-failed unit RegimePhase (judah: timed out)
;; class RegimePhase(Enum):
;;     INIT = "init"
;;     OBSERVED = "observed"
(defn regime-phase [& _]
  (throw (ex-info "TODO: port-failed" {:from "RegimePhase"})))

(def regime-state
  {:phase "RegimePhase.INIT"
   :net {}
   :risk-tag {}
   :regime ""
   :risk-net 0.0
   :safe-net 0.0
   :no-trade-notice true})

;; TODO: port-failed unit transition_to_observed (/var/folders/px/b63lssbx5056kq_1t6pvc1f80000gn/T/tmpvm9ilm0_/scratch.clj:3:13: w)
;; def transition_to_observed(state: dict[str, Any]) -> dict[str, Any]:
;;     cs = RegimeState(**state.get("cell_state", {}))
;;     cs.net = state.get("net", cs.net)
;;     cs.risk_tag = state.get("risk_tag", cs.risk_tag)
;;     risk_net = sum(v for b, v in cs.net.items() if cs.risk_tag.get(b) == "risk")
;;     safe_net = sum(v for b, v in cs.net.items() if cs.risk_tag.get(b) == "safe")
;;     if risk_net == 0.0 and safe_net == 0.0:
;;         label = "indeterminate"
;;     elif risk_net > 0 and safe_net <= 0:
;;         label = "risk-on"
;;     elif risk_net < 0 and safe_net >= 0:
;;         label = "risk-off"
;;     else:
;;         label = "mixed"
;;     cs.risk_net, cs.safe_net, cs.regime = round(risk_net, 4), round(safe_net, 4), label
;;     cs.no_trade_notice = True
;;     cs.phase = RegimePhase.OBSERVED.value
;;     return {"cell_state": cs.__dict__}
(defn transition-to-observed [& _]
  (throw (ex-info "TODO: port-failed" {:from "transition_to_observed"})))

