;; ported from 20-actors/hikari/methods/microgrid.py (real port replacing the
;; unit_refactor stage-0 "TODO: port-failed" stub). NS fixed:
;; root.hikari.methods.microgrid -> hikari.methods.microgrid (20-actors is the bb
;; source root). Self-contained: the only require is the SIBLING REAL substrate port
;; (hikari.methods.substrate.cljc), which is _substrate.py's faithful port — not a stub.
(ns hikari.methods.microgrid
  "microgrid.py — hikari grid_edge operational control loop (R0 :representative).

  1:1 Clojure port of methods/microgrid.py. Proves the islanded microgrid stabilises:
  a load step knocks bus frequency down, the droop + secondary-PI loop drives
  dispatchable generation until the frequency error integrates back to zero, and an
  anti-islanding ROCOF guard trips on an abnormal rate-of-change of frequency.
  CommissioningResult is a string-keyed map; pure (no host I/O)."
  (:require [hikari.methods.substrate :as sub]))

;; hikari grid civilian-use allowlist (closed-world, N1).
(def PERMITTED-USES #{"grid-control" "island" "black-start" "dispatch" "load-shed"})

;; Anti-islanding: trip if |df/dt| exceeds this (Hz/s). Mirrors open-ot ROCOF cell.
(def ^:const ROCOF-TRIP-HZ-PER-S 2.0)

(defn- round-n [x n]
  (-> (java.math.BigDecimal/valueOf (double x))
      (.setScale (int n) java.math.RoundingMode/HALF_EVEN)
      .doubleValue))

(defn rocof
  "Max |df/dt| over a frequency trajectory, measured over a `window-s` window.
  Real anti-islanding ROCOF relays average over a short window (~100 ms), not a
  single sample; we compare each sample with the one ~`window-s` earlier."
  ([trajectory] (rocof trajectory 0.1))
  ([trajectory window-s]
   (if (< (count trajectory) 2)
     0.0
     (let [dt-sample (- (first (nth trajectory 1)) (first (nth trajectory 0)))
           span (if (> dt-sample 0) (max 1 (Math/round (/ window-s dt-sample))) 1)]
       (reduce
        (fn [worst i]
          (let [[t0 f0 _] (nth trajectory (- i span))
                [t1 f1 _] (nth trajectory i)
                dt (- t1 t0)]
            (if (> dt 0)
              (max worst (/ (Math/abs (double (- f1 f0))) dt))
              worst)))
        0.0
        (range span (count trajectory)))))))

(defn commission-microgrid
  "Run the microgrid acceptance test. Raises (assert-civilian) before any run.
  Applies `load-step-kw`, runs primary droop + secondary PI, and confirms frequency
  returns to 50 Hz with generation tracking load and the battery SoC staying in band.
  Returns a string-keyed CommissioningResult map."
  [load-step-kw & {:keys [use inertia-h initial-soc droop-r p-base-kw kp ki p-max-kw steps dt]
                   :or {use "grid-control" inertia-h 4.0 initial-soc 0.6 droop-r 0.04
                        p-base-kw 100.0 kp 4.0 ki 20.0 p-max-kw 200.0 steps 8000 dt 0.01}}]
  (sub/assert-civilian use PERMITTED-USES)            ; N1 gate before any actuation modelling
  (let [grid (sub/microgrid-plant {:inertia-h inertia-h :soc initial-soc :p-load 100.0 :f 50.0})
        _ ((:set-load grid) load-step-kw)
        f-nom (:f-nom grid)
        d (sub/droop {:nominal f-nom :droop-r droop-r :p-base p-base-kw :p-min 0.0 :p-max p-max-kw})
        p (sub/pid {:kp kp :ki ki :out-min (- p-max-kw) :out-max p-max-kw})
        controller (sub/droop-pi d p)
        res (sub/simulate grid controller f-nom steps dt :tol 1e-2)
        traj (get res "trajectory")
        r (rocof traj)
        settling-step (get res "settling_step")
        settling-seconds (if (>= settling-step 0) (* settling-step dt) -1.0)]
    {"use" use
     "load_step_kw" load-step-kw
     "final_freq_hz" (round-n (get res "final_value") 4)
     "freq_restored" (get res "converged")
     "final_generation_kw" (round-n (nth (peek traj) 2) 4)
     "final_soc" (round-n ((:soc grid)) 4)
     "settling_seconds" (round-n settling-seconds 3)
     "rocof_max_hz_per_s" (round-n r 4)
     "rocof_tripped" (> r ROCOF-TRIP-HZ-PER-S)
     "representative" true}))

(defn to-datoms
  "Project a commissioning result into kotoba EAVT-shaped datoms (G6).
  Aggregate-only (no smart-meter PII, G9). Returns the entity map a transactor writes."
  [result microgrid-id]
  {":microgrid/id" microgrid-id
   ":microgrid/use" (get result "use")
   ":microgrid/load-step-kw" (get result "load_step_kw")
   ":microgrid/final-freq-hz" (get result "final_freq_hz")
   ":microgrid/freq-restored" (get result "freq_restored")
   ":microgrid/final-generation-kw" (get result "final_generation_kw")
   ":microgrid/final-soc" (get result "final_soc")
   ":microgrid/settling-seconds" (get result "settling_seconds")
   ":microgrid/rocof-max-hz-per-s" (get result "rocof_max_hz_per_s")
   ":microgrid/rocof-tripped" (get result "rocof_tripped")
   ":microgrid/representative" (get result "representative") ; G10
   ":microgrid/dry-run" true})                              ; G10: R0 offline only
