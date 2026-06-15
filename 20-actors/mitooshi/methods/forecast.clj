#!/usr/bin/env bb
;; Working Clojure (babashka) port of methods/forecast.py.
(ns mitooshi.methods.forecast
  "mitooshi 見通し — baseline forecasts from the persisted chokepoint trail (R1, offline).

  ADR-2606051800. Closes the observe→bridge→persist→**forecast** loop:
  forecasts the next value of each chokepoint series as a DISTRIBUTION (G1 — never a point),
  using ONLY observations strictly before the target time (G5 leak-free), and — when the
  realizing observation is already in the trail — scores the forecast against it with proper
  scoring rules and reports skill vs the climatology baseline (G12).

  Constitutional invariants:
    G1  distribution-only  — point-asserted is always false; a deterministic single-future
                             is unrepresentable (非終末論).
    G5  leak-free          — forecast-next filters to t < target-at; score-pair RAISES on a
                             look-ahead violation; the backtest walks origins in order so each
                             origin only sees prior residuals.
    G12 anti-pseudoscience — skill is computed vs the climatology baseline; :skilled only
                             when it beats the baseline on a proper scoring rule.

  apply-correction (from cells/online_update/state_machine.py) is inlined here as a pure
  function (no dynamic import): mean + bias-corr, max(sd * var-infl, 1e-9).

  stdlib only (babashka v1.12). Run:
    bb --classpath 20-actors 20-actors/mitooshi/methods/forecast.clj \\
       --trail ../data/persisted/chokepoint-trail.kotoba.edn --at 7"
  (:require [clojure.java.io :as io]
            [clojure.edn :as edn]
            [clojure.string :as str]
            [mitooshi.methods.score :as score]
            [mitooshi.methods.analyze :as analyze]))

(def ^:private this-file *file*)
(defn- actor-root [] (-> this-file io/file .getAbsoluteFile .getParentFile .getParentFile))

;; ── Python round(x, n) — HALF_EVEN on the exact double ──────────────────────
(defn- py-round-n
  "Python round(x, n): HALF_EVEN rounding to n decimal places, returns a double."
  [x n]
  (-> (java.math.BigDecimal. (double x))
      (.setScale (int n) java.math.RoundingMode/HALF_EVEN)
      .doubleValue))

;; ── apply_correction (inlined from cells/online_update/state_machine.py) ────
(defn- apply-correction
  "Corrected forecast under a proposed update: shift the mean by the learned bias,
  scale the spread by the learned inflation. Inlined from online_update/state_machine.py.
  apply_correction(mean, sd, bias_corr, var_infl) → (mean + bias_corr, max(sd * var_infl, 1e-9))"
  [mean sd bias-corr var-infl]
  [(+ mean bias-corr) (max (* sd var-infl) 1e-9)])

;; ── EDN keyword → string conversion (persist.clj pattern) ───────────────────
(defn- kw->str [k]
  (if (keyword? k)
    (str ":" (if (namespace k) (str (namespace k) "/" (name k)) (name k)))
    k))

(defn- rec->str-keys [m]
  (when (map? m)
    (into {} (map (fn [[k v]] [(kw->str k) v]) m))))

;; ── load-edn — reads the trail file; converts real kw keys → string keys ────
(defn load-trail-edn
  "Read a kotoba-EDN trail file (vector of maps) → vector of string-keyed maps.
  Real EDN keywords (:series/id) are converted to string \":series/id\" to match the
  Python pipeline's string-key convention."
  [path]
  (let [raw (edn/read-string (slurp (io/file path)))]
    (mapv rec->str-keys raw)))

(def methods #{"climatology" "persistence"})

;; ── series-histories ─────────────────────────────────────────────────────────
(defn series-histories
  "Build {series-id [[observed-at value] ...] sorted by observed-at} from trail rows.
  Mirrors forecast.py series_histories."
  [rows]
  (let [acc (reduce (fn [m r]
                      (if (and (contains? r ":obs/series") (contains? r ":obs/observed-at"))
                        (update m (get r ":obs/series")
                                (fnil conj [])
                                [(long (get r ":obs/observed-at"))
                                 (double (get r ":obs/value"))])
                        m))
                    {} rows)]
    (reduce-kv (fn [m k v] (assoc m k (vec (sort-by first v)))) {} acc)))

;; ── forecast-next ────────────────────────────────────────────────────────────
(defn forecast-next
  "Forecast series `sid` at `target-at` as a Gaussian distribution, using ONLY
  observations strictly before target-at (leak-free). Returns nil if no prior history.
  method must be one of #{\"climatology\" \"persistence\"}.
  Returns a score/->forecast map."
  ([sid history target-at] (forecast-next sid history target-at "climatology"))
  ([sid history target-at method]
   (when-not (contains? methods method)
     (throw (ex-info (str "method must be one of " methods ", got " (pr-str method))
                     {:method method})))
   (let [prior (filterv (fn [[t _v]] (< t target-at)) history)]
     (when (seq prior)
       (let [values (mapv second prior)
             info-as-of (reduce max (map first prior))   ; G5 — newest fact the forecaster saw
             [mu sd] (if (= method "climatology")
                       (score/climatology-gaussian values)
                       (score/persistence-gaussian values))]
         (score/->forecast (str "fc." sid "." target-at "." method) "gaussian"
                           :info-as-of info-as-of
                           :use ":resilience"
                           :point-asserted false
                           :mean (py-round-n mu 4)
                           :sd (py-round-n sd 6)))))))

;; ── forecast-trail ───────────────────────────────────────────────────────────
(defn forecast-trail
  "Forecast every series at target-at; score leak-free against the realizing obs if
  it is already in the trail. Returns a vector of rows:
  {\"series\" sid \"forecast\" fc [\"crps\" c \"climatology_crps\" b \"skill\" s]}.
  Mirrors forecast.py forecast_trail."
  ([rows target-at] (forecast-trail rows target-at "climatology"))
  ([rows target-at method]
   (let [hist (series-histories rows)
         ;; actual: {[series observed-at] value}
         actual (reduce (fn [m r]
                          (if (and (contains? r ":obs/series") (contains? r ":obs/observed-at"))
                            (assoc m [(get r ":obs/series") (long (get r ":obs/observed-at"))]
                                   (double (get r ":obs/value")))
                            m))
                        {} rows)]
     (reduce
      (fn [out [sid h]]
        (let [fc (forecast-next sid h target-at method)]
          (if (nil? fc)
            out
            (let [row {"series" sid "forecast" fc}
                  key [sid target-at]]
              (if (contains? actual key)
                (let [y (get actual key)
                      obs (score/->observation (str "obs." sid "." target-at)
                                              :observed-at target-at :value y)
                      s (score/score-pair fc obs)             ; raises on G5 leak
                      prior (mapv second (filterv (fn [[t _]] (< t target-at)) h))
                      [cmu csd] (score/climatology-gaussian prior)
                      base (score/gaussian-crps cmu csd y)]
                  (conj out (assoc row
                                   "crps"             (py-round-n (get s "crps") 6)
                                   "climatology_crps" (py-round-n base 6)
                                   "skill"            (py-round-n (score/skill-score (get s "crps") base) 4))))
                (conj out row))))))
      []
      (sort-by first (seq hist))))))

;; ── backtest-rolling ─────────────────────────────────────────────────────────
(defn backtest-rolling
  "Rolling-origin backtest: at EVERY observed-at origin (after the first), forecast each
  series from history strictly before it and score against the realized obs. This is the
  leak-free, all-origins answer to 'does this method have skill?'. Returns
  {method n mean_crps mean_skill calibration per_origin}.
  Mirrors forecast.py backtest_rolling."
  ([rows] (backtest-rolling rows "climatology"))
  ([rows method]
   (let [hist (series-histories rows)
         all-ts (sort (set (mapcat (fn [[_ pairs]] (map first pairs)) hist)))
         targets (rest all-ts)                               ; skip the first (no prior history)
         crps-all (atom [])
         skill-all (atom [])
         pit-all   (atom [])
         per-origin (atom [])]
     (doseq [target-at targets]
       (let [scored (filterv #(contains? % "crps")
                             (forecast-trail rows target-at method))]
         (when (seq scored)
           (let [o-crps  (mapv #(get % "crps") scored)
                 o-skill (mapv #(get % "skill") scored)]
             (swap! crps-all  into o-crps)
             (swap! skill-all into o-skill)
             (doseq [r scored]                               ; collect PIT for calibration
               (let [sid (get r "series")
                     h   (get hist sid)
                     y   (second (first (filter (fn [[t _]] (= t target-at)) h)))
                     fc  (get r "forecast")
                     obs (score/->observation "o" :observed-at target-at :value y)
                     sp  (score/score-pair fc obs)]
                 (swap! pit-all conj (get sp "pit"))))
             (swap! per-origin conj
                    {"target_at"  target-at
                     "n"          (count scored)
                     "mean_crps"  (py-round-n (/ (reduce + 0.0 o-crps) (count o-crps)) 6)
                     "mean_skill" (py-round-n (/ (reduce + 0.0 o-skill) (count o-skill)) 4)})))))
     (let [n (count @crps-all)]
       {"method"     method
        "n"          n
        "mean_crps"  (when (pos? n) (py-round-n (/ (reduce + 0.0 @crps-all) n) 6))
        "mean_skill" (when (pos? n) (py-round-n (/ (reduce + 0.0 @skill-all) n) 4))
        "calibration" (score/calibration-summary @pit-all)
        "per_origin" @per-origin}))))

;; ── compare-methods ──────────────────────────────────────────────────────────
(defn compare-methods
  "Rolling-origin backtest for every method → {method: summary}.
  Mirrors forecast.py compare_methods."
  [rows]
  (into {} (map (fn [m] [m (backtest-rolling rows m)]) methods)))

;; ── _recalib-params ──────────────────────────────────────────────────────────
(defn- recalib-params
  "Batch bias + variance-inflation from PAST residuals.
  bias = mean(error); var-infl = clamp(resid-std / mean-claimed-sd).
  Returns [0.0 1.0] — the identity correction — when there is nothing to learn from yet.
  Mirrors forecast.py _recalib_params exactly."
  [residuals]
  (let [errs (mapv #(double (get % "error")) (filter #(contains? % "error") residuals))
        sds  (mapv #(double (get % "sd"))
                   (filter #(and (contains? % "sd") (> (get % "sd" 0) 0)) residuals))]
    (if (empty? errs)
      [0.0 1.0]
      (let [n        (count errs)
            mean-err (/ (reduce + 0.0 errs) n)
            resid-std (if (>= n 2)
                        (let [rv (/ (reduce + 0.0 (map #(Math/pow (- % mean-err) 2) errs))
                                    (dec n))]
                          (if (> rv 0) (Math/sqrt rv) 0.0))
                        (Math/abs (first errs)))
            mean-sd  (if (seq sds) (/ (reduce + 0.0 sds) (count sds)) 1.0)
            raw      (if (> mean-sd 0) (/ resid-std mean-sd) 1.0)]
        [(py-round-n mean-err 6)
         (py-round-n (max 0.25 (min 4.0 raw)) 6)]))))

;; ── backtest-calibrated ──────────────────────────────────────────────────────
(defn backtest-calibrated
  "Leak-free ONLINE-recalibrated rolling backtest. At each origin, the raw forecast is
  corrected using ONLY residuals from origins strictly before it. Per-series recalibration.
  Returns same shape as backtest-rolling plus {bias_var {series [bias var-infl]}}.
  Mirrors forecast.py backtest_calibrated."
  ([rows] (backtest-calibrated rows "climatology"))
  ([rows method]
   (let [hist    (series-histories rows)
         all-ts  (sort (set (mapcat (fn [[_ pairs]] (map first pairs)) hist)))
         targets (rest all-ts)
         ;; mutable residuals per series
         resid   (atom (into {} (map (fn [[sid _]] [sid []]) hist)))
         crps-all  (atom [])
         skill-all (atom [])
         pit-all   (atom [])
         final-bias-var (atom {})]
     (doseq [target-at targets]
       (doseq [[sid h] (sort-by first (seq hist))]
         (let [raw (forecast-next sid h target-at method)
               has-realized? (some (fn [[t _]] (= t target-at)) h)]
           (when (and (some? raw) has-realized?)
             (let [y       (second (first (filter (fn [[t _]] (= t target-at)) h)))
                   [bias infl] (recalib-params (get @resid sid))  ; from PAST residuals only
                   _       (swap! final-bias-var assoc sid [bias infl])
                   [cmean csd] (apply-correction (:mean raw) (:sd raw) bias infl)
                   corr    (score/->forecast (str (:fid raw) ".cal") "gaussian"
                                            :info-as-of (:info-as-of raw)
                                            :use ":resilience"
                                            :point-asserted false
                                            :mean cmean :sd csd)
                   obs     (score/->observation (str "obs." sid "." target-at)
                                               :observed-at target-at :value y)
                   s       (score/score-pair corr obs)
                   prior   (mapv second (filterv (fn [[t _]] (< t target-at)) h))
                   [cmu csd0] (score/climatology-gaussian prior)
                   base    (score/gaussian-crps cmu csd0 y)]
               (swap! crps-all  conj (get s "crps"))
               (swap! pit-all   conj (get s "pit"))
               (swap! skill-all conj (score/skill-score (get s "crps") base))
               ;; NOW record this origin's residual for FUTURE origins (leak-free ordering)
               (swap! resid update sid conj {"error" (- y (:mean raw)) "sd" (:sd raw)}))))))
     (let [n (count @crps-all)]
       {"method"     method
        "n"          n
        "calibrated" true
        "mean_crps"  (when (pos? n) (py-round-n (/ (reduce + 0.0 @crps-all) n) 6))
        "mean_skill" (when (pos? n) (py-round-n (/ (reduce + 0.0 @skill-all) n) 4))
        "calibration" (score/calibration-summary @pit-all)
        "bias_var"   @final-bias-var}))))

;; ── emit-scorecard-edn ───────────────────────────────────────────────────────
(defn emit-scorecard-edn
  "Serialise the rolling-origin backtest comparison to a kotoba EDN string.
  Mirrors forecast.py emit_scorecard_edn."
  [comparison]
  (let [lines (concat
               [";; chokepoint-backtest-scorecard.kotoba.edn — ROLLING-ORIGIN leak-free backtest."
                ";; Aggregate skill vs climatology over ALL origins (no cherry-picked target)."
                ";; G5 leak-free at each origin; G12 skill vs a documented baseline. DERIVED"
                ";; :representative. Live promotion G10-gated. ADR-2606051800."
                ""
                "["]
               (for [[m s] (sort-by first (seq comparison))
                     :let [cal (get s "calibration")]]
                 (str " {:fc.score/method :" m " :fc.score/n " (get s "n")
                      " :fc.score/mean-crps " (get s "mean_crps")
                      " :fc.score/mean-skill " (get s "mean_skill")
                      " :fc.score/pit-mean " (py-round-n (get cal "pit_mean") 4)
                      " :fc.score/calibration-deviation " (py-round-n (get cal "deviation") 4)
                      " :fc.score/sourcing :representative}"))
               ["]"])]
    (str (str/join "\n" lines) "\n")))

;; ── emit-forecast-edn ────────────────────────────────────────────────────────
(defn emit-forecast-edn
  "Serialise point-in-time distribution forecasts to a kotoba EDN string.
  Mirrors forecast.py emit_forecast_edn."
  [forecasts target-at method]
  (let [lines (concat
               [(str ";; chokepoint-forecast.kotoba.edn — DISTRIBUTION forecasts @ target=" target-at " (" method ").")
                ";; G1 distribution-only (:forecast/point-asserted false, 非終末論). G5 leak-free"
                ";; (info-as-of < target). DERIVED :representative. Live promotion G10-gated. ADR-2606051800."
                ""
                "["]
               (for [row forecasts
                     :let [fc (get row "forecast")]]
                 (str " {:forecast/id \"" (:fid fc) "\" :forecast/series \"" (get row "series") "\" "
                      ":forecast/dist :gaussian :forecast/point-asserted false :forecast/use :resilience "
                      ":forecast/info-as-of " (:info-as-of fc) " :forecast/target-at " target-at
                      " :forecast/mean " (:mean fc) " :forecast/sd " (:sd fc)
                      " :forecast/sourcing :representative}"))
               ["]"])]
    (str (str/join "\n" lines) "\n")))

;; ── main ─────────────────────────────────────────────────────────────────────
(defn main [& argv]
  (let [args (vec argv)]
    (when (or (not (.contains args "--trail"))
              (not (some #(contains? #{["--at"] ["--backtest"] ["--calibrated"]}
                                     [%]) args)))
      ;; require --trail and at least one of --at / --backtest / --calibrated
      (when-not (some #(= % "--at") args)
        (when-not (some #(= % "--backtest") args)
          (when-not (some #(= % "--calibrated") args)
            (println "forecast: --trail <path> and one of --at / --backtest / --calibrated are required")
            (System/exit 1)))))
    (let [trail-path  (nth args (inc (.indexOf args "--trail")))
          rows        (load-trail-edn trail-path)
          method      (if (.contains args "--method")
                        (nth args (inc (.indexOf args "--method")))
                        "climatology")]

      (cond
        (.contains args "--backtest")
        (let [cal? (.contains args "--calibrated")
              comp (if cal?
                     (into {} (map (fn [m] [m (backtest-calibrated rows m)]) methods))
                     (compare-methods rows))]
          (when (.contains args "--out")
            (let [outdir (io/file (nth args (inc (.indexOf args "--out"))))]
              (.mkdirs outdir)
              (let [fname (if cal?
                            "chokepoint-backtest-scorecard-calibrated.kotoba.edn"
                            "chokepoint-backtest-scorecard.kotoba.edn")]
                (spit (io/file outdir fname) (emit-scorecard-edn comp)))))
          (println (str "mitooshi rolling-origin backtest ("
                        (if cal? "calibrated, " "") "leak-free at each origin):"))
          (doseq [[m s] (sort-by first (seq comp))]
            (println (format "  %-12s n=%3d  mean-CRPS=%s  mean-skill=%s  PIT-mean=%s"
                             m (int (get s "n"))
                             (str (get s "mean_crps"))
                             (str (get s "mean_skill"))
                             (str (py-round-n (get (get s "calibration") "pit_mean") 3))))))

        (.contains args "--calibrated")
        (do
          (println "mitooshi raw vs online-recalibrated backtest (leak-free recalibration):")
          (let [lines (atom [";; chokepoint-calibration-compare.kotoba.edn — raw vs online-recalibrated."
                             ";; Bias from PAST residuals only (leak-free); apply_correction from"
                             ";; cells/online_update. PIT-mean→0.5 = bias removed. DERIVED :representative."
                             ";; G10-gated for live promotion. ADR-2606051800."
                             ""
                             "["])]
            (doseq [m (sort methods)]
              (let [raw (backtest-rolling rows m)
                    cal (backtest-calibrated rows m)]
                (println (str "  " m ":"))
                (println (str "    raw        CRPS=" (get raw "mean_crps")
                              "  PIT-mean=" (py-round-n (get (get raw "calibration") "pit_mean") 3)
                              "  dev=" (py-round-n (get (get raw "calibration") "deviation") 3)))
                (println (str "    calibrated CRPS=" (get cal "mean_crps")
                              "  PIT-mean=" (py-round-n (get (get cal "calibration") "pit_mean") 3)
                              "  dev=" (py-round-n (get (get cal "calibration") "deviation") 3)))
                (swap! lines conj
                       (str " {:fc.calib/method :" m
                            " :fc.calib/raw-crps " (get raw "mean_crps")
                            " :fc.calib/cal-crps " (get cal "mean_crps")
                            " :fc.calib/raw-pit-mean " (py-round-n (get (get raw "calibration") "pit_mean") 4)
                            " :fc.calib/cal-pit-mean " (py-round-n (get (get cal "calibration") "pit_mean") 4)
                            " :fc.calib/raw-deviation " (py-round-n (get (get raw "calibration") "deviation") 4)
                            " :fc.calib/cal-deviation " (py-round-n (get (get cal "calibration") "deviation") 4)
                            " :fc.calib/sourcing :representative}"))))
            (swap! lines conj "]")
            (when (.contains args "--out")
              (let [outdir (io/file (nth args (inc (.indexOf args "--out"))))]
                (.mkdirs outdir)
                (spit (io/file outdir "chokepoint-calibration-compare.kotoba.edn")
                      (str (str/join "\n" @lines) "\n"))))))

        :else
        (let [target-at (Long/parseLong (nth args (inc (.indexOf args "--at"))))
              fcs (forecast-trail rows target-at method)]
          (when (.contains args "--out")
            (let [outdir (io/file (nth args (inc (.indexOf args "--out"))))]
              (.mkdirs outdir)
              (spit (io/file outdir "chokepoint-forecast.kotoba.edn")
                    (emit-forecast-edn fcs target-at method))))
          (let [scored (filterv #(contains? % "crps") fcs)]
            (println (str "mitooshi forecast @ target=" target-at " (" method "): "
                          (count fcs) " series forecast, "
                          (count scored) " scored leak-free against the realized obs"))
            (doseq [r fcs]
              (let [fc (get r "forecast")
                    tail (if (contains? r "crps")
                           (str "  CRPS " (get r "crps") " vs climatology " (get r "climatology_crps")
                                " (skill " (get r "skill") ")")
                           "  (no realized obs yet)")]
                (println (str "  " (get r "series") ": N(μ=" (:mean fc) ", σ=" (:sd fc)
                              ") info-as-of=" (:info-as-of fc) tail))))))))))

(when (= *file* (System/getProperty "babashka.file"))
  (apply main *command-line-args*))
