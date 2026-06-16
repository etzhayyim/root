(ns mitooshi.methods.horizon
  "mitooshi 見通し — multi-horizon skill-decay analysis.
  Clojure port of methods/horizon.py (1:1). ADR-2606051800.

  A real forecaster predicts at MANY lead times, and its skill decays as the horizon
  grows — eventually a long-range forecast does no better than climatology. This
  demonstrates that honestly on a mean-reverting AR(1) process, scoring a leak-free
  h-step forecaster against the climatology baseline at each horizon h.

    AR(1):  y_t = μ + φ·(y_{t-1} − μ) + ε_t          (φ = 0.9, mean-reverting)
    optimal h-step mean:  μ + φ^h·(y_t − μ)  →  μ as h→∞
    h-step sd:  σ_ε·sqrt((1 − φ^{2h})/(1 − φ²))  →  the unconditional σ as h→∞

  Short horizon uses recent state and beats climatology; long horizon becomes
  climatology and skill → 0 (非終末論: no flat-skill crystal ball). Dependencies are
  the already-ported same-actor score (->forecast / ->observation / gaussian-crps /
  score-pair / skill-score). stdlib only; deterministic (no RNG)."
  (:require [clojure.string :as str]
            [mitooshi.methods.score :as score]))

(def ^:private MU 10.0)
(def PHI 0.9)                       ; strong mean-reversion → clear short-horizon predictability
(def ^:private SIGMA-E 1.0)
(def ^:private SIGMA-UNCOND (/ SIGMA-E (Math/sqrt (- 1.0 (* PHI PHI)))))

(defn- innov
  "Deterministic, non-repeating, ~zero-mean innovation (no RNG — reproducible)."
  [t]
  (- (+ (* 1.1 (Math/sin (* 2.3 t)))
        (* 0.7 (Math/cos (+ (* 0.9 t) 1.0))))
     (* 0.5 (Math/sin (* 0.37 t)))))

(defn build-path
  "The AR(1) sample path of length n (y[0] = μ)."
  [n]
  (loop [t 1, y [MU]]
    (if (>= t n)
      y
      (recur (inc t) (conj y (+ MU (* PHI (- (peek y) MU)) (innov t)))))))

(defn- model-forecast
  "Optimal h-step-ahead [mean sd] from current state y_t."
  [y-t h]
  (let [mean (+ MU (* (Math/pow PHI h) (- y-t MU)))
        var  (/ (* SIGMA-E SIGMA-E (- 1.0 (Math/pow PHI (* 2 h)))) (- 1.0 (* PHI PHI)))]
    [mean (Math/sqrt var)]))

(defn horizon-skill
  "For each horizon, mean CRPS of the AR(1) forecaster vs the climatology baseline,
  aggregated leak-free over all valid origins. One row per horizon."
  ([] (horizon-skill 160 [1 3 6 12]))
  ([n horizons]
   (let [y (build-path n)]
     (mapv
      (fn [h]
        (let [origins (range 2 (- n h))   ; origin t sees y[0..t]; target t+h is strictly after
              [msum csum cnt]
              (reduce (fn [[ms cs k] t]
                        (let [target (+ t h)
                              yt     (nth y target)
                              [mu sd] (model-forecast (nth y t) h)
                              fc (score/->forecast (str "f" t "." h) "gaussian"
                                                   :info-as-of t :mean mu :sd sd)
                              sc (score/score-pair fc (score/->observation
                                                       (str "o" target) :observed-at target :value yt))]
                          [(+ ms (get sc "crps"))
                           (+ cs (score/gaussian-crps MU SIGMA-UNCOND yt))
                           (inc k)]))
                      [0.0 0.0 0] origins)
              mc (/ msum cnt)
              cc (/ csum cnt)]
          {"h" h "mean_crps" mc "clim_crps" cc
           "skill_vs_clim" (score/skill-score mc cc) "n" cnt}))
      horizons))))

(defn- fmt4 [x]
  #?(:clj (format "%.4f" (double x)) :cljs (.toFixed (double x) 4)))

(defn render-md
  "Markdown table — one row per horizon."
  [rows]
  (let [head [(str "# mitooshi 見通し — multi-horizon skill decay (AR(1), φ=" PHI ")") ""
              "_Skill vs climatology decays as the lead time grows — a long-range forecast eventually_"
              "_does no better than the climatological mean. mitooshi never claims flat-skill foresight (非終末論)._" ""
              "| horizon h | mean CRPS | climatology CRPS | skill vs clim | n |"
              "|---|---|---|---|---|"]
        body (map (fn [r]
                    (str "| " (get r "h") " | " (fmt4 (get r "mean_crps")) " | "
                         (fmt4 (get r "clim_crps")) " | " (fmt4 (get r "skill_vs_clim"))
                         " | " (get r "n") " |"))
                  rows)
        tail ["" "→ CRPS rises and skill falls with horizon; the useful-foresight range is where skill > 0." ""]]
    (str/join "\n" (concat head body tail))))
