#!/usr/bin/env bb
;; Working Clojure (babashka) port of methods/forecast_quantile.py.
;; Replaces the broken forecast_quantile.cljc stub (never edit the .cljc).
(ns mitooshi.methods.forecast-quantile
  "mitooshi 見通し — quantile (pinball-scored) forecaster (R1, offline).

  ADR-2606051800. A second forecaster family alongside the Gaussian baselines in forecast.clj:
  emit a forecast as a set of QUANTILES (0.1/0.5/0.9) rather than a mean±sd, and score it
  with the pinball (quantile) loss already in score.cljc. Same constitutional invariants:

    G1 distribution-only — dist_kind=\"quantile\", point-asserted false; a spread of quantiles
                           is a distribution, never a single asserted future (非終末論).
    G2 non-speculative   — use \":resilience\".
    G5 leak-free         — uses ONLY observations strictly before target-at; score-pair RAISES
                           on a look-ahead violation (inherited from score.cljc, do not suppress).
    G12 anti-pseudoscience — skill is pinball vs the documented persistence-quantile baseline
                           (every quantile = last observed value); :skilled only when it beats it.

  stdlib only (babashka v1.12). Run:
    bb --classpath 20-actors 20-actors/mitooshi/methods/forecast_quantile.clj   # self-test"
  (:require [clojure.string :as str]
            [mitooshi.methods.score :as score]))

;; ── DEFAULT_LEVELS ───────────────────────────────────────────────────────────
(def DEFAULT_LEVELS [0.1 0.5 0.9])

;; ── empirical-quantiles (inlined from analyze.clj — private there, so copied) ──
;; Mirrors analyze.clj empirical-quantiles / analyze.py _empirical_quantiles:
;; linear-interpolated empirical quantiles at the given levels.
(defn- empirical-quantiles
  "Linear-interpolated empirical quantiles at the given levels.
  Mirrors analyze.clj's private empirical-quantiles (and analyze.py _empirical_quantiles).
  Inlined here because the analyze.clj fn is private."
  [history levels]
  (let [h (vec (sort history))
        n (count h)]
    (reduce
     (fn [out tau]
       (if (= n 1)
         (assoc out tau (h 0))
         (let [idx (* tau (- n 1))
               lo  (int idx)
               hi  (min (+ lo 1) (- n 1))]
           (assoc out tau (+ (h lo) (* (- idx lo) (- (h hi) (h lo))))))))
     {} levels)))

;; ── persistence-quantiles ────────────────────────────────────────────────────
(defn- persistence-quantiles
  "Documented naive baseline: every quantile = the last observed value (no spread).
  A 'tomorrow = today, with certainty' straw-man the real forecaster must beat (G12).
  Mirrors forecast_quantile.py _persistence_quantiles."
  [values levels]
  (let [last-val (double (last values))]
    (into {} (map (fn [tau] [(double tau) last-val]) levels))))

;; ── py-round-n ───────────────────────────────────────────────────────────────
(defn- py-round-n
  "Python round(x, n): HALF_EVEN rounding to n decimal places, returns a double."
  [x n]
  (-> (java.math.BigDecimal. (double x))
      (.setScale (int n) java.math.RoundingMode/HALF_EVEN)
      .doubleValue))

;; ── forecast-next-quantile ───────────────────────────────────────────────────
(defn forecast-next-quantile
  "Forecast series `sid` at `target-at` as empirical QUANTILES of the prior values
  (leak-free — only observations strictly before target-at). Returns nil if no prior history.
  history is a sequence of [observed-at value] pairs (same convention as forecast.clj).
  Mirrors forecast_quantile.py forecast_next_quantile."
  ([sid history target-at] (forecast-next-quantile sid history target-at DEFAULT_LEVELS))
  ([sid history target-at levels]
   (let [prior (filterv (fn [[t _v]] (< t target-at)) history)]
     (when (seq prior)
       (let [values      (mapv second prior)
             info-as-of  (reduce max (map first prior))    ; G5 — newest fact seen
             q           (empirical-quantiles values levels)]
         (score/->forecast (str "fc." sid "." target-at ".quantile") "quantile"
                           :info-as-of  info-as-of
                           :use         ":resilience"
                           :point-asserted false
                           :quantiles   q))))))

;; ── score-quantile ───────────────────────────────────────────────────────────
(defn score-quantile
  "Score a quantile forecast against the realizing value (leak-checked by score/score-pair).
  Mirrors forecast_quantile.py score_quantile."
  [fc y observed-at]
  (score/score-pair fc (score/->observation (str "o." (:fid fc))
                                            :observed-at observed-at
                                            :value       (double y))))

;; ── forecast-quantile-trail ──────────────────────────────────────────────────
(defn forecast-quantile-trail
  "Forecast every series at target-at as quantiles; when the realizing obs is already in
  the trail, score pinball + skill vs the persistence-quantile baseline (G12).
  rows: vector of string-keyed maps with keys ':obs/series', ':obs/observed-at', ':obs/value'.
  Returns a vector of rows: {\"series\" sid \"forecast\" fc [\"pinball\" p \"baseline_pinball\" b
                                                             \"skill\" s \"skilled\" bool]}.
  Mirrors forecast_quantile.py forecast_quantile_trail."
  ([rows target-at] (forecast-quantile-trail rows target-at DEFAULT_LEVELS))
  ([rows target-at levels]
   ;; build series histories and actuals index
   (let [;; hist: {sid [[t v] ...] sorted by t}
         hist-raw (reduce
                   (fn [m r]
                     (if (and (contains? r ":obs/series") (contains? r ":obs/observed-at"))
                       (update m (get r ":obs/series")
                               (fnil conj [])
                               [(long (get r ":obs/observed-at"))
                                (double (get r ":obs/value"))])
                       m))
                   {} rows)
         hist     (reduce-kv (fn [m k v]
                               (assoc m k (vec (sort-by first v))))
                             {} hist-raw)
         ;; actual: {[sid observed-at] value}
         actual   (reduce
                   (fn [m r]
                     (if (and (contains? r ":obs/series") (contains? r ":obs/observed-at"))
                       (assoc m [(get r ":obs/series") (long (get r ":obs/observed-at"))]
                              (double (get r ":obs/value")))
                       m))
                   {} rows)]
     (reduce
      (fn [out [sid h]]
        (let [fc (forecast-next-quantile sid h target-at levels)]
          (if (nil? fc)
            out
            (let [row       {"series" sid "forecast" fc}
                  act-key   [sid (long target-at)]]
              (if (contains? actual act-key)
                (let [y       (get actual act-key)
                      s       (score-quantile fc y target-at)   ; raises on G5 leak
                      prior   (mapv second (filterv (fn [[t _]] (< t target-at)) h))
                      base-q  (persistence-quantiles prior levels)
                      base    (score/pinball-loss base-q y)]
                  (conj out (assoc row
                                   "pinball"          (py-round-n (get s "pinball") 6)
                                   "baseline_pinball" (py-round-n base 6)
                                   "skill"            (py-round-n (score/skill-score (get s "pinball") base) 4)
                                   "skilled"          (boolean (< (get s "pinball") base)))))
                (conj out row))))))
      []
      (sort-by first (seq hist))))))

;; ── _run (self-test, mirrors forecast_quantile.py _run) ─────────────────────
(defn- _run []
  ;; rising series 1..7; forecast quantiles at t=7 from history t<7, score against y=24
  (let [hist (mapv (fn [t] [t (double (+ 10 (* 2 t)))]) (range 1 7))
        fc   (forecast-next-quantile "s-x" hist 7)]
    (assert (some? fc)           "fc must not be nil")
    (assert (= "quantile" (:dist-kind fc)) "dist-kind must be quantile")
    (assert (false? (:point-asserted fc)) "point-asserted must be false")   ; G1
    (assert (= ":resilience" (:use fc))   "use must be :resilience")       ; G2
    (assert (= 6 (:info-as-of fc))        "info-as-of must be 6")          ; G5
    ;; monotone quantiles
    (let [qs (sort-by key (:quantiles fc))]
      (assert (<= (val (first qs)) (val (second qs)) (val (last qs)))
              "quantiles must be monotone"))
    ;; scoring works without raising
    (let [s (score-quantile fc 24.0 7)]
      (assert (contains? s "pinball") "score must contain pinball key")
      (assert (contains? s "pit")     "score must contain pit key"))
    ;; trail with scoring
    (let [rows (mapv (fn [t] {":obs/series"      "s-x"
                               ":obs/observed-at" t
                               ":obs/value"       (double (+ 10 (* 2 t)))})
                     (range 1 8))
          trail (forecast-quantile-trail rows 7)]
      (assert (seq trail)              "trail must not be empty")
      (assert (contains? (first trail) "skill") "trail row must have skill"))
    (println "forecast_quantile.clj: self-test passed")
    true))

(when (= *file* (System/getProperty "babashka.file"))
  (_run)
  (System/exit 0))
