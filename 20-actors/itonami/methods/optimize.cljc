(ns itonami.methods.optimize
  "itonami 営み — R1 optimization-proposal engine (ADR-2606082300).
  1:1 Clojure port of `methods/optimize.py`.

  Turns the R0 observation KPIs into two CONCRETE, QUANTIFIED improvement proposals — the
  charter-clean form of the FOX \"cut 10% energy\" headline. Both are *proposals to a human /
  Council*, never write-backs (G1), and never reach below the station/line scale (G2).

    1. idle power-down  — recoverable kWh by powering stations down during non-producing
       (idle/down) windows, with a CONSERVATIVE recoverable fraction.
    2. bottleneck relief — raising the weakest station to the 2nd-weakest lifts the whole
       serial line's OEE to the 2nd-weakest value.

  House style: Python ':…' keyword strings stay strings; string-keyed data; pure fns;
  file I/O only at #?(:clj) edges. Float formatting mirrors Python's `{:g}` / `{:.1%}`.
  Reuses itonami.methods.analyze (load-file* / analyze)."
  (:require [clojure.string :as str]
            [itonami.methods.analyze :as analyze]
            #?(:clj [clojure.java.io :as io])))

;; Conservative share of non-producing energy that is actually recoverable by power-down.
;; Representative + documented (G5). NOT a guarantee — the assumption behind the proposal.
(def RECOVERABLE-IDLE-FRACTION 0.7)

(defn- res-stations
  "[s for s in res if not s.startswith('_')] — dict-iteration order."
  [res]
  (filter #(not (str/starts-with? % "_"))
          (or (:itonami.methods.analyze/order (meta res)) (keys res))))

(defn idle-powerdown
  "Recoverable energy from powering down during non-producing windows."
  ([res] (idle-powerdown res RECOVERABLE-IDLE-FRACTION))
  ([res recoverable]
   (let [sids (vec (res-stations res))
         per (reduce (fn [m s] (assoc m s (* (get-in res [s "idle_kwh"]) recoverable))) {} sids)
         total-idle (reduce + 0.0 (map #(get-in res [% "idle_kwh"]) sids))
         total-kwh (reduce + 0.0 (map #(get-in res [% "kwh"]) sids))
         recoverable-kwh (* total-idle recoverable)]
     {"per_station" per
      "recoverable_kwh" recoverable-kwh
      "line_kwh" total-kwh
      "energy_reduction_frac" (if (> total-kwh 0) (/ recoverable-kwh total-kwh) 0.0)
      "recoverable_fraction_assumed" recoverable
      ;; the single station with the biggest power-down win (where to start)
      "top_station" (when (seq sids)
                      (reduce (fn [best s] (if (> (get per s) (get per best)) s best))
                              (first sids) (rest sids)))})))

(defn bottleneck-relief
  "Lifting the worst station to the 2nd-worst raises the whole serial line's OEE."
  [res]
  (let [sids (vec (res-stations res))]
    (if (< (count sids) 2)
      {"current_line_oee" (get-in res ["_line" "oee"])
       "target_line_oee" (get-in res ["_line" "oee"])
       "oee_uplift_frac" 0.0 "bottleneck" nil "lifts_to" nil}
      (let [by-oee (sort-by (fn [s] (get-in res [s "oee"])) sids)
            worst (nth by-oee 0)
            second (nth by-oee 1)
            cur (get-in res [worst "oee"])
            target (get-in res [second "oee"])]
        {"current_line_oee" cur
         "target_line_oee" target
         "oee_uplift_frac" (if (> cur 0) (/ (- target cur) cur) 0.0)
         "bottleneck" worst
         "lifts_to" second
         ;; relief is availability/performance recovery, never sub-takt speed-up (G2)
         "relief_levers" ["availability (remove unplanned stops)"
                          "performance (reduce minor stops / idle), within takt"]}))))

(defn optimize
  ([stations ticks] (optimize stations ticks nil))
  ([stations ticks res]
   (let [res (or res (analyze/analyze stations ticks))]
     {"idle_powerdown" (idle-powerdown res)
      "bottleneck_relief" (bottleneck-relief res)})))

(defn- label
  [stations sid]
  (if sid (get-in stations [sid ":station/label"] sid) "—"))

;; ── float formatting (Python f-string parity: HALF_EVEN over the exact double) ──
(defn- fmt-f [x n]
  (-> (java.math.BigDecimal. (double x))
      (.setScale (int n) java.math.RoundingMode/HALF_EVEN)
      (.toPlainString)))
(defn- fmt-pct [x] (str (fmt-f (* 100.0 (double x)) 1) "%"))
(defn- fmt-pct0 [x] (str (fmt-f (* 100.0 (double x)) 0) "%"))
(defn- fmt0 [x] (fmt-f x 0))
(defn- fmt1 [x] (fmt-f x 1))

(defn- fmt-g
  "Mirror Python's `{v:g}` for moderate-magnitude doubles."
  [v]
  (let [d (double v)]
    (if (and (== d (Math/rint d)) (< (Math/abs d) 1e15))
      (str (long d))
      (let [s (format "%.6g" d)]
        (if (str/includes? s ".")
          (-> s (str/replace #"0+$" "") (str/replace #"\.$" ""))
          s)))))

(defn report-md
  [stations opt]
  (let [e (get opt "idle_powerdown")
        b (get opt "bottleneck_relief")
        L (transient [])
        P (fn [s] (conj! L s))]
    (P "# itonami 営み — R1 optimization proposals (to a human / Council)\n")
    (P (str "> **G1 — these are PROPOSALS with estimates, never write-backs.** itonami does "
            "not actuate. **G2** — relief targets availability/performance + energy waste, "
            "NEVER sub-takt speed-up or labor intensification. Energy fraction is a documented "
            "assumption, not a guarantee (G5).\n"))
    (P "\n## 1 · Idle power-down (energy reduction)\n")
    (P (str "Recoverable energy by powering down during non-producing windows, assuming "
            "**" (fmt-pct0 (get e "recoverable_fraction_assumed")) "** of non-producing draw is cuttable:\n"))
    (P (str "- **" (fmt1 (get e "recoverable_kwh")) " kWh** recoverable of "
            (fmt0 (get e "line_kwh")) " kWh → **"
            (fmt-pct (get e "energy_reduction_frac")) "** line energy reduction"))
    (P (str "- start at **" (label stations (get e "top_station")) "** ("
            (fmt1 (get-in e ["per_station" (get e "top_station")] 0)) " kWh recoverable)"))
    (P "\n## 2 · Bottleneck relief (throughput, within takt)\n")
    (P (str "- bottleneck **" (label stations (get b "bottleneck")) "** OEE "
            (fmt-pct (get b "current_line_oee")) " → lifting it to **"
            (label stations (get b "lifts_to")) "** raises line OEE to **"
            (fmt-pct (get b "target_line_oee")) "** (**+"
            (fmt-pct (get b "oee_uplift_frac")) "**)"))
    (P (str "- levers (G2-safe): " (str/join ", " (get b "relief_levers"))))
    (P (str "\n---\n_itonami 営み R1 · ADR-2606082300 · proposals-only · no-actuation · "
            "efficiency-not-intensification._\n"))
    (str/join "\n" (persistent! L))))

(defn emit-proposals
  "Transient EAVT proposal datoms (computed on read, never durable — G3)."
  ([opt] (emit-proposals opt 1))
  ([opt tx]
   (let [e (get opt "idle_powerdown")
         b (get opt "bottleneck_relief")
         L (transient [";; itonami R1 optimization proposals — TRANSIENT (:bond/is-transient true), G1/G3."
                       "["])]
     (conj! L (str "[:line.sarutahiko-a :ops/proposal-energy-reduction-frac "
                   (fmt-g (get e "energy_reduction_frac")) " " tx " :derived] ;; :bond/is-transient true"))
     (conj! L (str "[:line.sarutahiko-a :ops/proposal-recoverable-kwh "
                   (fmt-g (get e "recoverable_kwh")) " " tx " :derived] ;; :bond/is-transient true"))
     (when (get b "bottleneck")
       (conj! L (str "[:line.sarutahiko-a :ops/proposal-bottleneck " (get b "bottleneck")
                     " " tx " :derived] ;; :bond/is-transient true"))
       (conj! L (str "[:line.sarutahiko-a :ops/proposal-oee-uplift-frac "
                     (fmt-g (get b "oee_uplift_frac")) " " tx " :derived] ;; :bond/is-transient true")))
     (conj! L "]")
     (str (str/join "\n" (persistent! L)) "\n"))))

#?(:clj
   (defn -main
     [& argv]
     (let [argv (vec argv)
           here (-> *file* io/file .getParentFile .getParentFile)
           seed (if (and (seq argv) (not (str/starts-with? (first argv) "--")))
                  (io/file (first argv))
                  (io/file here "data" "seed-factory-ops.kotoba.edn"))
           outdir (if (some #{"--out"} argv)
                    (io/file (nth argv (inc (.indexOf argv "--out"))))
                    (io/file here "out"))
           tx (if (some #{"--tx"} argv)
                (Long/parseLong (nth argv (inc (.indexOf argv "--tx")))) 1)
           {:keys [stations ticks]} (analyze/load-file* seed)
           opt (optimize stations ticks)]
       (.mkdirs outdir)
       (spit (io/file outdir "optimization-proposals.md") (report-md stations opt))
       (spit (io/file outdir "itonami-proposals.kotoba.edn") (emit-proposals opt tx))
       0)))
