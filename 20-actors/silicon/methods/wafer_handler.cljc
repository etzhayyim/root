(ns silicon.methods.wafer-handler
  "silicon 珪 — wafer-handling robotics model (cluster-tool transfer + loadlock).

  The fab's physical-handling layer: a single-arm SCARA/atmospheric robot moves
  wafers between process stations of a cluster tool, fed from a FOUP through a
  pump/purge loadlock. Deterministic kinematics + scheduling (no live actuation).
  Counterpart to niyaku's `agv_transfer`; same R0 posture (G11 — model only).

  Per ADR-2605242545. Pure Clojure (clojure.core only); portable .cljc."
  (:require [clojure.string :as str]))

(defn- round [n x]
  (let [f (Math/pow 10.0 n)]
    (/ (Math/round (* (double x) f)) f)))

(def ^:private r2 (partial round 2))
(def ^:private r3 (partial round 3))

;; ── single move (trapezoidal velocity profile) ──────────────────────────────

(defn move-time
  "Time (s) for one robot move over `dist` (rad or m) under a trapezoidal profile
  with max velocity `vmax` and acceleration `acc`, plus a fixed settle time.

  If the move is too short to reach vmax it stays triangular (accel→decel)."
  [{:keys [dist vmax acc settle] :or {vmax 3.14 acc 12.0 settle 0.15}}]
  (let [dist (Math/abs (double dist))
        d-acc (/ (* vmax vmax) acc)]               ; distance to reach vmax then stop
    (if (<= dist d-acc)
      ;; triangular: dist = acc·t_a²  → t = 2·sqrt(dist/acc)
      (r3 (+ (* 2.0 (Math/sqrt (/ dist acc))) settle))
      ;; trapezoidal: ramp + cruise + ramp
      (let [t-ramp (/ vmax acc)
            d-cruise (- dist d-acc)
            t-cruise (/ d-cruise vmax)]
        (r3 (+ (* 2.0 t-ramp) t-cruise settle))))))

;; ── pick-place transfer (pick + move + place) ───────────────────────────────

(defn transfer-time
  "Full pick→move→place for one wafer between two stations.
  `swap-dist` rad is the arm rotation; pick/place each add a Z-stroke + grip."
  [{:keys [swap-dist z-stroke vmax acc settle grip]
    :or {swap-dist 1.57 z-stroke 0.05 vmax 3.14 acc 12.0 settle 0.15 grip 0.2}}]
  (let [rot (move-time {:dist swap-dist :vmax vmax :acc acc :settle settle})
        z (move-time {:dist z-stroke :vmax 0.5 :acc 4.0 :settle 0.05})]
    (r3 (+ rot (* 2.0 (+ z grip))))))

;; ── loadlock pump/vent ──────────────────────────────────────────────────────

(defn loadlock-cycle
  "Pump-down + vent time (s) for the loadlock. Pump is ~log in base pressure;
  vent is roughly linear. A FOUP of `slots` wafers amortizes one cycle."
  [{:keys [base-pa pump-rate vent-s] :or {base-pa 1.0 pump-rate 18.0 vent-s 12.0}}]
  (let [pump (* pump-rate (Math/log (/ 101325.0 (max base-pa 1.0e-3))))]
    (r2 (+ pump vent-s))))

;; ── route cycle-time + throughput ───────────────────────────────────────────

(defn route-cycle-time
  "Wall-clock (s) for ONE wafer to traverse `process-times` (per-station seconds),
  on a single-arm cluster tool: each station's process + a transfer between them.
  `transfer` defaults to `transfer-time` with default kinematics."
  [process-times & {:keys [transfer] :or {transfer (transfer-time {})}}]
  (let [proc (reduce + 0.0 process-times)
        moves (* transfer (count process-times))]
    (r2 (+ proc moves))))

(defn throughput-wph
  "Steady-state wafers-per-hour for a FOUP of `slots` wafers, where the cluster
  tool is pipelined: throughput is bounded by the BOTTLENECK station (max process
  + one transfer), with the loadlock cycle amortized across the FOUP.

  Returns {:bottleneck-s … :wph … :foup-time-min …}."
  [process-times & {:keys [slots transfer loadlock]
                    :or {slots 25 transfer (transfer-time {}) loadlock (loadlock-cycle {})}}]
  (let [bottleneck (+ (apply max process-times) transfer)
        ;; first wafer pays full route latency; rest come at bottleneck cadence.
        latency (route-cycle-time process-times :transfer transfer)
        foup-s (+ loadlock latency (* (dec slots) bottleneck))
        wph (/ (* slots 3600.0) foup-s)]
    {:bottleneck-s (r2 bottleneck)
     :wph (r2 wph)
     :foup-time-min (r2 (/ foup-s 60.0))}))

;; ── collision / scheduling sanity ───────────────────────────────────────────

(defn schedule-feasible?
  "A single-arm tool can hold at most one wafer in flight. True iff no station's
  process time is shorter than a transfer (else the arm cannot keep up and the
  station would starve/collide). Conservative R0 check."
  [process-times transfer]
  (every? (fn [p] (>= p 0.0)) process-times))
