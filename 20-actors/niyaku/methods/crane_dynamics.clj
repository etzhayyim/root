#!/usr/bin/env bb
;; Working Clojure port of methods/crane_dynamics.py.
(ns niyaku.methods.crane-dynamics
  "crane_dynamics — gantry / ship-to-shore (STS) crane anti-sway physics core (ADR-2606082000).

  The defining control problem of automated container handling is ANTI-SWAY: a quay crane moves
  a 20-40 t container suspended on cables while the trolley traverses 30-50 m ship→shore. The
  load is a pendulum; an aggressive move excites residual sway that must settle to < a few cm
  before the spreader can land the box. Cart + hanging payload — the same Cartpole topology
  isaac_sway_sim drives through the clean-room isaacsim.core.api surface.

  Analytic/control core: a physically-correct hanging pendulum (RK4), a state-feedback
  anti-sway controller, and a ZV input-shaper (the terminal-deployed technique). Pure compute,
  no NumPy; state is a plain [x x_dot theta theta_dot] vector. Equilibrium is the load hanging
  down (theta=0, STABLE — gravity restores).

  Run:  bb --classpath 20-actors 20-actors/niyaku/methods/crane_dynamics.clj"
  (:require [clojure.string :as str]))

(defn make-crane
  [& {:keys [cable-length gravity sway-damping accel-max velocity-max rail-length]
      :or {cable-length 30.0 gravity 9.81 sway-damping 0.02
           accel-max 0.6 velocity-max 4.0 rail-length 60.0}}]
  {:cable-length cable-length :gravity gravity :sway-damping sway-damping
   :accel-max accel-max :velocity-max velocity-max :rail-length rail-length})

(defn- clamp [v lim] (max (- lim) (min lim v)))

(defn natural-frequency
  "Undamped sway natural frequency ω = sqrt(g/L) (rad/s)."
  [c] (Math/sqrt (/ (:gravity c) (:cable-length c))))

(defn sway-period
  "Sway period T = 2π/ω (s) — sets the input-shaper impulse spacing."
  [c] (/ (* 2.0 Math/PI) (natural-frequency c)))

(defn derivatives
  "Continuous-time state derivative for [x x_dot theta theta_dot]. Full (non-linearised)
  hanging-pendulum-on-trolley with viscous sway damping; trolley accel = clamped command u."
  [c state u]
  (let [[_ x-dot theta theta-dot] state
        a (clamp u (:accel-max c))
        L (:cable-length c)
        g (:gravity c)
        zeta-w (* (:sway-damping c) (natural-frequency c))
        theta-acc (+ (* (- (/ g L)) (Math/sin theta))
                     (* (- (/ a L)) (Math/cos theta))
                     (* -2.0 zeta-w theta-dot))]
    [x-dot a theta-dot theta-acc]))

(defn- add4 [s k h] (mapv (fn [si ki] (+ si (* h ki))) s k))

(defn step
  "Advance one step by classic RK4 (stable for the stiff sway mode); enforce velocity envelope."
  [c state u dt]
  (let [k1 (derivatives c state u)
        k2 (derivatives c (add4 state k1 (/ dt 2.0)) u)
        k3 (derivatives c (add4 state k2 (/ dt 2.0)) u)
        k4 (derivatives c (add4 state k3 dt) u)
        nxt (mapv (fn [i] (+ (nth state i)
                             (* (/ dt 6.0)
                                (+ (nth k1 i) (* 2.0 (nth k2 i)) (* 2.0 (nth k3 i)) (nth k4 i)))))
                  (range 4))]
    (assoc nxt 1 (clamp (nth nxt 1) (:velocity-max c)))))

;; ── anti-sway state-feedback controller ─────────────────────────────────────
(defn make-controller
  [& {:keys [kp kd k-theta k-thetad] :or {kp 0.4 kd 1.7 k-theta 5.0 k-thetad 3.0}}]
  {:kp kp :kd kd :k-theta k-theta :k-thetad k-thetad})

(defn command
  "u = -kp·ω²(x-x_target) - kd·ω·x_dot + k_theta·θ + k_thetad/ω·θ_dot, clamped to accel-max.
  The sway terms (positive sign at θ=0 equilibrium) actively bleed pendulum energy."
  [ctrl c state x-target]
  (let [[x x-dot theta theta-dot] state
        w (natural-frequency c)
        u (+ (* (- (:kp ctrl)) w w (- x x-target))
             (* (- (:kd ctrl)) w x-dot)
             (* (:k-theta ctrl) theta)
             (* (/ (:k-thetad ctrl) w) theta-dot))]
    (clamp u (:accel-max c))))

;; ── ZV input shaper (open-loop anti-sway) ────────────────────────────────────
(defn zv-shaper
  "Zero-Vibration shaper impulses [[t0 a0] [t1 a1]] (Singer-Seering), amplitudes summing to 1."
  [c]
  (let [zeta (:sway-damping c)
        w (natural-frequency c)
        wd (* w (Math/sqrt (max 1e-9 (- 1.0 (* zeta zeta)))))
        td (/ Math/PI wd)
        k (Math/exp (/ (* (- zeta) Math/PI) (Math/sqrt (max 1e-9 (- 1.0 (* zeta zeta))))))
        a0 (/ 1.0 (+ 1.0 k))
        a1 (/ k (+ 1.0 k))]
    [[0.0 a0] [td a1]]))

;; ── high-level traverse simulation ──────────────────────────────────────────
(defn simulate-traverse
  "Drive the trolley from rest at x=0 to x-target under anti-sway control. 'Settled' = trolley
  within pos-tol-m AND lateral load excursion (L·sinθ) within sway-tol-m AND sway rate ~0."
  [c x-target & {:keys [controller dt max-time-s pos-tol-m sway-tol-m record]
                 :or {controller (make-controller) dt (/ 1.0 50.0) max-time-s 120.0
                      pos-tol-m 0.10 sway-tol-m 0.05 record false}}]
  (when (> (Math/abs (double x-target)) (:rail-length c))
    (throw (ex-info (str "x_target " x-target " exceeds rail_length " (:rail-length c))
                    {:type :value-error})))
  (let [L (:cable-length c)
        n (int (/ max-time-s dt))
        finalize (fn [state peak settle-time steps traj]
                   {:reached (>= settle-time 0.0)
                    :settle-time-s (if (>= settle-time 0.0) settle-time max-time-s)
                    :residual-sway-m (Math/abs (* L (Math/sin (nth state 2))))
                    :peak-sway-m peak
                    :final-x (nth state 0)
                    :steps steps
                    :trajectory (persistent! traj)})]
    (loop [i 0, state [0.0 0.0 0.0 0.0], peak 0.0, traj (transient [])]
      (if (>= i n)
        (finalize state peak -1.0 n traj)
        (let [u (command controller c state x-target)
              nstate (step c state u dt)
              sway (Math/abs (* L (Math/sin (nth nstate 2))))
              npeak (max peak sway)
              traj' (if record (conj! traj nstate) traj)
              settled (and (<= (Math/abs (- (nth nstate 0) x-target)) pos-tol-m)
                           (<= sway sway-tol-m)
                           (<= (Math/abs (nth nstate 3)) 0.01))]
          (if settled
            (finalize nstate npeak (* (+ i 1) dt) (+ i 1) traj')
            (recur (inc i) nstate npeak traj')))))))

(defn lift-cycle-time
  "Single-box cycle time (s): hoist-up → traverse (anti-sway settle time) → hoist-down."
  [c traverse-m hoist-up-m hoist-down-m & {:keys [hoist-speed-mps] :or {hoist-speed-mps 1.5}}]
  (let [res (simulate-traverse c traverse-m)
        hoist (/ (+ hoist-up-m hoist-down-m) (max 1e-6 hoist-speed-mps))]
    (+ (:settle-time-s res) hoist)))

(defn moves-per-hour
  "Convert a per-box cycle time to the terminal productivity KPI."
  [cycle-time-s]
  (when (<= cycle-time-s 0)
    (throw (ex-info "cycle_time_s must be positive" {:type :value-error})))
  (/ 3600.0 cycle-time-s))

(defn main [& _]
  (let [c (make-crane :cable-length 25.0 :accel-max 0.7)
        res (simulate-traverse c 30.0 :max-time-s 300.0)]
    (println (format "niyaku crane anti-sway: ω=%.4f rad/s  T=%.2fs" (natural-frequency c) (sway-period c)))
    (println (format "  traverse 30 m → reached=%s settle=%.2fs residual=%.4f m peak=%.4f m"
                     (:reached res) (double (:settle-time-s res))
                     (double (:residual-sway-m res)) (double (:peak-sway-m res))))
    (let [t (lift-cycle-time c 30.0 20.0 18.0)]
      (println (format "  cycle %.1fs → %.1f moves/hour" t (moves-per-hour t))))))

(when (= *file* (System/getProperty "babashka.file"))
  (main))
