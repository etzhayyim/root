;; ported from /Users/junkawasaki/github/com-junkawasaki/orgs/etzhayyim/root/20-actors/hikari/methods/microgrid.py (unit_refactor stage 0)
;; microgrid — hikari grid_edge operational control loop (R0 :representative).
(ns root.hikari.methods.microgrid
  (:require [clojure.string :as str]
            [clojure.set :as set]
            [clojure.edn :as edn]))

(declare permitted-uses commissioning-result rocof commission-microgrid to-datoms)

(def PERMITTED_USES (set ["grid-control" "island" "black-start" "dispatch" "load-shed"]))
(def ROCOF_TRIP_HZ_PER_S 2.0)

(defn commissioning-result
  "Outcome of a microgrid acceptance test (black-start + droop-P-f response).
  Represented as an immutable map with the following keys:
  - load_step_kw: float
  - final_freq_hz: float
  - freq_restored: boolean
  - final_generation_kw: float
  - final_soc: float
  - settling_seconds: float
  - rocof_max_hz_per_s: float
  - rocof_tripped: boolean
  - representative: boolean"
  []
  {:load_step_kw nil
   :final_freq_hz nil
   :freq_restored nil
   :final_generation_kw nil
   :final_soc nil
   :settling_seconds nil
   :rocof_max_hz_per_s nil
   :rocof_tripped nil
   :representative nil})

;; TODO: port-failed unit rocof (assembled-lint error)
;; def rocof(trajectory: list[tuple[float, float, float]], window_s: float = 0.1) -> float:
;;     """Max |df/dt| over a frequency trajectory, measured over a `window_s` window.
;; 
;;     Real anti-islanding ROCOF relays average over a short window (~100 ms), not a
;;     single sample, so a one-sample df/dt over-reports a step transient. We mirror
;;     that: compare each sample with the one ~`window_s` earlier.
;;     """
;;     if len(trajectory) < 2:
;;         return 0.0
;;     dt_sample = trajectory[1][0] - trajectory[0][0]
;;     span = max(1, round(window_s / dt_sample)) if dt_sample > 0 else 1
;;     worst = 0.0
;;     for i in range(span, len(trajectory)):
;;         t0, f0, _ = trajectory[i - span]
;;         t1, f1, _ = trajectory[i]
;;         dt = t1 - t0
;;         if dt > 0:
;;             worst = max(worst, abs(f1 - f0) / dt)
;;     return worst
(defn rocof [& _]
  (throw (ex-info "TODO: port-failed" {:from "rocof"})))

;; TODO: port-failed unit commission_microgrid (/var/folders/31/st4xq0g12v3cn1b9yg5zcrsm0000gn/T/tmpf1rrko8z/scratch.clj:5:9: er)
;; def commission_microgrid(
;;     load_step_kw: float,
;;     use: str = "grid-control",
;;     inertia_h: float = 4.0,
;;     initial_soc: float = 0.6,
;;     droop_r: float = 0.04,
;;     p_base_kw: float = 100.0,
;;     kp: float = 4.0,
;;     ki: float = 20.0,
;;     p_max_kw: float = 200.0,
;;     steps: int = 8000,
;;     dt: float = 0.01,
;; ) -> CommissioningResult:
;;     """Run the microgrid acceptance test. Raises (assert_civilian) before any run.
;; 
;;     A reference acceptance test for kuni-umi commissioning: apply `load_step_kw`,
;;     run primary droop + secondary PI, and confirm the frequency returns to 50 Hz
;;     with generation tracking load and the battery SoC staying in band. The fast
;;     droop term keeps the ROCOF below the anti-islanding trip threshold for a
;;     normal load step.
;;     """
;;     assert_civilian(use, PERMITTED_USES)  # N1 gate before any actuation modelling
;; 
;;     grid = MicrogridPlant(inertia_h=inertia_h, soc=initial_soc, p_load=100.0, f=50.0)
;;     grid.set_load(load_step_kw)
;;     droop = Droop(nominal=grid.f_nom, droop_r=droop_r, p_base=p_base_kw, p_min=0.0, p_max=p_max_kw)
;;     pid = PID(kp=kp, ki=ki, out_min=-p_max_kw, out_max=p_max_kw)
;;     controller = DroopPI(droop, pid)
;;     res = simulate(grid, controller, setpoint=grid.f_nom, steps=steps, dt=dt, tol=1e-2)
;; 
;;     r = rocof(res.trajectory)
;;     settling_seconds = res.settling_step * dt if res.settling_step >= 0 else -1.0
;;     return CommissioningResult(
;;         use=use,
;;         load_step_kw=load_step_kw,
;;         final_freq_hz=round(res.final_value, 4),
;;         freq_restored=res.converged,
;;         final_generation_kw=round(res.trajectory[-1][2], 4),
;;         final_soc=round(grid.soc, 4),
;;         settling_seconds=round(settling_seconds, 3),
;;         rocof_max_hz_per_s=round(r, 4),
;;         rocof_tripped=r > ROCOF_TRIP_HZ_PER_S,
;;         representative=True,
;;     )
(defn commission-microgrid [& _]
  (throw (ex-info "TODO: port-failed" {:from "commission_microgrid"})))

;; TODO: port-failed unit to_datoms (/var/folders/31/st4xq0g12v3cn1b9yg5zcrsm0000gn/T/tmp0615gxb3/scratch.clj:7:3: er)
;; def to_datoms(result: CommissioningResult, microgrid_id: str) -> dict:
;;     """Project a commissioning result into kotoba EAVT-shaped datoms (G6).
;; 
;;     Aggregate-only (no smart-meter PII, G9). The transactor appends these to the
;;     canonical Datom log; here we return the entity map a transactor would write.
;;     """
;;     return {
;;         ":microgrid/id": microgrid_id,
;;         ":microgrid/use": result.use,
;;         ":microgrid/load-step-kw": result.load_step_kw,
;;         ":microgrid/final-freq-hz": result.final_freq_hz,
;;         ":microgrid/freq-restored": result.freq_restored,
;;         ":microgrid/final-generation-kw": result.final_generation_kw,
;;         ":microgrid/final-soc": result.final_soc,
;;         ":microgrid/settling-seconds": result.settling_seconds,
;;         ":microgrid/rocof-max-hz-per-s": result.rocof_max_hz_per_s,
;;         ":microgrid/rocof-tripped": result.rocof_tripped,
;;         ":microgrid/representative": result.representative,  # G10
;;         ":microgrid/dry-run": True,                          # G10: R0 offline only
;;     }
(defn to-datoms [& _]
  (throw (ex-info "TODO: port-failed" {:from "to_datoms"})))

