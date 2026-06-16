(ns mizuho.methods.chlorination
  "chlorination — mizuho residual-disinfection dosing loop (R0 :representative).

  1:1 Clojure port of methods/chlorination.py.

  The runnable, tested core behind the disinfection half of `water_supply`. The
  residual decays (demand + time), a secondary-PI doser raises it back to a target
  (default 0.5 mg/L), and — critically — the dose is STRUCTURALLY CLAMPED so the
  modeled residual can never exceed the regulatory ceiling MAX-RESIDUAL-MGL = 4.0
  mg/L (WHO guideline / US-EPA MRDL).

  mizuho constitutional gates apply:
    - G4: a plain PI over a lumped residual model, never commercial UV/dosing firmware.
    - G6 (anti-paternalism): chlorine disinfection runs without per-member consent;
      FLUORIDE REFUSES (SafetyError) unless per-member-consent=true.
    - G10: live dosing is consent-gated; this module is offline sim only.

  House style: data maps are STRING-keyed; Python ':water.dosing/*' attr keywords
  stay strings; host I/O behind #?(:clj) (none needed here — pure). Float rounding
  mirrors Python round(x, n) via BigDecimal HALF_EVEN. The DosingResult dataclass is
  modeled as a string-keyed map. Omits the Python __main__ demo."
  (:require [mizuho.methods.-substrate :as sub]))

;; WHO guideline value / US-EPA maximum residual disinfectant level for free chlorine.
(def MAX-RESIDUAL-MGL 4.0)

;; Agents mizuho can model dosing for.
(def PERMITTED-AGENTS ["disinfect" "fluoridate"])

;; ── float rounding parity (Python round(x, n)) ──────────────────────────────────
(defn- round-n [x n]
  #?(:clj (-> (java.math.BigDecimal. (double x))
              (.setScale (int n) java.math.RoundingMode/HALF_EVEN)
              (.doubleValue))
     :cljs (let [p (Math/pow 10 n)] (/ (js/Math.round (* (double x) p)) p))))

;; ── ResidualChlorinePlant (a substrate Plant: measure / step) ───────────────────
;; First-order: dC/dt = dose_command - k_decay * C, with a hard structural ceiling.

(defn make-residual-chlorine-plant
  "Free-chlorine residual dynamics in a distribution volume (a Plant)."
  [& {:keys [residual-mgl k-decay] :or {residual-mgl 0.0 k-decay 0.05}}]
  {:kind :residual-chlorine-plant
   :k-decay (double k-decay)
   :state (atom {:residual (double residual-mgl)})
   :measure (fn [p] (:residual @(:state p)))
   :step! (fn [p command dt]
            (let [st @(:state p)
                  c (:residual st)
                  dcdt (- command (* (:k-decay p) c))
                  c' (+ c (* dcdt dt))
                  c' (if (< c' 0.0) 0.0 c')
                  ;; Structural hard ceiling: the modeled residual can NEVER exceed
                  ;; the regulatory MRDL.
                  c' (if (> c' MAX-RESIDUAL-MGL) MAX-RESIDUAL-MGL c')]
              (reset! (:state p) {:residual c'})))})

;; ── ClampedDoser (a substrate controller: reset! / step!) ───────────────────────
;; A PI doser whose output is STRUCTURALLY clamped so the residual can never exceed
;; MAX-RESIDUAL-MGL, independent of gains. Wraps a substrate PID.

(defn make-clamped-doser
  "A PI doser whose output is structurally clamped (port of ClampedDoser)."
  [plant pid dt]
  {:kind :clamped-doser
   :plant plant
   :pid pid
   :dt (double dt)
   :reset! (fn [d] (sub/pid-reset! (:pid d)))
   :step! (fn [d error dt]
            (let [raw0 (sub/pid-step! (:pid d) error dt)
                  raw (if (< raw0 0.0) 0.0 raw0)
                  headroom (- MAX-RESIDUAL-MGL (sub/plant-measure (:plant d)))
                  max-dose-rate (if (> dt 0) (max 0.0 (/ headroom dt)) 0.0)]
              (min raw max-dose-rate)))})

;; ── commission_dosing ───────────────────────────────────────────────────────────

(defn commission-dosing
  "Run the dosing acceptance test. Raises (SafetyError) before any run on a gate
  violation. Returns a string-keyed DosingResult map. Port of commission_dosing."
  [& {:keys [agent target-residual-mgl per-member-consent k-decay kp ki steps dt]
      :or {agent "disinfect" target-residual-mgl 0.5 per-member-consent false
           k-decay 0.05 kp 0.4 ki 0.15 steps 4000 dt 0.1}}]
  (when-not (some #(= % agent) PERMITTED-AGENTS)
    (sub/safety-error
     (str "dosing agent " (pr-str agent) " is not permitted; allowlist "
          (pr-str (vec PERMITTED-AGENTS)))))
  (when (and (= agent "fluoridate") (not per-member-consent))
    (sub/safety-error
     (str "G6: fluoride dosing requires per_member_consent=True (no mandatory "
          "fluoridation; anti-paternalism). Chlorine disinfection needs no consent.")))
  (when (> target-residual-mgl MAX-RESIDUAL-MGL)
    (sub/safety-error
     (str "target residual " target-residual-mgl " mg/L exceeds the regulatory "
          "ceiling " MAX-RESIDUAL-MGL " mg/L (WHO/EPA); structurally refused")))
  (let [plant (make-residual-chlorine-plant :residual-mgl 0.0 :k-decay k-decay)
        pid (sub/make-pid :kp kp :ki ki :out-min 0.0 :out-max MAX-RESIDUAL-MGL)
        doser (make-clamped-doser plant pid dt)
        res (sub/simulate plant doser target-residual-mgl steps dt :tol 1e-3)
        ;; max residual ever modeled across the whole trajectory.
        max-residual (reduce (fn [m [_ pv _]] (max m pv)) 0.0 (:trajectory res))
        settling-seconds (if (>= (:settling-step res) 0)
                           (* (:settling-step res) dt)
                           -1.0)]
    {"agent" agent
     "target_residual_mgl" target-residual-mgl
     "final_residual_mgl" (round-n (:final-value res) 4)
     "max_residual_mgl" (round-n max-residual 4)
     "residual_held" (:converged res)
     "ceiling_respected" (<= max-residual (+ MAX-RESIDUAL-MGL 1e-9))
     "settling_seconds" (round-n settling-seconds 3)
     "representative" true}))

;; ── to_datoms ────────────────────────────────────────────────────────────────────

(defn to-datoms
  "Project a dosing acceptance result into kotoba EAVT-shaped datoms.
  Aggregate-only. String-keyed; Python ':water.dosing/*' attrs stay strings."
  [result source-id]
  {":water.dosing/source-id" source-id
   ":water.dosing/agent" (get result "agent")
   ":water.dosing/target-residual-mgl" (get result "target_residual_mgl")
   ":water.dosing/final-residual-mgl" (get result "final_residual_mgl")
   ":water.dosing/max-residual-mgl" (get result "max_residual_mgl")
   ":water.dosing/ceiling-mgl" MAX-RESIDUAL-MGL
   ":water.dosing/residual-held" (get result "residual_held")
   ":water.dosing/ceiling-respected" (get result "ceiling_respected")
   ":water.dosing/settling-seconds" (get result "settling_seconds")
   ":water.dosing/representative" (get result "representative")
   ":water.dosing/server-held-key" false
   ":water.dosing/dry-run" true})
