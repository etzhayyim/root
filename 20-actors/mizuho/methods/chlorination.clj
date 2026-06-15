#!/usr/bin/env bb
;; Working Clojure port of methods/chlorination.py.
(ns mizuho.methods.chlorination
  "chlorination — mizuho residual-disinfection dosing loop (R0 :representative).

  Proves the dosing loop holds a safe free-chlorine residual in distribution: the residual
  decays (demand + time), a secondary-PI doser raises it to a target (default 0.5 mg/L), and —
  critically — the dose is STRUCTURALLY CLAMPED so the modeled residual can never exceed the
  regulatory ceiling MAX-RESIDUAL-MGL = 4.0 mg/L (WHO guideline / US-EPA MRDL).

  mizuho gates: G4 plain PI (never commercial UV/dosing firmware) · G6 anti-paternalism —
  chlorine disinfection is community-wide (no per-member consent) but FLUORIDE refuses unless
  per-member-consent=true (no mandatory fluoridation) · G10 live dosing consent-gated; this
  module is offline sim only.

  Run:  bb --classpath 20-actors 20-actors/mizuho/methods/chlorination.clj"
  (:require [mizuho.methods.substrate :as s]))

;; WHO guideline / US-EPA maximum residual disinfectant level for free chlorine. A modeled
;; residual can NEVER exceed this — enforced by a structural clamp, not merely by tuning.
(def MAX-RESIDUAL-MGL 4.0)

;; "disinfect" = free chlorine (community-wide, no consent). "fluoridate" = fluoride (personal
;; supplementation; requires per-member consent under G6 anti-paternalism).
(def permitted-agents #{"disinfect" "fluoridate"})

(defn residual-chlorine-plant
  "Free-chlorine residual dynamics in a distribution volume (a Plant): dC/dt = command −
  k_decay·C, with a hard ceiling clamp (defence in depth on top of the clamped doser)."
  [residual-mgl k-decay]
  (let [c (atom (double residual-mgl))]
    {:measure (fn [] @c)
     :residual c
     :step (fn [command dt]
             (let [dcdt (- command (* k-decay @c))]
               (swap! c #(+ % (* dcdt dt)))
               (when (< @c 0.0) (reset! c 0.0))
               (when (> @c MAX-RESIDUAL-MGL) (reset! c MAX-RESIDUAL-MGL))))}))

(defn clamped-doser
  "A PI doser whose output is STRUCTURALLY clamped so the residual can never exceed the
  ceiling: max-dose·dt ≤ ceiling − current. Independent of gains — no kp/ki can cross the
  regulatory limit."
  [plant pid]
  {:reset (fn [] (s/pid-reset! pid))
   :step (fn [error dt]
           (let [raw (max 0.0 (s/pid-step! pid error dt))
                 headroom (- MAX-RESIDUAL-MGL ((:measure plant)))
                 max-dose-rate (if (> dt 0) (max 0.0 (/ headroom dt)) 0.0)]
             (min raw max-dose-rate)))})

(defn commission-dosing
  "Run the dosing acceptance test. Raises (safety-error) BEFORE any run on a gate violation.
  Returns a DosingResult map."
  [{:keys [agent target-residual-mgl per-member-consent k-decay kp ki steps dt]
    :or {agent "disinfect" target-residual-mgl 0.5 per-member-consent false
         k-decay 0.05 kp 0.4 ki 0.15 steps 4000 dt 0.1}}]
  (when-not (permitted-agents agent)
    (s/safety-error (str "dosing agent " (pr-str agent) " is not permitted; allowlist "
                         (pr-str permitted-agents))))
  (when (and (= agent "fluoridate") (not per-member-consent))
    (s/safety-error (str "G6: fluoride dosing requires per-member-consent=true (no mandatory "
                         "fluoridation; anti-paternalism). Chlorine disinfection needs no consent.")))
  (when (> target-residual-mgl MAX-RESIDUAL-MGL)
    (s/safety-error (str "target residual " target-residual-mgl " mg/L exceeds the regulatory "
                         "ceiling " MAX-RESIDUAL-MGL " mg/L (WHO/EPA); structurally refused")))
  (let [plant (residual-chlorine-plant 0.0 k-decay)
        pid (s/make-pid {:kp kp :ki ki :out-min 0.0 :out-max MAX-RESIDUAL-MGL})
        doser (clamped-doser plant pid)
        res (s/simulate plant doser target-residual-mgl steps dt :tol 1e-3)
        max-residual (reduce max 0.0 (map second (:trajectory res)))
        settling-seconds (if (>= (:settling-step res) 0) (* (:settling-step res) dt) -1.0)]
    {:agent agent
     :target-residual-mgl target-residual-mgl
     :final-residual-mgl (s/round6 (:final-value res))
     :max-residual-mgl (s/round6 max-residual)
     :residual-held (:converged res)
     :ceiling-respected (<= max-residual (+ MAX-RESIDUAL-MGL 1e-9))
     :settling-seconds (/ (Math/round (* settling-seconds 1000.0)) 1000.0)
     :representative true}))

(defn to-datoms
  "Project a dosing acceptance result into kotoba EAVT-shaped datoms (aggregate-only)."
  [result source-id]
  {:water.dosing/source-id source-id
   :water.dosing/agent (:agent result)
   :water.dosing/target-residual-mgl (:target-residual-mgl result)
   :water.dosing/final-residual-mgl (:final-residual-mgl result)
   :water.dosing/max-residual-mgl (:max-residual-mgl result)
   :water.dosing/ceiling-mgl MAX-RESIDUAL-MGL
   :water.dosing/residual-held (:residual-held result)
   :water.dosing/ceiling-respected (:ceiling-respected result)  ; G: hard clamp held
   :water.dosing/settling-seconds (:settling-seconds result)
   :water.dosing/representative (:representative result)         ; G10
   :water.dosing/server-held-key false                          ; no-server-key
   :water.dosing/dry-run true})                                 ; G10: R0 offline only

(defn main [& _]
  (let [r (commission-dosing {:agent "disinfect" :target-residual-mgl 0.5})]
    (println (format "mizuho chlorination: agent=%s target=%.2f mg/L final=%.4f max=%.4f held=%s settle=%.1fs ceiling-ok=%s"
                     (:agent r) (double (:target-residual-mgl r)) (double (:final-residual-mgl r))
                     (double (:max-residual-mgl r)) (:residual-held r)
                     (double (:settling-seconds r)) (:ceiling-respected r)))))

(when (= *file* (System/getProperty "babashka.file"))
  (main))
