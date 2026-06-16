;; ported from 20-actors/hikari/methods/_substrate.py (real port replacing the
;; unit_refactor stage-0 "TODO: port-failed" stub). NS fixed:
;; root.hikari.methods.substrate -> hikari.methods.substrate (20-actors is the bb
;; source root, so the actor.method shape resolves; the root.* prefix never did).
;;
;; _substrate.py merely re-exports the shared infra-robotics substrate that lives in
;; 20-actors/kuni-umi/robotics/ (control.py / kinematics.py / plant.py / safety.py).
;; Babashka has no Python sys.path re-export, so this single SELF-CONTAINED namespace
;; INLINES faithful 1:1 ports of those four modules — exactly the surface __all__
;; exposed: PID, ControlResult, Droop, DroopPI, simulate, PlanarArm, Pose,
;; joint-trajectory, FirstOrderPlant, MicrogridPlant, SafetyEnvelope, SafetyError,
;; assert-civilian, require-member-signature, witness-quorum-ok.
(ns hikari.methods.substrate
  "_substrate.py — shared infra-robotics substrate for hikari/methods.

  1:1 Clojure port of 20-actors/kuni-umi/robotics/{control,kinematics,plant,safety}.py
  (the modules _substrate.py re-exports). The Python dataclasses become string-keyed
  maps; mutable plants/controllers carry their state in atoms so the swing-equation /
  PID loops mutate exactly as the Python objects do. Pure arithmetic; no host I/O."
  (:require [clojure.string :as str]))

;; ── safety.py ────────────────────────────────────────────────────────────────
(def ^:const MIN-WITNESS-SIGS 2)

(def FORBIDDEN-USES
  #{"weapon" "directed-energy" "munition" "fire-control"
    "interdiction" "covert-force" "surveillance-targeting"})

;; SafetyError — a tagged ex-info so callers `(thrown? ... )` can pin it.
(defn safety-error
  "Raise the structural safety/charter refusal (mirrors safety.SafetyError)."
  [msg]
  (throw (ex-info msg {:type ::safety-error})))

(defn safety-error?
  "True iff `ex` is a SafetyError raised by this namespace."
  [ex]
  (= ::safety-error (:type (ex-data ex))))

(defn assert-civilian
  "Closed-world civilian-use gate (N1). Raise unless `use` is explicitly permitted.
  `permitted` is the domain's civilian allowlist; the cross-domain forbidden anchors
  are rejected even if a caller mistakenly lists one."
  [use permitted]
  (when (contains? FORBIDDEN-USES use)
    (safety-error
     (str "N1: use " (pr-str use) " is a forbidden-force use and can never be energised "
          "(Mission Charter §1.12 constitutional invariant)")))
  (when-not (contains? (set permitted) use)
    (safety-error
     (str "N1: use " (pr-str use) " is not in the civilian allowlist " (pr-str permitted) "; "
          "closed-world refusal (only explicitly-permitted civilian uses run)"))))

(defn require-member-signature
  "No-server-key gate (G15 / G7). Raise unless a member/operator signs and the
  platform holds no key. A non-empty server-sig is a structural violation; an empty
  member-sig means nobody authorised the action."
  ([member-sig] (require-member-signature member-sig ""))
  ([member-sig server-sig]
   (when (and server-sig (not= "" server-sig))
     (safety-error
      (str "G15/G7 violation: a server/platform signature was supplied; the platform "
           "holds no key and never signs actuation (ADR-2605231525)")))
   (when (or (nil? member-sig) (= "" member-sig))
     (safety-error
      (str "G15/G7 violation: a member/operator signature is required to authorise "
           "any actuation (no-server-key)")))))

(defn witness-quorum-ok
  "Witness quorum >=2 independent robot DIDs (G8); N<2 or duplicates rejected.
  Returns a string-keyed map (does not raise) so callers can attach the
  Council-escalation flag to a Datom."
  [witness-sigs]
  (cond
    (< (count witness-sigs) MIN-WITNESS-SIGS)
    {"ok" false
     "reason" (str "witness quorum " (count witness-sigs) " < " MIN-WITNESS-SIGS " (G8 constitutional)")
     "escalate_council_lv6" true}
    (< (count (set witness-sigs)) MIN-WITNESS-SIGS)
    {"ok" false
     "reason" "duplicate witness DIDs detected (G8)"
     "escalate_council_lv6" true}
    :else {"ok" true "reason" "witness quorum satisfied"}))

(defn safety-envelope
  "A motion safety envelope (frozen SafetyEnvelope dataclass → immutable map)."
  ([] (safety-envelope {}))
  ([{:keys [max-joint-speed human-proximity-speed max-reach]
     :or {max-joint-speed 1.0 human-proximity-speed 0.25 max-reach ##Inf}}]
   {:max-joint-speed max-joint-speed
    :human-proximity-speed human-proximity-speed
    :max-reach max-reach}))

(defn check-trajectory
  "Validate a joint-space trajectory. Returns {\"ok\" bool \"violations\" [...]}.
  Per-step joint rate |Δq|/dt must stay under the applicable ceiling (the lower
  human-proximity ceiling whenever a person may be present)."
  ([env trajectory dt] (check-trajectory env trajectory dt false))
  ([env trajectory dt human-present]
   (let [ceiling (if human-present (:human-proximity-speed env) (:max-joint-speed env))
         violations
         (reduce
          (fn [vs i]
            (let [prev (nth trajectory (dec i))
                  cur  (nth trajectory i)]
              (if (not= (count prev) (count cur))
                (conj vs (str "step " i ": joint-count mismatch"))
                (reduce
                 (fn [vs j]
                   (let [a (nth prev j) b (nth cur j)
                         rate (if (> dt 0) (/ (Math/abs (double (- b a))) dt) ##Inf)]
                     (if (> rate (+ ceiling 1e-9))
                       (conj vs (str "step " i " joint " j ": rate "
                                     (format "%.4f" rate) " > ceiling " (format "%.4f" ceiling)
                                     (if human-present " (human present)" "")))
                       vs)))
                 vs
                 (range (count prev))))))
          []
          (range 1 (count trajectory)))]
     {"ok" (empty? violations) "violations" violations})))

;; ── kinematics.py ────────────────────────────────────────────────────────────
(defn pose
  "A planar end-effector pose (frozen Pose dataclass → immutable map)."
  ([x y] (pose x y 0.0))
  ([x y theta] {:x x :y y :theta theta}))

(defn planar-arm
  "A planar serial arm defined by its link lengths (metres)."
  [link-lengths]
  (let [lengths (vec link-lengths)
        max-reach (reduce + 0.0 lengths)
        longest (apply max lengths)
        rest (- max-reach longest)
        min-reach (max 0.0 (- longest rest))]
    {:link-lengths lengths
     :max-reach max-reach
     :min-reach min-reach}))

(defn arm-fk
  "Forward kinematics: joint angles (rad, relative) → end-effector Pose."
  [arm joints]
  (let [lengths (:link-lengths arm)]
    (when (not= (count joints) (count lengths))
      (throw (ex-info (str "expected " (count lengths) " joints, got " (count joints)) {})))
    (let [[x y theta]
          (reduce (fn [[x y theta] [length q]]
                    (let [theta (+ theta q)]
                      [(+ x (* length (Math/cos theta)))
                       (+ y (* length (Math/sin theta)))
                       theta]))
                  [0.0 0.0 0.0]
                  (map vector lengths joints))]
      (pose (-> x (* 1e9) Math/round (/ 1e9))
            (-> y (* 1e9) Math/round (/ 1e9))
            (-> theta (* 1e9) Math/round (/ 1e9))))))

(defn arm-reachable
  "True iff (x, y) lies within the arm's annular workspace."
  [arm x y]
  (let [r (Math/hypot (double x) (double y))]
    (and (<= (- (:min-reach arm) 1e-9) r)
         (<= r (+ (:max-reach arm) 1e-9)))))

(defn arm-ik2
  "Analytic 2-link inverse kinematics. Returns [q0 q1] (rad) or nil if unreachable.
  `elbow-up` selects between the two mirror solutions."
  ([arm x y] (arm-ik2 arm x y true))
  ([arm x y elbow-up]
   (let [lengths (:link-lengths arm)]
     (when (not= 2 (count lengths))
       (throw (ex-info "ik2 requires a 2-link arm" {})))
     (let [[l1 l2] lengths
           r2 (+ (* x x) (* y y))
           cos-q1 (/ (- r2 (* l1 l1) (* l2 l2)) (* 2.0 l1 l2))]
       (if (or (< cos-q1 (- -1.0 1e-9)) (> cos-q1 (+ 1.0 1e-9)))
         nil
         (let [cos-q1 (min 1.0 (max -1.0 cos-q1))
               sin-q1 (Math/sqrt (max 0.0 (- 1.0 (* cos-q1 cos-q1))))
               sin-q1 (if elbow-up (- sin-q1) sin-q1)
               q1 (Math/atan2 sin-q1 cos-q1)
               q0 (- (Math/atan2 (double y) (double x))
                     (Math/atan2 (* l2 (Math/sin q1)) (+ l1 (* l2 (Math/cos q1)))))]
           [(-> q0 (* 1e9) Math/round (/ 1e9))
            (-> q1 (* 1e9) Math/round (/ 1e9))]))))))

(defn joint-trajectory
  "Linear joint-space interpolation from q-start to q-goal over `steps` steps.
  Returns `steps + 1` configurations (inclusive of both endpoints)."
  [q-start q-goal steps]
  (when (not= (count q-start) (count q-goal))
    (throw (ex-info "start and goal must have equal joint count" {})))
  (when (< steps 1)
    (throw (ex-info "steps must be >= 1" {})))
  (vec (for [k (range (inc steps))]
         (let [a (/ (double k) steps)]
           (vec (map (fn [s g] (+ s (* a (- g s)))) q-start q-goal))))))

;; ── plant.py ─────────────────────────────────────────────────────────────────
;; A Plant is anything with measure() and step(command, dt). Mutable state lives in
;; an atom so `simulate` advances the plant exactly as the Python object mutates.

(defn first-order-plant
  "Generic first-order lag: τ·ẋ = −x + K·u (+ constant disturbance d)."
  [{:keys [gain tau disturbance x] :or {gain 1.0 tau 1.0 disturbance 0.0 x 0.0}}]
  (let [state (atom {:x x})]
    {:measure (fn [] (:x @state))
     :step (fn [command dt]
             (let [xv (:x @state)
                   dxdt (/ (+ (- xv) (* gain command) disturbance) tau)]
               (swap! state assoc :x (+ xv (* dxdt dt)))))
     :state state}))

(defn microgrid-plant
  "Islanded microgrid frequency dynamics (swing equation) + battery SoC.
  Controlled quantity is bus frequency (Hz). Returns a Plant map; `:set-load`,
  `:f-nom`, and `:soc` expose the fields the commissioning harness reads."
  [{:keys [f-nom inertia-h damping-d s-base p-load battery-kwh soc f]
    :or {f-nom 50.0 inertia-h 4.0 damping-d 1.5 s-base 200.0
         p-load 100.0 battery-kwh 500.0 soc 0.6 f 50.0}}]
  (let [state (atom {:p-load p-load :soc soc :f f})]
    {:f-nom f-nom
     :measure (fn [] (:f @state))
     :set-load (fn [p-load-kw] (swap! state assoc :p-load p-load-kw))
     :soc (fn [] (:soc @state))
     :step (fn [command dt]
             (let [{:keys [p-load soc f]} @state
                   imbalance-pu (/ (- command p-load) s-base)
                   dfdt (/ (- (* imbalance-pu f-nom) (* damping-d (- f f-nom)))
                           (* 2.0 inertia-h))
                   f' (+ f (* dfdt dt))
                   net-kwh (* (- command p-load) (/ dt 3600.0))
                   soc' (min 1.0 (max 0.0 (+ soc (/ net-kwh battery-kwh))))]
               (swap! state assoc :f f' :soc soc')))
     :state state}))

;; ── control.py ───────────────────────────────────────────────────────────────
;; round-to-n-decimals helper (Python round(x, n), banker's rounding).
(defn- round-n [x n]
  (-> (java.math.BigDecimal/valueOf (double x))
      (.setScale (int n) java.math.RoundingMode/HALF_EVEN)
      .doubleValue))

(defn pid
  "Limited PID with anti-windup — mirrors open-ot PID_LIMITED. Mutable state in an
  atom; `:step` returns the clamped command, `:reset` clears integral/prev-error."
  [{:keys [kp ki kd out-min out-max]
    :or {ki 0.0 kd 0.0 out-min ##-Inf out-max ##Inf}}]
  (let [state (atom {:integral 0.0 :prev-error nil :saturated false})]
    {:kind :pid
     :reset (fn [] (reset! state {:integral 0.0 :prev-error nil :saturated false}))
     :step (fn [error dt]
             (let [{:keys [integral prev-error]} @state
                   deriv (if (and (some? prev-error) (> dt 0))
                           (/ (- error prev-error) dt)
                           0.0)
                   tentative (+ integral (* error dt))
                   raw (+ (* kp error) (* ki tentative) (* kd deriv))
                   clamped (min out-max (max out-min raw))
                   saturated (not= clamped raw)]
               (swap! state assoc
                      :saturated saturated
                      :integral (if saturated integral tentative)
                      :prev-error error)
               clamped))
     :state state}))

(defn droop
  "Proportional frequency/voltage droop — mirrors open-ot DROOP_P_F."
  [{:keys [nominal droop-r p-base p-min p-max]
    :or {p-base 0.0 p-min ##-Inf p-max ##Inf}}]
  {:nominal nominal :droop-r droop-r :p-base p-base :p-min p-min :p-max p-max
   :command (fn [measured]
              (let [p (+ p-base (/ (- nominal measured) droop-r))]
                (min p-max (max p-min p))))})

(defn droop-pi
  "Primary droop (instantaneous) + secondary PI (zero steady-state error).
  `:step` calls with error = nominal − measured; output is clamped to the droop band."
  [a-droop a-pid]
  {:kind :droop-pi
   :droop a-droop :pid a-pid
   :reset (fn [] ((:reset a-pid)))
   :step (fn [error dt]
           (let [measured (- (:nominal a-droop) error)
                 cmd (+ ((:command a-droop) measured) ((:step a-pid) error dt))]
             (min (:p-max a-droop) (max (:p-min a-droop) cmd))))})

(defn simulate
  "Run a closed loop against a plant and report convergence.
  Returns a string-keyed ControlResult map. Deterministic: same inputs ⇒ same
  trajectory. `converged` iff |error| < tol for the last `settle-window` steps."
  [plant controller setpoint steps dt & {:keys [tol settle-window]
                                          :or {tol 1e-3 settle-window 10}}]
  ((:reset controller))
  (let [{:keys [traj errors max-abs]}
        (reduce
         (fn [{:keys [traj errors max-abs]} k]
           (let [pv ((:measure plant))
                 error (- setpoint pv)
                 cmd ((:step controller) error dt)]
             ((:step plant) cmd dt)
             {:traj (conj traj [(round-n (* k dt) 6) pv cmd])
              :errors (conj errors (Math/abs (double error)))
              :max-abs (max max-abs (Math/abs (double error)))}))
         {:traj [] :errors [] :max-abs 0.0}
         (range steps))
        final-pv ((:measure plant))
        steady-error (- setpoint final-pv)
        settling-step (loop [i 0]
                        (cond
                          (>= i (count errors)) -1
                          (every? #(< % tol) (subvec errors i)) i
                          :else (recur (inc i))))
        tail (if (>= (count errors) settle-window)
               (subvec errors (- (count errors) settle-window))
               errors)
        converged (and (seq tail) (every? #(< % tol) tail))]
    {"setpoint" setpoint
     "final_value" (round-n final-pv 6)
     "steady_error" (round-n steady-error 6)
     "converged" converged
     "settling_step" settling-step
     "max_abs_error" (round-n max-abs 6)
     "steps" steps
     "trajectory" traj}))
