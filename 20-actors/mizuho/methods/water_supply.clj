#!/usr/bin/env bb
;; Working Clojure port of methods/water_supply.py (reuses the clj control substrate).
(ns mizuho.methods.water-supply
  "water_supply — mizuho potable-water control loop (R0 :representative).

  Proves a community-scale supply holds pressure: a demand step (households open taps) drops
  the reservoir level, the pump's secondary-PI loop drives inflow until the level error
  integrates back to the service setpoint, and the modeled supply restores service pressure.

  mizuho gates: G3 community-scale only (service population hard-capped; a municipal utility is
  N1, structurally unrepresentable) · G4 plain PI over a lumped tank (never commercial
  water-utility firmware) · N1 civilian-use gate (assert-civilian) · G10 live actuation
  consent-gated; this module is offline sim only.

  Run:  bb --classpath 20-actors 20-actors/mizuho/methods/water_supply.clj"
  (:require [mizuho.methods.substrate :as s]))

;; civilian-use allowlist (closed-world, N1): water is for people + crops, never force.
(def permitted-uses #{"supply" "treat" "sample" "recycle" "irrigate"})

;; G3 community-scale invariant: per-source service population is hard-capped. Above the cap is
;; N1 (a municipal utility) and is refused structurally.
(def MAX-SERVICE-POPULATION 2500)

(defn reservoir-plant
  "Community service-reservoir level dynamics (a Plant: measure/step). State = stored volume
  (L); pump command = inflow (L/s); a constant demand drains it; gravity-fed distribution leak
  rises with head (self-regulating, real first-order lag). Level (m) = V / area / 1000."
  [{:keys [area-m2 level-m demand-lps max-level-m leak-coeff-lps-per-m]
    :or {area-m2 20.0 level-m 3.0 demand-lps 0.0 max-level-m 6.0 leak-coeff-lps-per-m 100.0}}]
  (let [vol (atom (* level-m area-m2 1000.0))
        demand (atom (double demand-lps))
        measure (fn [] (/ @vol (* area-m2 1000.0)))]
    {:measure measure
     :area-m2 area-m2
     :set-demand! (fn [d] (reset! demand (double d)))
     :pressure-bar (fn [] (* (measure) 0.0981))   ; 1 m water ≈ 0.0981 bar
     :step (fn [command dt]
             (let [leak (* leak-coeff-lps-per-m (measure))]
               (swap! vol #(+ % (* (- command @demand leak) dt)))
               (when (< @vol 0.0) (reset! vol 0.0))
               (let [max-v (* max-level-m area-m2 1000.0)]
                 (when (> @vol max-v) (reset! vol max-v)))))}))

(defn commission-water-supply
  "Run the supply acceptance test. Raises (assert-civilian + G3) before any run. Apply
  `demand-step-lps`, run a secondary-PI pump loop, and confirm the level returns to
  `setpoint-level-m` (service pressure restored)."
  [{:keys [demand-step-lps use setpoint-level-m area-m2 service-population kp ki max-inflow-lps steps dt]
    :or {use "supply" setpoint-level-m 3.0 area-m2 20.0 service-population 200
         kp 10.0 ki 2.0 max-inflow-lps 2000.0 steps 4000 dt 1.0}}]
  (s/assert-civilian use permitted-uses)               ; N1 gate before any actuation modelling
  (when (> service-population MAX-SERVICE-POPULATION)
    (s/safety-error (str "G3: service-population " service-population " exceeds the community-scale "
                         "cap " MAX-SERVICE-POPULATION "; a larger system is N1 (a municipal utility) "
                         "and is structurally unrepresentable in mizuho")))
  (let [tank (reservoir-plant {:area-m2 area-m2 :level-m setpoint-level-m :demand-lps 0.0})
        _ ((:set-demand! tank) demand-step-lps)
        pid (s/make-pid {:kp kp :ki ki :out-min 0.0 :out-max max-inflow-lps})
        controller {:reset (fn [] (s/pid-reset! pid)) :step (fn [e dt] (s/pid-step! pid e dt))}
        res (s/simulate tank controller setpoint-level-m steps dt :tol 1e-3)
        settling-seconds (if (>= (:settling-step res) 0) (* (:settling-step res) dt) -1.0)]
    {:use use
     :demand-step-lps demand-step-lps
     :setpoint-level-m setpoint-level-m
     :final-level-m (/ (Math/round (* (:final-value res) 10000.0)) 10000.0)
     :final-pressure-bar (/ (Math/round (* ((:pressure-bar tank)) 10000.0)) 10000.0)
     :level-restored (:converged res)
     :settling-seconds (/ (Math/round (* settling-seconds 1000.0)) 1000.0)
     :service-population service-population
     :representative true}))

(defn to-datoms
  "Project a supply acceptance result into kotoba EAVT-shaped datoms (aggregate-only; no
  per-household consumption PII)."
  [result source-id]
  {:water.supply/source-id source-id
   :water.supply/use (:use result)
   :water.supply/demand-step-lps (:demand-step-lps result)
   :water.supply/setpoint-level-m (:setpoint-level-m result)
   :water.supply/final-level-m (:final-level-m result)
   :water.supply/final-pressure-bar (:final-pressure-bar result)
   :water.supply/level-restored (:level-restored result)
   :water.supply/settling-seconds (:settling-seconds result)
   :water.supply/service-population (:service-population result)  ; aggregate, ≤ G3 cap
   :water.supply/representative (:representative result)          ; G10
   :water.supply/server-held-key false                           ; no-server-key
   :water.supply/dry-run true})                                  ; G10: R0 offline only

(defn main [& _]
  (let [r (commission-water-supply {:demand-step-lps 20.0})]
    (println (format "mizuho water-supply: use=%s demand=%.1f L/s final-level=%.4f m pressure=%.4f bar restored=%s settle=%.0fs pop=%d"
                     (:use r) (double (:demand-step-lps r)) (double (:final-level-m r))
                     (double (:final-pressure-bar r)) (:level-restored r)
                     (double (:settling-seconds r)) (:service-population r)))))

(when (= *file* (System/getProperty "babashka.file"))
  (main))
