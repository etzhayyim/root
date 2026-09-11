;; ported from 20-actors/ake/cells/edit_triage/state_machine.py — gold reference (Fable)
;; 朱 (ake) triage cell の phase 状態機械 — G2/G6 advisory membrane。
;; screened proposal を採点 (risk + quality, Wikipedia ORES 相当) しルートを割り当てる。
;; G2 不変条件: モデルは SCORE し、純関数 route-for が ROUTE する — どちらも accept/reject を
;; 出さない (非裁定)。G6: スコアの LLM 精緻化は Murakumo-only。hard gate 失敗で REFUSED。
;;
;; cell の状態遷移は「現状態 map → 新状態 map」の純関数。score-edit は I/O 注入。
(ns ake.cells.edit-triage.state-machine
  (:require [clojure.string :as str]))

(def phases #{:init :triaged :refused})

(def default-state
  {:phase :init
   :edit {}
   :risk ""
   :quality 0.0
   :route ""
   :by "murakumo:gemma3:4b"
   :refusal ""
   :payload {}})

(defn- current-state [state]
  (merge default-state (:cell-state state)))

(defn triage
  "state {:cell-state… :edit… :by…} → {:cell-state 新状態}。
  score-edit は注入される採点関数 (fn [edit by] → {:triage/risk… :triage/quality… :triage/route… :triage/edit…})。
  例外 (hard gate 失敗) は :refused へ。"
  [score-edit state]
  (let [cs (-> (current-state state)
               (assoc :edit (merge (:edit (current-state state)) (:edit state)))
               (assoc :by (get state :by (:by (current-state state)))))]
    (try
      (let [t (score-edit (:edit cs) (:by cs))
            risk (:triage/risk t)
            route (:triage/route t)]
        {:cell-state
         (assoc cs
                :risk risk
                :quality (:triage/quality t)
                :route route
                :payload {:edit-id (:triage/edit t)
                          :risk (str/replace-first (str risk) #"^:" "")
                          :quality (:triage/quality t)
                          :route (str/replace-first (str route) #"^:" "")
                          :by (:by cs)}
                :refusal ""
                :phase :triaged)})
      (catch clojure.lang.ExceptionInfo e
        {:cell-state (assoc cs :refusal (ex-message e) :phase :refused)}))))
