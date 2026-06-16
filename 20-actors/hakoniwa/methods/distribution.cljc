;; ported from 20-actors/hakoniwa/methods/distribution.py — real port replacing the unit_refactor
;; stage-0 "TODO: port-failed" stubs. NS fixed root.hakoniwa.* → hakoniwa.* (20-actors source root).
(ns hakoniwa.methods.distribution
  "distribution.py — hakoniwa 箱庭 ensemble → outcome DISTRIBUTION + mitooshi-shaped forecast record.
  1:1 Clojure port of `methods/distribution.py` (ADR-2606111500).

  Turns the raw replica ensemble (simulate/ensemble) into the ONLY thing hakoniwa asserts: a
  DISTRIBUTION over the population statistic — quantiles + histogram — and a forecast record
  shaped for mitooshi 見通し proper-scoring.

  G2 — DISTRIBUTION-ONLY: :forecast/point-asserted is structurally false; NO :forecast/point.
  G3 — NON-STEERING: :forecast/use is resilience-only (a breach throws).
  G7 — leak-free as-of carried on the record.

  House style: string-keyed maps, ':kw' strings; pure fns. The Python `__main__` file-writer
  is omitted (the report-md / forecast-edn fns are the API)."
  (:require [clojure.string :as str]
            [hakoniwa.methods.world :as w]))

;; RESILIENCE-only use enum (G3). Steering/speculation uses are NOT members → unrepresentable.
(def allowed-use #{":resilience" ":preparedness" ":robustness" ":research"})
(def ^:private hist-bins 10)

(defn quantile
  "Linear-interpolated quantile of an already-sorted vector (mirrors quantile)."
  ^double [sorted-vals ^double q]
  (let [n (count sorted-vals)]
    (cond
      (zero? n) 0.0
      (= n 1) (double (nth sorted-vals 0))
      :else (let [pos (* q (dec n))
                  lo (int pos)
                  frac (- pos lo)]
              (if (>= (inc lo) n)
                (double (nth sorted-vals (dec n)))
                (+ (* (double (nth sorted-vals lo)) (- 1 frac))
                   (* (double (nth sorted-vals (inc lo))) frac)))))))

(defn histogram
  ([vals] (histogram vals hist-bins))
  ([vals bins]
   (reduce (fn [counts v]
             (let [b (min (dec bins) (max 0 (int (* (double v) bins))))]
               (update counts b inc)))
           (vec (repeat bins 0))
           vals)))

(defn distribution
  "Replica outcomes → distribution map (mirrors distribution)."
  [results]
  (let [s (vec (sort results))
        n (count s)
        mean (if (pos? n) (/ (reduce + 0.0 s) n) 0.0)
        var (if (pos? n) (/ (reduce + 0.0 (map (fn [v] (Math/pow (- (double v) mean) 2)) s)) n) 0.0)]
    {"n" n
     "mean" mean
     "stdev" (Math/sqrt var)
     "quantiles" {":p10" (quantile s 0.10) ":p25" (quantile s 0.25)
                  ":p50" (quantile s 0.50) ":p75" (quantile s 0.75)
                  ":p90" (quantile s 0.90)}
     "min" (if (pos? n) (double (nth s 0)) 0.0)
     "max" (if (pos? n) (double (nth s (dec n))) 0.0)
     "histogram" (histogram s)}))

(defn forecast-record
  "mitooshi-shaped forecast record — DISTRIBUTION-ONLY (G2), resilience-USE-only (G3)."
  ([nodes dist meta as-of] (forecast-record nodes dist meta as-of ":preparedness"))
  ([nodes dist meta as-of use]
   (when-not (contains? allowed-use use)
     (throw (ex-info (str "G3 violation: :forecast/use " use " is not a resilience use "
                          (sort allowed-use) "; steering/speculation is unrepresentable")
                     {:use use})))
   (let [outs (w/outcomes nodes)
         target (if (seq outs)
                  (let [o (val (first outs))]
                    (get o ":sim/label" (get o ":sim/id" "outcome")))
                  "outcome")]
     {":forecast/actor" ":hakoniwa"
      ":forecast/target" target
      ":forecast/kind" ":distribution"
      ":forecast/point-asserted" false
      ":forecast/horizon-steps" (get meta "steps")
      ":forecast/replicas" (get meta "replicas")
      ":forecast/quantiles" (get dist "quantiles")
      ":forecast/histogram" (get dist "histogram")
      ":forecast/mean" (get dist "mean")
      ":forecast/stdev" (get dist "stdev")
      ":forecast/use" use
      ":forecast/as-of" as-of
      ":forecast/sourced-from" ":hakoniwa-synthetic-ensemble"})))

;; ── EDN serialisation (mirrors Python _fmt_edn with %g floats) ───────────────────────────────
(defn- fmt-g
  "Python-`%g`-equivalent float formatting: up to 6 significant digits, trailing zeros stripped."
  [^double v]
  (if (and (== v (Math/rint v)) (not (Double/isInfinite v)) (<= (Math/abs v) 1.0e15))
    (str (long v))
    (let [s (format "%.6g" v)]
      ;; strip trailing zeros in the fractional/mantissa part like %g does
      (if (str/includes? s "e")
        (let [[m e] (str/split s #"e")
              m (if (str/includes? m ".") (str/replace (str/replace m #"0+$" "") #"\.$" "") m)]
          (str m "e" e))
        (if (str/includes? s ".")
          (str/replace (str/replace s #"0+$" "") #"\.$" "")
          s)))))

(defn- fmt-edn [v]
  (cond
    (true? v) "true"
    (false? v) "false"
    (nil? v) "nil"
    (and (string? v) (str/starts-with? v ":")) v
    (string? v) (str "\"" (-> v (str/replace "\\" "\\\\") (str/replace "\"" "\\\"")) "\"")
    (and (number? v) (not (integer? v))) (fmt-g (double v))
    (map? v) (str "{" (str/join " " (map (fn [[k val]] (str k " " (fmt-edn val))) v)) "}")
    (sequential? v) (str "[" (str/join " " (map fmt-edn v)) "]")
    :else (str v)))

(defn forecast-edn [rec]
  (let [body (str/join "\n " (map (fn [[k v]] (str k " " (fmt-edn v))) rec))]
    (str ";; hakoniwa 箱庭 — GENERATED mitooshi-shaped forecast record (ADR-2606111500).\n"
         ";; DISTRIBUTION-ONLY (G2): no :forecast/point field exists. resilience-USE-only (G3).\n"
         "{" body "}\n")))

(defn report-md [nodes dist meta as-of]
  (let [outs (w/outcomes nodes)
        target (if (seq outs) (get (val (first outs)) ":sim/label" "outcome") "outcome")
        q (get dist "quantiles")
        L (transient [])]
    (conj! L "# hakoniwa 箱庭 — forward-simulation outcome DISTRIBUTION (never a point)\n")
    (conj! L (str "> **G2 — DISTRIBUTION-ONLY.** hakoniwa asserts a distribution over possible "
                  "futures, never a single foretold outcome (非終末論). **G1 — every agent is a "
                  "SYNTHETIC latent persona**, not a real person (no PII). **G3 — routed to "
                  "RESILIENCE / preparedness**, never to trading, targeting, or persuasion.\n"))
    (conj! L (str "**Scenario**: " target))
    (conj! L (str "**Box**: " (get meta "personas") " synthetic personas · " (get meta "edges") " 縁 · "
                  (get meta "steps") " steps × " (get meta "replicas") " replicas (seed " (get meta "seed")
                  ", jitter " (get meta "jitter") ") · as-of " as-of "\n"))
    (conj! L "\n## Outcome distribution — town-wide mean adoption stance\n")
    (conj! L "| statistic | value |")
    (conj! L "|---|---:|")
    (conj! L (format "| mean | %.4f |" (double (get dist "mean"))))
    (conj! L (format "| stdev | %.4f |" (double (get dist "stdev"))))
    (conj! L (format "| p10 | %.4f |" (double (get q ":p10"))))
    (conj! L (format "| p25 | %.4f |" (double (get q ":p25"))))
    (conj! L (format "| **p50 (median, a quantile — NOT 'the prediction')** | %.4f |" (double (get q ":p50"))))
    (conj! L (format "| p75 | %.4f |" (double (get q ":p75"))))
    (conj! L (format "| p90 | %.4f |" (double (get q ":p90"))))
    (conj! L (format "| min / max | %.4f / %.4f |" (double (get dist "min")) (double (get dist "max"))))
    (conj! L "\n## Histogram (10 bins over [0,1])\n")
    (conj! L "| bin | range | count |")
    (conj! L "|---:|---|---:|")
    (doseq [[b c] (map-indexed vector (get dist "histogram"))]
      (conj! L (format "| %d | [%.1f, %.1f) | %d |" b (/ b 10.0) (/ (+ b 1) 10.0) c)))
    (conj! L "\n## Handoff to mitooshi 見通し\n")
    (conj! L (str "_This distribution is handed to mitooshi (ADR-2606051800) as a "
                  "`:forecast/kind :distribution` record (`:forecast/point-asserted false`, "
                  "`:forecast/use :preparedness`) for leak-free proper-scoring against the realised "
                  "outcome. hakoniwa generates the ensemble; mitooshi scores the skill._\n"))
    (conj! L (str "\n---\n_hakoniwa 箱庭 · ADR-2606111500 · synthetic-persona forward simulation · "
                  "distribution-only · resilience-routed · transparent (相互監視). Live large-swarm "
                  "runs + any social emission are G8/Council-gated._\n"))
    (str/join "\n" (persistent! L))))
