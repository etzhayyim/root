#!/usr/bin/env bb
;; shinogi 鎬 — discrete-time stock-flow SIMULATION of the involution loops (clj-native).
(ns shinogi.methods.simulate
  "simulate.cljc — shinogi 鎬 deepens the static regime read-off (analyze.cljc) into a
  deterministic discrete-time STOCK-FLOW SIMULATION over the 9 pressure stocks
  (ADR-2606291200). The loops become a coupling matrix; the driver net pressures
  become the exogenous forcing; the simulation rolls the stocks forward to an
  equilibrium and lets you apply a structural INTERVENTION (a re-routing of effort,
  designed by energy_flow.cljc) and watch the vicious spiral flip toward relief.

  This is a STRUCTURAL WHAT-IF over shinogi's own model — a HYPOTHESIS (G5), NEVER a
  point-forecast of reality (N3) and NEVER a directive (G11). Deterministic: no
  Math/random, no wall clock (G-determinism). Pure; no I/O; no outward channel (G4)."
  (:require [shinogi.methods.analyze :as az]
            [clojure.string :as str]))

;; ── the coupling read off the canonical loops (mirror ontology :loops :edges) ──
;; reinforcing edges = bidirectional positive coupling between the two member stocks.
(def reinforcing-edges
  [[:positional-scarcity :effort-inflation]
   [:credential-signaling :effort-inflation]
   [:family-capture :effort-inflation]
   [:failure-penalty :wellbeing-erosion]
   [:credential-signaling :labor-absorption-deficit]
   [:labor-absorption-deficit :effort-efficacy-collapse]
   [:effort-efficacy-collapse :withdrawal-prevalence]])

;; balancing loops damp their dominant stock back toward zero.
(def balancing-stocks #{:positional-scarcity :wellbeing-erosion :labor-absorption-deficit})

;; ── parameters (DISCLOSED + auditable) ───────────────────────────────────────
(def params {:alpha 0.12   ;; reinforcing coupling gain
             :beta  0.35   ;; natural decay toward 0
             :gamma 0.30   ;; balancing-loop damping (B-stocks only)
             :dt    1.0
             :ticks 20
             :x0    0.30}) ;; neutral starting level

(defn- clamp01 [x] (max 0.0 (min 1.0 (double x))))
(defn- round3 [x] (/ (Math/round (* (double x) 1000.0)) 1000.0))

(defn drives
  "Exogenous forcing per stock = the analyze net pressure (driver push), with optional
  :drive-overrides {stock delta} applied (a structural intervention; negative delta =
  relief routed onto that stock)."
  [drivers overrides]
  (let [stocks (get (az/analyze drivers) "stocks")]
    (into {}
          (for [s az/stock-order]
            [s (+ (double (:net (get stocks (name s))))
                  (double (or (get overrides s) 0.0)))]))))

(defn- step
  "One Euler step of the coupled stock-flow system."
  [x drive {:keys [alpha beta gamma dt]}]
  (into {}
        (for [s az/stock-order]
          (let [in (reduce (fn [acc [a b]]
                             (cond (= b s) (+ acc (* alpha (get x a 0.0)))
                                   (= a s) (+ acc (* alpha (get x b 0.0)))
                                   :else acc))
                           0.0 reinforcing-edges)
                bal (if (balancing-stocks s) (* gamma (get x s 0.0)) 0.0)
                dx (+ (get drive s 0.0) in (- (* beta (get x s 0.0))) (- bal))]
            [s (clamp01 (+ (get x s 0.0) (* dt dx)))]))))

(defn run
  "Roll the system forward. Returns {:trajectory [{stock level}...] :equilibrium {stock level}
   :involution-index <mean equilibrium level>}. Pure + deterministic."
  ([drivers] (run drivers {}))
  ([drivers overrides] (run drivers overrides params))
  ([drivers overrides p]
   (let [drive (drives drivers overrides)
         x0 (into {} (for [s az/stock-order] [s (:x0 p)]))
         traj (vec (take (inc (:ticks p))
                         (iterate #(step % drive p) x0)))
         eq (last traj)
         idx (round3 (/ (reduce + (map #(get eq %) az/stock-order)) (count az/stock-order)))]
     {:trajectory (mapv (fn [m] (into {} (map (fn [[k v]] [(name k) (round3 v)]) m))) traj)
      :equilibrium (into {} (map (fn [[k v]] [(name k) (round3 v)]) eq))
      :involution-index idx
      :hypothesis? true})))

(defn compare-scenarios
  "Baseline vs an intervention (drive-overrides). Returns both runs + the per-stock delta
  and the involution-index improvement (>0 = the intervention eased the spiral). A
  STRUCTURAL what-if (G5), never a forecast (N3), never a directive (G11)."
  [drivers overrides]
  (let [base (run drivers {})
        interv (run drivers overrides)
        deltas (into {} (for [s az/stock-order]
                          [(name s) (round3 (- (get (:equilibrium interv) (name s))
                                               (get (:equilibrium base) (name s))))]))]
    {:baseline base
     :intervention interv
     :overrides (into {} (map (fn [[k v]] [(name k) v]) overrides))
     :stock-deltas deltas
     :index-improvement (round3 (- (:involution-index base) (:involution-index interv)))
     :hypothesis? true
     :forecast? false}))

;; ── datom emission (append-only EAVT; HYPOTHESIS; structural what-if) ─────────
(defn- add [e a v] [":db/add" e a v])

(defn datoms
  "Append-only EAVT datoms for one scenario comparison (equilibria + index improvement).
  Flagged hypothesis + structural (never forecast/directive)."
  [cmp]
  (let [e "shinogi-sim:involution-scenario"]
    (vec (concat
          [(add e ":shinogi.exam.sim/involution-index-baseline" (get-in cmp [:baseline :involution-index]))
           (add e ":shinogi.exam.sim/involution-index-intervention" (get-in cmp [:intervention :involution-index]))
           (add e ":shinogi.exam.sim/index-improvement" (:index-improvement cmp))
           (add e ":shinogi/hypothesis" ":true")
           (add e ":shinogi/derived" true)]
          (for [s az/stock-order]
            (add (str "shinogi-sim-eq:" (name s))
                 ":shinogi.exam.sim/equilibrium-baseline"
                 (get-in cmp [:baseline :equilibrium (name s)])))))))

(defn render-report [cmp]
  (str
   "## Stock-flow SIMULATION — vicious spiral vs a relief intervention (HYPOTHESIS, G5)\n\n"
   "_時系列シミュレーション: ループを結合行列、driver の net 圧力を外生入力として 9 stock を"
   "前進させ、構造的介入(エネルギー流の再設計)で involution が緩和へ反転するかを見る。"
   "**モデル上の what-if (G5) であり現実の予測ではない (N3)、指令でもない (G11)。**_\n\n"
   "- involution-index baseline: **" (get-in cmp [:baseline :involution-index]) "**"
   " → intervention: **" (get-in cmp [:intervention :involution-index]) "**"
   " (improvement **" (:index-improvement cmp) "**, >0 = 緩和)\n\n"
   "| stock | baseline eq | intervention eq | Δ |\n|---|---|---|---|\n"
   (str/join "\n"
             (for [s az/stock-order
                   :let [n (name s)]]
               (str "| " (az/stock-label s)
                    " | " (get-in cmp [:baseline :equilibrium n])
                    " | " (get-in cmp [:intervention :equilibrium n])
                    " | " (get (:stock-deltas cmp) n) " |")))
   "\n\n_Δ<0 = その stock の圧力が介入で下がった(好転)。_\n"))

;; ── CLI (bb) ─────────────────────────────────────────────────────────────────
#?(:clj
   (defn -main [& args]
     (let [seed (or (first args) "20-actors/shinogi/kotoba/seed.exam-involution.edn")
           drivers (vec (filter #(= (:type %) :driver) (clojure.edn/read-string (slurp seed))))
           ;; a sample relief intervention: route effort out of the zero-sum core + cushion withdrawal
           overrides {:effort-inflation -0.25 :positional-scarcity -0.2 :credential-signaling -0.15
                      :wellbeing-erosion -0.2 :labor-absorption-deficit -0.2
                      :effort-efficacy-collapse -0.2 :withdrawal-prevalence -0.15}
           cmp (compare-scenarios drivers overrides)]
       (println (render-report cmp)))))

#?(:clj
   (when (= *file* (System/getProperty "babashka.file"))
     (apply -main *command-line-args*)))
