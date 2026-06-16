(ns mitooshi.methods.forecast-quantile
  "mitooshi 見通し — quantile (pinball-scored) forecaster (R1, offline).
  Clojure port of methods/forecast_quantile.py (1:1). ADR-2606051800.

  A second forecaster family alongside the Gaussian baselines: emit a forecast as a
  set of QUANTILES (10/50/90) rather than mean±sd, scored with pinball (quantile)
  loss. Same constitutional invariants:

    G1 distribution-only — dist-kind 'quantile', point-asserted false.
    G2 non-speculative   — use ':resilience'.
    G5 leak-free         — only observations strictly before target; score-pair RAISES
                           on a look-ahead leak.
    G12 anti-pseudoscience — skill is pinball vs a documented persistence baseline;
                           :skilled only when it beats the baseline.

  Dependencies are the already-ported same-actor analyze (empirical-quantiles*) and
  score (->forecast / ->observation / pinball-loss / score-pair / skill-score). stdlib only."
  (:require [mitooshi.methods.analyze :as analyze]
            [mitooshi.methods.score :as score]))

(def DEFAULT-LEVELS [0.1 0.5 0.9])

(defn- pyround
  "round(x, n) with banker's rounding (round-half-to-even), matching Python round()."
  [x n]
  (let [f (Math/pow 10.0 n)]
    (/ (Math/rint (* (double x) f)) f)))

(defn forecast-next-quantile
  "Forecast series `sid` at `target-at` as empirical QUANTILES of the prior values
  (leak-free — only observations strictly before target-at). nil if no prior history."
  ([sid history target-at] (forecast-next-quantile sid history target-at DEFAULT-LEVELS))
  ([sid history target-at levels]
   (let [prior (filter (fn [[t _]] (< t target-at)) history)]
     (when (seq prior)
       (let [values     (mapv second prior)
             info-as-of (apply max (map first prior))      ; G5
             q          (analyze/empirical-quantiles* values levels)]
         (score/->forecast (str "fc." sid "." target-at ".quantile") "quantile"
                           :info-as-of info-as-of :use ":resilience"
                           :point-asserted false :quantiles q))))))

(defn- persistence-quantiles
  "Documented naive baseline: every quantile = the last observed value (no spread).
  A 'tomorrow = today, with certainty' straw man the real forecaster must beat (G12)."
  [values levels]
  (let [last-v (double (last values))]
    (into {} (map (fn [tau] [(double tau) last-v]) levels))))

(defn score-quantile
  "Score a quantile forecast against the realizing value (leak-checked by score-pair)."
  [fc y observed-at]
  (score/score-pair fc (score/->observation (str "o." (:fid fc))
                                            :observed-at observed-at :value y)))

(defn forecast-quantile-trail
  "Forecast every series at target-at as quantiles; when the realizing obs is already in
  the trail, score pinball + skill vs the persistence-quantile baseline (G12)."
  ([rows target-at] (forecast-quantile-trail rows target-at DEFAULT-LEVELS))
  ([rows target-at levels]
   (let [{:keys [hist actual]}
         (reduce (fn [acc r]
                   (if (and (contains? r ":obs/series") (contains? r ":obs/observed-at"))
                     (let [sid (get r ":obs/series")
                           t   (long (get r ":obs/observed-at"))
                           v   (double (get r ":obs/value"))]
                       (-> acc
                           (update-in [:hist sid] (fnil conj []) [t v])
                           (assoc-in [:actual [sid t]] v)))
                     acc))
                 {:hist {} :actual {}} rows)]
     (vec
      (keep
       (fn [sid]
         (let [h  (vec (sort (get hist sid)))
               fc (forecast-next-quantile sid h target-at levels)]
           (when fc
             (let [row {"series" sid "forecast" fc}]
               (if (contains? actual [sid target-at])
                 (let [y     (get actual [sid target-at])
                       s     (score-quantile fc y target-at)        ; raises on G5 leak
                       prior (mapv second (filter (fn [[t _]] (< t target-at)) h))
                       base  (score/pinball-loss (persistence-quantiles prior levels) y)]
                   (assoc row
                          "pinball"          (pyround (get s "pinball") 6)
                          "baseline_pinball" (pyround base 6)
                          "skill"            (pyround (score/skill-score (get s "pinball") base) 4)
                          "skilled"          (boolean (< (get s "pinball") base)))) ; G12
                 row)))))
       (sort (keys hist)))))))
