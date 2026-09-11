;; ported from 20-actors/himawari/cells/cell_process/cell.py (condensed) — gold reference (Fable)
;; CellProcessCell — himawari Pregel cell。solar-grade c-Si セル線の super-step 状態機械。
;; LangGraph StateGraph → langgraph-clj への正準マッピングを示す gold:
;;   init → texture → junction → metallization → flash-iv → gas-abatement (G3 gate)
;;        → witness → emit-record → END  (gas-abatement は DRE<99% で halt へ分岐)
;;
;; ノードは (fn [state] → 部分更新 map) の純関数。グラフ組立は langgraph-clj の
;; state-graph/add-node/add-conditional-edges。channels の reducer で messages を蓄積。
(ns himawari.cells.cell-process
  (:require [langgraph.graph :as g]))

;; G3: 100年 GWP が ≥99% 除去 (DRE) または代替を強制するフッ素系 etch/clean ガス (AR5)。
(def high-gwp-gases
  {"NF3" 16100 "SF6" 23500 "CF4" 6630 "C2F6" 11100 "C3F8" 8900})

(def min-dre 0.99)                                  ; G3: ≥99% destruction-removal floor
(def metallization-on-roadmap #{"ag-cu-hybrid" "copper"}) ; G6: Ag→Cu roadmap

;; ── node functions: state → 部分更新 ──

(defn texture [state]
  {:steps [:texture] :reflectance (max 0.0 (- 0.30 (* 0.01 (:texture-passes state 4))))})

(defn junction [_state]
  {:steps [:junction] :sheet-resistance 90.0})       ; diffusion/PECVD

(defn metallization [state]
  (let [m (:metallization state "silver")]
    {:steps [:metallization]
     :metal m
     :off-roadmap? (not (contains? metallization-on-roadmap m))})) ; G6 flag

(defn flash-iv [state]
  {:steps [:flash-iv]
   :efficiency (* 0.235 (- 1.0 (:reflectance state 0.1)))})

(defn gas-abatement [state]
  ;; G3 gate: フッ素系ガスの DRE が floor 未満かつ代替なし → halt
  (let [dre (:dre state 1.0)
        substituted? (:substituted? state false)]
    {:steps [:gas-abatement]
     :g3-ok (or substituted? (>= dre min-dre))}))

(defn witness [_state] {:steps [:witness] :witnessed? true})

(defn emit-record [state]
  {:steps [:emit-record]
   :record {:efficiency (:efficiency state)
            :metal (:metal state)
            :witnessed? (:witnessed? state)}})

(defn- after-abatement
  "G3 ゲート: 通れば witness へ、落ちれば END (halt)。"
  [state]
  (if (:g3-ok state) :witness g/END))

(defn build
  "セル線グラフを組み立てて compile する。compile-opts は checkpointer 等。"
  ([] (build {}))
  ([compile-opts]
   (-> (g/state-graph {:channels {:steps {:reducer (fnil into []) :default []}}})
       (g/add-node :texture texture)
       (g/add-node :junction junction)
       (g/add-node :metallization metallization)
       (g/add-node :flash-iv flash-iv)
       (g/add-node :gas-abatement gas-abatement)
       (g/add-node :witness witness)
       (g/add-node :emit-record emit-record)
       (g/set-entry-point :texture)
       (g/add-edge :texture :junction)
       (g/add-edge :junction :metallization)
       (g/add-edge :metallization :flash-iv)
       (g/add-edge :flash-iv :gas-abatement)
       (g/add-conditional-edges :gas-abatement after-abatement)
       (g/add-edge :witness :emit-record)
       (g/set-finish-point :emit-record)
       (g/compile-graph compile-opts))))
