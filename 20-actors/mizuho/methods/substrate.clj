#!/usr/bin/env bb
(ns mizuho.methods.substrate
  "_substrate — the minimal infra-robotics control substrate mizuho's clj methods need,
  faithfully ported from 20-actors/kuni-umi/robotics/control.py + safety.py (the Python
  methods import the same primitives across the actor boundary). Self-contained so the clj
  ports run on any babashka with no cross-language import (the ainori reuse pattern).

  Provides: a PID with anti-windup (clamp-aware integral hold), a deterministic closed-loop
  `simulate`, and a `safety-error` signal. Plants and controllers are plain maps of closures
  ({:measure :step} / {:reset :step}) so `simulate` stays generic.")

(defn round6 [x] (/ (Math/round (* (double x) 1e6)) 1e6))

;; ── SafetyError ────────────────────────────────────────────────────────────────
(defn safety-error
  "Signal a mizuho safety-gate violation (the clj analogue of substrate SafetyError)."
  [msg] (throw (ex-info msg {:type :safety-error})))

(defn safety-error? [e]
  (and (instance? clojure.lang.ExceptionInfo e) (= :safety-error (:type (ex-data e)))))

;; cross-domain forbidden-force anchors (N1, Mission Charter §1.12) — rejected even if a
;; caller mistakenly lists one in its allowlist.
(def forbidden-uses
  #{"weapon" "directed-energy" "munition" "fire-control" "interdiction"
    "covert-force" "surveillance-targeting"})

(defn assert-civilian
  "Closed-world civilian-use gate (N1). Raise (safety-error) unless `use` is explicitly in the
  domain's `permitted` allowlist and not a forbidden-force anchor."
  [use permitted]
  (when (forbidden-uses use)
    (safety-error (str "N1: use " (pr-str use) " is a forbidden-force use and can never be "
                       "energised (Mission Charter §1.12 constitutional invariant)")))
  (when-not (contains? (set permitted) use)
    (safety-error (str "use " (pr-str use) " is not permitted; allowlist " (pr-str permitted))))
  use)

;; ── PID (anti-windup: integral only advances when the output is NOT saturated) ──
(defn make-pid [{:keys [kp ki kd out-min out-max] :or {kd 0.0}}]
  {:kp kp :ki ki :kd kd :out-min out-min :out-max out-max
   :integral (atom 0.0) :prev-error (atom nil) :saturated (atom false)})

(defn pid-reset! [p]
  (reset! (:integral p) 0.0) (reset! (:prev-error p) nil) (reset! (:saturated p) false))

(defn pid-step! [p error dt]
  (let [pe @(:prev-error p)
        deriv (if (and pe (> dt 0)) (/ (- error pe) dt) 0.0)
        tentative (+ @(:integral p) (* error dt))
        raw (+ (* (:kp p) error) (* (:ki p) tentative) (* (:kd p) deriv))
        clamped (min (:out-max p) (max (:out-min p) raw))
        sat (not= clamped raw)]
    (reset! (:saturated p) sat)
    (when-not sat (reset! (:integral p) tentative))
    (reset! (:prev-error p) error)
    clamped))

;; ── deterministic closed-loop simulation ──────────────────────────────────────
;; plant      = {:measure (fn [] pv) :step (fn [command dt] …mutate…)}
;; controller = {:reset (fn []) :step (fn [error dt] command)}
(defn simulate
  [plant controller setpoint steps dt & {:keys [tol settle-window] :or {tol 1e-3 settle-window 10}}]
  ((:reset controller))
  (let [traj (transient [])
        errors (transient [])
        max-abs (atom 0.0)]
    (dotimes [k steps]
      (let [pv ((:measure plant))
            error (- setpoint pv)
            cmd ((:step controller) error dt)]
        (conj! traj [(round6 (* k dt)) pv cmd])
        (conj! errors (Math/abs (double error)))
        (swap! max-abs max (Math/abs (double error)))
        ((:step plant) cmd dt)))
    (let [errs (persistent! errors)
          final-pv ((:measure plant))
          steady-error (- setpoint final-pv)
          n (count errs)
          settling-step (loop [i 0]
                          (cond (>= i n) -1
                                (every? #(< % tol) (subvec errs i)) i
                                :else (recur (inc i))))
          tail (if (>= n settle-window) (subvec errs (- n settle-window)) errs)
          converged (boolean (and (seq tail) (every? #(< % tol) tail)))]
      {:setpoint setpoint
       :final-value (round6 final-pv)
       :steady-error (round6 steady-error)
       :converged converged
       :settling-step settling-step
       :max-abs-error (round6 @max-abs)
       :steps steps
       :trajectory (persistent! traj)})))
