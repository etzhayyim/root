(ns itonami.methods.trend
  "itonami 営み — R7 KPI trend / drift detector (ADR-2606082300).
  1:1 Clojure port of `methods/trend.py`.

  Reads the durable daily ops-KPI snapshots (:opsday/*) and surfaces DRIFT — an OEE slowly
  degrading, scrap creeping up, energy per unit rising — before any single day looks alarming.

    load-history   — read durable :opsday/* snapshots (the as-of series; ground state)
    analyze-trends — per (scope, KPI): first/last, relative change, least-squares slope, and a
                     polarity-aware direction {:improving :flat :degrading} + regression flag

  CONSTITUTIONAL: G1 surfaces drift + recommends; G2 line/station scope only (no worker series);
  G3 non-adjudicating (directions read-time, snapshots are the durable facts).

  House style: Python ':…' keyword strings stay strings; string-keyed data; pure fns;
  file I/O only at #?(:clj) edges. Reuses itonami.methods.analyze (read-edn)."
  (:require [clojure.string :as str]
            [itonami.methods.analyze :as analyze]
            #?(:clj [clojure.java.io :as io])))

;; KPI polarity: true = higher is better, false = lower is better.
;; Insertion order matters for analyze-trends' kpis dict iteration (Python dict order).
(def ^:private kpi-order [":opsday/oee" ":opsday/scrap-rate" ":opsday/energy-per-good"])
(def KPI-POLARITY {":opsday/oee" true ":opsday/scrap-rate" false ":opsday/energy-per-good" false})
(def FLAT-REL-THRESHOLD 0.05)

(defn load-history
  [text]
  (let [forms (analyze/read-edn text)
        recs (vec (filter #(and (map? %) (contains? % ":opsday/day")) forms))]
    (doseq [r recs]
      (doseq [bad [":worker/" ":person/" ":operator/"]]
        (when (some #(str/starts-with? (str %) bad) (keys r))
          (throw (ex-info (str "G2 violation: ops history carries a person/worker series (" bad ")")
                          {:bad bad})))))
    recs))

(defn- slope
  [xs ys]
  (let [n (count xs)]
    (if (< n 2)
      0.0
      (let [mx (/ (reduce + 0.0 xs) n)
            my (/ (reduce + 0.0 ys) n)
            den (reduce + 0.0 (map (fn [x] (Math/pow (- x mx) 2)) xs))]
        (if (zero? den)
          0.0
          (/ (reduce + 0.0 (map (fn [x y] (* (- x mx) (- y my))) xs ys)) den))))))

(defn- direction
  [first last higher-better]
  (let [base (if (not= first 0) (Math/abs (double first)) 1.0)
        rel (/ (- last first) base)]
    (if (< (Math/abs (double rel)) FLAT-REL-THRESHOLD)
      ":flat"
      (let [improving (if higher-better (> rel 0) (< rel 0))]
        (if improving ":improving" ":degrading")))))

(defn analyze-trends
  "Per scope, per KPI: first/last/rel_change/slope/direction/regression."
  [records]
  (let [;; group by scope, preserving first-touch scope order
        [by-scope scope-order]
        (reduce (fn [[bs order] r]
                  (let [sc (get r ":opsday/scope")
                        order (if (contains? bs sc) order (conj order sc))]
                    [(update bs sc (fnil conj []) r) order]))
                [{} []] records)]
    (reduce
     (fn [out scope]
       (let [recs (sort-by #(get % ":opsday/day") (get by-scope scope))
             days (mapv #(double (get % ":opsday/day")) recs)
             kpis (reduce
                   (fn [kpis attr]
                     (let [higher-better (get KPI-POLARITY attr)
                           ys (vec (for [r recs :when (contains? r attr)] (double (get r attr))))]
                       (if (< (count ys) 2)
                         kpis
                         (let [first (nth ys 0)
                               last (nth ys (dec (count ys)))
                               base (if (not= first 0) (Math/abs first) 1.0)
                               dir (direction first last higher-better)]
                           (assoc kpis attr
                                  {"first" first "last" last
                                   "rel_change" (/ (- last first) base)
                                   "slope" (slope (subvec days 0 (count ys)) ys)
                                   "direction" dir
                                   "regression" (= dir ":degrading")})))))
                   {} kpi-order)]
         (assoc out scope kpis)))
     {} scope-order)))

(defn- trend-kpi-order
  "iteration order of a scope's kpis map (subset of kpi-order present)."
  [kpis]
  (filter #(contains? kpis %) kpi-order))

(defn regressions
  "Flat list of [scope kpi rel_change] for every degrading series — the attention list."
  [trends]
  (let [scope-order (or (keys trends) [])
        rows (for [scope (keys trends)
                   attr (trend-kpi-order (get trends scope))
                   :let [t (get-in trends [scope attr])]
                   :when (get t "regression")]
               [scope attr (get t "rel_change")])]
    (vec (sort-by (fn [r] (- (Math/abs (double (nth r 2))))) rows))))

(defn- fmt-g [v]
  (let [d (double v)]
    (if (and (== d (Math/rint d)) (< (Math/abs d) 1e15))
      (str (long d))
      (let [s (format "%.6g" d)]
        (if (str/includes? s ".") (-> s (str/replace #"0+$" "") (str/replace #"\.$" "")) s)))))

(defn- fmt-f [x n]
  (-> (java.math.BigDecimal. (double x))
      (.setScale (int n) java.math.RoundingMode/HALF_EVEN) (.toPlainString)))
(defn- fmt-pct-signed [x]
  (let [s (fmt-f (* 100.0 (double x)) 1)]
    (str (if (and (not (str/starts-with? s "-")) (>= (double x) 0)) "+" "") s "%")))

(defn- short-attr [attr] (last (str/split attr #"/")))
(defn- lstrip-colon [s] (if (str/starts-with? s ":") (subs s 1) s))

(defn report-md
  [trends]
  (let [regs (regressions trends)
        L (transient []) P (fn [s] (conj! L s))]
    (P "# itonami 営み — R7 KPI trend / drift report (as-of trajectory)\n")
    (P (str "> **G1** surfaces drift + recommends attention, never actuates. **G2** line/"
            "station scope only — no worker trajectory. **G3** directions are read-time over "
            "disclosed daily snapshots; the snapshots are the durable as-of facts.\n"))
    (P (str "\n**" (count regs) " degrading series** (attention, worst rel-change first):\n"))
    (doseq [[scope attr rel] regs]
      (P (str "- " scope " · " (short-attr attr) " · " (fmt-pct-signed rel) " over window")))
    (P "\n## All series\n")
    (P "| scope | KPI | first → last | direction |")
    (P "|---|---|---|---|")
    (doseq [scope (sort (keys trends))]
      (doseq [attr (trend-kpi-order (get trends scope))]
        (let [t (get-in trends [scope attr])]
          (P (str "| " scope " | " (short-attr attr) " | " (fmt-g (get t "first")) " → "
                  (fmt-g (get t "last")) " | " (lstrip-colon (get t "direction")) " |")))))
    (P (str "\n---\n_itonami 営み R7 · ADR-2606082300 · trajectory-not-snapshot · "
            "drift-surfacing · recommend-not-actuate · station-scale._\n"))
    (str/join "\n" (persistent! L))))

(defn emit
  "Transient EAVT trend datoms (computed on read, never durable — G3)."
  ([trends] (emit trends 1))
  ([trends tx]
   (let [L (transient [";; itonami R7 KPI trends — TRANSIENT (:bond/is-transient true), G1/G3." "["])]
     (doseq [scope (sort (keys trends))]
       (doseq [attr (trend-kpi-order (get trends scope))]
         (let [t (get-in trends [scope attr])
               s (short-attr attr)]
           (conj! L (str "[" scope " :trend/" s "-direction " (get t "direction")
                         " " tx " :derived] ;; :bond/is-transient true"))
           (when (get t "regression")
             (conj! L (str "[" scope " :trend/" s "-regression true "
                           tx " :derived] ;; :bond/is-transient true"))))))
     (conj! L "]")
     (str (str/join "\n" (persistent! L)) "\n"))))

#?(:clj
   (defn -main
     [& argv]
     (let [argv (vec argv)
           here (-> *file* io/file .getParentFile .getParentFile)
           seed (if (and (seq argv) (not (str/starts-with? (first argv) "--")))
                  (io/file (first argv))
                  (io/file here "data" "seed-ops-history.kotoba.edn"))
           outdir (if (some #{"--out"} argv)
                    (io/file (nth argv (inc (.indexOf argv "--out"))))
                    (io/file here "out"))
           tx (if (some #{"--tx"} argv) (Long/parseLong (nth argv (inc (.indexOf argv "--tx")))) 1)
           records (load-history (slurp seed))
           trends (analyze-trends records)]
       (.mkdirs outdir)
       (spit (io/file outdir "trend-report.md") (report-md trends))
       (spit (io/file outdir "itonami-trends.kotoba.edn") (emit trends tx))
       0)))
