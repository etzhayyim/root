#!/usr/bin/env bb
;; Working Clojure port of methods/terminal_cycle.py.
(ns niyaku.methods.terminal-cycle
  "terminal_cycle — end-to-end vessel-discharge orchestration (ADR-2606082000).

  Ties the method cores into one deterministic discharge simulation (berth → stow → spreader →
  hoist → traverse → yard):

    stow-plan       → where each box sits + the no-rehandle discharge order
    crane-dynamics  → per-box hoist + anti-sway traverse time & residual sway
    agv-transfer    → quay-apron → yard legs dispatched (LPT) across the AGV fleet

  Returns a discharge report: overall discharge time (max of the crane-bound and AGV-bound
  timelines, since they pipeline), terminal productivity (moves/hour), the worst per-box
  residual sway, and a per-box ledger. Pure planning compute; moves no real equipment
  (G12 no-server-key). use-isaac falls back to the analytic model (isaac_sway_sim is not part
  of the clj port surface).

  Run:  bb --classpath 20-actors 20-actors/niyaku/methods/terminal_cycle.clj"
  (:require [niyaku.methods.agv-transfer :as agv]
            [niyaku.methods.crane-dynamics :as cd]
            [niyaku.methods.stow-plan :as st]
            [clojure.string :as str]))

(defn yard-layout [& {:keys [apron-to-yard-m per-row-offset-m]
                      :or {apron-to-yard-m 120.0 per-row-offset-m 6.0}}]
  {:apron-to-yard-m apron-to-yard-m :per-row-offset-m per-row-offset-m})

(defn- round2 [x] (/ (Math/round (* (double x) 100.0)) 100.0))
(defn- round4 [x] (/ (Math/round (* (double x) 10000.0)) 10000.0))

(defn moves-per-hour [report]
  (if (<= (:discharge-time-s report) 0) 0.0
      (/ (* 3600.0 (:moves report)) (:discharge-time-s report))))

(defn- traverse-distance
  "Ship→shore traverse distance for a box: outreach scaled by yard row, bounded by the rail."
  [crane slot-row]
  (let [base (min (* (:rail-length crane) 0.5) 25.0)]
    (min (:rail-length crane) (+ base (* slot-row 2.0)))))

(defn simulate-discharge
  "Simulate discharging every box bound for `discharge-port`. The crane works boxes serially in
  the no-rehandle order; AGVs run the yard legs in parallel (LPT). use-isaac falls back to the
  analytic crane model."
  [containers rotation discharge-port bays rows tiers
   & {:keys [crane agv agv-ids yard plan use-isaac]
      :or {crane (cd/make-crane) agv (agv/make-agv) agv-ids ["AGV1" "AGV2" "AGV3"]
           yard (yard-layout) plan nil use-isaac false}}]
  (let [plan (or plan (st/build-stow-plan containers rotation bays rows tiers))
        by-id (into {} (map (juxt :box-id identity) containers))
        seq* (filter (fn [b] (and (by-id b) (= (:discharge-port (by-id b)) discharge-port)))
                     (st/discharge-sequence plan discharge-port))
        ;; crane works each box serially; collect moves + per-box records
        {:keys [crane-timeline max-sway moves records]}
        (reduce
         (fn [acc box-id]
           (let [slot (st/slot-of plan box-id)
                 dist (traverse-distance crane (:row slot))
                 res (cd/simulate-traverse crane dist :max-time-s 300.0)
                 hoist (/ (+ (* (:cable-length crane) 0.4) (* (:tier slot) 2.6) 12.0) 1.5)
                 crane-time (+ (:settle-time-s res) hoist)
                 sway (:residual-sway-m res)
                 agv-dist (+ (:apron-to-yard-m yard) (* (:row slot) (:per-row-offset-m yard)))]
             (-> acc
                 (update :crane-timeline + crane-time)
                 (update :max-sway max sway)
                 (update :moves conj (agv/move box-id agv-dist))
                 (update :records conj {:box-id box-id :crane-time-s (round2 crane-time)
                                        :residual-sway-m (round4 sway) :agv-id ""
                                        :agv-time-s (round2 (agv/travel-time agv-dist agv))}))))
         {:crane-timeline 0.0 :max-sway 0.0 :moves [] :records []}
         seq*)
        disp (agv/dispatch moves agv-ids agv)
        box->agv (into {} (for [[a bids] (:assignment disp) bid bids] [bid a]))
        records (mapv (fn [r] (assoc r :agv-id (get box->agv (:box-id r) ""))) records)
        agv-makespan (agv/makespan disp)]
    {:records records
     :crane-timeline-s (round2 crane-timeline)
     :agv-makespan-s (round2 agv-makespan)
     :discharge-time-s (round2 (max crane-timeline agv-makespan))
     :max-residual-sway-m (round4 max-sway)
     :moves (count records)}))

(defn main [& _]
  (let [boxes (map-indexed (fn [i _] (st/container (str "B" i) (- 20.0 i) "JPYOK")) (range 6))
        r (simulate-discharge boxes ["JPYOK"] "JPYOK" 2 2 3)]
    (println (format "niyaku discharge: %d moves  crane %.1fs  agv %.1fs  overall %.1fs  %.1f moves/h  max-sway %.4f m"
                     (:moves r) (double (:crane-timeline-s r)) (double (:agv-makespan-s r))
                     (double (:discharge-time-s r)) (moves-per-hour r) (double (:max-residual-sway-m r))))))

(when (= *file* (System/getProperty "babashka.file"))
  (main))
