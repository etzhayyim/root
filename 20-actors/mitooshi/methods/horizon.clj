#!/usr/bin/env bb
;; Working Clojure (babashka) port of methods/horizon.py.
;; Replaces the broken horizon.cljc stub (hollow -main never invoked under bb).
;; DO NOT edit the .cljc file — this .clj takes precedence under bb classpath resolution.
(ns mitooshi.methods.horizon
  "mitooshi 見通し — multi-horizon skill-decay analysis (ADR-2606051800).

  A real forecaster predicts at MANY lead times, and its skill decays as the horizon grows —
  eventually a long-range forecast can do no better than climatology. This module demonstrates
  that property honestly on a mean-reverting AR(1) process, scoring a leak-free h-step
  Gaussian forecaster against the climatology baseline at each horizon h.

    AR(1):  y_t = μ + φ·(y_{t-1} − μ) + ε_t          (φ = 0.9, mean-reverting)
    optimal h-step mean:  μ + φ^h·(y_t − μ)  →  μ as h→∞
    h-step sd:  σ_ε·sqrt((1 − φ^{2h})/(1 − φ²))  →  the unconditional σ as h→∞

  So at short horizon the forecast uses recent state and beats climatology; at long horizon it
  becomes climatology and skill → 0. That decay keeps mitooshi honest about how far ahead it
  can usefully see (非終末論 — it never claims flat-skill foresight).

  stdlib only (babashka v1.12). Run:
    bb --classpath 20-actors 20-actors/mitooshi/methods/horizon.clj [--out OUTDIR]"
  (:require [clojure.string :as str]
            [clojure.java.io :as io]
            [mitooshi.methods.score :as score]))

;; ── AR(1) constants ──────────────────────────────────────────────────────────
(def mu 10.0)
(def phi 0.9)          ; strong mean-reversion → clear short-horizon predictability
(def sigma-e 1.0)
(def sigma-uncond (/ sigma-e (Math/sqrt (- 1.0 (* phi phi)))))

;; ── deterministic innovation (no RNG — reproducible) ────────────────────────
(defn- innov
  "1.1·sin(2.3t) + 0.7·cos(0.9t+1.0) − 0.5·sin(0.37t). Mirrors horizon._innov."
  [t]
  (+ (* 1.1 (Math/sin (* 2.3 (double t))))
     (* 0.7 (Math/cos (+ (* 0.9 (double t)) 1.0)))
     (- (* 0.5 (Math/sin (* 0.37 (double t)))))))

;; ── build-path ───────────────────────────────────────────────────────────────
(defn build-path
  "AR(1) path of length n starting at MU. Mirrors horizon.build_path."
  [n]
  (loop [t 1, y [mu]]
    (if (>= t n)
      y
      (recur (inc t) (conj y (+ mu (* phi (- (peek y) mu)) (innov t)))))))

;; ── model-forecast ───────────────────────────────────────────────────────────
(defn- model-forecast
  "Optimal h-step Gaussian [mean sd] from state y_t. Mirrors horizon._model_forecast.
  mean = MU + PHI^h * (y_t - MU)
  var  = SIGMA_E^2 * (1 - PHI^(2h)) / (1 - PHI^2)
  PHI^h = (Math/pow phi h) — matches Python ** on integer exponents."
  [y-t h]
  (let [mean (+ mu (* (Math/pow phi (int h)) (- y-t mu)))
        var  (/ (* sigma-e sigma-e
                   (- 1.0 (Math/pow phi (* 2 (int h)))))
                (- 1.0 (* phi phi)))]
    [mean (Math/sqrt var)]))

;; ── horizon-skill ────────────────────────────────────────────────────────────
(defn horizon-skill
  "For each horizon, mean CRPS of the AR(1) forecaster vs the climatology baseline,
  aggregated leak-free over all valid origins. Returns one string-keyed map per horizon.
  Mirrors horizon.horizon_skill."
  ([] (horizon-skill 160 [1 3 6 12]))
  ([n horizons]
   (let [y (build-path n)]
     (mapv
      (fn [h]
        (let [origins (range 2 (- n h))   ; origin t sees y[0..t]; target t+h is strictly after
              [model-crps clim-crps]
              (reduce
               (fn [[mc cc] t]
                 (let [target (+ t h)
                       yt     (nth y target)
                       [m sd] (model-forecast (nth y t) h)
                       ;; G5 leak-free: info-as-of=t, observed-at=target=t+h > t ✓
                       fc     (score/->forecast (str "f" t "." h) "gaussian"
                                               :info-as-of t
                                               :use ":resilience"
                                               :point-asserted false
                                               :mean m :sd sd)
                       sc     (score/score-pair
                               fc
                               (score/->observation (str "o" target)
                                                   :observed-at target
                                                   :value yt))]
                   [(conj mc (get sc "crps"))
                    (conj cc (score/gaussian-crps mu sigma-uncond yt))]))
               [[] []]
               origins)
              n*  (count model-crps)
              mc  (/ (reduce + 0.0 model-crps) n*)
              cc  (/ (reduce + 0.0 clim-crps) n*)]
          {"h"            h
           "mean_crps"    mc
           "clim_crps"    cc
           "skill_vs_clim" (score/skill-score mc cc)
           "n"            n*}))
      horizons))))

;; ── render-md ────────────────────────────────────────────────────────────────
(defn render-md
  "Markdown table, one row per horizon. Mirrors horizon.render_md (:.4f formatting)."
  [rows]
  (let [header [(str "# mitooshi 見通し — multi-horizon skill decay (AR(1), φ=" phi ")") ""
                "_Skill vs climatology decays as the lead time grows — a long-range forecast eventually_"
                "_does no better than the climatological mean. mitooshi never claims flat-skill foresight (非終末論)._"
                ""
                "| horizon h | mean CRPS | climatology CRPS | skill vs clim | n |"
                "|---|---|---|---|---|"]
        data-rows (mapv (fn [r]
                          (str "| " (get r "h") " | "
                               (format "%.4f" (get r "mean_crps")) " | "
                               (format "%.4f" (get r "clim_crps")) " | "
                               (format "%.4f" (get r "skill_vs_clim")) " | "
                               (get r "n") " |"))
                        rows)
        footer ["" "→ CRPS rises and skill falls with horizon; the useful-foresight range is where skill > 0." ""]]
    (str/join "\n" (concat header data-rows footer))))

;; ── main ─────────────────────────────────────────────────────────────────────
(defn main [& argv]
  (let [argv (vec argv)
        rows (horizon-skill)]
    (println (str "mitooshi multi-horizon skill (AR(1), φ=" phi "):"))
    (doseq [r rows]
      (println (str "  h=" (get r "h") ": CRPS=" (format "%.4f" (get r "mean_crps"))
                    " skill_vs_clim=" (format "%.4f" (get r "skill_vs_clim")))))
    (when (some #{"--out"} argv)
      (let [outdir (io/file (nth argv (inc (.indexOf argv "--out"))))]
        (.mkdirs outdir)
        (spit (io/file outdir "horizon-skill.md") (render-md rows))
        (println (str "  → " (io/file outdir "horizon-skill.md")))))
    0))

(when (= *file* (System/getProperty "babashka.file"))
  (apply main *command-line-args*))
