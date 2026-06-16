(ns rasen.methods.coverage-report
  "rasen 螺旋 — public-genetics COVERAGE report (ADR-2606101000).
  1:1 Clojure port of `methods/coverage_report.py`.

  Honest coverage measurement of the genome graph: how much of the target space the seed
  covers — by external denominator (genes, ClinVar variants, dbSNP), by inheritance mode, by
  clinical-significance spread, by taxon, by population-aggregate, and by pathway — and a gap
  map naming what is thin/missing.

  NOT a completeness claim: coverage of *all* genes/variants is ~0 by design (a bounded
  :representative seed). This makes the real, useful coverage (the well-characterised
  clinically-actionable backbone) measurable, and names the next wave's targets.

  House style: Python ':…' keyword strings stay strings; pure fns; reuses rasen.methods.analyze
  (load-graph / read-edn / load-file*). File I/O only at the #?(:clj) edge."
  (:require [clojure.string :as str]
            [rasen.methods.analyze :as analyze]
            #?(:clj [clojure.java.io :as io])))

;; honest external denominators
(def gene-denom
  [["Human protein-coding genes (~)" 20000]
   ["HGNC named genes (~)" 43000]])
(def variant-denom
  [["ClinVar submitted variants (~)" 3500000]
   ["ClinVar P/LP variants (~)" 800000]
   ["dbSNP variants (~)" 1100000000]])

(def inheritance [":AD" ":AR" ":XL" ":mitochondrial" ":complex" ":somatic" ":trait"])
(def clinsig [":pathogenic" ":likely-pathogenic" ":risk-factor" ":drug-response"
              ":uncertain" ":likely-benign" ":benign" ":protective"])
(def taxa [":homo-sapiens" ":loxodonta" ":oryza-sativa" ":bacteria"])
(def pops [":global" ":AFR" ":AMR" ":EAS" ":EUR" ":SAS"])
(def pathway-src [":GO" ":reactome" ":kegg"])
(def thin 2) ;; a bucket with < THIN members is flagged thin

(defn- lstrip-colon [s] (if (and (string? s) (str/starts-with? s ":")) (subs s 1) s))

(defn- counter
  "Like collections.Counter: {value count} over the seq (nil values are kept, mirroring Python)."
  [coll]
  (reduce (fn [m v] (update m v (fnil inc 0))) {} coll))

(defn- group-thousands
  "Python f-string `{n:,}` thousands-grouped integer."
  [n]
  (let [s (str (long n))
        neg (str/starts-with? s "-")
        digits (if neg (subs s 1) s)
        grouped (->> (reverse digits)
                     (partition-all 3)
                     (map (comp str/join reverse))
                     reverse
                     (str/join ","))]
    (str (when neg "-") grouped)))

(defn- sci2e
  "Python f-string `{x:.2e}` — scientific notation, 2 fraction digits, e+NN / e-NN exponent."
  [x]
  #?(:clj
     (let [d (double x)]
       (if (zero? d)
         "0.00e+00"
         (let [s (format "%.2e" d)]
           ;; Java %.2e → e.g. "5.00e-04"; Python → "5.00e-04" (same), but Java may emit
           ;; a single-digit exponent on some locales — normalise to 2+ digits w/ sign.
           (let [[mant exp] (str/split s #"[eE]")
                 sign (if (str/starts-with? exp "-") "-" "+")
                 mag (-> exp (str/replace #"^[+-]" ""))
                 mag (if (= 1 (count mag)) (str "0" mag) mag)]
             (str mant "e" sign mag)))))
     :cljs (str x)))

(defn report
  "Render the coverage-report markdown (1:1 with coverage_report.report)."
  [nodes edges]
  (let [vals* (vals nodes)
        genes (filterv #(= ":gene" (get % ":genome/kind")) vals*)
        variants (filterv #(= ":variant" (get % ":genome/kind")) vals*)
        phenos (filterv #(= ":phenotype" (get % ":genome/kind")) vals*)
        pops* (filterv #(= ":population" (get % ":genome/kind")) vals*)
        pathways (filterv #(= ":pathway" (get % ":genome/kind")) vals*)
        inh-c (counter (map #(get % ":phenotype/inheritance") phenos))
        taxon-c (counter (map #(get % ":gene/taxon") genes))
        pop-c (counter (map #(get % ":population/code") pops*))
        pw-c (counter (map #(get % ":pathway/source") pathways))
        clinsig-c (counter (keep #(get % ":en/clinsig") edges))
        L (transient [])]
    (conj! L "# rasen 螺旋 — public-genetics coverage report\n")
    (conj! L (str "> Honest denominator: coverage of all genes/variants is ~0 by design (bounded "
                  "seed). This names the clinically-actionable backbone covered and the next-wave "
                  "gaps. PUBLIC reference data only — no individual genotypes (G1).\n"))
    (conj! L (str "**Seed**: " (count genes) " genes · " (count variants) " variants · "
                  (count phenos) " phenotypes · " (count pops*) " populations · "
                  (count pathways) " pathways · " (count edges) " 縁\n"))

    (conj! L "\n## Gene coverage vs denominators\n")
    (conj! L "| denominator | count | seed | fraction |")
    (conj! L "|---|---:|---:|---:|")
    (doseq [[name denom] gene-denom]
      (conj! L (str "| " name " | " (group-thousands denom) " | " (count genes) " | "
                    (sci2e (/ (double (count genes)) denom)) " |")))

    (conj! L "\n## Variant coverage vs denominators\n")
    (conj! L "| denominator | count | seed | fraction |")
    (conj! L "|---|---:|---:|---:|")
    (doseq [[name denom] variant-denom]
      (conj! L (str "| " name " | " (group-thousands denom) " | " (count variants) " | "
                    (sci2e (/ (double (count variants)) denom)) " |")))

    (conj! L "\n## Clinical-significance spread (DISCLOSED facts, not verdicts)\n")
    (conj! L "| category | edges |")
    (conj! L "|:--:|---:|")
    (doseq [cat clinsig]
      (conj! L (str "| " (lstrip-colon cat) " | " (get clinsig-c cat 0) " |")))

    (let [bucket (fn [title keys* cntr]
                   (conj! L (str "\n## " title "\n"))
                   (conj! L "| bucket | count | status |")
                   (conj! L "|---|---:|:--|")
                   (doseq [k keys*]
                     (let [c (get cntr k 0)
                           status (cond (zero? c) "— **MISSING**"
                                        (< c thin) "⚠ thin"
                                        :else "ok")]
                       (conj! L (str "| " (lstrip-colon k) " | " c " | " status " |")))))]
      (bucket "Inheritance-mode coverage" inheritance inh-c)
      (bucket "Taxon coverage (life is broader than humans)" taxa taxon-c)
      (bucket "Population-aggregate coverage" pops pop-c)
      (bucket "Pathway-source coverage" pathway-src pw-c))

    (let [missing (concat
                   (for [b inheritance :when (zero? (get inh-c b 0))] (lstrip-colon b))
                   (for [t taxa :when (zero? (get taxon-c t 0))] (lstrip-colon t))
                   (for [p pops :when (zero? (get pop-c p 0))] (lstrip-colon p))
                   (for [s pathway-src :when (zero? (get pw-c s 0))] (lstrip-colon s)))]
      (conj! L "\n## Gap map — next-wave targets\n")
      (if (seq missing)
        (conj! L (str "Missing buckets: " (str/join ", " missing) "."))
        (conj! L "No fully-missing buckets in the tracked spines (thin buckets still listed above).")))
    (conj! L "\n---\n_rasen 螺旋 · ADR-2606101000 · coverage honesty (G5)._\n")
    (str/join "\n" (persistent! L))))

#?(:clj
   (defn -main
     "CLI entry: analyze a seed EDN graph → out/coverage-report.md (file I/O at the edge)."
     [& argv]
     (let [argv (vec argv)
           here (-> *file* io/file .getParentFile .getParentFile)
           seed (if (and (seq argv) (not (str/starts-with? (first argv) "--")))
                  (io/file (first argv))
                  (io/file here "data" "seed-genome-graph.kotoba.edn"))
           outdir (if (some #{"--out"} argv)
                    (io/file (nth argv (inc (.indexOf argv "--out"))))
                    (io/file here "out"))
           {:keys [nodes edges]} (analyze/load-file* seed)]
       (.mkdirs outdir)
       (spit (io/file outdir "coverage-report.md") (report nodes edges))
       (println (str "rasen coverage → " (io/file outdir "coverage-report.md")))
       0)))
