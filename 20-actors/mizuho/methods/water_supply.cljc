(ns mizuho.methods.water-supply
  "water_supply — mizuho potable-water control loop (R0 :representative).

  1:1 Clojure port of methods/water_supply.py.

  Proves a community-scale supply holds pressure: a demand step drops the reservoir
  level, the pump's secondary-PI loop drives inflow until the level error integrates
  back to the service setpoint, and the modeled supply restores service pressure.

  mizuho constitutional gates apply: community-scale only (G3 — service population
  hard-capped; a municipal utility is N1), no commercial water-utility software (G4),
  Murakumo-only inference (G7 — unused here), live actuation consent-gated (G10 —
  offline sim only).

  House style: data maps are STRING-keyed; Python ':water.supply/*' attr keywords
  stay strings; pure fns; no host I/O. Float rounding mirrors Python round(x, n) via
  BigDecimal HALF_EVEN. The WaterSupplyResult dataclass is modeled as a string-keyed
  map. Omits the Python __main__ demo."
  (:require [mizuho.methods.-substrate :as sub]))

;; mizuho civilian-use allowlist (closed-world, N1).
(def PERMITTED-USES ["supply" "treat" "sample" "recycle" "irrigate"])

;; G3 community-scale invariant: per-source service population is hard-capped.
(def MAX-SERVICE-POPULATION 2500)

;; ── float rounding parity (Python round(x, n)) ──────────────────────────────────
(defn- round-n [x n]
  #?(:clj (-> (java.math.BigDecimal. (double x))
              (.setScale (int n) java.math.RoundingMode/HALF_EVEN)
              (.doubleValue))
     :cljs (let [p (Math/pow 10 n)] (/ (js/Math.round (* (double x) p)) p))))

;; ── ReservoirPlant (a substrate Plant: measure / step) ──────────────────────────
;; dV/dt = inflow(command) - demand - leak(level); level = V / area_m2 / 1000.

(defn make-reservoir-plant
  "Community service-reservoir level dynamics (a Plant). Port of ReservoirPlant."
  [& {:keys [area-m2 level-m demand-lps max-level-m leak-coeff-lps-per-m]
      :or {area-m2 20.0 level-m 3.0 demand-lps 0.0 max-level-m 6.0
           leak-coeff-lps-per-m 100.0}}]
  {:kind :reservoir-plant
   :area-m2 (double area-m2)
   :max-level-m (double max-level-m)
   :leak-coeff (double leak-coeff-lps-per-m)
   :state (atom {:volume-l (* (double level-m) (double area-m2) 1000.0)
                 :demand-lps (double demand-lps)})
   :measure (fn [p] (/ (:volume-l @(:state p)) (* (:area-m2 p) 1000.0)))
   :step! (fn [p command dt]
            (let [st @(:state p)
                  level (/ (:volume-l st) (* (:area-m2 p) 1000.0))
                  leak-lps (* (:leak-coeff p) level)
                  v (+ (:volume-l st) (* (- command (:demand-lps st) leak-lps) dt))
                  v (if (< v 0.0) 0.0 v)
                  max-v (* (:max-level-m p) (:area-m2 p) 1000.0)
                  v (if (> v max-v) max-v v)]
              (reset! (:state p) (assoc st :volume-l v))))})

(defn reservoir-set-demand!
  "Apply a demand step (the disturbance the pump loop must reject)."
  [p demand-lps]
  (swap! (:state p) assoc :demand-lps (double demand-lps)))

(defn reservoir-measure
  "Service level (m). Mirror of ReservoirPlant.measure."
  [p]
  (sub/plant-measure p))

(defn reservoir-pressure-bar
  "Service pressure (bar) ∝ static head (1 m water ≈ 0.0981 bar). Property port."
  [p]
  (* (reservoir-measure p) 0.0981))

;; ── commission_water_supply ─────────────────────────────────────────────────────

(defn commission-water-supply
  "Run the supply acceptance test. Raises (assert_civilian + G3) before any run.
  Returns a string-keyed WaterSupplyResult map. Port of commission_water_supply."
  [& {:keys [demand-step-lps use setpoint-level-m area-m2 service-population
             kp ki max-inflow-lps steps dt]
      :or {use "supply" setpoint-level-m 3.0 area-m2 20.0 service-population 200
           kp 10.0 ki 2.0 max-inflow-lps 2000.0 steps 4000 dt 1.0}}]
  (sub/assert-civilian use PERMITTED-USES) ; N1 gate before any actuation modelling
  (when (> service-population MAX-SERVICE-POPULATION)
    (sub/safety-error
     (str "G3: service_population " service-population " exceeds the community-scale "
          "cap " MAX-SERVICE-POPULATION "; a larger system is N1 (a municipal utility) "
          "and is structurally unrepresentable in mizuho")))
  (let [tank (make-reservoir-plant :area-m2 area-m2 :level-m setpoint-level-m
                                   :demand-lps 0.0)
        _ (reservoir-set-demand! tank demand-step-lps)
        ;; Pump inflow is non-negative.
        pid (sub/make-pid :kp kp :ki ki :out-min 0.0 :out-max max-inflow-lps)
        res (sub/simulate tank pid setpoint-level-m steps dt :tol 1e-3)
        settling-seconds (if (>= (:settling-step res) 0)
                           (* (:settling-step res) dt)
                           -1.0)]
    {"use" use
     "demand_step_lps" demand-step-lps
     "setpoint_level_m" setpoint-level-m
     "final_level_m" (round-n (:final-value res) 4)
     "final_pressure_bar" (round-n (reservoir-pressure-bar tank) 4)
     "level_restored" (:converged res)
     "settling_seconds" (round-n settling-seconds 3)
     "service_population" service-population
     "representative" true}))

;; ── to_datoms ────────────────────────────────────────────────────────────────────

(defn to-datoms
  "Project a supply acceptance result into kotoba EAVT-shaped datoms (G6/G9).
  Aggregate-only. String-keyed; Python ':water.supply/*' attrs stay strings."
  [result source-id]
  {":water.supply/source-id" source-id
   ":water.supply/use" (get result "use")
   ":water.supply/demand-step-lps" (get result "demand_step_lps")
   ":water.supply/setpoint-level-m" (get result "setpoint_level_m")
   ":water.supply/final-level-m" (get result "final_level_m")
   ":water.supply/final-pressure-bar" (get result "final_pressure_bar")
   ":water.supply/level-restored" (get result "level_restored")
   ":water.supply/settling-seconds" (get result "settling_seconds")
   ":water.supply/service-population" (get result "service_population")
   ":water.supply/representative" (get result "representative")
   ":water.supply/server-held-key" false
   ":water.supply/dry-run" true})
