#!/usr/bin/env bb
;; Working Clojure (babashka) port of methods/analyze.py.
(ns mitooshi.methods.analyze
  "mitooshi 見通し — forecasting-observatory backtest analyzer.

  ADR-2606051800. Reads a kotoba-EDN forecasting graph (:series/* :obs/* :forecast/*
  :fc.model/* :baseline/*) and emits:

    1. an aggregate-first scorecard (out/scorecard.md): per-model mean CRPS / log-score,
       calibration (PIT mean + deviation), and SKILL vs the climatology + persistence
       baselines.
    2. the derived score datoms (out/forecast-scorecard.kotoba.edn), flagged :derived.

  Uses clojure.edn/read-string (real EDN keywords) and converts keyword keys/values to
  their ':ns/name' string representations so the pipeline stays string-keyed (matching the
  Python port's string-key convention). Nested maps (quantiles, probs) preserve their own
  key types (numeric / string).

  Constitutional invariants: G1 G2 G5 G12 — see mitooshi CLAUDE.md."
  (:require [clojure.java.io :as io]
            [clojure.edn :as edn]
            [clojure.string :as str]
            [mitooshi.methods.score :as score]))

(def ^:private this-file *file*)
(defn- actor-root [] (-> this-file io/file .getAbsoluteFile .getParentFile .getParentFile))

;; ── EDN keyword helpers (persist.clj / forecast.clj pattern) ─────────────────
(defn- kw->str
  "Clojure keyword :ns/name → string \":ns/name\". Non-keywords pass through."
  [k]
  (if (keyword? k)
    (str ":" (if (namespace k) (str (namespace k) "/" (name k)) (name k)))
    k))

(defn- edn-val->pipeline
  "Convert a value from clojure.edn space to the string-keyed pipeline convention.
  - keyword → \":ns/name\" string
  - map     → string-keyed map (keys converted, values recursed)
  - vector  → vector with values recursed
  - others  → unchanged (numbers, strings, booleans, nil)"
  [v]
  (cond
    (keyword? v) (kw->str v)
    (map? v) (into {} (map (fn [[k vv]] [(kw->str k) (edn-val->pipeline vv)]) v))
    (vector? v) (mapv edn-val->pipeline v)
    (seq? v) (mapv edn-val->pipeline v)
    :else v))

(defn load-edn
  "Read a kotoba-EDN file via clojure.edn/read-string and convert to the string-keyed
  pipeline representation. Real keywords become ':ns/name' strings; nested maps/vectors
  are recursed. Returns a vector of string-keyed record maps."
  [path]
  (let [raw (edn/read-string (slurp (io/file path)))]
    (mapv edn-val->pipeline raw)))

;; ── float formatting (HALF_EVEN on the exact double, matching Python {x:.Nf}) ──
(defn- fmt-fixed
  "Python f\"{x:.Nf}\" — fixed-point with HALF_EVEN rounding on the exact double value."
  [x n]
  (-> (java.math.BigDecimal. (double x))
      (.setScale (int n) java.math.RoundingMode/HALF_EVEN)
      .toPlainString))

(defn- py-round
  "Python round(x) → nearest integer, HALF_EVEN, as a long."
  [x]
  (-> (java.math.BigDecimal. (double x))
      (.setScale 0 java.math.RoundingMode/HALF_EVEN)
      .longValueExact))

(defn- fmt-width
  "Python f\"{x:4.0f}\" — width 4, 0 decimals, HALF_EVEN, right-justified, space-padded."
  [x width]
  (let [s (fmt-fixed x 0)]
    (str (apply str (repeat (max 0 (- width (count s))) " ")) s)))

(defn- _fmt [x] (if (nil? x) "n/a" (fmt-fixed x 4)))

;; ── metric-aware baselines ────────────────────────────────────────────────────
(defn- empirical-quantiles
  "_empirical_quantiles: linear-interpolated empirical quantiles at the given levels."
  [history levels]
  (let [h (vec (sort history))
        n (count h)]
    (reduce
     (fn [out tau]
       (if (= n 1)
         (assoc out tau (h 0))
         (let [idx (* tau (- n 1))
               lo (int idx)
               hi (min (+ lo 1) (- n 1))]
           (assoc out tau (+ (h lo) (* (- idx lo) (- (h hi) (h lo))))))))
     {} levels)))

(defn- class-freqs
  "_class_freqs: empirical class frequencies {class freq}."
  [classes]
  (let [n (count classes)
        counts (reduce (fn [m c] (update m c (fnil inc 0))) {} classes)]
    (into {} (map (fn [[k v]] [k (/ (double v) n)]) counts))))

;; ── backtest ──────────────────────────────────────────────────────────────────
(defn- lstrip-colon [s]
  (if (and (string? s) (str/starts-with? s ":")) (subs s 1) s))

(defn- f->double [v] (double v))

(defn backtest
  "Port of analyze.backtest. Returns {\"series\" {sid rec} \"models\" {mid rec} \"cards\" [..]}.
  Cards are sorted by model id (Python sorted(per_model.items()))."
  [records]
  (let [records (vec records)
        series  (reduce (fn [m r] (if (contains? r ":series/id")
                                    (assoc m (get r ":series/id") r) m))
                        {} records)
        obs      (filterv #(contains? % ":obs/id") records)
        forecasts (filterv #(contains? % ":forecast/id") records)
        models   (reduce (fn [m r] (if (contains? r ":fc.model/id")
                                     (assoc m (get r ":fc.model/id") r) m))
                         {} records)
        ;; index full observations by series, sorted by observed-at
        by-series (reduce (fn [m o] (update m (get o ":obs/series") (fnil conj []) o))
                          {} obs)
        by-series (reduce-kv (fn [m k v]
                               (assoc m k (vec (sort-by #(get % ":obs/observed-at") v))))
                             {} by-series)
        ;; fold forecasts into per-model accumulators
        per-model
        (reduce
         (fn [pm fc]
           (let [sid    (get fc ":forecast/series")
                 mid    (get fc ":forecast/model" "?")
                 info   (get fc ":forecast/info-as-of")
                 target (get fc ":forecast/target-at")
                 dk     (lstrip-colon (get fc ":forecast/dist-kind"))
                 use    (lstrip-colon (get fc ":forecast/use" ":resilience"))
                 point  (boolean (get fc ":forecast/point-asserted" false))
                 hit    (first (filter #(= (get % ":obs/observed-at") target)
                                       (get by-series sid [])))]
             (if (nil? hit)
               pm
               (let [seen (filterv #(<= (get % ":obs/observed-at") info)
                                   (get by-series sid []))
                     m0   (get pm mid {"dist" dk "metric" "" "primary" [] "logscore" []
                                       "pit" [] "base_clim" [] "base_persist" [] "n" 0})
                     [m sc]
                     (cond
                       (= dk "gaussian")
                       (let [y    (f->double (get hit ":obs/value"))
                             f    (score/->forecast (get fc ":forecast/id") "gaussian"
                                                    :info-as-of info
                                                    :mean (f->double (get fc ":forecast/mean"))
                                                    :sd   (f->double (get fc ":forecast/sd"))
                                                    :use use :point-asserted point)
                             sc   (score/score-pair f (score/->observation (str "obs@" target)
                                                                            :observed-at target :value y))
                             hist (mapv #(f->double (get % ":obs/value")) seen)
                             m    (-> m0
                                      (assoc "metric" "CRPS")
                                      (update "primary" conj (get sc "crps"))
                                      (update "logscore" conj (get sc "log_score")))
                             m    (if (>= (count hist) 2)
                                    (let [[cmu csd] (score/climatology-gaussian hist)
                                          [pmu psd] (score/persistence-gaussian hist)]
                                      (-> m
                                          (update "base_clim"    conj (score/gaussian-crps cmu csd y))
                                          (update "base_persist" conj (score/gaussian-crps pmu psd y))))
                                    m)]
                         [m sc])

                       (= dk "quantile")
                       (let [y    (f->double (get hit ":obs/value"))
                             ;; quantile map keys are already numeric doubles after edn-val->pipeline
                             qraw (get fc ":forecast/quantiles")
                             q    (into {} (map (fn [[k v]] [(f->double k) (f->double v)]) qraw))
                             f    (score/->forecast (get fc ":forecast/id") "quantile"
                                                    :info-as-of info :quantiles q
                                                    :use use :point-asserted point)
                             sc   (score/score-pair f (score/->observation (str "obs@" target)
                                                                            :observed-at target :value y))
                             hist (mapv #(f->double (get % ":obs/value")) seen)
                             m    (-> m0
                                      (assoc "metric" "pinball")
                                      (update "primary" conj (get sc "pinball")))
                             m    (if (>= (count hist) 2)
                                    (update m "base_clim" conj
                                            (score/pinball-loss (empirical-quantiles hist (keys q)) y))
                                    m)]
                         [m sc])

                       (= dk "categorical")
                       (let [cls   (get hit ":obs/class" "")
                             ;; probs map keys are already strings after edn-val->pipeline
                             probs (into {} (map (fn [[k v]] [(str k) (f->double v)])
                                                 (get fc ":forecast/probs")))
                             f     (score/->forecast (get fc ":forecast/id") "categorical"
                                                     :info-as-of info :probs probs
                                                     :use use :point-asserted point)
                             sc    (score/score-pair f (score/->observation (str "obs@" target)
                                                                             :observed-at target :cls cls))
                             histc (filterv some?
                                            (map #(get % ":obs/class")
                                                 (filter #(contains? % ":obs/class") seen)))
                             m     (-> m0
                                       (assoc "metric" "Brier")
                                       (update "primary" conj (get sc "brier"))
                                       (update "logscore" conj (get sc "log_score")))
                             m     (if (seq histc)
                                     (update m "base_clim" conj
                                             (score/brier-score (class-freqs histc) cls))
                                     m)]
                         [m sc])

                       (= dk "ensemble")
                       (let [y       (f->double (get hit ":obs/value"))
                             members (mapv f->double (get fc ":forecast/members"))
                             f       (score/->forecast (get fc ":forecast/id") "ensemble"
                                                       :info-as-of info :members members
                                                       :use use :point-asserted point)
                             sc      (score/score-pair f (score/->observation (str "obs@" target)
                                                                               :observed-at target :value y))
                             hist    (mapv #(f->double (get % ":obs/value")) seen)
                             m       (-> m0
                                         (assoc "metric" "CRPS")
                                         (update "primary" conj (get sc "crps")))
                             m       (if (>= (count hist) 2)
                                       (update m "base_clim" conj (score/ensemble-crps hist y))
                                       m)]
                         [m sc])

                       :else [nil nil])]
                 (if (nil? m)
                   pm
                   (assoc pm mid (-> m
                                     (update "pit" conj (get sc "pit"))
                                     (update "n" inc))))))))
         {}
         forecasts)
        cards
        (mapv
         (fn [mid]
           (let [m             (get per-model mid)
                 n             (get m "n")
                 mean-primary  (/ (reduce + 0.0 (get m "primary")) n)
                 ls            (get m "logscore")
                 mean-ls       (when (seq ls) (/ (reduce + 0.0 ls) (count ls)))
                 calib         (score/calibration-summary (get m "pit"))
                 bc            (get m "base_clim")
                 bp            (get m "base_persist")
                 skill-clim    (when (seq bc)
                                 (score/skill-score mean-primary
                                                    (/ (reduce + 0.0 bc) (count bc))))
                 skill-persist (when (seq bp)
                                 (score/skill-score mean-primary
                                                    (/ (reduce + 0.0 bp) (count bp))))
                 skilled       (if (= (get m "dist") "gaussian")
                                 (boolean (and skill-clim (> skill-clim 0)
                                               skill-persist (> skill-persist 0)))
                                 (boolean (and (some? skill-clim) (> skill-clim 0))))]
             {"model"               mid
              "name"                (get (get models mid {}) ":fc.model/name" mid)
              "dist"                (get m "dist")
              "metric"              (get m "metric")
              "n"                   n
              "mean_primary"        mean-primary
              "mean_logscore"       mean-ls
              "pit_mean"            (get calib "pit_mean")
              "calib_deviation"     (get calib "deviation")
              "pit_hist"            (get calib "hist")
              "skill_vs_climatology"  skill-clim
              "skill_vs_persistence"  skill-persist
              "skilled"             skilled}))
         (sort (keys per-model)))]
    {"series" series "models" models "cards" cards}))

;; ── render ────────────────────────────────────────────────────────────────────
(defn render-md
  "1:1 with analyze.render_md."
  [res]
  (let [L (transient
           ["# mitooshi 見通し — forecasting scorecard" ""
            "_Leak-free proper-scoring backtest. Lower CRPS / log-score = better; skill > 0 = beats the baseline._"
            "_All figures :representative (G11). 非終末論: this is a moving record, not a final verdict._" ""])
        series (get res "series")]
    (doseq [[_sid s] (sort-by key series)]
      (conj! L (str "- **series** `" (get s ":series/id") "` — " (get s ":series/name" "") " "
                    "(" (get s ":series/kind" "") ", " (get s ":series/unit" "")
                    ", source-class " (get s ":series/source-class" "") ")")))
    (conj! L "")
    (conj! L "## Per-model scorecard")
    (conj! L "")
    (conj! L "| model | dist | n | metric | mean score | PIT mean | calib dev | skill vs clim | skill vs persist | skilled? |")
    (conj! L "|---|---|---|---|---|---|---|---|---|---|")
    (doseq [c (get res "cards")]
      (conj! L (str "| " (get c "name") " | " (get c "dist") " | " (get c "n")
                    " | " (get c "metric") " | " (_fmt (get c "mean_primary"))
                    " | " (_fmt (get c "pit_mean"))
                    " | " (_fmt (get c "calib_deviation"))
                    " | " (_fmt (get c "skill_vs_climatology"))
                    " | " (_fmt (get c "skill_vs_persistence"))
                    " | " (if (get c "skilled") "✅" "❌ (honest)") " |")))
    (conj! L "")
    (conj! L "## Reading this")
    (conj! L "- **mean score** is a PROPER scoring rule (CRPS / pinball / Brier) — the distance between the forecast distribution and the realized fact; lower = better; it is the model error.")
    (conj! L "- **PIT mean ≈ 0.5 + low calib-deviation** = the forecast's stated uncertainty matches reality (calibrated).")
    (conj! L "- **skilled** is true ONLY when the model beats BOTH climatology and persistence (G12). An honest ❌")
    (conj! L "  means: keep the baseline; do not promote (calibration_gate would refuse, G7/G12).")
    (conj! L "- The residuals feeding online_update are exactly `y − mean` per forecast; that is what corrects the weights.")
    (conj! L "")
    (str/join "\n" (persistent! L))))

(defn render-datoms
  "1:1 with analyze.render_datoms."
  [res]
  (let [L (transient
           [";; forecast-scorecard.kotoba.edn — DERIVED (:fc.score/derived true). Do NOT re-ingest as fact."
            ";; ADR-2606051800 · generated by methods/analyze.py" "" "["])]
    (doseq [c (get res "cards")]
      (conj! L (str " {:fc.score/id \"score-" (get c "model") "\""
                    " :fc.score/model \"" (get c "model") "\""
                    " :fc.score/metric \"" (get c "metric") "\""
                    " :fc.score/value " (fmt-fixed (get c "mean_primary") 6)
                    " :fc.score/pit " (fmt-fixed (get c "pit_mean") 6)
                    " :fc.score/skill "
                    (if (nil? (get c "skill_vs_climatology"))
                      "nil"
                      (fmt-fixed (get c "skill_vs_climatology") 6))
                    " :fc.model/skilled " (if (get c "skilled") "true" "false")
                    " :fc.score/derived true}")))
    (conj! L "]")
    (str (str/join "\n" (persistent! L)) "\n")))

(defn render-reliability
  "1:1 with analyze.render_reliability — text reliability diagram per model."
  [res]
  (let [L (transient
           ["# mitooshi 見通し — reliability diagrams (PIT calibration)" ""
            "_PIT ~ Uniform(0,1) ⇔ calibrated. Each `#` ≈ 2% of mass; `·` marks the 10% uniform ideal._"
            "_非終末論: a moving record (G7). All figures :representative._"
            "_HONEST small-sample caveat: each model here has only 3–6 PIT points over 10 bins, so the_"
            "_histogram is necessarily lumpy and `deviation` is inflated — a calibration verdict needs_"
            "_a far larger sample (R1, live-gated). The PIT MEAN (≈0.5 ⇔ unbiased) is the reliable signal here._"
            ""])]
    (doseq [c (get res "cards")]
      (let [hist (or (get c "pit_hist") [])]
        (conj! L (str "## " (get c "name") " (" (get c "dist") ") — PIT mean "
                      (fmt-fixed (get c "pit_mean") 3)
                      ", deviation " (fmt-fixed (get c "calib_deviation") 3)))
        (conj! L "")
        (let [ideal       (if (seq hist) (/ 1.0 (count hist)) 0.1)
              ideal-cells (py-round (* ideal 50))]
          (doseq [[i f] (map-indexed vector hist)]
            (let [lo    (/ (double i) (count hist))
                  hi    (/ (double (+ i 1)) (count hist))
                  bar-n (py-round (* f 50))
                  bar   (apply str (repeat bar-n "#"))
                  bar   (if (<= ideal-cells bar-n)
                          (if (> bar-n ideal-cells)
                            (str (subs bar 0 ideal-cells) "·" (subs bar (+ ideal-cells 1)))
                            (str bar "·"))
                          (str bar (apply str (repeat (- ideal-cells bar-n) " ")) "·"))]
              (conj! L (str "`[" (fmt-fixed lo 1) "–" (fmt-fixed hi 1) ")` "
                            bar " " (fmt-width (* f 100) 4) "%")))))
        (let [verdict (if (<= (get c "calib_deviation") 0.4)
                        "calibrated"
                        "MISCALIBRATED → calibration_gate would refuse (G7)")]
          (conj! L "")
          (conj! L (str "→ " verdict))
          (conj! L ""))))
    (str/join "\n" (persistent! L))))

(defn render-reliability-datoms
  "1:1 with analyze.render_reliability_datoms."
  [res]
  (let [L (transient
           [";; reliability.kotoba.edn — DERIVED PIT calibration (:fc.calib/*). Do NOT re-ingest as fact."
            ";; ADR-2606051800 · generated by methods/analyze.py" "" "["])]
    (doseq [c (get res "cards")]
      (let [hist (str/join " " (map #(fmt-fixed % 4) (or (get c "pit_hist") [])))]
        (conj! L (str " {:fc.calib/id \"calib-" (get c "model") "\""
                      " :fc.calib/model \"" (get c "model") "\""
                      " :fc.calib/pit-mean " (fmt-fixed (get c "pit_mean") 6)
                      " :fc.calib/deviation " (fmt-fixed (get c "calib_deviation") 6)
                      " :fc.calib/hist \"[" hist "]\"}"))))
    (conj! L "]")
    (str (str/join "\n" (persistent! L)) "\n")))

;; ── main ─────────────────────────────────────────────────────────────────────
(defn main [& argv]
  (let [args    (vec argv)
        here    (-> this-file io/file .getAbsoluteFile .getParentFile)
        seed    (if (and (seq args) (not (str/starts-with? (first args) "--")))
                  (io/file (first args))
                  (io/file (actor-root) "data" "seed-forecast-graph.kotoba.edn"))
        outdir  (if (some #{"--out"} args)
                  (io/file (nth args (inc (.indexOf args "--out"))))
                  (io/file here "out"))
        records (load-edn seed)
        res     (backtest records)]
    (.mkdirs outdir)
    (spit (io/file outdir "scorecard.md")                      (render-md res))
    (spit (io/file outdir "forecast-scorecard.kotoba.edn")     (render-datoms res))
    (spit (io/file outdir "reliability.md")                    (render-reliability res))
    (spit (io/file outdir "reliability.kotoba.edn")            (render-reliability-datoms res))
    (println (str "mitooshi: scored " (reduce + 0 (map #(get % "n") (get res "cards")))
                  " forecast(s) across " (count (get res "cards")) " model(s)"))
    (doseq [c (get res "cards")]
      (println (str "  " (get c "name") " [" (get c "dist") "]: " (get c "metric") "="
                    (fmt-fixed (get c "mean_primary") 4)
                    " skill_vs_clim=" (_fmt (get c "skill_vs_climatology"))
                    " skill_vs_persist=" (_fmt (get c "skill_vs_persistence"))
                    " skilled=" (if (get c "skilled") "True" "False"))))
    (println (str "  → " (io/file outdir "scorecard.md") " + " (io/file outdir "reliability.md")))
    0))

(when (= *file* (System/getProperty "babashka.file"))
  (apply main *command-line-args*))
